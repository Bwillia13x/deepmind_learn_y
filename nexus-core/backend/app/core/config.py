"""
NEXUS Backend Application Configuration.

Handles environment variables and application settings with privacy-first defaults.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"
    app_name: str = "NEXUS"
    app_version: str = "0.1.0"

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/nexus"
    )
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None

    # Security
    jwt_secret: str = Field(min_length=32, default="development-secret-key-min-32-chars!!")
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    encryption_key: str | None = None

    # LLM Providers - OpenAI
    openai_api_key: str | None = None
    openai_realtime_model: str = "gpt-4o-realtime-preview-2024-12-17"
    openai_model: str = "gpt-4o-mini"

    # LLM Providers - Azure OpenAI (for enterprise/education compliance)
    azure_openai_endpoint: str | None = None
    azure_openai_key: str | None = None
    azure_openai_deployment: str | None = None
    azure_openai_version: str = "2024-02-15-preview"

    # LLM Providers - Google
    google_api_key: str | None = None
    gemini_model: str = "gemini-pro"

    # Azure Speech (separate from OpenAI)
    azure_speech_key: str | None = None
    azure_speech_region: str | None = None

    # Default LLM provider (auto, openai, azure_openai, gemini, mock)
    llm_provider: str = "auto"

    # CORS
    allowed_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse comma-separated CORS origins string into list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def has_openai(self) -> bool:
        """Check if OpenAI API key is configured."""
        return bool(self.openai_api_key)

    @property
    def has_azure_openai(self) -> bool:
        """Check if Azure OpenAI is configured."""
        return bool(self.azure_openai_endpoint and self.azure_openai_key)

    @property
    def has_gemini(self) -> bool:
        """Check if Google Gemini is configured."""
        return bool(self.google_api_key)


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


# Export singleton for easy import
settings = get_settings()
