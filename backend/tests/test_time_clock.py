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


def test_the_latest_check_out_wins(client: TestClient) -> None:
    user = _employee(client, "clock_out_twice")
    assert client.post(f"{CLOCK}/check-in", headers=user).status_code == 201
    out = client.post(f"{CLOCK}/check-out", headers=user)
    assert out.status_code == 200, out.text
    first = out.json()["check_out_at"]
    assert first is not None
    again = client.post(f"{CLOCK}/check-out", headers=user)
    assert again.status_code == 200, again.text
    assert again.json()["check_out_at"] >= first


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


# --- admin: everyone's month and corrections (2026-11-13) -------------------

def _admin_and_id(client: TestClient, username: str) -> tuple[dict[str, str], int, dict[str, str]]:
    user = _employee(client, username)
    uid = client.get(f"{V}/users/me", headers=user).json()["id"]
    return _login(client, "admin", "admin123"), uid, user


def test_admin_fixes_a_forgotten_check_out(client: TestClient) -> None:
    admin, uid, user = _admin_and_id(client, "clock_fix_out")
    day = "2026-03-10"
    res = client.put(f"{CLOCK}/staff", headers=admin,
                     json={"user_id": uid, "work_date": day, "check_in": "05:10"})
    assert res.status_code == 200, res.text
    assert res.json()["check_out_at"] is None

    res = client.put(f"{CLOCK}/staff", headers=admin,
                     json={"user_id": uid, "work_date": day,
                           "check_in": "05:10", "check_out": "14:20"})
    assert res.status_code == 200, res.text
    body = res.json()
    # Europe/Berlin in March is UTC+1.
    assert body["check_in_at"].startswith("2026-03-10T04:10")
    assert body["check_out_at"].startswith("2026-03-10T13:20")

    rows = client.get(f"{CLOCK}/staff?year=2026&month=3", headers=admin).json()
    mine = [r for r in rows if r["user_id"] == uid]
    assert len(mine) == 1 and mine[0]["full_name"] == "clock_fix_out"
    assert mine[0]["code"]
    assert (mine[0]["check_in_local"], mine[0]["check_out_local"]) == ("05:10", "14:20")
    assert mine[0]["corrected"] is True

    # The employee sees the corrected day in their own history.
    own = client.get(f"{CLOCK}/me?year=2026&month=3", headers=user).json()
    assert own[0]["check_out_at"].startswith("2026-03-10T13:20")


def test_correction_rejects_out_before_in_and_future_days(client: TestClient) -> None:
    admin, uid, _ = _admin_and_id(client, "clock_fix_bad")
    res = client.put(f"{CLOCK}/staff", headers=admin,
                     json={"user_id": uid, "work_date": "2026-03-11",
                           "check_in": "14:00", "check_out": "06:00"})
    assert res.status_code == 422
    res = client.put(f"{CLOCK}/staff", headers=admin,
                     json={"user_id": uid, "work_date": "2099-01-01", "check_in": "06:00"})
    assert res.status_code == 422


def test_staff_clock_is_admin_only(client: TestClient) -> None:
    _, uid, user = _admin_and_id(client, "clock_fix_rbac")
    assert client.get(f"{CLOCK}/staff?year=2026&month=3", headers=user).status_code == 403
    res = client.put(f"{CLOCK}/staff", headers=user,
                     json={"user_id": uid, "work_date": "2026-03-12", "check_in": "06:00"})
    assert res.status_code == 403


def test_board_reads_the_punches_against_the_codes(client: TestClient) -> None:
    admin, uid, _ = _admin_and_id(client, "clock_board")
    for day, code in (("2026-02-02", "A"), ("2026-02-03", "D"),
                      ("2026-02-04", "X"), ("2026-02-05", "A"), ("2026-02-06", "B")):
        res = client.put(f"{V}/attendance", headers=admin,
                         json={"user_id": uid, "work_date": day, "code": code})
        assert res.status_code == 200, res.text
    punches = (("2026-02-03", "05:00", "13:30"), ("2026-02-04", "06:00", "09:00"),
               ("2026-02-05", "05:30", None))
    for day, cin, cout in punches:
        body = {"user_id": uid, "work_date": day, "check_in": cin}
        if cout:
            body["check_out"] = cout
        assert client.put(f"{CLOCK}/staff", headers=admin, json=body).status_code == 200

    cells = {
        c["work_date"]: c
        for c in client.get(f"{CLOCK}/board?year=2026&month=2", headers=admin).json()
        if c["user_id"] == uid
    }
    assert {d: c["status"] for d, c in cells.items()} == {
        "2026-02-02": "absent",      # due at work, never checked in
        "2026-02-03": "ok",
        "2026-02-04": "off_day",     # punched on an X day
        "2026-02-05": "missed_out",  # a past day still open
    }  # B (business trip) expects no punch
    assert cells["2026-02-03"]["check_in_local"] == "05:00"
    assert cells["2026-02-03"]["corrected"] is True


# --- roster tints (owner 2026-11-13) ------------------------------------------

def _published_roster(cells: list[tuple[int, str, str, bool]]) -> None:
    """Publish 2025-07 with the given (user, day, code, manual) cells."""
    from datetime import date as _date

    from app.core.database import SessionLocal
    from app.models.enums import AttendanceCode, ScheduleStatus
    from app.models.schedule import MonthlySchedule, ShiftAssignment

    db = SessionLocal()
    try:
        schedule = db.query(MonthlySchedule).filter_by(year=2025, month=7).one_or_none()
        if schedule is None:
            schedule = MonthlySchedule(year=2025, month=7, status=ScheduleStatus.published)
            db.add(schedule)
            db.flush()
        for uid, day, code, manual in cells:
            db.add(ShiftAssignment(
                schedule_id=schedule.id, user_id=uid, work_date=_date.fromisoformat(day),
                code=AttendanceCode(code), is_manual_override=manual,
            ))
        db.commit()
    finally:
        db.close()


def test_roster_days_are_tinted_red_when_missed_and_yellow_when_adjusted(
    client: TestClient,
) -> None:
    admin, uid, _ = _admin_and_id(client, "clock_tint")
    _published_roster([
        (uid, "2025-07-01", "A", False),   # no punch → red
        (uid, "2025-07-02", "D", False),   # in, no out → red
        (uid, "2025-07-03", "A", False),   # in and out → nothing
        (uid, "2025-07-04", "D", True),    # admin edited the roster → yellow
        (uid, "2025-07-05", "A", False),   # admin recorded S → yellow
        (uid, "2025-07-06", "X", False),   # off → nothing
    ])
    for day, cin, cout in (("2025-07-02", "05:00", None), ("2025-07-03", "05:00", "13:00")):
        body = {"user_id": uid, "work_date": day, "check_in": cin}
        if cout:
            body["check_out"] = cout
        assert client.put(f"{CLOCK}/staff", headers=admin, json=body).status_code == 200
    assert client.put(f"{V}/attendance", headers=admin,
                      json={"user_id": uid, "work_date": "2025-07-05", "code": "S"}).status_code == 200

    tints = {
        c["work_date"]: c["tint"]
        for c in client.get(f"{CLOCK}/board?year=2025&month=7", headers=admin).json()
        if c["user_id"] == uid
    }
    assert tints == {
        "2025-07-01": "missing",
        "2025-07-02": "missing",
        "2025-07-03": None,
        "2025-07-04": "adjusted",
        "2025-07-05": "adjusted",
    }
