"""Per-kind effective history is reconstructed, never accumulated twice."""

from datetime import date

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models.attendance import AttendanceRecord
from app.models.enums import AttendanceCode, Role, ScheduleStatus, UserStatus
from app.models.schedule import MonthlySchedule, ShiftAssignment
from app.models.user import User
from app.scheduler.domain import RestTurnHistory
from app.services import schedule_history, schedule_input_builder

X, AL, CD, AD = AttendanceCode.X, AttendanceCode.AL, AttendanceCode.CD, AttendanceCode.AD


def test_history_effective_overrides_window_and_boundary_once():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = User(
            username="turn-history",
            code="T999",
            full_name="History",
            hashed_password="x",
            role=Role.T,
            status=UserStatus.active,
        )
        db.add(user)
        db.flush()
        uid = user.id
        schedules = {}
        planned = {
            # Boundary at LEFT edge: belongs to August by its second day.
            date(2026, 7, 31): X,
            date(2026, 8, 1): X,
            # Before 12-month window, excluded.
            date(2026, 7, 24): X,
            date(2026, 7, 25): X,
            date(2027, 6, 4): X,
            date(2027, 6, 5): X,
            date(2027, 6, 11): AL,
            date(2027, 6, 12): X,
            date(2027, 6, 18): X,
            date(2027, 6, 19): CD,
            date(2027, 7, 2): AD,
            date(2027, 7, 3): AD,
            # Right edge pair belongs to August: not in August's prior history.
            date(2027, 7, 31): X,
            date(2027, 8, 1): X,
        }
        rows = {}
        for day, code in planned.items():
            key = day.year, day.month
            if key not in schedules:
                schedules[key] = MonthlySchedule(
                    year=day.year, month=day.month, status=ScheduleStatus.published
                )
                db.add(schedules[key])
                db.flush()
            row = ShiftAssignment(
                schedule_id=schedules[key].id, user_id=uid, work_date=day, code=code
            )
            rows[day] = row
            db.add(row)
        # Actual breaks June planned pair; actual creates July pair.
        for day, code in [(date(2027, 6, 5), AD), (date(2027, 7, 2), X), (date(2027, 7, 3), X)]:
            db.add(AttendanceRecord(user_id=uid, work_date=day, code=code))
        db.flush()
        statements = []

        def listener(conn, cursor, statement, *args):
            statements.append(statement)

        event.listen(engine, "before_cursor_execute", listener)
        try:
            history = schedule_history.rest_turn_history(db, {uid, 99999}, 2027, 8)
        finally:
            event.remove(engine, "before_cursor_execute", listener)
        assert history[uid] == {
            4: RestTurnHistory(2, date(2027, 7, 3)),
            5: RestTurnHistory(),
            6: RestTurnHistory(),
        }
        assert history[99999] == {k: RestTurnHistory() for k in (4, 5, 6)}
        assert len(statements) == 2
        # Regenerating/removing a planned pair changes effective memory, no ledger double count.
        rows[date(2026, 8, 1)].code = AD
        db.flush()
        assert schedule_history.rest_turn_history(db, {uid}, 2027, 8)[uid][4].count == 1
        september = schedule_history.rest_turn_history(db, {uid}, 2027, 9)[uid]
        assert september[4] == RestTurnHistory(1, date(2027, 7, 3))
        assert september[5] == RestTurnHistory(1, date(2027, 8, 1))
        assert schedule_history.rest_turn_history(db, set(), 2027, 8) == {}
        # Builder carries independent histories along with compatible legacy fields.
        built = schedule_input_builder.build(db, 2027, 9)
        assert built.people[0].rest_turns == september
