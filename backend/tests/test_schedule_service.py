"""Phase 05 integration — generate / visibility / override / publish / autorun."""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

from app.core.i18n import t

# Full-month solves over every user in the shared session DB: a short limit
# times out on slower CI runners (two-phase solve gives phase 1 only 40 %).
GENERATE_TIME_LIMIT = 20.0

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


def test_autorun_trigger_logic(client: TestClient, monkeypatch) -> None:
    """Decision #9: fires only the day after AUTORUN_DAY; never clobbers an existing one."""
    from app.core.config import settings
    from app.services.schedule_autorun import maybe_run_autorun, next_month

    # The suite turns autorun off by default; enable it so the trigger runs.
    monkeypatch.setattr(settings, "AUTORUN_ENABLED", True)
    monkeypatch.setattr(settings, "AUTORUN_DAY", 20)
    monkeypatch.setattr(settings, "SOLVER_MAX_TIME_SECONDS", GENERATE_TIME_LIMIT)
    admin = _admin_headers(client)

    assert next_month(date(2026, 12, 20)) == (2027, 1)
    # Wrong day → no-op, nothing generated for the month after.
    assert maybe_run_autorun(date(2051, 3, 19)) is False
    assert client.get(f"{V}/schedules/2051/4", headers=admin).status_code == 404
    # Right day, no schedule yet → generates the 2051-04 draft.
    assert maybe_run_autorun(date(2051, 3, 21)) is True
    assert client.get(f"{V}/schedules/2051/4", headers=admin).status_code == 200
    # Right day but the schedule already exists → must not run again.
    assert maybe_run_autorun(date(2051, 3, 21)) is False


def test_autorun_fires_day_after_close(client: TestClient, monkeypatch) -> None:
    """The window stays open all of AUTORUN_DAY, so the draft is generated
    the next day (00:05 on day 21), never while users can still register."""
    from app.core.config import settings
    from app.services.schedule_autorun import maybe_run_autorun, start_scheduler

    monkeypatch.setattr(settings, "AUTORUN_ENABLED", True)
    monkeypatch.setattr(settings, "AUTORUN_DAY", 20)
    monkeypatch.setattr(settings, "SOLVER_MAX_TIME_SECONDS", GENERATE_TIME_LIMIT)
    admin = _admin_headers(client)

    # Day 20: registration for 2030-10 is still open → no draft yet.
    assert maybe_run_autorun(date(2030, 9, 20)) is False
    assert client.get("/api/v1/schedules/2030/10", headers=admin).status_code == 404
    # Day 21: the window has closed → the 2030-10 draft is generated.
    assert maybe_run_autorun(date(2030, 9, 21)) is True
    assert client.get("/api/v1/schedules/2030/10", headers=admin).status_code == 200

    scheduler = start_scheduler()
    assert scheduler is not None
    try:
        job = scheduler.get_job("autorun")
        fields = {field.name: str(field) for field in job.trigger.fields}
        assert (fields["hour"], fields["minute"]) == ("0", "5")
    finally:
        scheduler.shutdown(wait=False)


def test_autorun_uses_business_timezone_date(client: TestClient, monkeypatch) -> None:
    """The process may run in UTC (Docker sets no TZ): at 00:05 Berlin on day 21
    the UTC date is still day 20, so the run must read the date in TIMEZONE."""
    from datetime import UTC, datetime

    from app.core import business_time
    from app.core.config import settings
    from app.services.schedule_autorun import maybe_run_autorun

    monkeypatch.setattr(settings, "AUTORUN_ENABLED", True)
    monkeypatch.setattr(settings, "AUTORUN_DAY", 20)
    monkeypatch.setattr(settings, "TIMEZONE", "Europe/Berlin")
    monkeypatch.setattr(settings, "SOLVER_MAX_TIME_SECONDS", GENERATE_TIME_LIMIT)
    # 23:30 UTC on 2026-12-20 is already 00:30 on 2026-12-21 in Berlin (CET).
    monkeypatch.setattr(
        business_time, "_utcnow", lambda: datetime(2026, 12, 20, 23, 30, tzinfo=UTC)
    )
    admin = _admin_headers(client)

    assert business_time.business_today() == date(2026, 12, 21)
    assert client.get("/api/v1/schedules/2027/1", headers=admin).status_code == 404
    assert maybe_run_autorun() is True  # no injected date → business date
    assert client.get("/api/v1/schedules/2027/1", headers=admin).status_code == 200


