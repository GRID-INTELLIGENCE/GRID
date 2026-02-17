import logging
import os

from pydantic import PostgresDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = "GRID API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Server
    SERVER_HOST: str = "0.0.0.0"  # noqa: S104 bind-all is intentional for container deployment
    SERVER_PORT: int = 8000
    DEBUG: bool = False

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "grid"
    POSTGRES_PASSWORD: str = "grid"
    POSTGRES_DB: str = "grid"
    POSTGRES_PORT: int = 5432

    @property
    def DATABASE_URI(self) -> str:
        return str(
            PostgresDsn.build(
                scheme="postgresql",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_SERVER,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            )
        )

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None

    @property
    def REDIS_URI(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # Reduced from 8 days (60*24*8) to 30 minutes
    ALGORITHM: str = "HS256"

    @model_validator(mode="after")
    def _validate_secret_key(self) -> "Settings":
        """Validate SECRET_KEY strength — mirrors mothership secret_validation."""
        environment = os.getenv("GRID_ENVIRONMENT", "development").lower()
        weak_patterns = [
            "your-secret-key",
            "change-in-production",
            "password",
            "123456",
            "insecure",
            "default",
        ]
        key = self.SECRET_KEY
        key_lower = key.lower()
        is_weak = len(key) < 32 or any(p in key_lower for p in weak_patterns)
        if is_weak and environment == "production":
            raise ValueError(
                "SECRET_KEY is too weak for production. Set GRID_SECRET_KEY to a value >= 32 chars with good entropy."
            )
        if is_weak:
            _logger.warning(
                "SECURITY WARNING: SECRET_KEY appears weak (length=%d). "
                "Set GRID_SECRET_KEY before deploying to production.",
                len(key),
            )
        return self

    PASSWORD_MIN_LENGTH: int = 12
    PASSWORD_COMPLEXITY_SCORE: int = 3

    # Rate Limiting

    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds

    # Privacy
    PRIVACY_LEVEL: str = "balanced"  # strict, balanced, minimal

    # External Services
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    HUGGINGFACE_API_KEY: str | None = None

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", env_file_encoding="utf-8", extra="ignore")


# Global settings instance
settings = Settings()
