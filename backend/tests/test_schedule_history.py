"""End-to-end boundary state: previous A/D (or holiday work) earns next-month CD."""

from __future__ import annotations

from datetime import date

from sqlalchemy import event

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.security import get_password_hash
from app.models.attendance import AttendanceRecord
from app.models.enums import AttendanceCode, Role, ScheduleStatus, UserStatus
from app.models.holiday import Holiday
from app.models.schedule import MonthlySchedule, ShiftAssignment
from app.models.user import User
from app.scheduler import PersonInput, SchedulerEngine, SolverInput
from app.scheduler.calendar_utils import month_days
from app.services import carry_over_math
from app.services.schedule_history import build_boundary_states
from app.services.user_service import next_user_code


def test_planned_ad_becomes_cd_and_actual_overrides_plan(client) -> None:
    db = SessionLocal()
    try:
        user = User(
            username="history_comp_a",
            code=next_user_code(db, Role.A),
            full_name="History Comp A",
            hashed_password=get_password_hash("pass123"),
            role=Role.A,
            status=UserStatus.active,
        )
        db.add(user)
        db.flush()

        schedule = MonthlySchedule(
            year=2031, month=6, status=ScheduleStatus.published
        )
        db.add(schedule)
        db.flush()
        # Two planned doubles, but one was actually a single A: actual wins, so
        # exactly one compensation day remains owed.
        for day in (15, 20):
            db.add(
                ShiftAssignment(
                    schedule_id=schedule.id,
                    user_id=user.id,
                    work_date=date(2031, 6, day),
                    code=AttendanceCode.A_D,
                )
            )
        for day in (29, 30):
            db.add(
                ShiftAssignment(
                    schedule_id=schedule.id,
                    user_id=user.id,
                    work_date=date(2031, 6, day),
                    code=AttendanceCode.D,
                )
            )
        db.add(
            AttendanceRecord(
                user_id=user.id,
                work_date=date(2031, 6, 20),
                code=AttendanceCode.A,
            )
        )
        db.commit()

        state = build_boundary_states(db, [user], 2031, 7)[user.id]
        assert state.carry_comp == 1
        assert state.carry_streak == 2
        assert state.previous_working[date(2031, 6, 29)] is True
        assert state.previous_working[date(2031, 6, 30)] is True

        days = month_days(2031, 7)
        out = SchedulerEngine().solve(
            SolverInput(
                year=2031,
                month=7,
                people=[
                    PersonInput(
                        user.id,
                        Role.A,
                        carry_comp=state.carry_comp,
                        carry_streak=state.carry_streak,
                    )
                ],
                days=days,
                flight_pairs={day: 0 for day in days},
                previous_working={user.id: state.previous_working},
                max_solve_seconds=10,
            )
        )
        assert out.feasible and not out.violations
        assert sum(item.code is AttendanceCode.CD for item in out.assignments) == 1
    finally:
        db.close()


def test_role_t_holiday_work_carries_one_comp_day(client) -> None:
    """Owner D1 (2026-11-06): a role-T person who worked a public holiday owes
    one CD the next month; an OFF holiday earns nothing."""
    db = SessionLocal()
    try:
        user = User(
            username="history_holiday_t",
            code=next_user_code(db, Role.T),
            full_name="History Holiday T",
            hashed_password=get_password_hash("pass123"),
            role=Role.T,
            status=UserStatus.active,
        )
        db.add(user)
        db.add(Holiday(day=date(2036, 9, 2), name="Worked holiday"))
        db.add(Holiday(day=date(2036, 9, 3), name="Off holiday"))
        db.flush()

        schedule = MonthlySchedule(
            year=2036, month=9, status=ScheduleStatus.published
        )
        db.add(schedule)
        db.flush()
        for day, code in ((2, AttendanceCode.AD), (3, AttendanceCode.X)):
            db.add(
                ShiftAssignment(
                    schedule_id=schedule.id,
                    user_id=user.id,
                    work_date=date(2036, 9, day),
                    code=code,
                )
            )
        db.commit()

        state = build_boundary_states(db, [user], 2036, 10)[user.id]
        assert state.carry_comp == 1
    finally:
        db.close()


