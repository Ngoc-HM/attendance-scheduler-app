"""FastAPI application entry point.

Run locally with::

    uvicorn app.main:app --reload

Interactive docs at ``/docs``. Database schema is provisioned by Alembic
(``alembic upgrade head``), not at startup.

Startup order: environment guard (refuse unsafe production settings) →
bootstrap (tables in dev, seed admin) → day-20 autorun scheduler.
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
from app.core.config import settings
from app.core.database import engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN201
    # Guard: a staging/prod process must not run with dev secrets/passwords.
    settings.validate_for_environment()
    for warning in settings.production_config_warnings():
        logger.warning("Configuration: %s", warning)
    # Startup: ensure tables (dev) and the seed admin exist (F-01).
    run_startup_bootstrap()
    # Day-20 autorun: close registration + generate next month's draft (#9).
    from app.services.schedule_autorun import start_scheduler

    scheduler = start_scheduler()
    yield
    if scheduler is not None:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
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
