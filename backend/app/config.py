"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # API Keys
    anthropic_api_key: Optional[str] = None
    dashscope_api_key: Optional[str] = None

    # Application
    app_name: str = "Podcast-Anything"
    app_version: str = "0.1.0"
    debug: bool = False

    # Paths
    temp_dir: str = "/tmp/podcast-anything"
    audio_output_dir: str = "/tmp/podcast-anything/audio"

    # TTS Settings
    tts_model: str = "qwen3-tts-flash"
    tts_voice: str = "Cherry"
    tts_chunk_size: int = 500

    # Redis (for Celery)
    redis_url: str = "redis://localhost:6379/0"

    @property
    def is_configured(self) -> bool:
        """Check if required API keys are configured."""
        return bool(self.anthropic_api_key and self.dashscope_api_key)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
