import os
import uuid
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..core.dependencies import get_db, get_current_user
from ..db.models import User, CVTemplate
from ..core.config import settings
from ..parsers.docx_parser import extract_placeholders_from_docx

router = APIRouter()

@router.get("/")
async def list_templates(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(CVTemplate))
    templates = result.scalars().all()
    return templates

@router.post("/")
async def upload_template(
    name: str = Form(...),
    description: str = Form(""),
    company_name: str = Form(""),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.endswith(('.docx', '.pdf')):
        raise HTTPException(status_code=400, detail="Only DOCX and PDF files are allowed")
    
    ext = file.filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, "templates", filename)
    
    async with aiofiles.open(filepath, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
        
    placeholder_type = "manual"
    if ext == 'docx':
        placeholders = extract_placeholders_from_docx(filepath)
        if placeholders:
            placeholder_type = "manual" # Meaning it has explicit {{}} placeholders
        else:
            placeholder_type = "auto"
    else:
        placeholder_type = "auto" # PDF is always auto-mapped

    template = CVTemplate(
        name=name,
        description=description,
        company_name=company_name,
        file_path=filepath,
        file_type=ext,
        placeholder_type=placeholder_type,
        uploaded_by=current_user.id
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template

@router.get("/{id}")
async def get_template(id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(CVTemplate).where(CVTemplate.id == id))
    template = result.scalars().first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

@router.get("/{id}/placeholders")
async def get_template_placeholders(id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    template = await get_template(id, db, current_user)
    if template.file_type != 'docx':
        return {"placeholders": []}
    placeholders = extract_placeholders_from_docx(template.file_path)
    return {"placeholders": placeholders}

@router.delete("/{id}")
async def delete_template(id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    template = await get_template(id, db, current_user)
    if os.path.exists(template.file_path):
        os.remove(template.file_path)
    await db.delete(template)
    await db.commit()
    return {"msg": "Template deleted"}
