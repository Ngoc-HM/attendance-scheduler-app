"""A month's roster runs to the end of its last week (owner 2026-11-18).

Plan ``docs/superpowers/plans/2026-11-18-roster-through-week-end.md``:
generating month M also plans the next month's days up to the Sunday that
ends M's last week. They are stored in M+1's schedule as carried cells,
kept as they are when M+1 is generated, published with M, and counted in
their own month. The carry days get no X minimum and at most their
Saturdays and Sundays as X.

The scenario runs the real service on its own database: 4 A, 2 F, 2 T and
1 M; the usual flights (two pairs a day, one on Tuesday and Friday).
"""

from __future__ import annotations

import io
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, timedelta

import pytest
from fastapi import HTTPException
from openpyxl import load_workbook
from ortools.sat.python import cp_model
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base
from app.models.enums import AttendanceCode, Role, ScheduleStatus, UserStatus
from app.models.flight import FlightDay
from app.models.schedule import MonthlySchedule, ShiftAssignment
from app.models.user import User
from app.scheduler import PersonInput, SchedulerEngine, SolverInput, carried, constraints, role_f
from app.scheduler.calendar_utils import carry_days, month_days, window_days
from app.scheduler.slack_registry import SlackRegistry
from app.schemas.schedule import ManualOverrideRequest
from app.services import (
    dashboard_service,
    flight_service,
    roster_report,
    schedule_autorun,
    schedule_input_builder,
    schedule_service,
    shift_time_service,
    time_clock_service,
)
from app.services.roster_xlsx import build_workbook
from app.services.schedule_violation_checker import recheck

A, D, X, AD, CD = (AttendanceCode.A, AttendanceCode.D, AttendanceCode.X, AttendanceCode.AD,
                   AttendanceCode.CD)
NOV, DEC, JAN = (2026, 11), (2026, 12), (2027, 1)


def _usual(day: date) -> int:
    return 1 if day.weekday() in (1, 4) else 2


# --- calendar and flights -----------------------------------------------------


def test_carry_days_run_to_the_sunday_ending_the_last_week() -> None:
    assert carry_days(*NOV) == [date(2026, 12, d) for d in range(1, 7)]
    assert carry_days(2026, 10) == [date(2026, 11, 1)]  # ends on a Saturday
    assert carry_days(*DEC) == [date(2027, 1, d) for d in range(1, 4)]
    assert carry_days(2026, 5) == []  # 31 May 2026 is a Sunday
    assert window_days(*NOV)[-1] == date(2026, 12, 6)


@pytest.fixture
def db() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def test_carry_day_without_flight_data_takes_its_weekday_count(db: Session) -> None:
    """Acceptance 3: no row → the latest same weekday with one (five weeks
    back at most); a row of its own wins."""
    for d in month_days(*NOV):
        db.add(FlightDay(day=d, flight_pairs=_usual(d)))
    db.add(FlightDay(day=date(2026, 12, 4), flight_pairs=0))  # Friday, entered
    db.commit()
    pairs = flight_service.carry_flight_pairs(db, carry_days(*NOV))
    assert pairs == {
        date(2026, 12, 1): 1,  # Tuesday
        date(2026, 12, 2): 2,
        date(2026, 12, 3): 2,
        date(2026, 12, 4): 0,  # its own row
        date(2026, 12, 5): 2,
        date(2026, 12, 6): 2,
    }
    # Nothing within five weeks → 0.
    assert flight_service.carry_flight_pairs(db, [date(2027, 3, 1)]) == {date(2027, 3, 1): 0}

    db.add(User(username="a1", code="A1", full_name="A1", hashed_password="x",
                role=Role.A, status=UserStatus.active))
    db.commit()
    inp = schedule_input_builder.build(db, *NOV)
    assert inp.days == window_days(*NOV)
    assert {d: inp.flight_pairs[d] for d in carry_days(*NOV)} == pairs
    assert schedule_input_builder.build(db, *NOV, with_carry_days=False).days == month_days(*NOV)


# --- engine -------------------------------------------------------------------


def _window(people: list[PersonInput], days: list[date], **kw) -> SolverInput:
    return SolverInput(
        year=days[0].year, month=days[0].month, people=people, days=days,
        flight_pairs={d: _usual(d) for d in days}, max_solve_seconds=10, **kw,
    )


