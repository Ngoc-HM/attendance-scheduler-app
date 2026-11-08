"""Application settings.

Loaded from environment variables / ``.env`` via pydantic-settings.
All deployment-specific values (DB URL, secret key, cloud region, ...) live
here so nothing is hard-coded. See ``.env.example`` for the full list.
"""

from __future__ import annotations

from datetime import date
from functools import lru_cache
from typing import Annotated, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from sqlalchemy.engine.url import make_url

# Dev-only defaults. ``validate_for_environment`` refuses to start a
# staging/prod process that still carries them.
_DEFAULT_SECRET_KEY = "CHANGE_ME_dev_only_secret"
_DEFAULT_ADMIN_PASSWORD = "admin123"
_DEFAULT_DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/attendance"
_MIN_SECRET_LENGTH = 32
_MIN_ADMIN_PASSWORD_LENGTH = 12
# German working-time records must be kept at least 24 months (ArbZG §16(2)).
# DATA_RETENTION_MIN_MONTHS may raise this floor; the env can never lower it.
LEGAL_RETENTION_FLOOR_MONTHS = 24


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
    SECRET_KEY: str = _DEFAULT_SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # --- First admin (F-01 bootstrap) --------------------------------------
    # On startup the seed admin (role M) is created if missing. In DEV only,
    # an existing seed admin has its password reset to FIRST_ADMIN_PASSWORD
    # when FIRST_ADMIN_RESET_ON_STARTUP is on (one-click local login). In
    # staging/prod an existing admin's credentials are NEVER touched.
    FIRST_ADMIN_USERNAME: str = "admin"
    FIRST_ADMIN_PASSWORD: str = _DEFAULT_ADMIN_PASSWORD
    FIRST_ADMIN_FULL_NAME: str = "System Administrator"
    FIRST_ADMIN_RESET_ON_STARTUP: bool = True
    # Create DB tables on startup in dev (no Alembic step needed to run locally);
    # skipped once the database has ``alembic_version``. Refused in
    # staging/prod: manage the schema with Alembic migrations there.
    AUTO_CREATE_TABLES: bool = True

    # --- Database (PostgreSQL on an EU/Frankfurt cloud region, spec §9.4) --
    DATABASE_URL: str = _DEFAULT_DATABASE_URL

    # --- CORS (Flutter desktop client) -------------------------------------
    # ``NoDecode`` skips pydantic-settings' JSON pre-parse so the validator
    # below can accept a plain ``*`` or a comma-separated list from the env.
    # ``*`` is dev only: staging/prod refuse to start with it.
    BACKEND_CORS_ORIGINS: Annotated[list[str], NoDecode] = ["*"]

    # --- i18n: English primary, Vietnamese optional (spec §2) --------------
    DEFAULT_LANGUAGE: Literal["en", "vi"] = "en"

    # --- Frankfurt local time (STA/STD LT FRA, spec §8) --------------------
    TIMEZONE: str = "Europe/Berlin"

    # --- GDPR / BDSG compliance posture (spec §9) --------------------------
    # Deploy in an EU region (Frankfurt) — keep personnel data inside the
    # EU/EEA (§9.4). Sign a DPA with the cloud provider (Art. 28 GDPR).
    DATA_REGION: str = "eu-central-1"  # Frankfurt
    # The scheduler is rule-based (OR-Tools CP-SAT). It performs NO AI/ML
    # performance evaluation of staff (§9.6 / EU AI Act). Do not introduce
    # ML scoring of employees without a fresh legal review.
    SCHEDULER_IS_RULE_BASED: bool = True

    # --- Scheduler engine (OR-Tools) limits --------------------------------
    SOLVER_MAX_TIME_SECONDS: float = 30.0

    # --- Holiday comp days (owner decision D1, 2026-11-06) ------------------
    # Working a public holiday earns one CD for every role, but only for
    # holidays on/after this date: earlier holiday work earns nothing, so a
    # live database does not get a lump of back-owed CDs on the next draft.
    HOLIDAY_COMP_EFFECTIVE_FROM: date = date(2026, 11, 6)

    # --- Annual leave quota (owner decision D4, 2026-11-06) -----------------
    # Days of leave per calendar year a new user starts with; the admin edits
    # each person's quota afterwards. PLACEHOLDER until the customer confirms
    # the real figure. Remaining = quota - approved leave days in the year.
    ANNUAL_LEAVE_DEFAULT_DAYS: int = 30

    # --- Autorun (locked decision #9, F-05/F-07) ----------------------------
    # AUTORUN_DAY is the last day of the monthly leave window; at 00:05 on the
    # day after, the background job generates the next month's DRAFT (skips if
    # a schedule already exists). Manual generate stays available regardless.
    # Capped at 27 so AUTORUN_DAY + 1 exists in every month (February: 28).
    AUTORUN_ENABLED: bool = True
    AUTORUN_DAY: int = Field(default=20, ge=1, le=27)

    # --- Data retention (§9.3 / §26 BDSG data minimization) ----------------
    # Personnel records older than this are removed by the admin retention
    # purge (``/compliance/retention/purge``). German working-time records
    # must be kept at least 24 months (ArbZG §16(2)); the customer's DPO owns
    # the final figure — 36 months is the shipped default.
    DATA_RETENTION_MONTHS: int = 36
    DATA_RETENTION_MIN_MONTHS: int = LEGAL_RETENTION_FLOOR_MONTHS

    # --- Environment guard -------------------------------------------------
    @property
    def is_production(self) -> bool:
        """staging and prod are both production-like: no dev conveniences."""
        return self.ENVIRONMENT != "dev"

    @property
    def retention_floor_months(self) -> int:
        """The effective retention floor: never below the legal 24 months."""
        return max(LEGAL_RETENTION_FLOOR_MONTHS, self.DATA_RETENTION_MIN_MONTHS)

    def production_config_errors(self) -> list[str]:
        """Unsafe defaults that must never reach a production-like process."""
        if not self.is_production:
            return []
        errors: list[str] = []
        if self.SECRET_KEY == _DEFAULT_SECRET_KEY or len(self.SECRET_KEY) < _MIN_SECRET_LENGTH:
            errors.append(
                f"SECRET_KEY must be a random string of at least {_MIN_SECRET_LENGTH} "
                "characters (it still holds the dev default or is too short)"
            )
        if (
            self.FIRST_ADMIN_PASSWORD == _DEFAULT_ADMIN_PASSWORD
            or len(self.FIRST_ADMIN_PASSWORD) < _MIN_ADMIN_PASSWORD_LENGTH
        ):
            errors.append(
                "FIRST_ADMIN_PASSWORD must not be the dev default and needs at least "
                f"{_MIN_ADMIN_PASSWORD_LENGTH} characters"
            )
        if _is_sqlite_url(self.DATABASE_URL):
            errors.append(
                "DATABASE_URL points at SQLite; a production-like process needs the "
                "shared PostgreSQL database"
            )
        elif self.DATABASE_URL == _DEFAULT_DATABASE_URL:
            errors.append(
                "DATABASE_URL still holds the dev default (postgres:postgres@localhost)"
            )
        if "*" in self.BACKEND_CORS_ORIGINS:
            errors.append(
                "BACKEND_CORS_ORIGINS must list the allowed origins explicitly, not '*'"
            )
        if self.AUTO_CREATE_TABLES:
            errors.append(
                "AUTO_CREATE_TABLES must be false; manage the schema with "
                "'alembic upgrade head'"
            )
        if self.DATA_RETENTION_MIN_MONTHS < LEGAL_RETENTION_FLOOR_MONTHS:
            errors.append(
                f"DATA_RETENTION_MIN_MONTHS={self.DATA_RETENTION_MIN_MONTHS} is below the "
                f"legal floor of {LEGAL_RETENTION_FLOOR_MONTHS} months (ArbZG §16(2))"
            )
        if self.DATA_RETENTION_MONTHS < self.retention_floor_months:
            errors.append(
                f"DATA_RETENTION_MONTHS={self.DATA_RETENTION_MONTHS} is below the "
                f"minimum of {self.retention_floor_months} months"
            )
        return errors

    def production_config_warnings(self) -> list[str]:
        """Risky-but-allowed settings, logged loudly at startup."""
        if not self.is_production:
            return []
        warnings: list[str] = []
        if self.FIRST_ADMIN_RESET_ON_STARTUP:
            warnings.append(
                "FIRST_ADMIN_RESET_ON_STARTUP is ignored outside dev "
                "(an existing admin is never reset)"
            )
        return warnings

    def validate_for_environment(self) -> None:
        """Raise ``RuntimeError`` when a production-like process is unsafe."""
        errors = self.production_config_errors()
        if errors:
            raise RuntimeError(
                f"Refusing to start: unsafe settings for ENVIRONMENT={self.ENVIRONMENT}:\n- "
                + "\n- ".join(errors)
            )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _split_cors(cls, v: object) -> object:
        """Allow a comma-separated string in the env file."""
        if isinstance(v, str) and not v.startswith("["):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @field_validator("TIMEZONE")
    @classmethod
    def _known_timezone(cls, v: str) -> str:
        """Refuse an unknown zone at startup, in every environment: every
        business date (leave window, autorun) is computed in it."""
        try:
            ZoneInfo(v)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(f"TIMEZONE {v!r} is not a known IANA time zone") from exc
        return v


def _is_sqlite_url(url: str) -> bool:
    try:
        return make_url(url).get_backend_name() == "sqlite"
    except Exception:  # noqa: BLE001 — an unparsable URL fails at connect anyway
        return url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
