"""
Configuration settings for Coupang Wing CS Automation System
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings"""

    # Coupang API Settings
    COUPANG_ACCESS_KEY: str = "your_access_key_here"
    COUPANG_SECRET_KEY: str = "your_secret_key_here"
    COUPANG_VENDOR_ID: str = "your_vendor_id_here"
    COUPANG_WING_ID: str = "your_wing_id_here"
    COUPANG_API_BASE_URL: str = "https://api-gateway.coupang.com"

    # Coupang Wing Web Login Settings
    COUPANG_WING_USERNAME: Optional[str] = None
    COUPANG_WING_PASSWORD: Optional[str] = None

    # Naver API Settings
    NAVER_CLIENT_ID: Optional[str] = None
    NAVER_CLIENT_SECRET: Optional[str] = None
    NAVER_CALLBACK_URL: str = "http://localhost:3000/naver/callback"  # 프론트엔드 콜백 URL
    NAVER_API_BASE_URL: str = "https://openapi.naver.com"

    # Database Settings
    # Use /data for cloud (fly.io persistent volume), local path for development
    DATABASE_URL: str = (
        "sqlite:////data/coupang_cs.db"
        if os.environ.get("ENVIRONMENT") == "production"
        else f"sqlite:///{Path(__file__).resolve().parent.parent / 'database' / 'coupang_cs.db'}"
    )

    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379/0"

    # OpenAI Settings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"

    # Security Settings
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ENCRYPTION_KEY: Optional[str] = None  # Fernet encryption key for account credentials

    # Application Settings
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"

    # CORS Settings (comma-separated origins for production)
    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"

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

    # Scheduler Settings
    AUTO_START_SCHEDULER: bool = True

    # Email Settings (for notifications)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None
    ALERT_EMAIL_RECIPIENTS: List[str] = []
    REPORT_EMAIL_RECIPIENTS: List[str] = []

    # Slack Settings
    SLACK_WEBHOOK_URL: Optional[str] = None

    class Config:
        # Load from backend/.env explicitly
        env_file = str(Path(__file__).resolve().parent.parent / ".env")
        case_sensitive = True


# Global settings instance
settings = Settings()
