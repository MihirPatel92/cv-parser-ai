import os
import uuid
import time
import asyncio
import aiofiles
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    BackgroundTasks,
    Query,
)
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from typing import Optional

from ..core.dependencies import get_db, get_current_user, get_ai_config
from ..db.database import SessionLocal
from ..db.models import User, UserRole, CVTemplate, Conversion, AIModelConfig
from ..core.config import settings
from ..ai.orchestrator import AIOrchestrator
from ..parsers.pdf_parser import extract_text_from_pdf
from ..parsers.docx_parser import extract_text_from_docx, extract_placeholders_from_docx
from ..formatters.docx_formatter import DocxFormatter
from ..formatters.pdf_formatter import convert_docx_to_pdf

router = APIRouter()


async def process_conversion(conversion_id: str, config: AIModelConfig):
    """Background task: run the full AI conversion pipeline with an isolated DB session."""
    start_time = time.time()

    async with SessionLocal() as db:
        try:
            conv_uuid = uuid.UUID(conversion_id)
        except ValueError:
            print(f"Invalid conversion UUID: {conversion_id}")
            return

        result = await db.execute(select(Conversion).where(Conversion.id == conv_uuid))
        conversion = result.scalars().first()
        if not conversion:
            print(f"Conversion record not found: {conversion_id}")
            return

        try:
            # ── Step 1: Parse the uploaded CV ────────────────────────────────
            cv_path = conversion.source_cv_path
            if cv_path.lower().endswith(".pdf"):
                cv_text = extract_text_from_pdf(cv_path)
            else:
                cv_text = extract_text_from_docx(cv_path)

            if not cv_text or len(cv_text.strip()) < 30:
                raise ValueError(
                    "CV text extraction produced insufficient content. Ensure the uploaded CV contains selectable text."
                )

            # ── Step 2: AI extraction ─────────────────────────────────────────
            orchestrator = AIOrchestrator(config)
            cv_data = await orchestrator.extract_cv_data(cv_text)
            conversion.extracted_cv_data = cv_data
            conversion.ai_model_used = config.model_name

            # ── Step 3: Fetch Template ────────────────────────────────────────
            template = None
            if conversion.template_id:
                template_result = await db.execute(
                    select(CVTemplate).where(CVTemplate.id == conversion.template_id)
                )
                template = template_result.scalars().first()

            if not template:
                raise ValueError("Target CV Template not found in database.")

            # ── Step 4: Format output ─────────────────────────────────────────
            formatter = DocxFormatter()
            out_filename = str(uuid.uuid4())
            out_docx_path = os.path.join(
                settings.UPLOAD_DIR, "outputs", f"{out_filename}.docx"
            )
            out_pdf_path = None

            if template.file_type.lower() == "docx":
                placeholders = extract_placeholders_from_docx(template.file_path)

                if placeholders:
                    # Template has {{placeholders}} — map CV data directly to them
                    mapping = await orchestrator.map_to_placeholders(placeholders, cv_data)
                    conversion.placeholder_mapping = mapping
                    formatter.fill_placeholders(template.file_path, mapping, out_docx_path)
                else:
                    # Template without placeholders — AI mirrors the template structure
                    template_text = extract_text_from_docx(template.file_path)
                    structure = await orchestrator.analyze_template_structure(template_text)
                    section_data = await orchestrator.freeform_map(
                        str(structure), cv_data
                    )
                    formatter.freeform_fill(template.file_path, section_data, out_docx_path)
            else:
                # PDF template: extract structure and mirror
                template_text = extract_text_from_pdf(template.file_path)
                structure = await orchestrator.analyze_template_structure(template_text)
                section_data = await orchestrator.freeform_map(str(structure), cv_data)
                formatter.freeform_fill(None, section_data, out_docx_path)

            # ── Step 5: Convert to PDF if requested ──────────────────────────
            output_format = conversion.output_format.lower()
            if output_format in ("pdf", "both"):
                out_pdf_path = os.path.join(
                    settings.UPLOAD_DIR, "outputs", f"{out_filename}.pdf"
                )
                try:
                    convert_docx_to_pdf(out_docx_path, out_pdf_path)
                except Exception as pdf_err:
                    print(f"⚠️ PDF generation fallback note: {pdf_err}")
                    out_pdf_path = None

            # ── Step 6: Save results ──────────────────────────────────────────
            conversion.output_docx_path = (
                out_docx_path if output_format in ("docx", "both") else None
            )
            conversion.output_pdf_path = out_pdf_path
            conversion.status = "completed"
            conversion.completed_at = datetime.utcnow()
            conversion.processing_time_seconds = round(time.time() - start_time, 2)
            await db.commit()
            print(f"✅ Conversion {conversion_id} completed successfully in {conversion.processing_time_seconds}s")

        except Exception as e:
            conversion.status = "failed"
            conversion.error_message = str(e)
            conversion.processing_time_seconds = round(time.time() - start_time, 2)
            await db.commit()
            print(f"❌ Conversion {conversion_id} failed: {e}")


