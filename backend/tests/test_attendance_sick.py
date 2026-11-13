"""F-10/F-13 — sick backfill (pure §6 logic) + attendance/holiday integration."""

from __future__ import annotations

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


def test_recently_sick_rule_spans_month_boundary(client: TestClient) -> None:
    """An S on the last days of November still forces A/D cover in early
    December — the recently-sick memory is 30 days, not "this month" (§6)."""
    admin = _admin(client)
    # Created first → lowest id → the fairness pick if the S were forgotten.
    helper = _mk(client, admin, "boundary_helper", "A")
    was_sick = _mk(client, admin, "boundary_was_sick", "A")
    sick = _mk(client, admin, "boundary_sick", "A")

    res = client.put("/api/v1/attendance", headers=admin,
                     json={"user_id": was_sick, "work_date": "2028-11-28", "code": "S"})
    assert res.status_code == 200, res.text
    day = "2028-12-02"
    for uid, code in ((sick, "A"), (helper, "D"), (was_sick, "D")):
        res = client.put("/api/v1/attendance", headers=admin,
                         json={"user_id": uid, "work_date": day, "code": code})
        assert res.status_code == 200, res.text

    res = client.post("/api/v1/attendance/sick-cover", headers=admin,
                      json={"user_id": sick, "work_date": day, "code": "S"})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["cover"] is not None
    assert body["cover"]["user_id"] == was_sick and body["cover"]["code"] == "A/D"
    assert body["forced"] is True


# --- review-2 B6 / E: active covers only, no health text, published seed ----

def test_sick_cover_skips_disabled_users(client: TestClient) -> None:
    """B6 — a disabled colleague is never chosen as the A/D cover, even when
    they would win the fairness tie-break (lowest id, no A/D yet)."""
    admin = _admin(client)
    gone = _mk(client, admin, "b6_disabled", "A")  # lowest id of the three
    sick = _mk(client, admin, "b6_sick", "A")
    helper = _mk(client, admin, "b6_helper", "A")
    day = "2027-09-14"
    for uid, code in ((gone, "D"), (sick, "A"), (helper, "D")):
        res = client.put("/api/v1/attendance", headers=admin,
                         json={"user_id": uid, "work_date": day, "code": code})
        assert res.status_code == 200, res.text
    res = client.patch(f"/api/v1/users/{gone}", headers=admin, json={"status": "disabled"})
    assert res.status_code == 200, res.text

    res = client.post("/api/v1/attendance/sick-cover", headers=admin,
                      json={"user_id": sick, "work_date": day, "code": "S"})
    assert res.status_code == 200, res.text
    cover = res.json()["cover"]
    assert cover is not None
    assert cover["user_id"] == helper


def test_sick_cover_skips_pending_users(client: TestClient) -> None:
    """A not-yet-approved (pending) account is never the A/D cover either,
    even when it would win the fairness tie-break or is "recently sick"."""
    from app.core.database import SessionLocal
    from app.models.enums import UserStatus
    from app.models.user import User

    admin = _admin(client)
    waiting = _mk(client, admin, "b6_pending", "A")  # lowest id of the three
    sick = _mk(client, admin, "b6p_sick", "A")
    helper = _mk(client, admin, "b6p_helper", "A")
    # waiting was sick recently → would be the FORCED cover if eligible (§6).
    client.put("/api/v1/attendance", headers=admin,
               json={"user_id": waiting, "work_date": "2027-11-02", "code": "S"})
    day = "2027-11-09"
    for uid, code in ((waiting, "D"), (sick, "A"), (helper, "D")):
        res = client.put("/api/v1/attendance", headers=admin,
                         json={"user_id": uid, "work_date": day, "code": code})
        assert res.status_code == 200, res.text
    with SessionLocal() as db:
        user = db.get(User, waiting)
        assert user is not None
        user.status = UserStatus.pending
        db.commit()

    res = client.post("/api/v1/attendance/sick-cover", headers=admin,
                      json={"user_id": sick, "work_date": day, "code": "S"})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["cover"] is not None
    assert body["cover"]["user_id"] == helper and body["forced"] is False


