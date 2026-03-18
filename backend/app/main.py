"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.routes import health, repository, podcast

settings = get_settings()
logger = logging.getLogger(__name__)


def _configure_logging():
    """Ensure backend logs are visible when no external logging config is provided."""
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    _configure_logging()
    Path(settings.temp_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.audio_output_dir).mkdir(parents=True, exist_ok=True)
    logger.info(
        "Backend startup complete",
        extra={
            "temp_dir": settings.temp_dir,
            "audio_output_dir": settings.audio_output_dir,
        },
    )
    yield
    # Shutdown (cleanup if needed)
    logger.info("Backend shutdown")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Convert GitHub repositories into educational audio explanations",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(repository.router, prefix="/api/v1/repository", tags=["Repository"])
app.include_router(podcast.router, prefix="/api/v1/podcast", tags=["Podcast"])