def test_self_arrange_cannot_touch_al_or_cd_cell(client: TestClient) -> None:
    """Self-arrange may only move the employee's own AD/X cells: a pinned AL or
    an owed CD stays locked, and CD is never a code the employee may pick."""
    from app.core.i18n import t

    yr, mo = 2035, 3  # a month no other test touches
    admin = _admin_headers(client)
    me = _make_user(client, admin, "selfarr_t1", "T")

    gen = client.post(
        "/api/v1/schedules/generate", headers=admin, json={"year": yr, "month": mo}
    )
    assert gen.status_code == 200, gen.text
    schedule = gen.json()["schedule"]
    mine = sorted(
        (a for a in schedule["assignments"] if a["user_id"] == me["id"]),
        key=lambda a: a["work_date"],
    )
    al_day, cd_day, free_day = (a["work_date"] for a in mine[:3])
    # AL pinned, CD owed, and a plain AD cell for the CD-request check below.
    for day, code in ((al_day, "AL"), (cd_day, "CD"), (free_day, "AD")):
        res = client.post(
            f"/api/v1/schedules/{schedule['id']}/override",
            headers=admin,
            json={"user_id": me["id"], "work_date": day, "code": code},
        )
        assert res.status_code == 200, res.text
    res = client.post(f"/api/v1/schedules/{schedule['id']}/publish", headers=admin)
    assert res.status_code == 200, res.text

    user = _login(client, "selfarr_t1")
    for locked_day in (al_day, cd_day):
        res = client.post(
            "/api/v1/self-arrange",
            headers=user,
            json={"year": yr, "month": mo,
                  "changes": [{"work_date": locked_day, "code": "X"}]},
        )
        assert res.status_code == 422, res.text
        assert res.json()["detail"] == t("selfarrange.cell_locked")

    # CD comes only from comp debt — the employee can never pick it.
    res = client.post(
        "/api/v1/self-arrange",
        headers=user,
        json={"year": yr, "month": mo,
              "changes": [{"work_date": free_day, "code": "CD"}]},
    )
    assert res.status_code == 422, res.text
    assert res.json()["detail"] == t("selfarrange.invalid_code")


# --- Task 7: schedule lifecycle (violations, force-regenerate, roster changes) --


def _db_schedule(
    year: int, month: int, cells: dict[tuple[int, date], str], status: str = "draft"
) -> int:
    """Persist a schedule straight to the DB (no solver) and return its id."""
    from app.core.database import SessionLocal
    from app.models.enums import AttendanceCode, ScheduleStatus
    from app.models.schedule import MonthlySchedule, ShiftAssignment

    with SessionLocal() as db:
        schedule = MonthlySchedule(
            year=year, month=month, status=ScheduleStatus(status)
        )
        db.add(schedule)
        db.flush()
        for (user_id, day), code in cells.items():
            db.add(
                ShiftAssignment(
                    schedule_id=schedule.id, user_id=user_id, work_date=day,
                    code=AttendanceCode(code),
                )
            )
        db.commit()
        return schedule.id


def _month_cells(year: int, month: int, user_ids, code: str = "X"):
    import calendar

    last = calendar.monthrange(year, month)[1]
    return {
        (uid, date(year, month, d)): code
        for uid in user_ids
        for d in range(1, last + 1)
    }


