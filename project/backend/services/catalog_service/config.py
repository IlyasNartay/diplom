from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SERVICE_NAME: str = "catalog_service"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5445/ticketon_main_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    SEAT_SERVICE_URL: str = "http://seat_service:8000"
    MEDIA_ROOT: str = "data/media"
    # Публичный базовый URL API (например http://164.92.180.99:8080) — для абсолютного poster_url в ответах
    PUBLIC_MEDIA_BASE_URL: str = ""
    # Итоговый размер обложки (2:3, как афиша); cover-crop по центру при загрузке
    POSTER_CANVAS_WIDTH: int = 600
    POSTER_CANVAS_HEIGHT: int = 900
    POSTER_JPEG_QUALITY: int = 88

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
