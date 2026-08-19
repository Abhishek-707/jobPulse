from typing import List

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    """Application configuration."""

    DATABASE_URL: str = (
        "postgresql+psycopg://"
        "abhishekgiri@localhost:5432/jobpulse"
    )

    ENVIRONMENT: str = "development"

    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    API_TITLE: str = "JobPulse API"

    API_VERSION: str = "0.1.0"

    INGESTION_TIMEOUT: int = 30

    INGESTION_MAX_RETRIES: int = 3

    AI_ENABLED: bool = False

    AI_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()