def _rules_on(inp: SolverInput, grid: dict[tuple[int, date], AttendanceCode]):
    """The engine's rules evaluated on a fixed decision-layer grid."""
    model = cp_model.CpModel()
    x = SchedulerEngine()._build_vars(model, inp)
    registry = SlackRegistry()
    constraints.add_all(model, x, inp, registry)
    for (uid, day, code), var in x.items():
        model.add(var == int(grid[(uid, day)] is code))
    model.minimize(sum(registry.penalty_terms()))
    solver = cp_model.CpSolver()
    assert solver.solve(model) == cp_model.OPTIMAL
    return registry.violations(solver)


def test_carry_days_have_no_x_minimum_and_a_weekend_cap() -> None:
    """27–31 Dec, then Fri–Sun 1–3 Jan: four group-A people cover every
    flight of the short tail (no X there is fine); an X beyond the tail's
    Saturday and Sunday is reported, by the engine and by the re-check."""
    days = [date(2026, 12, d) for d in range(27, 32)] + carry_days(*DEC)
    people = [PersonInput(uid, Role.A) for uid in (1, 2, 3, 4)]
    inp = _window(people, days)
    out = SchedulerEngine(num_workers=1).solve(inp)
    assert out.feasible
    assert out.violations == []

    tail = carry_days(*DEC)
    grid = {(a.user_id, a.day): a.code for a in out.assignments}
    for d in tail:
        grid[(1, d)] = X  # three X on a tail with one Saturday and one Sunday
    found = [v for v in _rules_on(inp, grid) if v.rule == "monthly_off_excess"]
    assert [(v.user_id, v.key, v.params["target"], v.params["amount"]) for v in found] == [
        (1, "monthly_off_excess_carry", 2, 1)
    ]
    warned = recheck(
        grid={k: v for k, v in grid.items() if k[1] in tail},
        roles={p.user_id: p.role for p in people},
        carry_streaks={},
        days=tail,
        flight_pairs=inp.flight_pairs,
        carry_only=True,
    )
    quota = [v for v in warned if v.rule.startswith("monthly_off")]
    assert [(v.rule, v.user_id, v.key, v.params["amount"]) for v in quota] == [
        ("monthly_off_excess", 1, "monthly_off_excess_carry", 1)
    ]


def test_no_comp_day_on_the_carry_days() -> None:
    """Owed comp days are granted inside the month only."""
    days = month_days(*NOV)[-6:] + carry_days(*NOV)
    people = [PersonInput(1, Role.T, carry_comp=6)]
    out = SchedulerEngine(num_workers=1).solve(_window(people, days))
    tail = set(carry_days(*NOV))
    assert not [a for a in out.assignments if a.code is CD and a.day in tail]
    assert any(a.code is CD for a in out.assignments)


def test_fixed_cells_are_pinned_and_counted_like_the_recheck() -> None:
    """A carried A/D covers one A and one D, a carried T covers nothing, a
    carried AL is leave; an in-domain carried code is kept as it is."""
    days = month_days(2027, 2)[:7]  # Mon 1 Feb ..
    d1, d2, d3, d4 = days[1], days[2], days[3], days[4]
    stored = {1: {d1: AttendanceCode.A_D, d2: AttendanceCode.T, d3: AttendanceCode.AL,
                  d4: D}}
    fixed, leave = carried.split(stored, {1: Role.A})
    assert leave == {1: {d3: AttendanceCode.AL}}
    assert fixed == {1: {d1: AttendanceCode.A_D, d2: AttendanceCode.T, d4: D}}
    inp = SolverInput(
        year=2027, month=2, people=[PersonInput(1, Role.A)], days=days,
        flight_pairs={d1: 1, d2: 1, d4: 2}, approved_off=leave, fixed=fixed,
        max_solve_seconds=10,
    )
    out = SchedulerEngine(num_workers=1).solve(inp)
    codes = {a.day: a.code for a in out.assignments}
    assert codes[d4] is D and codes[d3] is X and codes[d1].is_working
    short = sorted((v.day, v.params["shift"]) for v in out.violations
                   if v.rule == "flight_staffing")
    # d1: A/D covers the single pair; d2: training covers nothing; d4: one D
    # of the two needed and no A.
    assert short == [(d2, "A"), (d2, "D"), (d4, "A"), (d4, "D")]


