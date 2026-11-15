"""Desktop app updates (owner 2026-11-15).

The server holds the newest client builds; a running app asks
``GET /app/latest`` and, when the build number is higher than its own,
downloads its platform's package from ``GET /app/download/{platform}``,
installs it and restarts. Public on purpose: the login screen updates too,
and a package holds nothing but the app (the server URL is in every build).

Releases live in ``settings.APP_RELEASES_DIR``::

    latest.json                       manifest (written by scripts/publish_release.sh)
    <build>/RosterFRA-Setup.exe       Windows installer
    <build>/attendance-scheduler-macos.zip
    <build>/attendance-scheduler-linux-x64.tar.gz
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.config import settings
from app.core.i18n import t

router = APIRouter()

Platform = Literal["windows", "macos", "linux"]


class AppRelease(BaseModel):
    build: int
    version: str
    # Builds below this must update before they can be used.
    min_build: int = 0
    notes: str = ""
    # platform -> download path (relative to the API base) and SHA-256.
    downloads: dict[str, str] = {}
    sha256: dict[str, str] = {}


def _root() -> Path:
    return Path(settings.APP_RELEASES_DIR).resolve()


def _manifest() -> dict | None:
    path = _root() / "latest.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


@router.get("/latest", response_model=AppRelease | None)
def latest_release() -> AppRelease | None:
    """The newest published build, or null when none is published."""
    data = _manifest()
    if data is None:
        return None
    files = data.get("files", {})
    return AppRelease(
        build=int(data["build"]),
        version=str(data.get("version", "")),
        min_build=int(data.get("min_build", 0)),
        notes=str(data.get("notes", "")),
        downloads={p: f"/app/download/{p}" for p in files},
        sha256={p: str(v) for p, v in data.get("sha256", {}).items()},
    )


@router.get("/download/{platform}")
def download(platform: Platform) -> FileResponse:
    """The newest package for ``platform`` (only files listed in the manifest)."""
    data = _manifest() or {}
    name = data.get("files", {}).get(platform)
    root = _root()
    path = (root / name).resolve() if isinstance(name, str) else None
    if path is None or root not in path.parents or not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=t("app.release_not_found"))
    return FileResponse(path, filename=path.name, media_type="application/octet-stream")
