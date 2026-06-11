"""FastAPI application entry point.

Run locally with::

    uvicorn app.main:app --reload

Interactive docs at ``/docs``. Database schema is provisioned by Alembic
(``alembic upgrade head``), not at startup.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.bootstrap import run_startup_bootstrap
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN201
    # Startup: ensure tables (dev) and the seed admin exist (F-01).
    run_startup_bootstrap()
    yield
    # Shutdown hooks go here.


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(o) for o in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok", "service": settings.PROJECT_NAME}
