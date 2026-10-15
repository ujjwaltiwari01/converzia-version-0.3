"""
Converzia — AI B2B Sales Outreach Platform
FastAPI Application Entry Point
------------------------------------------
Features:
- Enterprise API documentation via Swagger UI (/docs) and ReDoc (/redoc).
- Asynchronous lifespan management (auto-initializes PostgreSQL/SQLite schema on startup).
- Cross-Origin Resource Sharing (CORS) middleware.
- Centralized structured logging and global error handling.

INTERVIEW TALKING POINT:
- Demonstrates modern FastAPI with lifespan async context managers (replacing deprecated on_event).
- Clean separation of concerns: API routing, database sessions, business pipelines, and background workers.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logger import logger
from app.db.session import init_db
from app.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifespan Event Handler:
    Runs startup tasks (database migration, health checks)
    and graceful teardown on shutdown.
    """
    logger.info("Initializing Converzia AI Outreach Engine...")
    # Auto-initialize database tables
    try:
        init_db()
        logger.info("Database tables verified/created successfully.")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

    yield

    logger.info("Shutting down Converzia platform gracefully.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description=(
        "Production-grade B2B cold outreach engine powered by LangChain LLM pipelines, "
        "autonomous SDR agents, PostgreSQL telemetry, and deliverability optimization."
    ),
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Enable CORS for external dashboards and integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global catch-all exception handler to return clean JSON errors."""
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please check server logs."}
    )


# Mount Version 1 API routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Health"])
def root():
    """Root health and system status endpoint."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "status": "operational",
        "docs_url": "/docs",
        "endpoints": {
            "leads": f"{settings.API_V1_STR}/leads",
            "campaigns": f"{settings.API_V1_STR}/campaigns",
            "outreach": f"{settings.API_V1_STR}/outreach",
            "sdr_agent": f"{settings.API_V1_STR}/sdr",
            "telemetry": f"{settings.API_V1_STR}/tracking",
            "analytics": f"{settings.API_V1_STR}/analytics/overview"
        }
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Liveness probe for container orchestrators (Kubernetes / Docker Compose)."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
