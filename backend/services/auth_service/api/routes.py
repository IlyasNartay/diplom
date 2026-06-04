from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from services.auth_service.database import get_db
from services.auth_service.logic.auth_manager import AuthManager
from services.auth_service.schemas import RefreshTokenRequest, TokenResponse, UserCreate, UserLogin, UserResponse

router = APIRouter()

_optional_bearer = HTTPBearer(auto_error=False)


def get_auth_manager() -> AuthManager:
    return AuthManager()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    data: UserCreate, db: AsyncSession = Depends(get_db), auth_manager: AuthManager = Depends(get_auth_manager)
):
    """Регистрация нового пользователя"""
    return await auth_manager.register_user(data, db)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLogin, db: AsyncSession = Depends(get_db), auth_manager: AuthManager = Depends(get_auth_manager)
):
    """Вход и получение JWT токена"""
    return await auth_manager.authenticate_user(data, db)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token_endpoint(
    data: RefreshTokenRequest, db: AsyncSession = Depends(get_db), auth_manager: AuthManager = Depends(get_auth_manager)
):
    """Обновление access токена с помощью refresh токена"""
    return await auth_manager.refresh_tokens(data.refresh_token, db)