@router.post("/")
async def create_conversion(
    background_tasks: BackgroundTasks,
    template_id: str = Form(...),
    ai_provider: str = Form("gemini"),
    output_format: str = Form("docx"),
    file: Optional[UploadFile] = File(None),
    cv_file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ai_config: AIModelConfig = Depends(get_ai_config),
):
    """Upload a CV and trigger AI conversion against a selected template."""
    # Handle either field name: 'file' or 'cv_file'
    uploaded_file = file or cv_file
    if not uploaded_file:
        raise HTTPException(
            status_code=422,
            detail="CV file is required. Upload a file with parameter 'file' or 'cv_file'.",
        )

    # Validate file type
    filename = uploaded_file.filename or "cv.pdf"
    filename_lower = filename.lower()
    if not (filename_lower.endswith(".docx") or filename_lower.endswith(".pdf")):
        raise HTTPException(
            status_code=400, detail="Only DOCX and PDF files are accepted."
        )

    # Validate file size
    content = await uploaded_file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413, detail=f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit."
        )

    # Validate output_format
    fmt = output_format.lower()
    if fmt not in ("docx", "pdf", "both"):
        fmt = "docx"

    # Save uploaded CV
    ext = filename_lower.split(".")[-1]
    saved_name = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, "cvs", saved_name)
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)

    # Parse template UUID
    try:
        tmpl_uuid = uuid.UUID(template_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid template ID format")

    # Override config provider if user selected a different one
    if ai_provider != ai_config.provider:
        effective_config = AIModelConfig(
            provider=ai_provider,
            model_name=ai_config.model_name,
            api_key_encrypted=ai_config.api_key_encrypted,
            ollama_base_url=ai_config.ollama_base_url,
            temperature=ai_config.temperature,
            max_tokens=ai_config.max_tokens,
            is_active=True,
        )
    else:
        effective_config = ai_config

    # Create conversion record
    conversion = Conversion(
        recruiter_id=current_user.id,
        template_id=tmpl_uuid,
        source_cv_path=filepath,
        source_cv_filename=filename,
        source_cv_file_type=ext,
        output_format=fmt,
        ai_provider=ai_provider,
        status="processing",
    )
    db.add(conversion)
    await db.commit()
    await db.refresh(conversion)

    # Launch background processing with isolated SessionLocal
    background_tasks.add_task(
        process_conversion, str(conversion.id), effective_config
    )

    return {
        "id": str(conversion.id),
        "status": conversion.status,
        "message": "Conversion started. Poll GET /conversions/{id} for status.",
    }


def conversion_to_dict(c: Conversion, template_name: str = "", recruiter_name: str = "") -> dict:
    has_docx = bool(c.output_docx_path and os.path.exists(c.output_docx_path))
    has_pdf = bool(c.output_pdf_path and os.path.exists(c.output_pdf_path))
    return {
        "id": str(c.id),
        "recruiter_id": str(c.recruiter_id) if c.recruiter_id else None,
        "recruiter_name": recruiter_name or (c.recruiter.full_name if c.recruiter else "Admin"),
        "template_id": str(c.template_id) if c.template_id else None,
        "template_name": template_name or (c.template.name if c.template else "Default Template"),
        "source_cv_filename": c.source_cv_filename,
        "status": c.status,
        "ai_provider": c.ai_provider,
        "ai_model_used": c.ai_model_used,
        "output_format": c.output_format,
        "has_docx": has_docx,
        "has_pdf": has_pdf,
        "error_message": c.error_message,
        "processing_time_seconds": c.processing_time_seconds,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "completed_at": c.completed_at.isoformat() if c.completed_at else None,
    }


@router.get("/")
async def list_conversions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List conversions. Admins see all; recruiters see their own."""
    user_role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if user_role_str in ["super_admin", "admin"]:
        result = await db.execute(
            select(Conversion).order_by(Conversion.created_at.desc())
        )
    else:
        result = await db.execute(
            select(Conversion)
            .where(Conversion.recruiter_id == current_user.id)
            .order_by(Conversion.created_at.desc())
        )
    conversions = result.scalars().all()

    # Pre-fetch template names
    template_ids = [c.template_id for c in conversions if c.template_id]
    templates_map = {}
    if template_ids:
        t_res = await db.execute(
            select(CVTemplate).where(CVTemplate.id.in_(template_ids))
        )
        templates_map = {str(t.id): t.name for t in t_res.scalars().all()}

    return [
        conversion_to_dict(
            c,
            template_name=templates_map.get(str(c.template_id), "Company Template"),
        )
        for c in conversions
    ]


@router.get("/{id}")
async def get_conversion(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        conv_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversion ID format")

    result = await db.execute(select(Conversion).where(Conversion.id == conv_uuid))
    conversion = result.scalars().first()
    if not conversion:
        raise HTTPException(status_code=404, detail="Conversion not found")

    user_role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if user_role_str == "recruiter" and conversion.recruiter_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    template_name = "Company Template"
    if conversion.template_id:
        t_res = await db.execute(
            select(CVTemplate).where(CVTemplate.id == conversion.template_id)
        )
        t = t_res.scalars().first()
        if t:
            template_name = t.name

    return conversion_to_dict(conversion, template_name=template_name)


@router.get("/{id}/download")
@router.get("/{id}/download/{format}")
async def download_output(
    id: str,
    format: Optional[str] = None,
    format_query: Optional[str] = Query(None, alias="format"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download a completed conversion output as DOCX or PDF."""
    try:
        conv_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversion ID format")

    requested_format = (format or format_query or "docx").lower()

    result = await db.execute(select(Conversion).where(Conversion.id == conv_uuid))
    conversion = result.scalars().first()
    if not conversion:
        raise HTTPException(status_code=404, detail="Conversion not found")

    user_role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if user_role_str == "recruiter" and conversion.recruiter_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if conversion.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Conversion is not completed (current status: {conversion.status}). Error: {conversion.error_message or 'None'}",
        )

    base_name = conversion.source_cv_filename.rsplit(".", 1)[0]

    if requested_format == "docx" and conversion.output_docx_path and os.path.exists(conversion.output_docx_path):
        return FileResponse(
            conversion.output_docx_path,
            filename=f"formatted_{base_name}.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    elif requested_format == "pdf" and conversion.output_pdf_path and os.path.exists(conversion.output_pdf_path):
        return FileResponse(
            conversion.output_pdf_path,
            filename=f"formatted_{base_name}.pdf",
            media_type="application/pdf",
        )
    elif requested_format == "pdf" and conversion.output_docx_path and os.path.exists(conversion.output_docx_path):
        # Fallback: DOCX exists, return DOCX if PDF couldn't be generated
        return FileResponse(
            conversion.output_docx_path,
            filename=f"formatted_{base_name}.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Requested format '{requested_format}' is not available for this conversion.",
        )


@router.delete("/{id}")
async def delete_conversion(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        conv_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversion ID format")

    result = await db.execute(select(Conversion).where(Conversion.id == conv_uuid))
    conversion = result.scalars().first()
    if not conversion:
        raise HTTPException(status_code=404, detail="Conversion not found")

    user_role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if user_role_str == "recruiter" and conversion.recruiter_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    for path in [
        conversion.source_cv_path,
        conversion.output_docx_path,
        conversion.output_pdf_path,
    ]:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

    await db.delete(conversion)
    await db.commit()
    return {"message": "Conversion deleted successfully"}
