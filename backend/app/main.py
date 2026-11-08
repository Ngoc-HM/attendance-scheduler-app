"""FastAPI application entry point.

Run locally with::

    uvicorn app.main:app --reload

Interactive docs at ``/docs`` in dev only (disabled in staging/prod).
Database schema is provisioned by Alembic: run ``alembic upgrade head`` before
starting new code. Only in dev, and only for a brand-new database without an
``alembic_version`` table, does startup create the tables (``create_all``).

Startup order: environment guard (refuse unsafe production settings) →
bootstrap (tables in dev, seed admin) → autorun scheduler (draft at 00:05 from
the day after AUTORUN_DAY, plus one catch-up check at startup).
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.bootstrap import run_startup_bootstrap
from app.core.config import Settings, settings
from app.core.database import engine

_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def configure_app_logging() -> None:
    """Send the ``app.*`` loggers (autorun, bootstrap, ...) to stderr at INFO.

    Uvicorn configures only its own loggers, so without this every app message
    below WARNING was dropped. The root logger is left alone (no
    ``basicConfig``), so uvicorn's output is unchanged; the handler is added
    once even when the module is imported again (``--reload``).
    """
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.INFO)
    if not any(getattr(h, "_app_console", False) for h in app_logger.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(_LOG_FORMAT))
        handler._app_console = True  # type: ignore[attr-defined]
        app_logger.addHandler(handler)


configure_app_logging()
logger = logging.getLogger(__name__)


def api_docs_urls(s: Settings) -> dict[str, str | None]:
    """Swagger, ReDoc and the OpenAPI schema are served in dev only: in
    staging/prod they would publish the full API map to anyone."""
    if s.is_production:
        return {"docs_url": None, "redoc_url": None, "openapi_url": None}
    return {
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "openapi_url": f"{s.API_V1_STR}/openapi.json",
    }


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN201
    # Guard: a staging/prod process must not run with dev secrets/passwords.
    settings.validate_for_environment()
    for warning in settings.production_config_warnings():
        logger.warning("Configuration: %s", warning)
    # Startup: ensure tables (dev) and the seed admin exist (F-01).
    run_startup_bootstrap()
    # Autorun (#9): the leave window closes at the end of AUTORUN_DAY; at 00:05
    # (settings.TIMEZONE) the day after, next month's draft is generated. The
    # startup check catches up a month missed while the host was off.
    from app.services.schedule_autorun import start_scheduler

    scheduler = start_scheduler(check_on_startup=True)
    yield
    if scheduler is not None:
        scheduler.shutdown(wait=False)


_docs = api_docs_urls(settings)
app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    docs_url=_docs["docs_url"],
    redoc_url=_docs["redoc_url"],
    openapi_url=_docs["openapi_url"],
)

if settings.BACKEND_CORS_ORIGINS:
    _origins = [str(o) for o in settings.BACKEND_CORS_ORIGINS]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        # Credentials with a wildcard origin is invalid per the CORS spec; only
        # allow them when the origin list is explicit.
        allow_credentials="*" not in _origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.middleware("http")
async def _accept_language_middleware(request, call_next):  # noqa: ANN001, ANN201
    """Serve error messages in the caller's language (Flutter sends vi/en)."""
    from app.core.i18n import set_request_language

    accept = request.headers.get("accept-language", "")
    set_request_language("vi" if accept.lower().startswith("vi") else None)
    return await call_next(request)


app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["health"])
def health() -> JSONResponse:
    """Liveness + readiness probe: 200 when the database answers, else 503."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:  # noqa: BLE001 — any DB failure means "not ready"
        logger.exception("Health check: database unreachable")
        db_ok = False
    body = {
        "status": "ok" if db_ok else "degraded",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "database": "ok" if db_ok else "unreachable",
        "autorun": settings.AUTORUN_ENABLED,
    }
    return JSONResponse(body, status_code=200 if db_ok else 503)