def test_holiday_comp_respects_effective_date(client, monkeypatch) -> None:
    """Holidays worked before HOLIDAY_COMP_EFFECTIVE_FROM earn nothing, so a
    live database does not get a lump of back-owed CDs on the next draft."""
    db = SessionLocal()
    try:
        user = User(
            username="history_holiday_effective",
            code=next_user_code(db, Role.T),
            full_name="History Holiday Effective",
            hashed_password=get_password_hash("pass123"),
            role=Role.T,
            status=UserStatus.active,
        )
        db.add(user)
        db.add(Holiday(day=date(2038, 3, 2), name="Worked holiday"))
        db.flush()
        schedule = MonthlySchedule(
            year=2038, month=3, status=ScheduleStatus.published
        )
        db.add(schedule)
        db.flush()
        db.add(
            ShiftAssignment(
                schedule_id=schedule.id,
                user_id=user.id,
                work_date=date(2038, 3, 2),
                code=AttendanceCode.AD,
            )
        )
        db.commit()

        monkeypatch.setattr(settings, "HOLIDAY_COMP_EFFECTIVE_FROM", date(2038, 3, 3))
        assert build_boundary_states(db, [user], 2038, 4)[user.id].carry_comp == 0

        monkeypatch.setattr(settings, "HOLIDAY_COMP_EFFECTIVE_FROM", date(2038, 3, 2))
        assert build_boundary_states(db, [user], 2038, 4)[user.id].carry_comp == 1
    finally:
        db.close()


def test_stored_streak_fallback_only_without_any_history(client) -> None:
    """A user WITH history but no cell on the cutoff day has a broken run
    (unknown day = rest) → streak 0, never the stored value read back; only a
    user with no history at all falls back to the stored ``carry_streak``."""
    db = SessionLocal()
    try:
        users = []
        for username in ("history_streak_gap", "history_streak_none"):
            user = User(
                username=username,
                code=next_user_code(db, Role.T),
                full_name=username,
                hashed_password=get_password_hash("pass123"),
                role=Role.T,
                status=UserStatus.active,
                carry_streak=4,
            )
            db.add(user)
            db.flush()
            users.append(user)
        gap_user, no_history_user = users

        schedule = MonthlySchedule(
            year=2037, month=5, status=ScheduleStatus.published
        )
        db.add(schedule)
        db.flush()
        # Worked mid-month, but nothing on 31 May (deactivated / not scheduled).
        for day in (10, 11, 12):
            db.add(
                ShiftAssignment(
                    schedule_id=schedule.id,
                    user_id=gap_user.id,
                    work_date=date(2037, 5, day),
                    code=AttendanceCode.AD,
                )
            )
        db.commit()

        states = build_boundary_states(db, users, 2037, 6)

        gap = states[gap_user.id]
        assert gap.carry_streak == 0
        assert not any(gap.previous_working.values())

        none = states[no_history_user.id]
        assert none.carry_streak == 4
        assert [none.previous_working[date(2037, 5, d)] for d in range(26, 32)] == [
            False, False, True, True, True, True,
        ]
        assert none.prev_codes == ()
    finally:
        db.close()


def _user(db, username: str, role: Role = Role.A) -> User:
    user = User(
        username=username,
        code=next_user_code(db, role),
        full_name=username,
        hashed_password=get_password_hash("pass123"),
        role=role,
        status=UserStatus.active,
    )
    db.add(user)
    db.flush()
    return user


def _planned(db, year: int, month: int, cells) -> None:
    """Add a published schedule for (year, month) with ``cells``:
    ``[(user_id, day_of_month, code), ...]``."""
    schedule = MonthlySchedule(year=year, month=month, status=ScheduleStatus.published)
    db.add(schedule)
    db.flush()
    for user_id, day, code in cells:
        db.add(
            ShiftAssignment(
                schedule_id=schedule.id,
                user_id=user_id,
                work_date=date(year, month, day),
                code=code,
            )
        )


