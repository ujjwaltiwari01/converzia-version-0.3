"""
Structured Logging Configuration
--------------------------------
Provides unified, formatted logging across API routers, background workers,
and the LangChain pipeline for observability and audit trails.

INTERVIEW TALKING POINT:
- Standardized logging format allows seamless shipping to ELK, Datadog, or CloudWatch in production.
"""

import logging
import sys
from app.core.config import settings

def setup_logger(name: str = "converzia") -> logging.Logger:
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if already initialized
    if not logger.handlers:
        level = logging.DEBUG if settings.DEBUG else logging.INFO
        logger.setLevel(level)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

logger = setup_logger("converzia")