# --- the service scenario -------------------------------------------------------


@dataclass
class Scenario:
    db: Session
    ids: dict[str, int]
    nov: object
    dec_after_nov: dict[tuple[int, date], AttendanceCode]


def _cells(db: Session, year: int, month: int) -> dict[tuple[int, date], ShiftAssignment]:
    schedule = db.query(MonthlySchedule).filter_by(year=year, month=month).one()
    db.refresh(schedule)
    return {(a.user_id, a.work_date): a for a in schedule.assignments}


@pytest.fixture(scope="module")
def scenario() -> Iterator[Scenario]:
    patch = pytest.MonkeyPatch()
    patch.setattr(settings, "SOLVER_MAX_TIME_SECONDS", 30.0)
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine, autoflush=False)()
    ids = {}
    for role, n in [("A", 1), ("A", 2), ("A", 3), ("A", 4), ("F", 1), ("F", 2),
                    ("T", 1), ("T", 2), ("M", 1)]:
        user = User(username=f"{role}{n}".lower(), code=f"{role}{n}", full_name=f"{role}{n}",
                    hashed_password="x", role=Role(role), status=UserStatus.active)
        db.add(user)
        db.flush()
        ids[user.code] = user.id
    # November's flights only: 1–6 Dec take their weekday's count.
    for d in month_days(*NOV):
        db.add(FlightDay(day=d, flight_pairs=_usual(d)))
    db.commit()
    nov = schedule_service.generate(db, *NOV)
    dec_after_nov = {k: c.code for k, c in _cells(db, *DEC).items()}
    try:
        yield Scenario(db, ids, nov, dec_after_nov)
    finally:
        db.close()
        engine.dispose()
        patch.undo()


def test_acceptance_1_november_runs_to_6_december(scenario: Scenario) -> None:
    db, nov = scenario.db, scenario.nov
    assert nov.feasible and nov.violations == []
    own = nov.schedule.assignments
    assert {a.work_date for a in own} == set(month_days(*NOV))
    assert {a.work_date for a in nov.schedule.carry_assignments} == set(carry_days(*NOV))
    assert all(a.carried for a in nov.schedule.carry_assignments)

    dec = db.query(MonthlySchedule).filter_by(year=2026, month=12).one()
    assert dec.status is ScheduleStatus.draft
    assert all(a.carried for a in dec.assignments)
    assert {a.work_date for a in dec.assignments} == set(carry_days(*NOV))
    assert len(dec.assignments) == 9 * 6

    # Group F keeps its weekly swap across 30 Nov – 6 Dec: whoever's turn it
    # is works, and each rests twice that week.
    f_ids = sorted(scenario.ids[c] for c in ("F1", "F2"))
    week = [date(2026, 11, 30) + timedelta(days=n) for n in range(7)]
    cells = {**{(a.user_id, a.work_date): a.code for a in own},
             **scenario.dec_after_nov}
    duty = role_f.rotation_duty(window_days(*NOV), {d: _usual(d) for d in week}, {}, f_ids)
    for d in week:
        for uid in duty.get(d, []):
            assert cells[(uid, d)] is AD, (uid, d)
    for uid in f_ids:
        assert sum(cells[(uid, d)] is X for d in week) == 2
    # The week before swaps roles: F's off days differ week to week.
    before = [d - timedelta(days=7) for d in week]
    assert [cells[(f_ids[0], d)] for d in before] != [cells[(f_ids[0], d)] for d in week]

    # Acceptance 6: the re-check of both months agrees (nothing to report).
    assert schedule_service.violations_for(db, nov.schedule.id) == []
    assert schedule_service.violations_for(db, dec.id) == []

    # Not generated yet for the dashboard and the autorun.
    assert dashboard_service._schedule(db, *DEC).status is None
    assert schedule_autorun._schedule_exists(db, *DEC) is False


