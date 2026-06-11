"""Application settings.

Loaded from environment variables / ``.env`` via pydantic-settings.
All deployment-specific values (DB URL, secret key, cloud region, ...) live
here so nothing is hard-coded. See ``.env.example`` for the full list.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- General -----------------------------------------------------------
    PROJECT_NAME: str = "Attendance & Auto-Scheduler API"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: Literal["dev", "staging", "prod"] = "dev"

    # --- Security (lightweight JWT, spec §2) -------------------------------
    SECRET_KEY: str = "CHANGE_ME_dev_only_secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # --- First admin (F-01 bootstrap) --------------------------------------
    # On every backend startup the seed admin (role M) is created if missing,
    # or has its password reset back to these values if it already exists.
    # This guarantees there is always a way in; users may change the password
    # at runtime, but a restart restores the default.
    FIRST_ADMIN_USERNAME: str = "admin"
    FIRST_ADMIN_PASSWORD: str = "admin123"
    FIRST_ADMIN_FULL_NAME: str = "System Administrator"
    # Create DB tables on startup in dev (no Alembic step needed to run locally).
    # In prod, manage schema with Alembic migrations instead.
    AUTO_CREATE_TABLES: bool = True

    # --- Database (PostgreSQL on an EU/Frankfurt cloud region, spec §9.4) --
    DATABASE_URL: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/attendance"
    )

    # --- CORS (Flutter desktop client) -------------------------------------
    # ``NoDecode`` skips pydantic-settings' JSON pre-parse so the validator
    # below can accept a plain ``*`` or a comma-separated list from the env.
    BACKEND_CORS_ORIGINS: Annotated[list[str], NoDecode] = ["*"]

    # --- i18n: English primary, Vietnamese optional (spec §2) --------------
    DEFAULT_LANGUAGE: Literal["en", "vi"] = "en"

    # --- Frankfurt local time (STA/STD LT FRA, spec §8) --------------------
    TIMEZONE: str = "Europe/Berlin"

    # --- Scheduler engine (OR-Tools) limits --------------------------------
    SOLVER_MAX_TIME_SECONDS: float = 30.0

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _split_cors(cls, v: object) -> object:
        """Allow a comma-separated string in the env file."""
        if isinstance(v, str) and not v.startswith("["):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
