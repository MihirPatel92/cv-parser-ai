import os
import uuid
import base64
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..core.dependencies import get_db, get_current_user
from ..db.models import User, CVTemplate
from ..core.config import settings
from ..parsers.docx_parser import extract_placeholders_from_docx

router = APIRouter()


def ensure_template_on_disk(template: CVTemplate) -> str:
    """Ensure the template file exists on disk, reconstructing from DB if container restarted."""
    if template.file_path and os.path.exists(template.file_path):
        return template.file_path

    # Reconstruct from base64 stored in PostgreSQL
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "templates"), exist_ok=True)
    filename = f"{template.id}.{template.file_type}"
    filepath = os.path.join(settings.UPLOAD_DIR, "templates", filename)

    if template.file_data:
        try:
            raw_bytes = base64.b64decode(template.file_data)
            with open(filepath, "wb") as f:
                f.write(raw_bytes)
            template.file_path = filepath
            return filepath
        except Exception as e:
            print(f"Failed to reconstruct template file from DB: {e}")

    return template.file_path


def template_to_dict(t: CVTemplate) -> dict:
    return {
        "id": str(t.id),
        "name": t.name,
        "description": t.description,
        "company_name": t.company_name,
        "file_path": t.file_path,
        "file_name": t.file_name,
        "file_type": t.file_type,
        "file_size_bytes": t.file_size_bytes,
        "placeholder_type": t.placeholder_type,
        "detected_placeholders": t.detected_placeholders or [],
        "uploaded_by": str(t.uploaded_by) if t.uploaded_by else None,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


@router.get("/")
async def list_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(CVTemplate))
    templates = result.scalars().all()
    return [template_to_dict(t) for t in templates]


@router.post("/")
async def upload_template(
    name: str = Form(...),
    description: str = Form(""),
    company_name: str = Form(""),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename.lower().endswith((".docx", ".pdf")):
        raise HTTPException(status_code=400, detail="Only DOCX and PDF files are allowed")

    ext = file.filename.split(".")[-1].lower()
    filename = f"{uuid.uuid4()}.{ext}"
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "templates"), exist_ok=True)
    filepath = os.path.join(settings.UPLOAD_DIR, "templates", filename)

    content = await file.read()
    async with aiofiles.open(filepath, "wb") as out_file:
        await out_file.write(content)

    b64_content = base64.b64encode(content).decode("utf-8")

    detected_placeholders = []
    placeholder_type = "none"
    if ext == "docx":
        detected_placeholders = extract_placeholders_from_docx(filepath)
        if detected_placeholders:
            placeholder_type = "auto_detected"

    template = CVTemplate(
        name=name,
        description=description,
        company_name=company_name,
        file_path=filepath,
        file_name=file.filename,
        file_type=ext,
        file_size_bytes=len(content),
        file_data=b64_content,
        placeholder_type=placeholder_type,
        detected_placeholders=detected_placeholders,
        uploaded_by=current_user.id,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template_to_dict(template)


@router.get("/{id}")
async def get_template(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        tmpl_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")

    result = await db.execute(select(CVTemplate).where(CVTemplate.id == tmpl_uuid))
    template = result.scalars().first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    ensure_template_on_disk(template)
    return template_to_dict(template)


@router.get("/{id}/placeholders")
async def get_template_placeholders(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        tmpl_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")

    result = await db.execute(select(CVTemplate).where(CVTemplate.id == tmpl_uuid))
    template = result.scalars().first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    ensure_template_on_disk(template)

    if template.file_type != "docx":
        return {"placeholders": []}
    placeholders = extract_placeholders_from_docx(template.file_path)
    return {"placeholders": placeholders}


@router.delete("/{id}")
async def delete_template(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        tmpl_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")

    result = await db.execute(select(CVTemplate).where(CVTemplate.id == tmpl_uuid))
    template = result.scalars().first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    if template.file_path and os.path.exists(template.file_path):
        try:
            os.remove(template.file_path)
        except Exception:
            pass

    await db.delete(template)
    await db.commit()
    return {"msg": "Template deleted"}