def test_acceptance_4_carried_days_show_once_the_month_is_published(
    scenario: Scenario, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = scenario.db
    a1 = scenario.ids["A1"]
    nov = db.query(MonthlySchedule).filter_by(year=2026, month=11).one()
    worked = next(d for d in carry_days(*NOV) if scenario.dec_after_nov[(a1, d)].is_working)
    monkeypatch.setattr(shift_time_service, "business_today", lambda: worked)
    monkeypatch.setattr(time_clock_service, "_today", lambda: date(2026, 12, 7))

    def tinted() -> set[date]:
        return {c["work_date"] for c in time_clock_service.board(db, *DEC)
                if c["user_id"] == a1 and c["tint"] == "missing"}

    # November a draft: December shows nothing to an employee.
    with pytest.raises(HTTPException) as err:
        schedule_service.view(db, *DEC, is_admin=False)
    assert err.value.status_code == 404
    assert shift_time_service.today_for_user(db, a1).code is None
    assert tinted() == set()

    schedule_service.publish(db, nov.id)
    try:
        view = schedule_service.view(db, *DEC, is_admin=False)
        assert {a.work_date for a in view.assignments} == set(carry_days(*NOV))
        assert view.carry_assignments == []
        assert len(schedule_service.view(db, *NOV, is_admin=False).carry_assignments) == 54
        # The check-in page's shift and the board's due days read them.
        assert shift_time_service.today_for_user(db, a1).code == (
            scenario.dec_after_nov[(a1, worked)].value
        )
        due = {d for d in carry_days(*NOV) if scenario.dec_after_nov[(a1, d)].is_working}
        assert tinted() == due
    finally:
        nov.status = ScheduleStatus.draft
        db.commit()


def test_roster_download_prints_the_carried_days(scenario: Scenario) -> None:
    admin = scenario.db.get(User, scenario.ids["M1"])
    sheet = roster_report.build(scenario.db, *NOV, admin)
    assert [d.day for d in sheet.carry_days] == carry_days(*NOV)
    ws = load_workbook(io.BytesIO(build_workbook(sheet))).active
    labels = [ws.cell(r, 1).value for r in range(3, 3 + 30 * 2 + 12)]
    assert "30" in labels and "1/12" in labels and "6/12" in labels
    assert labels.index("1/12") > labels.index("30")
    assert "7/12" not in labels


def test_acceptance_2_5_december_keeps_its_carried_days(scenario: Scenario) -> None:
    db = scenario.db
    for d in month_days(*DEC):
        db.add(FlightDay(day=d, flight_pairs=_usual(d)))
    db.commit()

    dec = schedule_service.generate(db, *DEC)  # carry-only: no force needed
    assert dec.feasible and dec.violations == [] and dec.next_month_warnings == []
    cells = _cells(db, *DEC)
    kept = {k: c.code for k, c in cells.items() if c.carried}
    assert kept == scenario.dec_after_nov
    assert {d for _, d in cells} == set(month_days(*DEC))
    jan = _cells(db, *JAN)
    assert {d for _, d in jan} == set(carry_days(*DEC)) and all(c.carried for c in jan.values())
    # Group A is not over-staffed on the carry days (2026-11-20): 1–3 Jan
    # need 2 + 3 + 3 of the 12 person-days, so the other 4 are X — otherwise
    # January, whose spare days equal its X count, comes out short.
    a_ids = [uid for code, uid in scenario.ids.items() if code[0] == "A"]
    assert sum(jan[(uid, d)].code is X for uid in a_ids for d in carry_days(*DEC)) == 4
    for code, uid in scenario.ids.items():
        if code[0] in "ATM":
            xs = sum(cells[(uid, d)].code is X for d in month_days(*DEC))
            assert xs == 8, (code, xs)  # December 2026: 8 Saturdays and Sundays
    dec_id = dec.schedule.id
    jan_id = db.query(MonthlySchedule).filter_by(year=2027, month=1).one().id
    assert schedule_service.violations_for(db, dec_id) == []
    assert schedule_service.violations_for(db, jan_id) == []

    # An edit of December's own carried cell does not block a regenerate,
    # and the regenerate keeps it.
    a2 = scenario.ids["A2"]
    first = date(2026, 12, 1)
    schedule_service.manual_override(
        db, dec_id, ManualOverrideRequest(user_id=a2, work_date=first,
                                          code=scenario.dec_after_nov[(a2, first)]))
    again = schedule_service.generate(db, *DEC)
    assert again.feasible
    cell = _cells(db, *DEC)[(a2, first)]
    assert cell.carried and cell.is_manual_override
    assert {k: c.code for k, c in _cells(db, *DEC).items() if c.carried} == kept

    # An edit of a carry-day row made from December's grid lands in
    # January's schedule and blocks a non-forced regenerate of December.
    t1 = scenario.ids["T1"]
    jan2 = date(2027, 1, 2)
    old = _cells(db, *JAN)[(t1, jan2)].code
    new = X if old is AD else AD
    result = schedule_service.manual_override(
        db, dec_id, ManualOverrideRequest(user_id=t1, work_date=jan2, code=new))
    assert result.schedule.id == dec_id
    assert any(a.work_date == jan2 and a.code is new for a in result.schedule.carry_assignments)
    assert _cells(db, *JAN)[(t1, jan2)].code is new
    with pytest.raises(HTTPException) as err:
        schedule_service.generate(db, *DEC)
    assert err.value.status_code == 409
    with pytest.raises(HTTPException) as err:
        schedule_service.manual_override(
            db, dec_id, ManualOverrideRequest(user_id=t1, work_date=date(2027, 1, 4), code=X))
    assert err.value.status_code == 422

    # Owner 2026-11-20: a month ALWAYS runs to its last Sunday. Regenerating
    # November while December is a generated draft re-plans 1–6 Dec as
    # carried cells (the admin's edit there needs force) and leaves the rest
    # of December cell for cell.
    with pytest.raises(HTTPException) as err:
        schedule_service.generate(db, *NOV, force=False)
    assert err.value.status_code == 409  # November itself is a draft; the edit on 1 Dec blocks
    before = {k: (c.code, c.carried, c.is_manual_override) for k, c in _cells(db, *DEC).items()}
    nov = schedule_service.generate(db, *NOV, force=True)
    assert nov.feasible
    assert {a.work_date for a in nov.schedule.assignments} == set(month_days(*NOV))
    assert {a.work_date for a in nov.schedule.carry_assignments} == set(carry_days(*NOV))
    after = {k: (c.code, c.carried, c.is_manual_override) for k, c in _cells(db, *DEC).items()}
    tail = set(carry_days(*NOV))
    assert {k: v for k, v in after.items() if k[1] not in tail} == {
        k: v for k, v in before.items() if k[1] not in tail
    }
    assert all(v[1] and not v[2] for k, v in after.items() if k[1] in tail)
    assert {d for _, d in after} == set(month_days(*DEC))

    # A PUBLISHED next month is the staff's roster: untouched, and the
    # month still reads through its last Sunday from it.
    schedule_service.publish(db, dec_id)
    before = {k: (c.code, c.carried, c.is_manual_override) for k, c in _cells(db, *DEC).items()}
    nov = schedule_service.generate(db, *NOV, force=True)
    assert nov.feasible
    after = {k: (c.code, c.carried, c.is_manual_override) for k, c in _cells(db, *DEC).items()}
    assert after == before
    assert {a.work_date for a in nov.schedule.carry_assignments} == tail


def test_a_month_generated_before_the_previous_one_still_gets_the_tail(db: Session) -> None:
    """The owner's case of 2026-11-20: January generated first, then
    December. December still runs to Sunday 3 January: those days become
    carried cells and the rest of January stays."""
    patch = pytest.MonkeyPatch()
    patch.setattr(settings, "SOLVER_MAX_TIME_SECONDS", 20.0)
    try:
        for code, role in [("F1", Role.F), ("F2", Role.F), ("T1", Role.T)]:
            db.add(User(username=code.lower(), code=code, full_name=code, hashed_password="x",
                        role=role, status=UserStatus.active))
        for d in month_days(*DEC) + month_days(*JAN):
            db.add(FlightDay(day=d, flight_pairs=_usual(d)))
        db.commit()
        assert schedule_service.generate(db, *JAN).feasible
        january = {k: c.code for k, c in _cells(db, *JAN).items()}
        assert not any(c.carried for c in _cells(db, *JAN).values())

        dec = schedule_service.generate(db, *DEC)

        tail = set(carry_days(*DEC))  # 1–3 January
        assert dec.feasible and dec.notices == []
        assert {a.work_date for a in dec.schedule.carry_assignments} == tail
        cells = _cells(db, *JAN)
        assert {d for _, d in cells} == set(month_days(*JAN))
        assert all(c.carried == (d in tail) for (_, d), c in cells.items())
        assert {k: c.code for k, c in cells.items() if k[1] not in tail} == {
            k: code for k, code in january.items() if k[1] not in tail
        }
    finally:
        patch.undo()
