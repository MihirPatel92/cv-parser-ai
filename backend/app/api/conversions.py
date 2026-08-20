import os
import uuid
import time
import asyncio
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from typing import Optional

from ..core.dependencies import get_db, get_current_user, get_ai_config
from ..db.models import User, UserRole, CVTemplate, Conversion, AIModelConfig
from ..core.config import settings
from ..ai.orchestrator import AIOrchestrator
from ..parsers.pdf_parser import extract_text_from_pdf
from ..parsers.docx_parser import extract_text_from_docx, extract_placeholders_from_docx
from ..formatters.docx_formatter import DocxFormatter
from ..formatters.pdf_formatter import convert_docx_to_pdf

router = APIRouter()


async def process_conversion(conversion_id: str, db: AsyncSession, config: AIModelConfig):
    """Background task: run the full AI conversion pipeline."""
    start_time = time.time()

    result = await db.execute(select(Conversion).where(Conversion.id == conversion_id))
    conversion = result.scalars().first()
    if not conversion:
        return

    try:
        # ── Step 1: Parse the uploaded CV ────────────────────────────────────
        cv_path = conversion.source_cv_path
        if cv_path.lower().endswith('.pdf'):
            cv_text = extract_text_from_pdf(cv_path)
        else:
            cv_text = extract_text_from_docx(cv_path)

        if not cv_text or len(cv_text.strip()) < 50:
            raise ValueError("CV text extraction produced insufficient content. Ensure the file is text-based (not scanned).")

        # ── Step 2: AI extraction ─────────────────────────────────────────────
        orchestrator = AIOrchestrator(config)
        cv_data = await orchestrator.extract_cv_data(cv_text)
        conversion.extracted_cv_data = cv_data
        conversion.ai_model_used = config.model_name

        # ── Step 3: Fetch Template ────────────────────────────────────────────
        template_result = await db.execute(select(CVTemplate).where(CVTemplate.id == conversion.template_id))
        template = template_result.scalars().first()
        if not template:
            raise ValueError("Template not found in database.")

        # ── Step 4: Format output ─────────────────────────────────────────────
        formatter = DocxFormatter()
        out_filename = str(uuid.uuid4())
        out_docx_path = os.path.join(settings.UPLOAD_DIR, "outputs", f"{out_filename}.docx")
        out_pdf_path = None

        if template.file_type.lower() == 'docx':
            placeholders = extract_placeholders_from_docx(template.file_path)

            if placeholders:
                # Template has {{placeholders}} — map CV data to them
                mapping = await orchestrator.map_to_placeholders(placeholders, cv_data)
                conversion.placeholder_mapping = mapping
                formatter.fill_placeholders(template.file_path, mapping, out_docx_path)
            else:
                # No placeholders — AI mirrors the template structure
                template_text = extract_text_from_docx(template.file_path)
                structure = await orchestrator.analyze_template_structure(template_text)
                section_data = await orchestrator.freeform_map(str(structure), cv_data)
                formatter.freeform_fill(template.file_path, section_data, out_docx_path)
        else:
            # PDF template: extract structure and freeform fill
            from ..parsers.pdf_parser import extract_text_from_pdf as pdf_extract
            template_text = pdf_extract(template.file_path)
            structure = await orchestrator.analyze_template_structure(template_text)
            section_data = await orchestrator.freeform_map(str(structure), cv_data)
            formatter.freeform_fill(None, section_data, out_docx_path)

        # ── Step 5: Convert to PDF if requested ──────────────────────────────
        output_format = conversion.output_format
        if output_format in ('pdf', 'both'):
            out_pdf_path = os.path.join(settings.UPLOAD_DIR, "outputs", f"{out_filename}.pdf")
            try:
                convert_docx_to_pdf(out_docx_path, out_pdf_path)
            except Exception as pdf_err:
                # PDF generation failed but DOCX succeeded — non-fatal
                print(f"⚠️  PDF conversion failed (DOCX still available): {pdf_err}")
                out_pdf_path = None

        # ── Step 6: Save results ──────────────────────────────────────────────
        conversion.output_docx_path = out_docx_path if output_format in ('docx', 'both') else None
        conversion.output_pdf_path = out_pdf_path
        conversion.status = "completed"
        conversion.completed_at = datetime.utcnow()
        conversion.processing_time_seconds = round(time.time() - start_time, 2)
        await db.commit()

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
    output_format: str = Form("both"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ai_config: AIModelConfig = Depends(get_ai_config),
):
    """Upload a CV and trigger AI conversion against a selected template."""
    # Validate file type
    filename_lower = file.filename.lower()
    if not (filename_lower.endswith('.docx') or filename_lower.endswith('.pdf')):
        raise HTTPException(status_code=400, detail="Only DOCX and PDF files are accepted.")

    # Validate file size
    content = await file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit.")

    # Validate output_format
    if output_format not in ('docx', 'pdf', 'both'):
        raise HTTPException(status_code=400, detail="output_format must be 'docx', 'pdf', or 'both'.")

    # Save uploaded CV
    ext = filename_lower.split('.')[-1]
    saved_name = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, "cvs", saved_name)
    async with aiofiles.open(filepath, 'wb') as f:
        await f.write(content)

    # Override config provider if user selected a different one
    if ai_provider != ai_config.provider:
        # Create a temporary config object with the requested provider
        override_config = AIModelConfig(
            provider=ai_provider,
            model_name=ai_config.model_name,
            api_key_encrypted=ai_config.api_key_encrypted,
            ollama_base_url=ai_config.ollama_base_url,
            temperature=ai_config.temperature,
            max_tokens=ai_config.max_tokens,
            is_active=True,
        )
        effective_config = override_config
    else:
        effective_config = ai_config

    # Create conversion record
    conversion = Conversion(
        recruiter_id=current_user.id,
        template_id=template_id,
        source_cv_path=filepath,
        source_cv_filename=file.filename,
        source_cv_file_type=ext,
        output_format=output_format,
        ai_provider=ai_provider,
        status="processing",
    )
    db.add(conversion)
    await db.commit()
    await db.refresh(conversion)

    # Launch background processing
    background_tasks.add_task(process_conversion, str(conversion.id), db, effective_config)

    return {
        "id": str(conversion.id),
        "status": conversion.status,
        "message": "Conversion started. Poll GET /conversions/{id} for status.",
    }


