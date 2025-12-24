"""
Configuration settings for Coupang Wing CS Automation System
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings"""

    # Coupang API Settings
    COUPANG_ACCESS_KEY: str
    COUPANG_SECRET_KEY: str
    COUPANG_VENDOR_ID: str
    COUPANG_WING_ID: str
    COUPANG_API_BASE_URL: str = "https://api-gateway.coupang.com"

    # Coupang Wing Web Login Settings
    COUPANG_WING_USERNAME: Optional[str] = None
    COUPANG_WING_PASSWORD: Optional[str] = None

    # Database Settings
    DATABASE_URL: str = "sqlite:///./coupang_cs.db"

    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379/0"

    # OpenAI Settings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"

    # Security Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Application Settings
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"

    # Validation Settings
    CONFIDENCE_THRESHOLD: float = 80.0
    AUTO_APPROVE_THRESHOLD: float = 90.0
    MAX_RESPONSE_LENGTH: int = 1000

    # Rate Limiting
    INQUIRY_CHECK_INTERVAL: int = 300  # seconds
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    KNOWLEDGE_BASE_DIR: Path = BASE_DIR / "knowledge_base"
    POLICIES_DIR: Path = KNOWLEDGE_BASE_DIR / "policies"
    TEMPLATES_DIR: Path = KNOWLEDGE_BASE_DIR / "templates"
    FAQ_DIR: Path = KNOWLEDGE_BASE_DIR / "faq"
    PRODUCTS_DIR: Path = KNOWLEDGE_BASE_DIR / "products"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
