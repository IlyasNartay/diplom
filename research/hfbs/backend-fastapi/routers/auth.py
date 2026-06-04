"""
routers/auth.py — Authentication Router
Регистрация и получение JWT токена.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.security import hash_password, verify_password, create_access_token
from models.db_models import User
from schemas.schemas import TokenResponse, UserCreate

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post("/register/", status_code=status.HTTP_201_CREATED)
async def register(body: UserCreate, db: AsyncSession = Depends(get_db)):
    # Проверяем уникальность
    existing = await db.execute(select(User).where(User.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Пользователь уже существует")

    user = User(
        username=body.username,
        email=body.email,
        password=hash_password(body.password),
    )
    db.add(user)
    await db.commit()
    return {"message": "Пользователь создан", "username": body.username}


@router.post("/token/", response_model=TokenResponse, summary="Получить JWT токен")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession                     = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == form_data.username))
    user   = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
        )

    token = create_access_token({"sub": str(user.id), "username": user.username})
    return TokenResponse(access_token=token)
