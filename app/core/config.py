"""
Application Configuration Module
--------------------------------
Uses Pydantic BaseSettings to enforce type-safe environment configurations.
Loads variables from .env or system environment with sensible defaults.

INTERVIEW TALKING POINT:
- Centralized 12-factor application configuration.
- Graceful fallbacks: If PostgreSQL is not provided, defaults to SQLite for local development,
  ensuring anyone cloning the repo can run tests and the app immediately without standing up a DB container.
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
    # SYSTEM DESIGN NOTE: Production uses PostgreSQL with connection pooling.
    # Fallback to local SQLite enables seamless zero-config evaluation.
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "converzia_db"
    DATABASE_URL: Optional[str] = None

    @property
    def sync_database_uri(self) -> str:
        """Returns the active SQLAlchemy database URI."""
        if self.DATABASE_URL and self.DATABASE_URL.strip():
            # Ensure standard postgresql driver format
            uri = self.DATABASE_URL
            if uri.startswith("postgres://"):
                uri = uri.replace("postgres://", "postgresql://", 1)
            return uri
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # --- LLM & LangChain Configuration ---
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"  # Cost-effective, high-reasoning model for high-volume outreach
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    LLM_TEMPERATURE: float = 0.3  # Low temperature for grounded personalization, high enough for natural tone

    # --- Email Dispatcher Configuration (Brevo / Sendinblue / SMTP) ---
    BREVO_API_KEY: Optional[str] = None
    SENDER_EMAIL: str = "outreach@converzia.ai"
    SENDER_NAME: str = "Converzia Sales Team"
    USE_MOCK_DISPATCHER: bool = False  # Set to True for testing without sending real emails

    # --- CRM Integrations (HubSpot) ---
    HUBSPOT_ACCESS_TOKEN: Optional[str] = None
    HUBSPOT_ENABLED: bool = False

    # --- Outreach & SDR Engine Parameters ---
    # Targets: 1,000 leads/day processing, 50-70% open rate optimization
    MAX_DAILY_LEAD_CAPACITY: int = 1000
    SCRAPER_TIMEOUT_SECONDS: int = 12
    SCRAPER_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    MAX_CONCURRENT_SCRAPES: int = 10  # Concurrency limit for website intelligence gathering
    BASE_TRACKING_URL: str = "http://localhost:8000/api/v1/tracking"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
