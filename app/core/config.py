"""
Application Configuration Module
--------------------------------
Uses Pydantic BaseSettings to enforce type-safe environment configurations.
Loads variables from .env or system environment with sensible defaults.

INTERVIEW TALKING POINT:
- Centralized 12-factor application configuration.
- Zero-friction defaults: Defaults to local SQLite for development and testing.
  Setting DATABASE_URL=postgresql://... seamlessly switches to production PostgreSQL with connection pooling.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Project Metadata ---
    PROJECT_NAME: str = "Converzia — AI B2B Sales Outreach Platform"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # --- Database Configuration ---
    # SYSTEM DESIGN NOTE: Defaults to SQLite for immediate, zero-friction local execution.
    # Set DATABASE_URL in .env (or via Docker Compose) to point to production PostgreSQL.
    DATABASE_URL: str = "sqlite:///./converzia.db"
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_SERVER: Optional[str] = None
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: Optional[str] = None

    @property
    def sync_database_uri(self) -> str:
        """Returns the active SQLAlchemy database URI."""
        uri = self.DATABASE_URL
        if uri.startswith("postgres://"):
            uri = uri.replace("postgres://", "postgresql://", 1)
        return uri

    # --- LLM & LangChain Configuration ---
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    LLM_TEMPERATURE: float = 0.3

    # --- Email Dispatcher Configuration (Brevo / Sendinblue / SMTP) ---
    BREVO_API_KEY: Optional[str] = None
    SENDER_EMAIL: str = "outreach@converzia.ai"
    SENDER_NAME: str = "Converzia Sales Team"
    USE_MOCK_DISPATCHER: bool = True  # Default to mock/sandbox mode so no live emails are sent accidentally

    # --- CRM Integrations (HubSpot) ---
    HUBSPOT_ACCESS_TOKEN: Optional[str] = None
    HUBSPOT_ENABLED: bool = False

    # --- Outreach & SDR Engine Parameters ---
    MAX_DAILY_LEAD_CAPACITY: int = 1000
    SCRAPER_TIMEOUT_SECONDS: int = 12
    SCRAPER_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    MAX_CONCURRENT_SCRAPES: int = 10
    BASE_TRACKING_URL: str = "http://localhost:8000/api/v1/tracking"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
