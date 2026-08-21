from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from pydantic import BaseModel, EmailStr
import uuid
from ..core.security import hash_password
from ..core.dependencies import get_db, get_current_user, require_role
from ..db.models import User, UserRole

router = APIRouter()


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


def user_to_dict(user: User) -> dict:
    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": role_str,
        "is_active": user.is_active,
    }


@router.get("/", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(require_role(["super_admin", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role == UserRole.super_admin:
        result = await db.execute(select(User))
    else:
        result = await db.execute(select(User).where(User.created_by == current_user.id))
    users = result.scalars().all()
    return [user_to_dict(u) for u in users]


@router.post("/", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    current_user: User = Depends(require_role(["super_admin", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role == UserRole.admin and user.role != "recruiter":
        raise HTTPException(status_code=403, detail="Admins can only create recruiters")

    existing = await db.execute(select(User).where(User.email == user.email))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hash_password(user.password),
        role=UserRole(user.role),
        created_by=current_user.id,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return user_to_dict(db_user)


@router.get("/{id}", response_model=UserResponse)
async def get_user(
    id: str,
    current_user: User = Depends(require_role(["super_admin", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    try:
        user_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if current_user.role == UserRole.admin and user.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this user")
    return user_to_dict(user)


@router.put("/{id}", response_model=UserResponse)
async def update_user(
    id: str,
    user_update: UserUpdate,
    current_user: User = Depends(require_role(["super_admin", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    try:
        user_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if current_user.role == UserRole.admin and user.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this user")

    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    if user_update.is_active is not None:
        user.is_active = user_update.is_active

    await db.commit()
    await db.refresh(user)
    return user_to_dict(user)


@router.delete("/{id}")
async def delete_user(
    id: str,
    current_user: User = Depends(require_role(["super_admin", "admin"])),
    db: AsyncSession = Depends(get_db),
):
    try:
        user_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if current_user.role == UserRole.admin and user.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this user")

    await db.delete(user)
    await db.commit()
    return {"msg": "User deleted successfully"}
