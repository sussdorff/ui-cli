"""Configuration management using pydantic-settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="UNIFI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: str = Field(
        default="",
        description="UniFi API key for authentication",
    )
    api_url: str = Field(
        default="https://api.ui.com/v1",
        description="UniFi API base URL",
    )
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds",
    )

    @property
    def is_configured(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)


# Global settings instance
settings = Settings()
