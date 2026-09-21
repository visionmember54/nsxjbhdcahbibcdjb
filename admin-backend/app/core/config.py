from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = f"sqlite:///{DATA_DIR / 'bet_admin.db'}"

    @field_validator("DATABASE_URL")
    @classmethod
    def _normalize_postgres_scheme(cls, value: str) -> str:
        # Render (and formerly Heroku) hand out "postgres://", but SQLAlchemy 2.x
        # only recognizes "postgresql://" and raises NoSuchModuleError otherwise.
        if value.startswith("postgres://"):
            return "postgresql://" + value[len("postgres://"):]
        return value

    # No default: the app must fail to boot if this isn't set explicitly.
    JWT_SECRET: str
    JWT_ALG: str = "HS256"
    JWT_TTL_MIN: int = 480

    # "production" hides the interactive API docs.
    APP_ENV: str = "development"

    CORS_ORIGINS: str = "http://localhost:3000"
    LOGIN_MAX_FAILURES: int = 5
    LOGIN_LOCK_MINUTES: int = 15

    @property
    def cors_origins_list(self) -> list[str]:
        # A wildcard origin is invalid together with credentials, so it is never honoured.
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip() and o.strip() != "*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
