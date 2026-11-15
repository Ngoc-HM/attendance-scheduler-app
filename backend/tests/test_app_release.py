"""Desktop app updates: the newest build and its packages (2026-11-15)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings

V = "/api/v1/app"


@pytest.fixture
def releases(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(settings, "APP_RELEASES_DIR", str(tmp_path))
    return tmp_path


def _publish(root: Path, build: int, **extra) -> None:
    (root / str(build)).mkdir()
    (root / str(build) / "RosterFRA-Setup.exe").write_bytes(b"setup")
    manifest = {
        "build": build,
        "version": "1.0.0",
        "files": {"windows": f"{build}/RosterFRA-Setup.exe"},
        "sha256": {"windows": "abc"},
        **extra,
    }
    (root / "latest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_no_release_published_is_null(client: TestClient, releases: Path) -> None:
    res = client.get(f"{V}/latest")
    assert res.status_code == 200 and res.json() is None


def test_latest_and_download_need_no_login(client: TestClient, releases: Path) -> None:
    _publish(releases, 230, min_build=225, notes="Sửa lịch")
    body = client.get(f"{V}/latest").json()
    assert body["build"] == 230 and body["min_build"] == 225
    assert body["downloads"] == {"windows": "/app/download/windows"}
    res = client.get(f"{V}/download/windows")
    assert res.status_code == 200 and res.content == b"setup"


def test_unpublished_platform_and_escapes_are_404(client: TestClient, releases: Path) -> None:
    _publish(releases, 231)
    assert client.get(f"{V}/download/macos").status_code == 404
    (releases / "latest.json").write_text(
        json.dumps({"build": 232, "files": {"linux": "../../etc/passwd"}}), encoding="utf-8"
    )
    assert client.get(f"{V}/download/linux").status_code == 404
    assert client.get(f"{V}/download/android").status_code == 422
