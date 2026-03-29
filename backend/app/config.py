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
        extra="ignore",
    )

    # API Keys
    dashscope_api_key: Optional[str] = None

    # Application
    app_name: str = "Podcast-Anything"
    app_version: str = "0.1.0"
    debug: bool = False
    e2e_mock_pipeline: bool = False
    e2e_skip_tts: bool = False

    # CORS
    cors_allow_all: bool = False
    cors_allow_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    cors_allow_credentials: bool = True
    cors_allow_methods: str = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    cors_allow_headers: str = "*"

    # Paths
    temp_dir: str = "/tmp/podcast-anything"
    audio_output_dir: str = "/tmp/podcast-anything/audio"
    claude_output_dir: str = "/tmp/podcast-anything/claude-output"
    chat_db_path: str = "/tmp/podcast-anything/chat.sqlite3"

    # TTS Settings
    tts_model: str = "qwen3-tts-flash"
    tts_voice: str = "Cherry"
    tts_chunk_size: int = 500

    # Chat settings
    chat_max_context_chars: int = 16000
    chat_retrieval_top_k: int = 6
    chat_chunk_size: int = 1200
    chat_chunk_overlap: int = 160
    chat_generation_timeout_seconds: float = 20.0
    chat_generation_retries: int = 1

    # Redis (for Celery)
    redis_url: str = "redis://localhost:6379/0"

    @staticmethod
    def _parse_csv(value: str) -> list[str]:
        return [item.strip() for item in value.split(",") if item.strip()]

    @property
    def is_configured(self) -> bool:
        """Check if required API keys are configured."""
        return bool(self.dashscope_api_key)

    @property
    def cors_allow_origins_list(self) -> list[str]:
        """Return normalized CORS origin allowlist."""
        return self._parse_csv(self.cors_allow_origins)

    @property
    def cors_allow_methods_list(self) -> list[str]:
        """Return normalized CORS method allowlist."""
        return self._parse_csv(self.cors_allow_methods)

    @property
    def cors_allow_headers_list(self) -> list[str]:
        """Return normalized CORS header allowlist."""
        return self._parse_csv(self.cors_allow_headers)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
