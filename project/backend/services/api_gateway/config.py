import json
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SERVICE_NAME: str = "api_gateway"

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"

    BACKEND_CORS_ORIGINS: str = '["http://localhost:3000"]'

    AUTH_SERVICE_URL: str = "http://auth_service:8000"
    CATALOG_SERVICE_URL: str = "http://catalog_service:8000"
    ORCHESTRATOR_URL: str = "http://orchestrator:8000"
    SEAT_SERVICE_URL: str = "http://seat_service:8000"
    TICKET_SERVICE_URL: str = "http://ticket_service:8000"
    PAYMENT_SERVICE_URL: str = "http://payment_service:8000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> List[str]:
        try:
            return json.loads(self.BACKEND_CORS_ORIGINS)
        except (json.JSONDecodeError, TypeError):
            return [s.strip() for s in self.BACKEND_CORS_ORIGINS.split(",") if s.strip()]


settings = Settings()

ROUTES = {
    "/api/auth": settings.AUTH_SERVICE_URL,
    "/api/catalog": settings.CATALOG_SERVICE_URL,
    "/api/events": settings.CATALOG_SERVICE_URL,
    "/api/categories": settings.CATALOG_SERVICE_URL,
    "/api/cities": settings.CATALOG_SERVICE_URL,
    "/api/sessions": settings.CATALOG_SERVICE_URL,
    "/api/admin/categories": settings.CATALOG_SERVICE_URL,
    "/api/admin/cities": settings.CATALOG_SERVICE_URL,
    "/api/admin/events": settings.CATALOG_SERVICE_URL,
    "/api/admin/sessions": settings.CATALOG_SERVICE_URL,
    "/api/seats": settings.SEAT_SERVICE_URL,
    "/api/admin/seats": settings.SEAT_SERVICE_URL,
    "/api/buy": settings.ORCHESTRATOR_URL,
    "/api/status": settings.ORCHESTRATOR_URL,
    "/api/history": settings.ORCHESTRATOR_URL,
    "/api/cards": settings.PAYMENT_SERVICE_URL,
    "/media": settings.CATALOG_SERVICE_URL,
    "/tickets": settings.TICKET_SERVICE_URL,
}

PROTECTED_PREFIXES = [
    "/api/buy",
    "/api/status",
    "/api/history",
    "/api/cards",
]

ADMIN_PREFIXES = [
    "/api/admin",
]