@router.get("/")
async def list_conversions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List conversions. Admins see all; recruiters see their own."""
    if current_user.role in [UserRole.super_admin, UserRole.admin]:
        result = await db.execute(select(Conversion).order_by(Conversion.created_at.desc()))
    else:
        result = await db.execute(
            select(Conversion)
            .where(Conversion.recruiter_id == current_user.id)
            .order_by(Conversion.created_at.desc())
        )
    conversions = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "source_cv_filename": c.source_cv_filename,
            "template_id": str(c.template_id) if c.template_id else None,
            "status": c.status,
            "ai_provider": c.ai_provider,
            "ai_model_used": c.ai_model_used,
            "output_format": c.output_format,
            "error_message": c.error_message,
            "processing_time_seconds": c.processing_time_seconds,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "completed_at": c.completed_at.isoformat() if c.completed_at else None,
        }
        for c in conversions
    ]


@router.get("/{id}")
async def get_conversion(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Conversion).where(Conversion.id == id))
    conversion = result.scalars().first()
    if not conversion:
        raise HTTPException(status_code=404, detail="Conversion not found")
    # Recruiters can only see their own
    if current_user.role == UserRole.recruiter and conversion.recruiter_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return {
        "id": str(conversion.id),
        "source_cv_filename": conversion.source_cv_filename,
        "template_id": str(conversion.template_id) if conversion.template_id else None,
        "status": conversion.status,
        "ai_provider": conversion.ai_provider,
        "ai_model_used": conversion.ai_model_used,
        "output_format": conversion.output_format,
        "has_docx": conversion.output_docx_path is not None and os.path.exists(conversion.output_docx_path or ""),
        "has_pdf": conversion.output_pdf_path is not None and os.path.exists(conversion.output_pdf_path or ""),
        "error_message": conversion.error_message,
        "processing_time_seconds": conversion.processing_time_seconds,
        "created_at": conversion.created_at.isoformat() if conversion.created_at else None,
        "completed_at": conversion.completed_at.isoformat() if conversion.completed_at else None,
    }


@router.get("/{id}/download/{format}")
async def download_output(
    id: str,
    format: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download a completed conversion output as DOCX or PDF."""
    result = await db.execute(select(Conversion).where(Conversion.id == id))
    conversion = result.scalars().first()
    if not conversion:
        raise HTTPException(status_code=404, detail="Conversion not found")
    if current_user.role == UserRole.recruiter and conversion.recruiter_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    if conversion.status != "completed":
        raise HTTPException(status_code=400, detail=f"Conversion is not completed (status: {conversion.status})")

    if format == 'docx' and conversion.output_docx_path and os.path.exists(conversion.output_docx_path):
        return FileResponse(
            conversion.output_docx_path,
            filename=f"formatted_cv_{conversion.source_cv_filename.rsplit('.', 1)[0]}.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    elif format == 'pdf' and conversion.output_pdf_path and os.path.exists(conversion.output_pdf_path):
        return FileResponse(
            conversion.output_pdf_path,
            filename=f"formatted_cv_{conversion.source_cv_filename.rsplit('.', 1)[0]}.pdf",
            media_type="application/pdf",
        )
    else:
        raise HTTPException(status_code=404, detail=f"Requested format '{format}' is not available for this conversion.")


@router.delete("/{id}")
async def delete_conversion(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Conversion).where(Conversion.id == id))
    conversion = result.scalars().first()
    if not conversion:
        raise HTTPException(status_code=404, detail="Conversion not found")
    if current_user.role == UserRole.recruiter and conversion.recruiter_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Clean up files
    for path in [conversion.source_cv_path, conversion.output_docx_path, conversion.output_pdf_path]:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

    await db.delete(conversion)
    await db.commit()
    return {"message": "Conversion deleted successfully"}
