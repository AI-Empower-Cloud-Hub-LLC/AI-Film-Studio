"""
Application Configuration — multi-backend setup.

Default: Ollama (local LLM, free). Optional: Google AI (free tier),
Claude/Anthropic, ElevenLabs for premium features.
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

    # Database
    DATABASE_URL: str = "sqlite:///./ai_film_studio.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM Backend — "ollama" (default), "google" (free tier), or "claude" (premium)
    LLM_BACKEND: str = "ollama"

    # Ollama (local LLM server — https://ollama.ai)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral"

    # Google Generative AI (free tier — https://ai.google.dev)
    GOOGLE_API_KEY: str = ""
    GOOGLE_MODEL: str = "gemini-2.0-flash"

    # Anthropic Claude (premium — https://console.anthropic.com)
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"

    # ElevenLabs (premium voice — https://elevenlabs.io)
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_MODEL: str = "eleven_multilingual_v2"
    VOICE_BACKEND: str = "local"  # "local" (Coqui) or "elevenlabs"

    # Runway (video generation — https://docs.dev.runwayml.com)
    RUNWAY_API_KEY: str = ""

    # MongoDB (optional — for pipeline history persistence)
    MONGODB_URL: str = ""
    MONGODB_DB_NAME: str = "ai_film_studio"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # File Upload
    MAX_UPLOAD_SIZE: int = 104857600  # 100MB
    ALLOWED_EXTENSIONS: List[str] = [".mp4", ".mov", ".avi", ".png", ".jpg", ".jpeg"]

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Validate production settings
if settings.APP_ENV == "production":
    if settings.SECRET_KEY == generate_secret_key() or len(settings.SECRET_KEY) < 32:
        raise ValueError(
            "SECRET_KEY must be set to a secure random value in production. "
            "Generate one using: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
