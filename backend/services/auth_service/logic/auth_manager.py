import jwt
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.auth_service.config import settings
from services.auth_service.logic.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from services.auth_service.models import User
from services.auth_service.schemas import UserCreate, UserLogin


class AuthManager:
    async def register_user(self, data: UserCreate, db: AsyncSession) -> User:
        result = await db.execute(select(User).where(User.email == data.email))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")

        new_user = User(
            email=data.email,
            password_hash=get_password_hash(data.password),
            full_name=data.full_name,
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user

    async def authenticate_user(self, data: UserLogin, db: AsyncSession) -> dict:
        result = await db.execute(select(User).where(User.email == data.email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Incorrect email or password")

        token_data = {"sub": str(user.id), "role": user.role.value}

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user_id": user.id,
            "role": user.role,
        }

    async def refresh_tokens(self, refresh_token: str, db: AsyncSession) -> dict:
        """Метод проверки старого refresh токена и выдачи новой пары"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(refresh_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id: str = payload.get("sub")
            token_type: str = payload.get("type")

            if user_id is None or token_type != "refresh":
                raise credentials_exception

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Refresh token expired. Please log in again.")
        except jwt.PyJWTError:
            raise credentials_exception

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user is None:
            raise credentials_exception

        token_data = {"sub": str(user.id), "role": user.role.value}
        new_access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "user_id": user.id,
            "role": user.role,
        }
