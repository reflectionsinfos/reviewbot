"""
Application Configuration
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # App Info
    APP_NAME: str = "AI Tech & Delivery Review Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://review_user:review_password@localhost:5432/reviews_db"
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    ELEVENLABS_API_KEY: Optional[str] = None

    # LLM Provider Configuration
    ACTIVE_LLM_PROVIDER: str = "openai"
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    QWEN_API_KEY: Optional[str] = None
    AZURE_OPENAI_API_KEY: Optional[str] = None

    # Security
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours — suitable for CLI sessions
    
    # Vector Store
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    
    # Storage
    UPLOAD_DIR: str = "./uploads"
    REPORTS_DIR: str = "./reports"
    
    # Agent Settings
    DEFAULT_LANGUAGE: str = "en"
    VOICE_ENABLED: bool = True
    REQUIRE_HUMAN_APPROVAL: bool = True
    
    # Data directories
    DATA_DIR: str = "./data"
    TEMPLATES_DIR: str = "./data/templates"
    PROJECTS_DATA_DIR: str = "./data/projects"

    @field_validator("DEBUG", mode="before")
    @classmethod
    def normalize_debug(cls, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "1", "yes", "on", "debug", "dev", "development"}:
                return True
            if lowered in {"false", "0", "no", "off", "release", "prod", "production"}:
                return False
        return value
    
    class Config:
        env_file = (".env", "env.non-prod.gcp", "env.local")
        case_sensitive = True
        extra = "ignore"


# Global settings instance
settings = Settings()
