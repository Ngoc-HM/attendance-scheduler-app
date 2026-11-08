"""Time clock (check-in / check-out, owner request 2026-07-09).

Own data only; the DAY a punch belongs to is the business day in
``settings.TIMEZONE`` (spec §2), not the host's or UTC date.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.core.i18n import t

V = "/api/v1"
CLOCK = f"{V}/attendance/clock"


def _login(client: TestClient, username: str, password: str) -> dict[str, str]:
    res = client.post(f"{V}/auth/login", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _employee(client: TestClient, username: str) -> dict[str, str]:
    admin = _login(client, "admin", "admin123")
    res = client.post(
        f"{V}/users", headers=admin,
        json={"username": username, "password": "pass123", "full_name": username, "role": "A"},
    )
    assert res.status_code == 201, res.text
    return _login(client, username, "pass123")


def test_check_in_twice_409(client: TestClient) -> None:
    user = _employee(client, "clock_twice")
    first = client.post(f"{CLOCK}/check-in", headers=user)
    assert first.status_code == 201, first.text
    assert first.json()["check_in_at"] is not None

    again = client.post(f"{CLOCK}/check-in", headers=user)
    assert again.status_code == 409
    assert again.json()["detail"] == t("clock.already_checked_in")


def test_check_out_without_check_in_409(client: TestClient) -> None:
    user = _employee(client, "clock_no_in")
    res = client.post(f"{CLOCK}/check-out", headers=user)
    assert res.status_code == 409
    assert res.json()["detail"] == t("clock.not_checked_in")


def test_check_out_twice_409(client: TestClient) -> None:
    user = _employee(client, "clock_out_twice")
    assert client.post(f"{CLOCK}/check-in", headers=user).status_code == 201
    out = client.post(f"{CLOCK}/check-out", headers=user)
    assert out.status_code == 200, out.text
    assert out.json()["check_out_at"] is not None
    again = client.post(f"{CLOCK}/check-out", headers=user)
    assert again.status_code == 409
    assert again.json()["detail"] == t("clock.already_checked_out")


@pytest.mark.parametrize(
    ("tz", "expected_day"),
    [
        # 23:30 UTC on 2026-12-20 is already 00:30 on the 21st in Berlin (CET)…
        ("Europe/Berlin", "2026-12-21"),
        # …but still 18:30 on the 20th in New York: the zone is the setting's.
        ("America/New_York", "2026-12-20"),
    ],
)
def test_punch_near_midnight_uses_business_day(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tz: str, expected_day: str
) -> None:
    from app.core import business_time
    from app.core.config import settings

    monkeypatch.setattr(settings, "TIMEZONE", tz)
    monkeypatch.setattr(
        business_time, "_utcnow", lambda: datetime(2026, 12, 20, 23, 30, tzinfo=UTC)
    )
    user = _employee(client, f"clock_midnight_{tz.split('/')[1].lower()}")

    res = client.post(f"{CLOCK}/check-in", headers=user)
    assert res.status_code == 201, res.text
    assert res.json()["work_date"] == expected_day

    today = client.get(f"{CLOCK}/today", headers=user)
    assert today.status_code == 200
    assert today.json()["work_date"] == expected_day

    year, month = int(expected_day[:4]), int(expected_day[5:7])
    mine = client.get(f"{CLOCK}/me?year={year}&month={month}", headers=user).json()
    assert [e["work_date"] for e in mine] == [expected_day]


def test_schedule_visibility_window_uses_business_day(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The non-admin "current month + 2" window counts from the business day,
    not the host clock: at 23:30 UTC on 31 Dec it is already January in
    Berlin, so March is visible (404 = no schedule, not 403)."""
    from app.core import business_time
    from app.core.config import settings

    user = _employee(client, "clock_window")
    monkeypatch.setattr(settings, "ENVIRONMENT", "staging")
    monkeypatch.setattr(settings, "TIMEZONE", "Europe/Berlin")
    monkeypatch.setattr(
        business_time, "_utcnow", lambda: datetime(2040, 12, 31, 23, 30, tzinfo=UTC)
    )
    assert client.get(f"{V}/schedules/2041/3", headers=user).status_code == 404
    assert client.get(f"{V}/schedules/2041/4", headers=user).status_code == 403