def test_violations_endpoint_returns_recheck(client: TestClient) -> None:
    """C2 — the admin can read a month's rule check at any time (e.g. an
    autorun draft, or right before publishing): the same list the re-check
    after a manual edit returns."""
    admin = _admin_headers(client)
    users = [_make_user(client, admin, f"viol_a{i}", "A") for i in (1, 2)]
    ids = [u["id"] for u in users]
    schedule_id = _db_schedule(2051, 5, _month_cells(2051, 5, ids))

    res = client.post(
        f"{V}/schedules/{schedule_id}/override", headers=admin,
        json={"user_id": ids[0], "work_date": "2051-05-10", "code": "A"},
    )
    assert res.status_code == 200, res.text
    after_edit = res.json()["violations"]
    assert after_edit  # an all-X month breaks the off-chain / min-A rules

    res = client.get(f"{V}/schedules/{schedule_id}/violations", headers=admin)
    assert res.status_code == 200, res.text
    assert res.json() == after_edit
    assert set(res.json()[0]) == {"day", "user_id", "rule", "message"}

    res = client.get(f"{V}/schedules/987654/violations", headers=admin)
    assert res.status_code == 404
    assert res.json()["detail"] == t("schedule.not_found")


def test_violations_endpoint_admin_only(client: TestClient) -> None:
    admin = _admin_headers(client)
    user = _make_user(client, admin, "viol_emp1", "A")
    schedule_id = _db_schedule(2051, 6, _month_cells(2051, 6, [user["id"]]))

    res = client.get(
        f"{V}/schedules/{schedule_id}/violations", headers=_login(client, "viol_emp1")
    )
    assert res.status_code == 403
    assert res.json()["detail"] == t("auth.admin_required")
    assert client.get(f"{V}/schedules/{schedule_id}/violations").status_code == 401


def test_force_regenerate_published_resyncs_seeded_actuals(
    client: TestClient, monkeypatch
) -> None:
    """F11 — force-regenerating a published month must not leave actuals
    seeded from the OLD plan behind: seeded rows (``recorded_by`` NULL) follow
    the new plan at once, an admin-recorded actual stays, and the next month's
    boundary state is built from the new plan."""
    import calendar

    from app.core.config import settings
    from app.core.database import SessionLocal
    from app.models.attendance import AttendanceRecord
    from app.models.enums import AttendanceCode
    from app.models.schedule import ShiftAssignment
    from app.models.user import User
    from app.services import schedule_history

    monkeypatch.setattr(settings, "SOLVER_MAX_TIME_SECONDS", GENERATE_TIME_LIMIT)
    yr, mo = 2051, 7
    last = calendar.monthrange(yr, mo)[1]
    admin = _admin_headers(client)
    users = [_make_user(client, admin, f"regsync_a{i}", "A") for i in (1, 2, 3, 4)]
    u = users[0]["id"]

    gen = _generate(client, admin, yr, mo)
    assert gen.status_code == 200 and gen.json()["feasible"] is True, gen.text
    schedule = gen.json()["schedule"]
    pub = client.post(f"{V}/schedules/{schedule['id']}/publish", headers=admin)
    assert pub.status_code == 200, pub.text

    # An actual the admin recorded by hand.
    put = client.put(
        f"{V}/attendance", headers=admin,
        json={"user_id": u, "work_date": f"{yr}-{mo:02d}-10", "code": "B"},
    )
    assert put.status_code == 200, put.text
    recorder = put.json()["recorded_by"]
    assert recorder is not None

    # Make the published plan differ from anything the solver produces: the
    # last six days of ``u`` held O/D (never planned for role A) in both the
    # roster and the actuals seeded from it.
    stale_days = [date(yr, mo, d) for d in range(last - 5, last + 1)]
    with SessionLocal() as db:
        for day in stale_days:
            db.query(ShiftAssignment).filter(
                ShiftAssignment.user_id == u, ShiftAssignment.work_date == day
            ).update({"code": AttendanceCode.O_D})
            db.query(AttendanceRecord).filter(
                AttendanceRecord.user_id == u, AttendanceRecord.work_date == day
            ).update({"code": AttendanceCode.O_D})
        db.commit()

    regen = _generate(client, admin, yr, mo, force=True)
    assert regen.status_code == 200 and regen.json()["feasible"] is True, regen.text
    plan = {
        (a["user_id"], a["work_date"]): a["code"]
        for a in regen.json()["schedule"]["assignments"]
    }
    assert all(plan[(u, d.isoformat())] != "O/D" for d in stale_days)

    rows = client.get(
        f"{V}/attendance", params={"year": yr, "month": mo}, headers=admin
    ).json()
    mine = [r for r in rows if r["user_id"] in {x["id"] for x in users}]
    assert mine
    for row in mine:
        key = (row["user_id"], row["work_date"])
        if key == (u, f"{yr}-{mo:02d}-10"):
            # The admin-recorded actual is never overwritten.
            assert row["code"] == "B" and row["recorded_by"] == recorder
        else:
            assert row["recorded_by"] is None
            assert row["code"] == plan[key], key

    # The next month starts from the new plan, not from the stale seeded rows.
    with SessionLocal() as db:
        user = db.get(User, u)
        state = schedule_history.build_boundary_states(db, [user], yr, mo + 1)[u]
    new_codes = [AttendanceCode(plan[(u, d.isoformat())]) for d in stale_days]
    assert state.previous_working == {
        d: c.is_working for d, c in zip(stale_days, new_codes, strict=True)
    }
    expected_streak = 0
    for code in reversed(new_codes):
        if not code.is_working:
            break
        expected_streak += 1
    assert state.carry_streak == expected_streak


