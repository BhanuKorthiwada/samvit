"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "SAMVIT"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "text"] = "text"

    # API
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = "sqlite+aiosqlite:///./samvit_test.db"
    db_pool_size: int = 5
    db_pool_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600

    # Security
    secret_key: str = "your-super-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    bcrypt_rounds: int = 12

    # Multi-tenancy
    # Base domain for subdomain extraction (e.g., "samvit.bhanu.dev")
    base_domain: str = "samvit.bhanu.dev"
    # Reserved domains that cannot be used as tenant domains
    reserved_domains: list[str] = [
        "app.samvit.bhanu.dev",
        "www.samvit.bhanu.dev",
        "api.samvit.bhanu.dev",
        "admin.samvit.bhanu.dev",
    ]

    # CORS
    cors_origins: list[str] = ["http://localhost:3010", "http://localhost:3000"]

    # Rate Limiting
    rate_limit_per_minute: int = 60

    # AI/LLM
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    google_api_key: str | None = None

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str, info: object) -> str:
        """Ensure secret key is secure in production."""
        # Access other field values via info.data in Pydantic v2
        data = getattr(info, "data", {})
        env = data.get("environment", "development")
        default_key = "your-super-secret-key-change-in-production"
        if env == "production" and v == default_key:
            raise ValueError("SECRET_KEY must be changed in production!")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
