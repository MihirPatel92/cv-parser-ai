from pydantic import BaseModel
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from ..core.dependencies import get_db, get_current_user, require_role
from ..db.models import User, UserRole, AIModelConfig, CVTemplate, Conversion

router = APIRouter()


class AIConfigUpdate(BaseModel):
    provider: str
    model_name: str
    api_key: Optional[str] = None        # New key (optional — keep existing if omitted)
    ollama_base_url: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


@router.get("/ai-config")
async def get_ai_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["super_admin"])),
):
    """Get current active AI model configuration."""
    result = await db.execute(select(AIModelConfig).where(AIModelConfig.is_active == True))
    config = result.scalars().first()
    if not config:
        raise HTTPException(status_code=404, detail="No active AI configuration found")
    return {
        "id": str(config.id),
        "provider": config.provider,
        "model_name": config.model_name,
        "has_api_key": bool(config.api_key_encrypted),
        "ollama_base_url": config.ollama_base_url,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "is_active": config.is_active,
    }


@router.put("/ai-config")
async def update_ai_config(
    payload: AIConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["super_admin"])),
):
    """Update the active AI model configuration."""
    valid_providers = ['gemini', 'openai', 'ollama']
    if payload.provider not in valid_providers:
        raise HTTPException(status_code=400, detail=f"Provider must be one of: {valid_providers}")

    result = await db.execute(select(AIModelConfig).where(AIModelConfig.is_active == True))
    config = result.scalars().first()

    if not config:
        # Create fresh config
        config = AIModelConfig(is_active=True)
        db.add(config)

    config.provider = payload.provider
    config.model_name = payload.model_name
    config.updated_by = current_user.id

    if payload.api_key:
        config.api_key_encrypted = payload.api_key
    if payload.ollama_base_url is not None:
        config.ollama_base_url = payload.ollama_base_url
    if payload.temperature is not None:
        config.temperature = max(0.0, min(1.0, payload.temperature))
    if payload.max_tokens is not None:
        config.max_tokens = max(256, payload.max_tokens)

    await db.commit()
    return {"message": "AI configuration updated successfully", "provider": config.provider, "model_name": config.model_name}


@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dashboard statistics: user/template/conversion counts + recent activity."""
    # User counts
    users_result = await db.execute(select(func.count(User.id)))
    total_users = users_result.scalar() or 0

    # Template counts
    templates_result = await db.execute(select(func.count(CVTemplate.id)))
    total_templates = templates_result.scalar() or 0

    # Conversion counts by status
    conv_result = await db.execute(select(Conversion))
    all_conversions = conv_result.scalars().all()
    total_conversions = len(all_conversions)
    completed = sum(1 for c in all_conversions if c.status == "completed")
    failed = sum(1 for c in all_conversions if c.status == "failed")
    processing = sum(1 for c in all_conversions if c.status in ("processing", "pending"))

    # Recent 10 conversions
    recent_result = await db.execute(
        select(Conversion).order_by(Conversion.created_at.desc()).limit(10)
    )
    recent = recent_result.scalars().all()

    return {
        "total_users": total_users,
        "total_templates": total_templates,
        "total_conversions": total_conversions,
        "completed_conversions": completed,
        "failed_conversions": failed,
        "processing_conversions": processing,
        "success_rate": round((completed / total_conversions * 100), 1) if total_conversions > 0 else 0,
        "recent_conversions": [
            {
                "id": str(c.id),
                "source_cv_filename": c.source_cv_filename,
                "status": c.status,
                "ai_provider": c.ai_provider,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in recent
        ],
    }
