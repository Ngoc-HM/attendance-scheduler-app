"""Group F follows the flights (customer 2026-11-18): duty per day, two X
per week, turns that swap every week — in the solver and in the re-check."""

from __future__ import annotations

from datetime import date, timedelta

from app.models.enums import AttendanceCode, Role
from app.scheduler import SchedulerEngine, role_f
from app.scheduler.calendar_utils import month_days
from app.scheduler.domain import PersonInput, SolverInput
from app.services import schedule_violation_checker as checker

AD, X, AL = AttendanceCode.AD, AttendanceCode.X, AttendanceCode.AL
F1, F2 = 5, 6


def _usual(days: list[date]) -> dict[date, int]:
    """Today's plan: two pairs a day, one on Tuesday and Friday."""
    return {d: 1 if d.weekday() in (1, 4) else 2 for d in days}


def _solve(year: int, month: int, flights=None, approved_off=None, prev=None):
    days = month_days(year, month)
    before = [days[0] - timedelta(days=n) for n in range(1, 7)]
    inp = SolverInput(
        year=year, month=month, days=days,
        people=[
            PersonInput(F1, Role.F, prev_codes=(prev or {}).get(F1, ())),
            PersonInput(F2, Role.F, prev_codes=(prev or {}).get(F2, ())),
        ],
        flight_pairs=flights or _usual(days),
        prev_flight_pairs=_usual(before),
        approved_off=approved_off or {},
        max_solve_seconds=20,
    )
    out = SchedulerEngine(num_workers=1).solve(inp)
    grid = {(a.user_id, a.day): a.code for a in out.assignments}
    rules = [v for v in out.violations if v.rule.startswith(("role_f", "max_consecutive"))]
    return days, grid, rules


def _recheck_f(grid, days, flights, prev=None):
    roles = {F1: Role.F, F2: Role.F}
    return (
        checker.check_role_f_staffing(grid, roles, days, flights)
        + checker.check_role_f_weekly_rest(grid, roles, days, prev or {})
        + checker.check_consecutive(grid, roles, {}, days)
    )


def test_need_follows_flights_on_weekdays_and_is_one_at_the_weekend() -> None:
    monday, saturday = date(2026, 12, 7), date(2026, 12, 12)
    assert role_f.need(monday, 2, 2) == 2
    assert role_f.need(monday, 1, 2) == 1
    assert role_f.need(monday, 0, 2) == 1  # no flight: one person still goes
    assert role_f.need(saturday, 2, 2) == 1
    assert role_f.need(monday, 2, 3) == 2
    assert role_f.need(monday, 2, 1) == 0  # one person alone: no duty rule


def test_turns_alternate_within_a_week_and_swap_the_next_week() -> None:
    days = month_days(2026, 12)
    duty = role_f.rotation_duty(days, _usual(days), {}, [F1, F2])
    week1 = [duty[date(2026, 12, n)][0] for n in (8, 11, 12, 13)]  # Tue Fri Sat Sun
    week2 = [duty[date(2026, 12, n)][0] for n in (15, 18, 19, 20)]
    assert week1[0] != week1[1] and week1[0] == week1[2] and week1[1] == week1[3]
    assert week2 == [week1[1], week1[0], week1[1], week1[0]]
    assert date(2026, 12, 7) not in duty  # two pairs: everybody works


def test_week_rest_is_exact_inside_the_month_and_a_range_at_its_end() -> None:
    days = month_days(2026, 12)  # ends on a Thursday
    weeks = role_f.week_rest(days, {}, {})
    full = next(w for w in weeks if w.monday == date(2026, 12, 7))
    assert (full.low, full.high) == (2, 2)
    last = weeks[-1]  # Mon 28 – Thu 31: three days of it belong to January
    assert (last.low, last.high) == (0, 2)
    # Leave on a Saturday takes the place of one rest day.
    leave = role_f.week_rest(days, {date(2026, 12, 12): AL}, {})
    assert next(w for w in leave if w.monday == date(2026, 12, 7)).target == 1


