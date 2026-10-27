"""Application configuration loaded from environment variables.

No external settings library needed — a small dataclass keeps the
footprint light and the behaviour obvious.
"""

import os
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    app_name: str = "Sage"
    app_version: str = "1.0.0"
    environment: str = "development"

    database_url: str = "sqlite:///./sage.db"
    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    max_upload_bytes: int = 20 * 1024 * 1024  # 20 MB
    allowed_extensions: tuple[str, ...] = (".txt", ".md", ".pdf")

    rate_limit: str = "100/minute"
    cors_origins: list[str] = field(default_factory=lambda: ["*"])

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_name=os.getenv("APP_NAME", "Sage"),
            app_version=os.getenv("APP_VERSION", "1.0.0"),
            environment=os.getenv("ENVIRONMENT", "development"),
            database_url=os.getenv("DATABASE_URL", "sqlite:///./sage.db"),
            secret_key=os.getenv("SECRET_KEY", "change-me-in-production"),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")),
            max_upload_bytes=int(os.getenv("MAX_UPLOAD_BYTES", str(20 * 1024 * 1024))),
            allowed_extensions=tuple(
                e.strip().lower()
                for e in os.getenv("ALLOWED_EXTENSIONS", ".txt,.md,.pdf").split(",")
                if e.strip()
            ),
            rate_limit=os.getenv("RATE_LIMIT", "100/minute"),
            cors_origins=[
                o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()
            ],
        )


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()