def test_sick_cover_note_has_no_health_text(client: TestClient) -> None:
    """§9.1 — the cover colleague's ordinary actual row must not say that
    somebody was sick: its note is None, also on the forced (§6) path."""
    admin = _admin(client)
    sick = _mk(client, admin, "note_sick", "A")
    helper = _mk(client, admin, "note_helper", "A")
    # helper was sick a week earlier → forced cover (§6).
    client.put("/api/v1/attendance", headers=admin,
               json={"user_id": helper, "work_date": "2027-10-05", "code": "S"})
    day = "2027-10-12"
    client.put("/api/v1/attendance", headers=admin,
               json={"user_id": sick, "work_date": day, "code": "A"})
    client.put("/api/v1/attendance", headers=admin,
               json={"user_id": helper, "work_date": day, "code": "D"})

    res = client.post("/api/v1/attendance/sick-cover", headers=admin,
                      json={"user_id": sick, "work_date": day, "code": "S"})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["cover"]["user_id"] == helper and body["forced"] is True
    assert body["cover"]["note"] is None

    rows = client.get("/api/v1/attendance?year=2027&month=10", headers=admin).json()
    stored = next(r for r in rows if r["user_id"] == helper and r["work_date"] == day)
    assert stored["note"] is None


def test_seed_refuses_draft_schedule(client: TestClient) -> None:
    """A draft roster is never copied into the actuals (employees would see
    unpublished codes through /attendance/me): 409
    ``attendance.schedule_not_published``."""
    from app.core.database import SessionLocal
    from app.core.i18n import t
    from app.models.enums import ScheduleStatus
    from app.models.schedule import MonthlySchedule

    with SessionLocal() as db:
        db.add(MonthlySchedule(year=2041, month=2, status=ScheduleStatus.draft))
        db.commit()

    admin = _admin(client)
    res = client.post("/api/v1/attendance/seed?year=2041&month=2", headers=admin)
    assert res.status_code == 409, res.text
    assert res.json()["detail"] == t("attendance.schedule_not_published")


# --- taking a sick day back restores its cover (2026-11-13) ----------------

def _put(client, admin, uid, day, code):
    res = client.put("/api/v1/attendance", headers=admin,
                     json={"user_id": uid, "work_date": day, "code": code})
    assert res.status_code == 200, res.text
    return res.json()


def _cell(client, admin, uid, day):
    year, month = day[:4], int(day[5:7])
    rows = client.get(f"/api/v1/attendance?year={year}&month={month}", headers=admin).json()
    return next(r for r in rows if r["user_id"] == uid and r["work_date"] == day)


def test_taking_the_sick_day_back_restores_the_cover(client: TestClient) -> None:
    admin = _admin(client)
    sick = _mk(client, admin, "undo_s1", "A")
    helper = _mk(client, admin, "undo_s2", "A")
    day = "2093-04-07"
    _put(client, admin, sick, day, "A")
    _put(client, admin, helper, day, "D")
    res = client.post("/api/v1/attendance/sick-cover", headers=admin,
                      json={"user_id": sick, "work_date": day, "code": "S"})
    assert res.json()["cover"]["user_id"] == helper

    _put(client, admin, sick, day, "A")  # recorded by mistake

    cover = _cell(client, admin, helper, day)
    assert cover["code"] == "D"
    assert cover["recorded_by"] is not None  # it was an admin-recorded D


def test_a_cover_edited_since_is_left_alone(client: TestClient) -> None:
    admin = _admin(client)
    sick = _mk(client, admin, "undo_e1", "A")
    helper = _mk(client, admin, "undo_e2", "A")
    day = "2093-04-08"
    _put(client, admin, sick, day, "A")
    _put(client, admin, helper, day, "D")
    client.post("/api/v1/attendance/sick-cover", headers=admin,
                json={"user_id": sick, "work_date": day, "code": "S"})
    _put(client, admin, helper, day, "T")  # the admin re-codes the cover

    _put(client, admin, sick, day, "A")

    assert _cell(client, admin, helper, day)["code"] == "T"


def test_a_plain_s_without_cover_changes_nobody_else(client: TestClient) -> None:
    admin = _admin(client)
    sick = _mk(client, admin, "undo_p1", "A")
    other = _mk(client, admin, "undo_p2", "A")
    day = "2093-04-09"
    _put(client, admin, other, day, "D")
    _put(client, admin, sick, day, "S")
    _put(client, admin, sick, day, "A")

    assert _cell(client, admin, other, day)["code"] == "D"
