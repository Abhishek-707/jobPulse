from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/jobpulse"
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # API
    API_TITLE: str = "JobPulse API"
    API_VERSION: str = "0.1.0"
    
    # Ingestion
    INGESTION_TIMEOUT: int = 30
    INGESTION_MAX_RETRIES: int = 3
    
    # AI (optional)
    AI_ENABLED: bool = False
    AI_API_KEY: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