def test_usual_plan_gives_five_days_a_week_with_swapped_days_off() -> None:
    days, grid, rules = _solve(2026, 12)
    assert rules == []
    assert _recheck_f(grid, days, _usual(days)) == []  # solver and re-check agree

    def off(uid: int, monday: date) -> set[int]:
        return {n for n in range(7) if grid[(uid, monday + timedelta(days=n))] is X}

    first, second = date(2026, 12, 7), date(2026, 12, 14)
    assert {frozenset(off(F1, first)), frozenset(off(F2, first))} == {
        frozenset({1, 5}), frozenset({4, 6})  # Tue+Sat and Fri+Sun
    }
    assert off(F1, second) == off(F2, first) and off(F2, second) == off(F1, first)
    for d in days:
        working = sum(grid[(u, d)] is AD for u in (F1, F2))
        assert working == role_f.need(d, _usual(days)[d], 2)


def test_a_week_asking_too_much_keeps_five_days_and_reports_the_short_day() -> None:
    days = month_days(2026, 12)
    flights = _usual(days)
    flights[date(2026, 12, 8)] = 2  # Tuesday with two pairs: 11 person-days
    _, grid, rules = _solve(2026, 12, flights=flights)
    assert [v.rule for v in rules] == ["role_f_staffing"]
    assert date(2026, 12, 7) <= rules[0].day <= date(2026, 12, 13)
    for uid in (F1, F2):
        worked = sum(
            grid[(uid, date(2026, 12, 7) + timedelta(days=n))] is AD for n in range(7)
        )
        assert worked == 5


def test_the_turn_continues_across_the_month_boundary() -> None:
    days, grid, _ = _solve(2026, 12)
    prev = {u: tuple(grid[(u, d)] for d in days[-6:]) for u in (F1, F2)}
    january, grid2, rules = _solve(2027, 1, prev=prev)
    assert rules == []
    assert _recheck_f(grid2, january, _usual(january), prev) == []
    # The week of Mon 28 Dec: each person has two days off over both months.
    both = {**grid, **grid2}
    for uid in (F1, F2):
        week = [date(2026, 12, 28) + timedelta(days=n) for n in range(7)]
        assert sum(both[(uid, d)] is X for d in week) == 2


def test_recheck_reports_a_short_day_and_a_week_without_rest() -> None:
    days = month_days(2026, 12)
    flights = _usual(days)
    grid = {(u, d): AD for u in (F1, F2) for d in days}
    grid[(F1, date(2026, 12, 7))] = AL  # Monday, two pairs, F1 on leave
    warnings = _recheck_f(grid, days, flights)
    assert any(
        v.rule == "role_f_staffing" and v.day == date(2026, 12, 7)
        and v.params["amount"] == 1 for v in warnings
    )
    assert any(v.rule == "role_f_weekly_off_shortfall" and v.user_id == F2 for v in warnings)


def test_group_f_is_outside_the_monthly_count_and_group_t_keeps_it() -> None:
    days = month_days(2026, 12)
    grid = {(u, d): AD for u in (F1, 7) for d in days}
    monthly = checker.check_monthly_quota(grid, {F1: Role.F, 7: Role.T}, days)
    assert [v.user_id for v in monthly] == [7]


# --- leave of a group-F person: the risk kept on the request ----------------


def test_leave_of_group_f_reports_the_days_below_duty() -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from app.core.database import Base
    from app.core.i18n import set_request_language
    from app.models.enums import LeaveStatus, LeaveType, UserStatus
    from app.models.flight import FlightDay
    from app.models.leave import LeaveRequest
    from app.models.user import User
    from app.services import leave_staffing

    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine, autoflush=False)()
    set_request_language("en")
    try:
        ids = []
        for code in ("F1", "F2"):
            user = User(username=code.lower(), code=code, full_name=code,
                        hashed_password="x", role=Role.F, status=UserStatus.active)
            db.add(user)
            db.flush()
            ids.append(user.id)
        monday, tuesday = date(2045, 3, 6), date(2045, 3, 7)
        db.add_all([FlightDay(day=monday, flight_pairs=2),
                    FlightDay(day=tuesday, flight_pairs=1)])
        req = LeaveRequest(user_id=ids[0], start_date=monday, end_date=tuesday,
                           leave_type=LeaveType.monthly, status=LeaveStatus.pending)
        db.add(req)
        db.commit()
        # Monday needs both; Tuesday needs one and the colleague is there.
        assert leave_staffing.staffing_warnings(db, req) == [
            "2045-03-06: 1 group-F staff left, 2 needed"
        ]
    finally:
        set_request_language(None)
        db.close()
        engine.dispose()
