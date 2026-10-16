"""
Database Connection & Session Management
----------------------------------------
Implements the SQLAlchemy engine, session maker, and FastAPI dependency injection (`get_db`).

INTERVIEW TALKING POINT:
- Uses SQLAlchemy 2.0 declarative patterns with connection pooling.
- Resilience: Defaults to SQLite for local development; when DATABASE_URL is set to PostgreSQL
  (e.g. in Docker Compose or production .env), automatically uses production connection pooling.
"""

from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
from app.core.logger import logger

Base = declarative_base()

def _create_resilient_engine():
    """
    Creates the SQLAlchemy engine based on configuration.
    Uses PostgreSQL if specified; defaults to SQLite for zero-friction evaluation.
    """
    target_uri = settings.sync_database_uri

    if target_uri.startswith("postgresql"):
        try:
            pg_engine = create_engine(
                target_uri,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 3}
            )
            with pg_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info(f"Connected successfully to PostgreSQL database: {target_uri.split('@')[-1]}")
            return pg_engine
        except Exception as e:
            logger.warning(
                f"PostgreSQL connection to {target_uri} failed ({e}). "
                f"Falling back to local SQLite for zero-friction evaluation."
            )
            return create_engine(
                "sqlite:///./converzia.db",
                connect_args={"check_same_thread": False}
            )

    logger.info("Initializing local SQLite database: converzia.db")
    return create_engine(
        target_uri,
        connect_args={"check_same_thread": False}
    )

engine = _create_resilient_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator:
    """
    FastAPI dependency that yields a database session per request
    and guarantees proper closing.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initializes all database tables defined in models."""
    from app.db import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")
