"""The good-pair carry read from the effective history (owner 2026-11-12).

``schedule_history.carry_pair_points``: the weekday-bonus points (Fri+Sat 3,
Sat+Sun 2, Sun+Mon 1) of each user's adjacent X+X pairs in the 12 months
before the month being generated — actual attendance wins over the plan,
only genuine X counts, a pair across a month boundary counts once, and the
whole group costs two statements.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import event

from app.core.database import SessionLocal, engine
from app.core.security import get_password_hash
from app.models.attendance import AttendanceRecord
from app.models.enums import AttendanceCode, Role, ScheduleStatus, UserStatus
from app.models.schedule import MonthlySchedule, ShiftAssignment
from app.models.user import User
from app.services.carry_over_math import pair_points
from app.services.schedule_history import carry_pair_points
from app.services.user_service import next_user_code

X, AL, CD, A, AD = (
    AttendanceCode.X,
    AttendanceCode.AL,
    AttendanceCode.CD,
    AttendanceCode.A,
    AttendanceCode.AD,
)


def test_pair_points_by_first_day_weekday() -> None:
    """Fri+Sat 3, Sat+Sun 2, Sun+Mon 1, others 0; a Fri–Sun run holds two
    pairs (3 + 2); a lone X earns nothing."""
    fri = date(2026, 11, 6)
    assert fri.weekday() == 4
    day = lambda n: date.fromordinal(fri.toordinal() + n)  # noqa: E731
    assert pair_points([day(0), day(1)]) == 3
    assert pair_points([day(1), day(2)]) == 2
    assert pair_points([day(2), day(3)]) == 1
    assert pair_points([day(3), day(4)]) == 0  # Mon+Tue
    assert pair_points([day(0), day(1), day(2)]) == 5
    assert pair_points([day(0)]) == 0
    assert pair_points([]) == 0


def _user(db, username: str) -> User:
    user = User(
        username=username,
        code=next_user_code(db, Role.T),
        full_name=username,
        hashed_password=get_password_hash("pass123"),
        role=Role.T,
        status=UserStatus.active,
    )
    db.add(user)
    db.flush()
    return user


def test_carry_pair_points_from_effective_history(client) -> None:
    """Target July 2072 → window 1 Jul 2071 – 30 Jun 2072.

    Counted: Fri+Sat 2–3 Oct 2071 (+3, planned), Sat 31 Oct + Sun 1 Nov 2071
    (+2, across two schedules, once), Sun+Mon 10–11 Jan 2072 (+1, planned
    work but actually X). Not counted: Fri+Sat 5–6 Jun 2071 (before the
    window), Fri+Sat 1–2 Jul 2072 (the target month), AL+X / X+CD 4–6 Dec
    2071, and Fri+Sat 1–2 Jan 2072 planned X whose Saturday was actually A.
    """
    planned: dict[tuple[int, int], list[tuple[int, AttendanceCode]]] = {
        (2071, 6): [(5, X), (6, X)],
        (2071, 10): [(2, X), (3, X), (31, X)],
        (2071, 11): [(1, X)],
        (2071, 12): [(4, AL), (5, X), (6, CD)],
        (2072, 1): [(1, X), (2, X), (10, AD), (11, AD)],
        (2072, 7): [(1, X), (2, X)],
    }
    actual = [(date(2072, 1, 2), A), (date(2072, 1, 10), X), (date(2072, 1, 11), X)]

    db = SessionLocal()
    try:
        user = _user(db, "pair_carry_user")
        empty = _user(db, "pair_carry_empty")
        for (year, month), cells in planned.items():
            schedule = MonthlySchedule(year=year, month=month, status=ScheduleStatus.published)
            db.add(schedule)
            db.flush()
            for day, code in cells:
                db.add(
                    ShiftAssignment(
                        schedule_id=schedule.id,
                        user_id=user.id,
                        work_date=date(year, month, day),
                        code=code,
                    )
                )
        for day, code in actual:
            db.add(AttendanceRecord(user_id=user.id, work_date=day, code=code))
        db.commit()
        uid, empty_id = user.id, empty.id  # loaded before counting statements

        statements: list[str] = []

        def listener(conn, cursor, statement, *args) -> None:
            statements.append(statement)

        event.listen(engine, "before_cursor_execute", listener)
        try:
            carry = carry_pair_points(db, {uid, empty_id}, 2072, 7)
        finally:
            event.remove(engine, "before_cursor_execute", listener)

        assert carry == {uid: 3 + 2 + 1, empty_id: 0}
        assert len(statements) == 2, statements
        # The month after: the Jun 2071 pair is still out, July 2072 now in.
        assert carry_pair_points(db, {uid}, 2072, 8) == {uid: 6 + 3}
    finally:
        db.close()
