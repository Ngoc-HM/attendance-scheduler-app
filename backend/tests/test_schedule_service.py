"""Phase 05 integration — generate / visibility / override / publish / autorun."""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

from app.core.i18n import t

V = "/api/v1"
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

    # Manual override (F-09): force a working code onto one of fixed[0]'s OFF
    # (X) days — always saved, and the re-check warns because that week now has
    # one fewer than the required 2 off days (off-quota drift).
    off_day = next(
        a["work_date"] for a in schedule["assignments"]
        if a["user_id"] == fixed[0]["id"] and a["code"] == "X"
    )
    res = client.post(
        f"/api/v1/schedules/{schedule['id']}/override",
        headers=admin,
        json={"user_id": fixed[0]["id"], "work_date": off_day, "code": "A/D"},
    )
    assert res.status_code == 200, res.text
    over = res.json()
    cell = next(
        a for a in over["schedule"]["assignments"]
        if a["user_id"] == fixed[0]["id"] and a["work_date"] == off_day
    )
    assert cell["code"] == "A/D" and cell["is_manual_override"] is True
    assert over["violations"]  # fewer than 2 off days that week → flagged

    # A manually edited month is protected: regenerate without force → 409.
    res = client.post(
        "/api/v1/schedules/generate", headers=admin,
        json={"year": YEAR, "month": MONTH},
    )
    assert res.status_code == 409

    # Publish → visible to normal users; regenerating now requires force.
    res = client.post(f"/api/v1/schedules/{schedule['id']}/publish", headers=admin)
    assert res.status_code == 200 and res.json()["status"] == "published"
    assert client.get(f"/api/v1/schedules/{YEAR}/{MONTH}", headers=user_hdr).status_code == 200
    res = client.post(
        "/api/v1/schedules/generate", headers=admin,
        json={"year": YEAR, "month": MONTH},
    )
    assert res.status_code == 409


def test_regenerate_with_force_replaces_cells(client: TestClient) -> None:
    """Regression: generating twice for the same month (force=True) must replace
    the old cells, not collide on uq_assignment_cell (schedule_id,user_id,date)."""
    yr, mo = 2027, 5  # a month no other test touches
    admin = _admin_headers(client)
    for i in (1, 2, 3, 4):
        _make_user(client, admin, f"regen_a{i}", "A")

    def _gen(force: bool):
        return client.post(
            "/api/v1/schedules/generate",
            headers=admin,
            json={"year": yr, "month": mo, "force": force},
        )

    first = _gen(False)
    assert first.status_code == 200, first.text
    n_first = len(first.json()["schedule"]["assignments"])
    assert n_first > 0

    # Second run with force must succeed (no UniqueViolation) and fully replace.
    second = _gen(True)
    assert second.status_code == 200, second.text
    assert len(second.json()["schedule"]["assignments"]) == n_first



def _generate(client, admin, year, month, force=None):
    body = {"year": year, "month": month}
    if force is not None:
        body["force"] = force
    return client.post(f"{V}/schedules/generate", headers=admin, json=body)


def _override_off_day(client, admin, schedule: dict, user_id: int) -> None:
    """Force a working code onto one of ``user_id``'s off (X) days."""
    off_day = next(
        a["work_date"] for a in schedule["assignments"]
        if a["user_id"] == user_id and a["code"] == "X"
    )
    res = client.post(
        f"{V}/schedules/{schedule['id']}/override", headers=admin,
        json={"user_id": user_id, "work_date": off_day, "code": "A/D"},
    )
    assert res.status_code == 200, res.text


def test_regenerate_published_requires_force(client: TestClient) -> None:
    """B1: a published month is locked — regenerate only with force, which
    drops the manual edits and resets the month to draft."""
    yr, mo = 2026, 12
    admin = _admin_headers(client)
    users = [_make_user(client, admin, f"lockpub_a{i}", "A") for i in (1, 2, 3, 4)]
    gen = _generate(client, admin, yr, mo)
    assert gen.status_code == 200, gen.text
    schedule = gen.json()["schedule"]
    pub = client.post(f"{V}/schedules/{schedule['id']}/publish", headers=admin)
    assert pub.status_code == 200 and pub.json()["status"] == "published"
    _override_off_day(client, admin, schedule, users[0]["id"])

    r = _generate(client, admin, yr, mo)
    assert r.status_code == 409 and "force" in r.json()["detail"]
    assert r.json()["detail"] == t("schedule.published_locked")
    # The refused call left the month alone: still published, edit kept.
    kept = client.get(f"{V}/schedules/{yr}/{mo}", headers=admin).json()
    assert kept["status"] == "published"
    assert any(a["is_manual_override"] for a in kept["assignments"])

    r = _generate(client, admin, yr, mo, force=True)
    assert r.status_code == 200 and r.json()["schedule"]["status"] == "draft"
    assert not any(a["is_manual_override"] for a in r.json()["schedule"]["assignments"])


def test_regenerate_with_overrides_requires_force(client: TestClient) -> None:
    """B1: a draft with manual edits is protected — regenerate only with force,
    which replaces the edited cells with a fresh solve."""
    yr, mo = 2027, 7
    admin = _admin_headers(client)
    users = [_make_user(client, admin, f"lockovr_a{i}", "A") for i in (1, 2, 3, 4)]
    gen = _generate(client, admin, yr, mo)
    assert gen.status_code == 200, gen.text
    schedule = gen.json()["schedule"]
    assert schedule["status"] == "draft"
    _override_off_day(client, admin, schedule, users[0]["id"])

    r = _generate(client, admin, yr, mo)
    assert r.status_code == 409 and "force" in r.json()["detail"]
    assert r.json()["detail"] == t("schedule.has_overrides")
    kept = client.get(f"{V}/schedules/{yr}/{mo}", headers=admin).json()
    assert any(a["is_manual_override"] for a in kept["assignments"])

    r = _generate(client, admin, yr, mo, force=True)
    assert r.status_code == 200, r.text
    assert r.json()["schedule"]["status"] == "draft"
    assert not any(a["is_manual_override"] for a in r.json()["schedule"]["assignments"])


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
