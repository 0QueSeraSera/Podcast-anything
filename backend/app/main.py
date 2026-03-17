"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.routes import health, repository, podcast

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    Path(settings.temp_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.audio_output_dir).mkdir(parents=True, exist_ok=True)
    yield
    # Shutdown (cleanup if needed)


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
