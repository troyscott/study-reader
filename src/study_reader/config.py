"""Environment-driven application configuration."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated settings shared by the reader and administration apps."""

    model_config = SettingsConfigDict(
        env_prefix="STUDY_READER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
    )

    environment: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    published_content_dir: Path = Field(default=Path("content/published"))


@lru_cache
def get_settings() -> Settings:
    """Return one validated settings object per application process."""

    return Settings()
