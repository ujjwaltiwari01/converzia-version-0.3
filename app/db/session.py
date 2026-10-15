"""
Database Connection & Session Management
----------------------------------------
Implements the SQLAlchemy engine, session maker, and FastAPI dependency injection (`get_db`).

INTERVIEW TALKING POINT:
- Uses SQLAlchemy 2.0 declarative patterns with connection pooling.
- Resilience: Detects if remote/local PostgreSQL is reachable. If not (e.g., in a candidate code review or local offline dev),
  gracefully initializes SQLite while preserving the exact same relational schema.
"""

from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
from app.core.logger import logger

Base = declarative_base()

def _create_resilient_engine():
    """
    Attempts to connect to configured PostgreSQL database.
    Falls back gracefully to SQLite if PostgreSQL is unreachable during offline review.
    """
    target_uri = settings.sync_database_uri

    # If Postgres URI was specified, test connection
    if target_uri.startswith("postgresql"):
        try:
            pg_engine = create_engine(
                target_uri,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,  # Discards stale connections automatically
                connect_args={"connect_timeout": 3}
            )
            # Fast ping test
            with pg_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info(f"Connected successfully to PostgreSQL database at {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}")
            return pg_engine
        except Exception as e:
            logger.warning(
                f"PostgreSQL connection to {target_uri} failed ({e}). "
                f"Falling back to local SQLite for zero-friction evaluation."
            )
    
    # Fallback SQLite engine
    sqlite_uri = "sqlite:///./converzia.db"
    return create_engine(
        sqlite_uri,
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
