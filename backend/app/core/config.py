"""
Application Configuration
"""
from pydantic_settings import BaseSettings
from typing import List
import secrets
import os


def generate_secret_key() -> str:
    """Generate a secure random secret key"""
    return secrets.token_urlsafe(32)


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "AI-Film-Studio"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_VERSION: str = "v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", generate_secret_key())

    # Database — PostgreSQL in production, SQLite for dev
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./ai_film_studio.db",
    )

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM Backend
    LLM_BACKEND: str = "google"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral"
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"

    # Orchestrator backend: "langgraph" (default) or "autogen"
    ORCHESTRATOR_BACKEND: str = "langgraph"

    # AI Services
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    GOOGLE_MODEL: str = "gemini-2.0-flash"
    STABILITY_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""
    REPLICATE_API_TOKEN: str = ""
    RUNWAY_API_KEY: str = ""

    # CORS — lock down in production
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # File Upload
    MAX_UPLOAD_SIZE: int = 104857600  # 100MB
    ALLOWED_EXTENSIONS: List[str] = [
        ".mp4", ".mov", ".avi", ".mkv",
        ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg",
        ".mp3", ".wav", ".ogg", ".flac",
        ".pdf", ".txt", ".doc", ".docx",
        ".json", ".csv",
        ".zip", ".tar", ".gz",
    ]

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Email (for verification and password reset)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@aifilmstudio.com"
    SMTP_TLS: bool = True
    EMAIL_VERIFICATION_REQUIRED: bool = False

    # Sentry (error monitoring)
    SENTRY_DSN: str = ""

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()

# Validate production settings
if settings.APP_ENV == "production":
    if settings.SECRET_KEY == generate_secret_key() or len(settings.SECRET_KEY) < 32:
        raise ValueError(
            "SECRET_KEY must be set to a secure random value in production. "
            "Generate one using: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
    if "sqlite" in settings.DATABASE_URL:
        import warnings
        warnings.warn(
            "SQLite detected in production. Set DATABASE_URL to a PostgreSQL connection string: "
            "postgresql://user:password@host:5432/dbname",
            stacklevel=2,
        )
    if not settings.CORS_ORIGINS or "localhost" in str(settings.CORS_ORIGINS):
        import warnings
        warnings.warn(
            "CORS_ORIGINS contains localhost in production. "
            "Set CORS_ORIGINS to your production domain(s).",
            stacklevel=2,
        )
