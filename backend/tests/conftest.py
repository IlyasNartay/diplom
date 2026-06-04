"""
Shared fixtures for E2E / integration tests.

Prerequisites:
    - The entire stack must be running (docker-compose up).
    - The API Gateway is reachable at GATEWAY_URL (default http://localhost:8080).
    - JWT_SECRET_KEY must match the one used by auth_service & api_gateway.

Override via environment variables:
    GATEWAY_URL          – base URL of the API Gateway
    TEST_JWT_SECRET_KEY  – JWT secret shared across services
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator

import httpx
import jwt
import pytest
import pytest_asyncio

GATEWAY_URL: str = os.getenv("GATEWAY_URL", "http://localhost:8080")
JWT_SECRET: str | None = os.getenv("TEST_JWT_SECRET_KEY") or os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM: str = "HS256"
ADMIN_EMAIL: str | None = os.getenv("TEST_ADMIN_EMAIL")
ADMIN_PASSWORD: str | None = os.getenv("TEST_ADMIN_PASSWORD")


def _make_admin_token(user_id: str | None = None) -> str:
    if not JWT_SECRET:
        raise ValueError("JWT secret is not configured")
    payload = {
        "sub": user_id or str(uuid.uuid4()),
        "role": "admin",
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


@pytest_asyncio.fixture
async def gateway() -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(base_url=GATEWAY_URL, timeout=30.0) as client:
        yield client


@pytest_asyncio.fixture
async def admin_headers(gateway: httpx.AsyncClient) -> dict[str, str]:
    # Preferred: obtain a real admin JWT through auth_service login.
    if ADMIN_EMAIL and ADMIN_PASSWORD:
        response = await gateway.post(
            "/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        if response.status_code == 200:
            token = response.json()["access_token"]
            return {"Authorization": f"Bearer {token}"}
        pytest.fail(
            "Admin login failed for TEST_ADMIN_EMAIL/TEST_ADMIN_PASSWORD. "
            f"Status={response.status_code}, body={response.text}"
        )

    # Fallback: mint local JWT only when explicit secret is provided.
    if JWT_SECRET:
        token = _make_admin_token()
        return {"Authorization": f"Bearer {token}"}

    pytest.skip(
        "Admin auth is not configured for E2E test. "
        "Set TEST_ADMIN_EMAIL/TEST_ADMIN_PASSWORD or TEST_JWT_SECRET_KEY."
    )
