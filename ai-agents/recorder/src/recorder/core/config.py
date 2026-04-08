"""Application configuration via Pydantic Settings.

All environment variables are declared here.
Never hardcode secrets — always use settings.*
"""

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://recorder_user:password@localhost:5436/recorder_db"

    # ── Security ──────────────────────────────────────────────────────────────
    secret_key: str = "change_me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 8  # 8 hours

    # ── CORS ──────────────────────────────────────────────────────────────────
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8100"]

    # ── LLM Provider ─────────────────────────────────────────────────────────
    active_llm_provider: str = "anthropic"  # anthropic | openai | groq | qwen
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    groq_api_key: str = ""
    qwen_api_key: str = ""

    # ── OBS Pipeline ─────────────────────────────────────────────────────────
    obs_watch_folder: str = "./data/segments"
    whisper_model: str = "large-v3"
    segment_duration_secs: int = 120
    file_watcher_debounce_secs: int = 3

    # ── Vector Store ─────────────────────────────────────────────────────────
    chroma_persist_dir: str = "./data/chroma"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # ── Voice Interface ───────────────────────────────────────────────────────
    voice_enabled: bool = True
    tts_provider: str = "openai"  # openai | elevenlabs | kokoro
    tts_output_device_index: int = 1
    tts_voice: str = "alloy"
    wake_word: str = "hey nexus"
    activation_hotkey: str = "ctrl+space"
    stt_listen_duration_secs: int = 8
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""

    # ── Storage ───────────────────────────────────────────────────────────────
    data_dir: str = "./data"
    raw_code_dir: str = "./data/code"
    segments_dir: str = "./data/segments"
    exports_dir: str = "./data/exports"

    # ── Code Indexer ─────────────────────────────────────────────────────────
    code_index_extra_exclusions: str = ""  # comma-separated additional exclusions

    # ── External Integrations ─────────────────────────────────────────────────
    jira_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""

    github_token: str = ""
    gitlab_token: str = ""
    gitlab_url: str = "https://gitlab.com"

    confluence_url: str = ""
    confluence_token: str = ""

    sharepoint_tenant_id: str = ""
    sharepoint_client_id: str = ""
    sharepoint_client_secret: str = ""

    @property
    def code_exclusions(self) -> list[str]:
        built_in = [
            ".env", "secrets/", "credentials/", "*.key", "*.pem",
            "node_modules/", "__pycache__/", "dist/", "build/", ".git/",
            "*.egg-info/", ".venv/", "venv/",
        ]
        if self.code_index_extra_exclusions:
            extras = [e.strip() for e in self.code_index_extra_exclusions.split(",") if e.strip()]
            return built_in + extras
        return built_in


settings = Settings()
