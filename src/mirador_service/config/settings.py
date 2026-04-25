"""Application settings — sourced from env vars / .env file.

Mirrors Spring Boot's `application.yml` + `@ConfigurationProperties` pattern.
Pydantic v2's `BaseSettings` provides typed access + validation + auto env-var
parsing (e.g. `DB_HOST` env → `db_host: str` field).

Conventions :
- `MIRADOR_` prefix for app-specific vars (avoids collision with system vars).
- Nested sections via `model_config.env_nested_delimiter='__'` (e.g. `MIRADOR_DB__HOST`).
- Defaults sane for local dev ; production overrides via env.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Postgres connection settings."""

    host: str = "localhost"
    port: int = 5432
    name: str = "mirador"
    user: str = "mirador"
    password: str = "mirador"  # noqa: S105 — local dev default, override in prod

    @property
    def url(self) -> str:
        """SQLAlchemy async DSN."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class RedisSettings(BaseSettings):
    """Redis connection settings."""

    host: str = "localhost"
    port: int = 6379
    db: int = 0


class KafkaSettings(BaseSettings):
    """Kafka connection settings."""

    bootstrap_servers: str = "localhost:9092"
    customer_request_topic: str = "customer.enrich.request"
    customer_reply_topic: str = "customer.enrich.reply"
    customer_created_topic: str = "customer.created"
    enrich_timeout_seconds: int = 5


class JwtSettings(BaseSettings):
    """JWT signing settings."""

    secret: str = "change-me-in-prod"  # noqa: S105
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30


class Settings(BaseSettings):
    """Top-level application settings."""

    model_config = SettingsConfigDict(
        env_prefix="MIRADOR_",
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server
    server_host: str = "0.0.0.0"  # noqa: S104 — intentional bind-all in container
    server_port: int = 8080
    dev_mode: bool = False

    # Sub-sections
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    kafka: KafkaSettings = Field(default_factory=KafkaSettings)
    jwt: JwtSettings = Field(default_factory=JwtSettings)

    # OTel
    otel_endpoint: str = "http://localhost:4318"
    otel_service_name: str = "mirador-service-python"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached singleton — DI via FastAPI `Depends(get_settings)`."""
    return Settings()