def test_force_regenerate_hides_draft_seeded_actuals_from_employee(
    client: TestClient, monkeypatch
) -> None:
    """Draft leak — after a forced regenerate the seeded actuals follow the
    DRAFT plan, so ``/attendance/me`` hides them until the month is published
    again; the admin-recorded row stays visible throughout."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "SOLVER_MAX_TIME_SECONDS", GENERATE_TIME_LIMIT)
    # 2064-05: test_schedule_history publishes 2052-05 earlier in the run.
    yr, mo = 2064, 5
    admin = _admin_headers(client)
    users = [_make_user(client, admin, f"draftleak_a{i}", "A") for i in (1, 2, 3, 4)]
    me = users[0]["id"]
    recorded_day = f"{yr}-{mo:02d}-10"

    gen = _generate(client, admin, yr, mo)
    assert gen.status_code == 200 and gen.json()["feasible"] is True, gen.text
    schedule_id = gen.json()["schedule"]["id"]
    pub = client.post(f"{V}/schedules/{schedule_id}/publish", headers=admin)
    assert pub.status_code == 200, pub.text
    put = client.put(
        f"{V}/attendance", headers=admin,
        json={"user_id": me, "work_date": recorded_day, "code": "B"},
    )
    assert put.status_code == 200, put.text

    employee = _login(client, "draftleak_a1")

    def _mine() -> list[dict]:
        r = client.get(
            f"{V}/attendance/me", params={"year": yr, "month": mo}, headers=employee
        )
        assert r.status_code == 200, r.text
        return r.json()

    assert len(_mine()) == 31  # published: the whole seeded month is visible

    regen = _generate(client, admin, yr, mo, force=True)
    assert regen.status_code == 200 and regen.json()["feasible"] is True, regen.text
    assert regen.json()["schedule"]["status"] == "draft"
    # Draft: no seeded (plan-copy) row, only what the admin recorded.
    assert [(r["work_date"], r["code"]) for r in _mine()] == [(recorded_day, "B")]

    pub = client.post(f"{V}/schedules/{schedule_id}/publish", headers=admin)
    assert pub.status_code == 200, pub.text
    plan = {
        a["work_date"]: a["code"]
        for a in regen.json()["schedule"]["assignments"]
        if a["user_id"] == me
    }
    rows = _mine()
    assert len(rows) == 31
    for row in rows:
        expected = "B" if row["work_date"] == recorded_day else plan[row["work_date"]]
        assert row["code"] == expected, row


def test_override_creates_missing_cell_for_active_user(client: TestClient) -> None:
    """F13 / R4 — a user approved after the month was generated has no row;
    the admin's override creates the cell (and, on a published month, its
    seeded actual)."""
    admin = _admin_headers(client)
    old = _make_user(client, admin, "rowadd_a1", "A")
    schedule_id = _db_schedule(
        2051, 9, _month_cells(2051, 9, [old["id"]]), status="published"
    )
    newcomer = _make_user(client, admin, "rowadd_a2", "A")

    res = client.post(
        f"{V}/schedules/{schedule_id}/override", headers=admin,
        json={"user_id": newcomer["id"], "work_date": "2051-09-05", "code": "A"},
    )
    assert res.status_code == 200, res.text
    cell = next(
        a for a in res.json()["schedule"]["assignments"]
        if a["user_id"] == newcomer["id"]
    )
    assert cell["work_date"] == "2051-09-05"
    assert cell["code"] == "A" and cell["is_manual_override"] is True

    rows = client.get(
        f"{V}/attendance", params={"year": 2051, "month": 9}, headers=admin
    ).json()
    actual = next(r for r in rows if r["user_id"] == newcomer["id"])
    assert actual["work_date"] == "2051-09-05" and actual["code"] == "A"
    assert actual["recorded_by"] is None


def test_override_missing_cell_for_disabled_user_404(client: TestClient) -> None:
    admin = _admin_headers(client)
    keep = _make_user(client, admin, "rowdis_a1", "A")
    gone = _make_user(client, admin, "rowdis_a2", "A")
    schedule_id = _db_schedule(2051, 10, _month_cells(2051, 10, [keep["id"]]))
    res = client.patch(
        f"{V}/users/{gone['id']}", headers=admin, json={"status": "disabled"}
    )
    assert res.status_code == 200, res.text

    res = client.post(
        f"{V}/schedules/{schedule_id}/override", headers=admin,
        json={"user_id": gone["id"], "work_date": "2051-10-05", "code": "A"},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == t("schedule.cell_not_found")


def test_override_date_outside_month_is_catalog_key(client: TestClient) -> None:
    admin = _admin_headers(client)
    user = _make_user(client, admin, "rowout_a1", "A")
    schedule_id = _db_schedule(2051, 11, _month_cells(2051, 11, [user["id"]]))
    res = client.post(
        f"{V}/schedules/{schedule_id}/override", headers=admin,
        json={"user_id": user["id"], "work_date": "2051-12-01", "code": "A"},
    )
    assert res.status_code == 422
    assert res.json()["detail"] == t("schedule.override_date_out_of_month")
    for lang in ("en", "vi"):
        for key in (
            "schedule.override_date_out_of_month",
            "schedule.cell_not_found",
            "schedule.disabled_user_duty",
        ):
            assert t(key, lang) != key


def test_recheck_flags_disabled_user_ad_cells(client: TestClient) -> None:
    """F13 / R4 — a user disabled after generation keeps their cells, but the
    re-check flags their duty cells and no longer counts them as cover."""
    admin = _admin_headers(client)
    a1 = _make_user(client, admin, "recheckdis_a1", "A")
    a2 = _make_user(client, admin, "recheckdis_a2", "A")
    duty_day = date(2052, 3, 10)
    res = client.put(
        f"{V}/flights/days", headers=admin,
        json={"day": duty_day.isoformat(), "flight_pairs": 1},
    )
    assert res.status_code in (200, 201), res.text
    cells = _month_cells(2052, 3, [a1["id"], a2["id"]])
    cells[(a1["id"], duty_day)] = "A/D"  # a1 alone covers the day's pair
    schedule_id = _db_schedule(2052, 3, cells)

    def _check() -> list[dict]:
        r = client.get(f"{V}/schedules/{schedule_id}/violations", headers=admin)
        assert r.status_code == 200, r.text
        return r.json()

    def _short_on_duty_day(items: list[dict]) -> bool:
        return any(
            "short flight coverage" in v["message"] and str(duty_day) in v["message"]
            for v in items
        )

    before = _check()
    assert not _short_on_duty_day(before)
    assert not any(v["rule"] == "disabled_user_duty" for v in before)

    res = client.patch(
        f"{V}/users/{a1['id']}", headers=admin, json={"status": "disabled"}
    )
    assert res.status_code == 200, res.text

    after = _check()
    flagged = [v for v in after if v["rule"] == "disabled_user_duty"]
    assert [(v["day"], v["user_id"]) for v in flagged] == [
        (duty_day.isoformat(), a1["id"])
    ]
    # The message itself names the day once (text-only callers show it too).
    assert flagged[0]["message"] == (
        f"{duty_day}: {t('schedule.disabled_user_duty')} (A/D)"
    )
    # The disabled user's A/D is no longer cover: the day is now short.
    assert _short_on_duty_day(after)
    staffing = [
        v["message"] for v in after
        if "short flight coverage" in v["message"] and str(duty_day) in v["message"]
    ]
    assert len(staffing) == 1 and staffing[0].count(str(duty_day)) == 1
    # Per-person rules no longer report the disabled user.
    assert not any(f"User {a1['id']}:" in v["message"] for v in after)

    # Text-only caller (leave decision): each line is "YYYY-MM: <message>" with
    # the message unchanged — no second day prefix on either kind of line.
    from app.core.database import SessionLocal
    from app.models.enums import AttendanceCode
    from app.services import schedule_service

    with SessionLocal() as db:
        lines = schedule_service.apply_leave_span(
            db, a2["id"], date(2052, 3, 20), date(2052, 3, 20), AttendanceCode.AL
        )
        db.rollback()
    for message in (flagged[0]["message"], staffing[0]):
        assert f"2052-03: {message}" in lines
        line = next(x for x in lines if message in x)
        assert line.count(str(duty_day)) == 1


# --- Final review fixes (I1, I2, M1) -----------------------------------------


def _seed_actuals(cells: dict[tuple[int, date], str]) -> None:
    """Insert actuals as ``seed_from_schedule`` would (``recorded_by`` NULL)."""
    from app.core.database import SessionLocal
    from app.models.attendance import AttendanceRecord
    from app.models.enums import AttendanceCode

    with SessionLocal() as db:
        for (user_id, day), code in cells.items():
            db.add(
                AttendanceRecord(
                    user_id=user_id, work_date=day, code=AttendanceCode(code)
                )
            )
        db.commit()


def _actual(user_id: int, day: date) -> str | None:
    from app.core.database import SessionLocal
    from app.models.attendance import AttendanceRecord

    with SessionLocal() as db:
        row = (
            db.query(AttendanceRecord)
            .filter(AttendanceRecord.user_id == user_id, AttendanceRecord.work_date == day)
            .one_or_none()
        )
        return None if row is None else row.code.value


def test_force_regenerate_then_override_reaches_next_month_boundary(
    client: TestClient, monkeypatch
) -> None:
    """I1 — after a forced regenerate the month is a draft, but its actuals
    are still the seeded copies of the plan: an admin edit of the draft must
    move them too, or next month's boundary keeps reading the replaced code.
    A further regenerate of the (draft) month resyncs them as well."""
    import calendar

    from app.core.config import settings
    from app.core.database import SessionLocal
    from app.models.attendance import AttendanceRecord
    from app.models.enums import AttendanceCode
    from app.models.user import User
    from app.services import schedule_history

    monkeypatch.setattr(settings, "SOLVER_MAX_TIME_SECONDS", GENERATE_TIME_LIMIT)
    yr, mo = 2063, 1
    last_day = date(yr, mo, calendar.monthrange(yr, mo)[1])
    admin = _admin_headers(client)
    users = [_make_user(client, admin, f"i1sync_a{i}", "A") for i in (1, 2, 3, 4)]
    ids = {x["id"] for x in users}

    gen = _generate(client, admin, yr, mo)
    assert gen.status_code == 200 and gen.json()["feasible"] is True, gen.text
    schedule_id = gen.json()["schedule"]["id"]
    pub = client.post(f"{V}/schedules/{schedule_id}/publish", headers=admin)
    assert pub.status_code == 200, pub.text

    regen = _generate(client, admin, yr, mo, force=True)
    assert regen.status_code == 200 and regen.json()["feasible"] is True, regen.text
    assert regen.json()["schedule"]["status"] == "draft"
    u = users[0]["id"]

    def _boundary():  # noqa: ANN202
        with SessionLocal() as db:
            return schedule_history.build_boundary_states(
                db, [db.get(User, u)], yr, mo + 1
            )[u]

    # Whatever the solver planned, make the seeded actual of the last day a
    # working code, so the edit below has something to move.
    with SessionLocal() as db:
        db.query(AttendanceRecord).filter(
            AttendanceRecord.user_id == u, AttendanceRecord.work_date == last_day
        ).update({"code": AttendanceCode.A})
        db.commit()
    assert _boundary().prev_codes[-1] is AttendanceCode.A

    res = client.post(
        f"{V}/schedules/{schedule_id}/override", headers=admin,
        json={"user_id": u, "work_date": last_day.isoformat(), "code": "X"},
    )
    assert res.status_code == 200, res.text
    assert _actual(u, last_day) == "X"
    state = _boundary()
    assert state.prev_codes[-1] is AttendanceCode.X
    assert state.previous_working[last_day] is False

    # A stale seeded actual on the draft month follows the next regenerate.
    stale_day = date(yr, mo, 3)
    with SessionLocal() as db:
        db.query(AttendanceRecord).filter(
            AttendanceRecord.user_id == u, AttendanceRecord.work_date == stale_day
        ).update({"code": AttendanceCode.O_D})
        db.commit()
    regen = _generate(client, admin, yr, mo, force=True)
    assert regen.status_code == 200 and regen.json()["feasible"] is True, regen.text
    plan = {
        (a["user_id"], a["work_date"]): a["code"]
        for a in regen.json()["schedule"]["assignments"]
    }
    rows = client.get(
        f"{V}/attendance", params={"year": yr, "month": mo}, headers=admin
    ).json()
    mine = [r for r in rows if r["user_id"] in ids]
    assert mine
    for row in mine:
        assert row["code"] == plan[(row["user_id"], row["work_date"])], row


def test_draft_edits_move_seeded_actuals(client: TestClient) -> None:
    """I1 — leave decisions and approved shift changes on a DRAFT month move
    its still-seeded actuals (left over from an earlier publication)."""
    from app.core.database import SessionLocal
    from app.models.enums import AttendanceCode, SwapKind
    from app.models.shift_change_request import ShiftChangeRequest
    from app.services import schedule_service

    admin = _admin_headers(client)
    user = _make_user(client, admin, "i1draft_t1", "T")
    uid = user["id"]
    yr, mo = 2063, 3
    leave_day, change_day = date(yr, mo, 5), date(yr, mo, 7)
    _db_schedule(yr, mo, _month_cells(yr, mo, [uid], code="AD"))
    _seed_actuals({(uid, leave_day): "AD", (uid, change_day): "AD"})

    with SessionLocal() as db:
        schedule_service.apply_leave_span(
            db, uid, leave_day, leave_day, AttendanceCode.AL
        )
        db.commit()
    assert _actual(uid, leave_day) == "AL"

    with SessionLocal() as db:
        req = ShiftChangeRequest(
            requester_id=uid, work_date=change_day, kind=SwapKind.change_code,
            requested_code=AttendanceCode.X,
        )
        schedule_service.apply_shift_change(db, req)
        db.commit()
    assert _actual(uid, change_day) == "X"


def test_disabled_user_past_cells_still_count_as_cover(
    client: TestClient, monkeypatch
) -> None:
    """I2 — a user disabled on the 15th really worked the days before: those
    cells stay normal cover and are not flagged; only cells from business
    today on are flagged and no longer count."""
    from datetime import UTC, datetime

    from app.core import business_time

    monkeypatch.setattr(
        business_time, "_utcnow", lambda: datetime(2063, 5, 15, 10, 0, tzinfo=UTC)
    )
    admin = _admin_headers(client)
    a1 = _make_user(client, admin, "i2past_a1", "A")
    a2 = _make_user(client, admin, "i2past_a2", "A")
    past_day, today, future_day = date(2063, 5, 10), date(2063, 5, 15), date(2063, 5, 20)
    cells = _month_cells(2063, 5, [a1["id"], a2["id"]])
    for day in (past_day, today, future_day):
        res = client.put(
            f"{V}/flights/days", headers=admin,
            json={"day": day.isoformat(), "flight_pairs": 1},
        )
        assert res.status_code in (200, 201), res.text
        cells[(a1["id"], day)] = "A/D"  # a1 alone covers the day's pair
    schedule_id = _db_schedule(2063, 5, cells)
    res = client.patch(
        f"{V}/users/{a1['id']}", headers=admin, json={"status": "disabled"}
    )
    assert res.status_code == 200, res.text

    res = client.get(f"{V}/schedules/{schedule_id}/violations", headers=admin)
    assert res.status_code == 200, res.text
    items = res.json()

    flagged = [
        (v["day"], v["user_id"]) for v in items if v["rule"] == "disabled_user_duty"
    ]
    assert flagged == [
        (today.isoformat(), a1["id"]), (future_day.isoformat(), a1["id"])
    ]

    def _short(day: date) -> bool:
        return any(
            "short flight coverage" in v["message"] and str(day) in v["message"]
            for v in items
        )

    assert not _short(past_day)
    assert _short(today) and _short(future_day)
    # Per-person rules still never report the disabled user.
    assert not any(f"User {a1['id']}:" in v["message"] for v in items)


def test_resync_seeded_actuals_query_count_is_flat(client: TestClient) -> None:
    """M1 — the regenerate resync reuses the month's loaded rows: the number
    of statements does not grow with the number of actuals."""
    from sqlalchemy import event

    from app.core.database import SessionLocal, engine
    from app.models.enums import AttendanceCode
    from app.services import schedule_service

    admin = _admin_headers(client)
    u1 = _make_user(client, admin, "m1flat_t1", "T")["id"]
    u2 = _make_user(client, admin, "m1flat_t2", "T")["id"]
    yr, mo = 2063, 7

    def _count_resync(user_ids: list[int]) -> int:
        plan = {key: AttendanceCode.AD for key in _month_cells(yr, mo, user_ids)}
        statements: list[str] = []

        def _on_execute(_conn, _cursor, statement, *_args):  # noqa: ANN001, ANN202
            statements.append(statement)

        with SessionLocal() as db:
            event.listen(engine, "before_cursor_execute", _on_execute)
            try:
                schedule_service._resync_seeded_actuals(db, yr, mo, plan)
                db.flush()
            finally:
                event.remove(engine, "before_cursor_execute", _on_execute)
            db.rollback()
        return len([s for s in statements if s.lstrip().upper().startswith("SELECT")])

    _seed_actuals(_month_cells(yr, mo, [u1]))
    one_user = _count_resync([u1])
    _seed_actuals(_month_cells(yr, mo, [u2]))
    two_users = _count_resync([u1, u2])
    assert one_user == two_users
    assert two_users <= 2
