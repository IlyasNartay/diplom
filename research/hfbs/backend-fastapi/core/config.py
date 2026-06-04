"""
core/config.py — конфигурация FastAPI через pydantic-settings
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str               = "postgresql+asyncpg://hfbs:hfbs_secret@postgres:5432/hfbs_db"
    redis_url: str                  = "redis://redis:6379/0"
    jwt_secret: str                 = "change-me"
    jwt_algorithm: str              = "HS256"
    jwt_access_token_expire_minutes: int = 60
    kafka_bootstrap_servers: str    = "kafka:9092"
    seat_lock_ttl: int              = 300

    class Config:
        env_file = ".env"


settings = Settings()
