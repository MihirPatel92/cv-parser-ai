from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from ..core.security import verify_password, create_access_token, hash_password
from ..core.dependencies import get_db, get_current_user
from ..db.models import User

router = APIRouter()


class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    role: str


class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalars().first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    access_token = create_access_token(data={"sub": str(user.id), "role": role_str})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(user.id),
        "role": role_str,
    }


@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": role_str,
    }


@router.put("/me/password")
async def change_password(
    passwords: PasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(passwords.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")

    current_user.hashed_password = hash_password(passwords.new_password)
    await db.commit()
    return {"msg": "Password updated successfully"}
