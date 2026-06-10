"""Application settings.

Loaded from environment variables / ``.env`` via pydantic-settings.
All deployment-specific values (DB URL, secret key, cloud region, ...) live
here so nothing is hard-coded. See ``.env.example`` for the full list.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # --- Database (PostgreSQL on an EU/Frankfurt cloud region, spec §9.4) --
    DATABASE_URL: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/attendance"
    )

    # --- CORS (Flutter desktop client) -------------------------------------
    BACKEND_CORS_ORIGINS: list[str] = ["*"]

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
