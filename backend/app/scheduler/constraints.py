"""Hard constraints for the CP-SAT model (spec §5.3).

``add_all`` wires every hard rule onto the model. ``x`` maps
``(user_id, day, AttendanceCode) -> BoolVar``. The "exactly one status" and
"respect approved off" rules are implemented as worked examples; the remaining
rules are scaffolded with precise TODOs tied to the spec so they can be filled
in without re-deriving the model shape.
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode, Role
from app.scheduler.domain import SolverInput

# Codes that mean "at work" within the engine's decision vocabulary.
WORK_CODES = (AttendanceCode.A, AttendanceCode.D, AttendanceCode.A_D)


def add_all(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    assignable_codes: tuple[AttendanceCode, ...],
) -> None:
    one_status_per_day(model, x, inp, assignable_codes)
    respect_approved_off(model, x, inp)
    two_days_off_per_week(model, x, inp)
    max_consecutive_working(model, x, inp)
    fixed_group_staffing(model, x, inp)


def one_status_per_day(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    assignable_codes: tuple[AttendanceCode, ...],
) -> None:
    """§5.3 #1 — exactly one status per (person, day). [implemented]"""
    for p in inp.people:
        for d in inp.days:
            model.AddExactlyOne(x[(p.user_id, d, c)] for c in assignable_codes)


def respect_approved_off(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
) -> None:
    """§5.3 #5 — approved leave / holidays are fixed OFF cells. [implemented]

    Modeled as OFF (``X``) in the decision layer; the concrete code (AL/CD/X)
    is restored from ``approved_off`` when persisting.
    """
    for uid, days in inp.approved_off.items():
        for d in days:
            if (uid, d, AttendanceCode.X) in x:
                model.Add(x[(uid, d, AttendanceCode.X)] == 1)


def two_days_off_per_week(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
) -> None:
    """§5.3 #2 — exactly 2 OFF days (X) per person per week.

    TODO: for each person and each ``inp.weeks`` group, constrain
    ``sum(X over the week's days) == 2``. Note: Sat/Sun are NOT off by default
    (spec §6); the 2 days may land on any weekday. Edge weeks at month
    boundaries may need a partial target — decide with the customer.
    """
    raise_not_implemented = False  # placeholder; see TODO above
    if raise_not_implemented:  # pragma: no cover
        raise NotImplementedError


def max_consecutive_working(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
) -> None:
    """§5.3 #3 + §5.5 — no more than 5 consecutive working days.

    TODO: for every window of 6 consecutive days, require at least one OFF
    (``sum(work over 6 days) <= 5``). For the first days of the month, fold in
    ``PersonInput.carry_streak`` so a run continuing from last month is capped
    (e.g. carry_streak=4 ⇒ at most 1 more working day before a required OFF).
    """
    raise_not_implemented = False  # placeholder; see TODO above
    if raise_not_implemented:  # pragma: no cover
        raise NotImplementedError


def fixed_group_staffing(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
) -> None:
    """§5.3 #4 — A1–A4 daily staffing driven by ``flight_pairs[d]``.

    Required headcount among the fixed group (roles A1–A4):
        flight_pairs == 2 → 1 person on A and 2 on D
        flight_pairs == 1 → 1 person on A and 1 on D
        flight_pairs == 0 → no flight-shift staffing required

    §5.3 #6 fallback: when short-staffed, one person may take A/D (covering
    both shifts), earning +1 working day and 1 comp day (CD) next month.

    TODO: sum the A and D BoolVars over fixed-role people per day and set the
    equality/inequality targets above; allow A/D to satisfy one A + one D.
    """
    fixed = [p for p in inp.people if p.role.is_fixed]
    _ = fixed  # used once implemented
    raise_not_implemented = False  # placeholder; see TODO above
    if raise_not_implemented:  # pragma: no cover
        raise NotImplementedError
