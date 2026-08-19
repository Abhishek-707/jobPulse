from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    ingestion_router,
    jobs_router,
    sources_router,
)
from app.config import settings


logging.basicConfig(
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""

    try:
        from app.database import Base, engine

        logger.info(
            "Creating database tables..."
        )

        Base.metadata.create_all(
            bind=engine
        )

        logger.info(
            "Database tables ready"
        )

    except Exception as exc:
        logger.exception(
            "Database initialization failed: %s",
            exc,
        )

        # Do not start a supposedly healthy API
        # when the database is unavailable.
        raise

    yield


app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=(
        "JobPulse — Resilient Job Intelligence Engine"
    ),
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    jobs_router
)

app.include_router(
    sources_router
)

app.include_router(
    ingestion_router
)


@app.get("/health")
def health_check():
    """Application health endpoint."""

    return {
        "status": "healthy",
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/")
def root():
    """API root."""

    return {
        "message": (
            "JobPulse API — "
            "Resilient Job Intelligence Engine"
        ),
        "docs": "/docs",
        "openapi": "/openapi.json",
    }