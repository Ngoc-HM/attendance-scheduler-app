"""End-to-end boundary state: previous A/D (or holiday work) earns next-month CD."""

from __future__ import annotations

from datetime import date

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.attendance import AttendanceRecord
from app.models.enums import AttendanceCode, Role, ScheduleStatus, UserStatus
from app.models.holiday import Holiday
from app.models.schedule import MonthlySchedule, ShiftAssignment
from app.models.user import User
from app.scheduler import PersonInput, SchedulerEngine, SolverInput
from app.scheduler.calendar_utils import build_weeks, month_days
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
                weeks=build_weeks(days),
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

