"""Global configuration management.

This module exposes a simple ``Settings`` class that reads environment
variables or falls back to sensible defaults.  The values mirror those in
``.env.example``.
"""
from functools import lru_cache
from pydantic import BaseSettings


class Settings(BaseSettings):
    secret_key: str = "supersecretkey"
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"
    database_url: str = "sqlite:///./test.db"
    redis_url: str = "redis://localhost:6379/0"

    class Config:
        env_prefix = ""
        case_sensitive = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
