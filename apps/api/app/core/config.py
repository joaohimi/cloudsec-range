from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CloudSec Range API"
    app_version: str = "0.4.0"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://cloudsec_app:local-only@localhost:5432/cloudsec_range"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: list[str] = ["http://localhost:3000"]
    session_cookie_name: str = "csr_session"
    csrf_cookie_name: str = "csr_csrf"
    session_ttl_hours: int = 12
    session_cookie_secure: bool = False

    model_config = SettingsConfigDict(
        env_file=None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache

def get_settings() -> Settings:
    return Settings()


settings = get_settings()
