"""
Application Configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # App Info
    APP_NAME: str = "AI Tech & Delivery Review Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./reviews.db"
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    ELEVENLABS_API_KEY: Optional[str] = None
    
    # Security
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
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
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
