"""Phase 05 integration — generate / visibility / override / publish / autorun."""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

YEAR, MONTH = 2027, 3  # a clean month nothing else touches


def _admin_headers(client: TestClient) -> dict[str, str]:
    res = client.post(
        "/api/v1/auth/login", data={"username": "admin", "password": "admin123"}
    )
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _make_user(client, admin, username, role) -> dict:
    res = client.post(
        "/api/v1/users",
        headers=admin,
        json={"username": username, "password": "pass123",
              "full_name": username, "role": role},
    )
    assert res.status_code in (200, 201), res.text
    return res.json()


def _login(client, username) -> dict[str, str]:
    res = client.post(
        "/api/v1/auth/login", data={"username": username, "password": "pass123"}
    )
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_generate_override_publish_pipeline(client: TestClient) -> None:
    admin = _admin_headers(client)
    fixed = [_make_user(client, admin, f"sched_a{i}", "A") for i in (1, 2, 3, 4)]

    # Flight input (F-04): 1 pair on the first 7 days of the month.
    for day in range(1, 8):
        res = client.put(
            "/api/v1/flights/days",
            headers=admin,
            json={"day": f"{YEAR}-{MONTH:02d}-{day:02d}", "flight_pairs": 1},
        )
        assert res.status_code in (200, 201), res.text

    # Generate (F-07).
    res = client.post(
        "/api/v1/schedules/generate",
        headers=admin,
        json={"year": YEAR, "month": MONTH},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["feasible"] is True
    schedule = body["schedule"]
    days_in_month = len(
        [a for a in schedule["assignments"] if a["user_id"] == fixed[0]["id"]]
    )
    assert days_in_month == 31  # March 2027 — full grid per person

    # Draft invisible to non-admin (G4), visible to admin.
    user_hdr = _login(client, "sched_a1")
    assert client.get(f"/api/v1/schedules/{YEAR}/{MONTH}", headers=user_hdr).status_code == 404
    assert client.get(f"/api/v1/schedules/{YEAR}/{MONTH}", headers=admin).status_code == 200

    # Manual override (F-09): force a working code on someone's day — always
    # saved, warning returned (recheck catches quota/staffing drift).
    res = client.post(
        f"/api/v1/schedules/{schedule['id']}/override",
        headers=admin,
        json={"user_id": fixed[0]["id"], "work_date": f"{YEAR}-{MONTH:02d}-01",
              "code": "A/D"},
    )
    assert res.status_code == 200, res.text
    over = res.json()
    cell = next(
        a for a in over["schedule"]["assignments"]
        if a["user_id"] == fixed[0]["id"] and a["work_date"] == f"{YEAR}-{MONTH:02d}-01"
    )
    assert cell["code"] == "A/D" and cell["is_manual_override"] is True
    assert over["violations"]  # over-coverage flagged by the re-check

    # Regenerate guard: manual edits present → 409 without force.
    res = client.post(
        "/api/v1/schedules/generate", headers=admin,
        json={"year": YEAR, "month": MONTH},
    )
    assert res.status_code == 409

    # Publish → visible to normal users; regenerate without force still 409.
    res = client.post(f"/api/v1/schedules/{schedule['id']}/publish", headers=admin)
    assert res.status_code == 200 and res.json()["status"] == "published"
    assert client.get(f"/api/v1/schedules/{YEAR}/{MONTH}", headers=user_hdr).status_code == 200
    res = client.post(
        "/api/v1/schedules/generate", headers=admin,
        json={"year": YEAR, "month": MONTH},
    )
    assert res.status_code == 409


def test_autorun_trigger_logic(client: TestClient) -> None:
    """Decision #9: fires only on AUTORUN_DAY; never clobbers an existing one."""
    from app.services.schedule_autorun import maybe_run_autorun, next_month

    assert next_month(date(2026, 12, 20)) == (2027, 1)
    # Wrong day → no-op regardless of whether schedule exists.
    assert maybe_run_autorun(date(2026, 6, 19)) is False
    # Ensure a 2027-03 schedule exists (may have been created by the pipeline
    # test which runs first in the same DB; if not, this call creates it).
    maybe_run_autorun(date(2027, 2, 20))
    # Right day but schedule already exists → must return False.
    assert maybe_run_autorun(date(2027, 2, 20)) is False  # 2027-03 now exists
