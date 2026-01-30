"""Configuration management using Pydantic settings."""

from pathlib import Path
from typing import Any

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Benchmark system settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database Configuration
    database_url: PostgresDsn = Field(
        ...,
        description="PostgreSQL database URL",
    )

    # Storage Configuration
    data_dir: Path = Field(default=Path("/data"), description="Data storage directory")
    results_dir: Path = Field(default=Path("/results"), description="Results storage directory")
    cache_dir: Path = Field(default=Path("/cache"), description="Cache storage directory")

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="json", description="Logging format (json or text)"
    )

    # Environment
    environment: str = Field(default="development", description="Environment name")

    @field_validator("data_dir", "results_dir", "cache_dir", mode="before")
    @classmethod
    def validate_path(cls, v: Any) -> Path:
        """Convert string to Path."""
        if isinstance(v, str):
            return Path(v)
        return v

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        for directory in [self.data_dir, self.results_dir, self.cache_dir]:
            directory.mkdir(parents=True, exist_ok=True)


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get or create global settings instance.

    Returns:
        Settings: Global settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
