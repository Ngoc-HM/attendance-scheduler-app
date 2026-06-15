"""F-10/F-13 — sick backfill (pure §6 logic) + attendance/holiday integration."""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

from app.models.enums import AttendanceCode, Role
from app.services import sick_backfill


# --- pure sick-backfill logic (§6) -----------------------------------------

ROLES = {1: Role.A, 2: Role.A, 3: Role.A, 4: Role.A, 5: Role.T}


def test_needs_cover_only_for_flight_duty() -> None:
    assert sick_backfill.needs_cover(AttendanceCode.A)
    assert sick_backfill.needs_cover(AttendanceCode.A_D)
    assert not sick_backfill.needs_cover(AttendanceCode.O_D)
    assert not sick_backfill.needs_cover(AttendanceCode.X)
    assert not sick_backfill.needs_cover(None)


def test_picks_least_loaded_fixed_colleague_on_single_shift() -> None:
    # user1 sick; 2 & 3 work single shifts; 3 already did more A/D this month.
    day_codes = {1: AttendanceCode.A, 2: AttendanceCode.D, 3: AttendanceCode.A}
    proposal = sick_backfill.pick_candidate(
        sick_user_id=1, day_codes=day_codes, roles=ROLES,
        recently_sick=[], month_ad_counts={2: 1, 3: 0},
    )
    assert proposal is not None
    assert proposal.user_id == 3 and proposal.new_code is AttendanceCode.A_D
    assert proposal.forced is False


def test_recently_sick_person_is_forced_to_cover() -> None:
    # user2 was sick earlier; today works a single shift → forced A/D (§6).
    day_codes = {1: AttendanceCode.A, 2: AttendanceCode.D, 3: AttendanceCode.A}
    proposal = sick_backfill.pick_candidate(
        sick_user_id=1, day_codes=day_codes, roles=ROLES,
        recently_sick=[2], month_ad_counts={2: 5, 3: 0},
    )
    assert proposal is not None
    assert proposal.user_id == 2 and proposal.forced is True


def test_no_eligible_colleague_returns_none() -> None:
    day_codes = {1: AttendanceCode.A, 5: AttendanceCode.O_D}  # 5 is flexible/off-duty
    proposal = sick_backfill.pick_candidate(
        sick_user_id=1, day_codes=day_codes, roles=ROLES,
        recently_sick=[], month_ad_counts={},
    )
    assert proposal is None


def test_flexible_role_never_picked_for_flight_cover() -> None:
    day_codes = {1: AttendanceCode.A, 5: AttendanceCode.A}  # 5 is role T
    proposal = sick_backfill.pick_candidate(
        sick_user_id=1, day_codes=day_codes, roles=ROLES,
        recently_sick=[5], month_ad_counts={},
    )
    assert proposal is None  # T excluded even though "recently sick"


# --- integration: endpoints ------------------------------------------------

def _admin(client: TestClient) -> dict[str, str]:
    res = client.post("/api/v1/auth/login", data={"username": "admin", "password": "admin123"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _mk(client, admin, username, role) -> int:
    res = client.post("/api/v1/users", headers=admin,
                      json={"username": username, "password": "pass123",
                            "full_name": username, "role": role})
    assert res.status_code in (200, 201), res.text
    return res.json()["id"]


def test_holiday_crud_does_not_pin_off(client: TestClient) -> None:
    admin = _admin(client)
    res = client.put("/api/v1/holidays", headers=admin,
                     json={"day": "2027-05-01", "name": "Labour Day"})
    assert res.status_code == 200
    hid = res.json()["id"]
    assert any(h["day"] == "2027-05-01"
               for h in client.get("/api/v1/holidays?year=2027", headers=admin).json())
    # rename (upsert is idempotent by day)
    res = client.put("/api/v1/holidays", headers=admin,
                     json={"day": "2027-05-01", "name": "May Day"})
    assert res.json()["id"] == hid
    assert client.delete(f"/api/v1/holidays/{hid}", headers=admin).status_code == 204


def test_sick_cover_assigns_ad_to_colleague(client: TestClient) -> None:
    admin = _admin(client)
    sick = _mk(client, admin, "sick_a1", "A")
    helper = _mk(client, admin, "sick_a2", "A")
    day = "2027-08-10"

    # both on single shifts that day (actuals)
    client.put("/api/v1/attendance", headers=admin,
               json={"user_id": sick, "work_date": day, "code": "A"})
    client.put("/api/v1/attendance", headers=admin,
               json={"user_id": helper, "work_date": day, "code": "D"})

    res = client.post("/api/v1/attendance/sick-cover", headers=admin,
                      json={"user_id": sick, "work_date": day, "code": "S"})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["sick"]["code"] == "S"
    assert body["cover"] is not None
    assert body["cover"]["user_id"] == helper and body["cover"]["code"] == "A/D"


def test_sick_cover_rejects_non_sick_code(client: TestClient) -> None:
    admin = _admin(client)
    uid = _mk(client, admin, "sick_bad", "A")
    res = client.post("/api/v1/attendance/sick-cover", headers=admin,
                      json={"user_id": uid, "work_date": "2027-08-11", "code": "A"})
    assert res.status_code == 400