def test_pre_cutoff_cd_does_not_consume_post_cutoff_comp(client, monkeypatch) -> None:
    """F10 / ruling R3: comp days consumed before HOLIDAY_COMP_EFFECTIVE_FROM
    only offset what was earned before it — a legacy manual CD never eats the
    holiday comp earned after the cut-off. A pre-cut-off A/D that its own CD
    already paid back stays paid back."""
    effective = date(2051, 3, 10)
    monkeypatch.setattr(settings, "HOLIDAY_COMP_EFFECTIVE_FROM", effective)
    holidays = {date(2051, 3, 15), date(2051, 3, 20)}

    A_D, CD, A, D = AttendanceCode.A_D, AttendanceCode.CD, AttendanceCode.A, AttendanceCode.D
    records = [
        (date(2051, 2, 3), A_D),   # pre: earns 1
        (date(2051, 2, 5), CD),    # pre: pays it back
        (date(2051, 2, 7), CD),    # pre: legacy manual CD, nothing left to pay
        (date(2051, 3, 15), A),    # post: holiday work earns 1
        (date(2051, 3, 20), D),    # post: holiday work earns 1
    ]
    assert carry_over_math.comp_balance(records, holidays, effective) == 2
    # A CD after the cut-off consumes post-cut-off comp as before.
    assert carry_over_math.comp_balance(
        [*records, (date(2051, 3, 25), CD)], holidays, effective
    ) == 1
    # No cut-off: one undivided history, as before.
    assert carry_over_math.comp_balance(records, holidays, None) == 1

    db = SessionLocal()
    try:
        user = _user(db, "history_comp_cutoff")
        for day in holidays:
            db.add(Holiday(day=day, name=f"Holiday {day}"))
        _planned(db, 2051, 2, [(user.id, d.day, c) for d, c in records if d.month == 2])
        _planned(db, 2051, 3, [(user.id, d.day, c) for d, c in records if d.month == 3])
        db.commit()

        assert build_boundary_states(db, [user], 2051, 4)[user.id].carry_comp == 2
    finally:
        db.close()


def test_boundary_states_prev_codes(client) -> None:
    """``prev_codes`` = the effective codes of the previous month's last six
    days, oldest first (actual over planned); a missing day cuts it short."""
    db = SessionLocal()
    try:
        full = _user(db, "history_prev_full", Role.T)
        gap = _user(db, "history_prev_gap", Role.T)
        X, AD, CD = AttendanceCode.X, AttendanceCode.AD, AttendanceCode.CD
        _planned(
            db, 2053, 5,
            [(full.id, d, X if d in (27, 28) else AD) for d in range(20, 32)]
            + [(gap.id, d, X) for d in (26, 27, 29, 30, 31)],
        )
        db.add(AttendanceRecord(user_id=full.id, work_date=date(2053, 5, 30), code=CD))
        db.commit()

        states = build_boundary_states(db, [full, gap], 2053, 6)
        assert states[full.id].prev_codes == (AD, X, X, AD, CD, AD)
        assert states[full.id].carry_streak == 1
        assert states[gap.id].prev_codes == (X, X, X)
        assert states[gap.id].carry_streak == 0
    finally:
        db.close()


def test_boundary_states_query_count_bounded(client) -> None:
    """F14: the number of SQL statements does not grow with the number of
    users (no per-user query, no full-history ORM load)."""
    db = SessionLocal()
    try:
        ids = []
        for n in range(8):
            user = _user(db, f"history_queries_{n}")
            ids.append(user.id)
        _planned(
            db, 2052, 5,
            [
                (uid, d, AttendanceCode.X if (d + uid) % 7 in (0, 1) else AttendanceCode.A)
                for uid in ids
                for d in range(1, 32)
            ],
        )
        for uid in ids:
            db.add(AttendanceRecord(user_id=uid, work_date=date(2052, 5, 31),
                                    code=AttendanceCode.A_D))
        db.commit()
    finally:
        db.close()

    fresh = SessionLocal()
    try:

        history_rows: list[object] = []

        def on_load(session, instance) -> None:
            if isinstance(instance, (ShiftAssignment, AttendanceRecord)):
                history_rows.append(instance)

        def count_statements(users: list[User]) -> int:
            statements: list[str] = []

            def listener(conn, cursor, statement, parameters, context, executemany):
                statements.append(statement)

            event.listen(engine, "before_cursor_execute", listener)
            try:
                states = build_boundary_states(fresh, users, 2052, 6)
            finally:
                event.remove(engine, "before_cursor_execute", listener)
            assert all(states[u.id].carry_comp == 1 for u in users)
            return len(statements)

        # Load the users up front so lazy refreshes are not counted.
        loaded = fresh.query(User).filter(User.id.in_(ids)).order_by(User.id).all()
        event.listen(fresh, "loaded_as_persistent", on_load)
        try:
            few = count_statements(loaded[:2])
            many = count_statements(loaded)
        finally:
            event.remove(fresh, "loaded_as_persistent", on_load)
        assert few == many
        assert many <= 4
        # History is aggregated in SQL, never loaded as ORM objects.
        assert history_rows == []
    finally:
        fresh.close()
