"""
PAIOS Centralized Configuration.

Single source of truth for all application settings.
Uses Pydantic Settings for validation, type safety, and environment variable loading.

Usage:
    from app.core.config import get_settings
    settings = get_settings()
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, MongoDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # backend/
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Immutable application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────────────────
    app_name: str = "PAIOS"
    app_version: str = "0.2.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    api_prefix: str = "/api/v1"

    # ── MongoDB ────────────────────────────────────────────────────────────
    mongodb_uri: str = Field(
        ...,
        description="MongoDB Atlas connection string",
    )
    database_name: str = Field(default="AGENT", description="MongoDB database name")

    # ── Security / JWT ─────────────────────────────────────────────────────
    secret_key: str = Field(
        ...,
        min_length=32,
        description="JWT signing key (min 32 chars)",
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # ── Encryption (Fernet) ────────────────────────────────────────────────
    encryption_key: str = Field(
        default="",
        description="Fernet encryption key for PII. Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'",
    )

    # ── Ollama (Local AI) ──────────────────────────────────────────────────
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama API base URL",
    )
    ollama_default_model: str = Field(
        default="llama3.1:8b",
        description="Default Ollama model for inference",
    )
    ollama_timeout_seconds: int = Field(
        default=120,
        description="Timeout for Ollama API calls",
    )
    ollama_max_retries: int = Field(
        default=3,
        description="Max retries for failed Ollama calls",
    )

    # ── Groq (Optional Fallback) ───────────────────────────────────────────
    groq_api_key: str = Field(
        default="",
        description="Groq API key (optional dev fallback)",
    )
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        description="Groq model name for fallback",
    )
    use_groq_fallback: bool = Field(
        default=False,
        description="Fall back to Groq if Ollama unavailable",
    )

    # ── Redis ──────────────────────────────────────────────────────────────
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )
    use_redis_event_bus: bool = Field(
        default=False,
        description="Use Redis pub/sub instead of in-memory event bus",
    )

    # ── File Storage ───────────────────────────────────────────────────────
    upload_dir: Path = Field(
        default=_PROJECT_ROOT / "uploads",
        description="Base directory for uploaded files",
    )
    max_upload_size_mb: int = Field(default=10, description="Max upload size in MB")

    # ── Logging ────────────────────────────────────────────────────────────
    log_level: str = Field(default="INFO", description="Root log level")
    log_format: Literal["json", "console"] = Field(
        default="console",
        description="Log output format: 'json' for production, 'console' for dev",
    )

    # ── Scheduler ──────────────────────────────────────────────────────────
    scheduler_enabled: bool = True
    job_collection_interval_minutes: int = Field(
        default=15,
        description="Interval between job collection runs",
    )

    # ── Celery (Background Tasks) ──────────────────────────────────────────
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1",
        description="Celery broker connection URL",
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/1",
        description="Celery result backend URL",
    )

    # ── ChromaDB (Vector Store) ────────────────────────────────────────────
    chroma_persist_dir: str = Field(
        default="chroma_db",
        description="Directory to store ChromaDB local files",
    )
    chroma_host: str = Field(
        default="",
        description="Remote ChromaDB host. If empty, runs in-process.",
    )
    chroma_port: int = Field(
        default=8000,
        description="Remote ChromaDB port.",
    )

    # ── Playwright (Browser Scraper) ───────────────────────────────────────
    playwright_headless: bool = Field(
        default=True,
        description="Run Playwright browser in headless mode",
    )
    playwright_timeout_ms: int = Field(
        default=30000,
        description="Global timeout for browser navigation in milliseconds",
    )

    # ── Notifications ──────────────────────────────────────────────────────
    telegram_bot_token: str = Field(default="", description="Telegram Bot token")
    telegram_chat_id: str = Field(default="", description="Telegram Chat ID for alerts")
    discord_webhook_url: str = Field(default="", description="Discord Webhook URL for logs/alerts")
    smtp_host: str = Field(default="", description="SMTP email host")
    smtp_port: int = Field(default=587, description="SMTP email port")
    smtp_username: str = Field(default="", description="SMTP username")
    smtp_password: str = Field(default="", description="SMTP password")
    smtp_from_email: str = Field(default="", description="SMTP sender address")

    # ── CORS ───────────────────────────────────────────────────────────────
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        description="Allowed CORS origins",
    )

    # ── Derived properties ─────────────────────────────────────────────────
    @property
    def upload_resumes_dir(self) -> Path:
        return self.upload_dir / "resumes"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}, got '{v}'")
        return upper


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the singleton Settings instance.

    Uses lru_cache so the .env file is read only once.
    Call `get_settings.cache_clear()` in tests to reload.
    """
    return Settings()  # type: ignore[call-arg]
