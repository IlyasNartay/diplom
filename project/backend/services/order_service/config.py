from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SERVICE_NAME: str = "order_service"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5445/ticketon_main_db"
    REDIS_URL: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
