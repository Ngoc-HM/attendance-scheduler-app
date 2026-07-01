"""Hard constraints + soft-rule delegation for the CP-SAT model (spec §5.3).

``add_all`` wires every §5.3 rule onto the model. ``x`` maps
``(user_id, day, AttendanceCode) -> BoolVar`` — keyed only for the codes that
belong to each person's role domain (see ``role_codes.codes_for``).

Truly HARD (can never break, decision #2):
    #1 exactly one status per (person, day)   — here (per-role domain)
    #5 approved leave/holidays pinned OFF     — here

SOFT with penalized slack (violations reported via ``SlackRegistry``):
    #2 two X per 7-day block                  — ``constraints_off_days``
    #3 max 5 consecutive working (+ §5.5)     — ``constraints_consecutive``
    #4 fixed-group (role A) staffing per fp   — ``constraints_staffing``
"""

from __future__ import annotations

from datetime import date

from ortools.sat.python import cp_model

from app.models.enums import AttendanceCode
from app.scheduler import (
    constraints_comp_days,
    constraints_consecutive,
    constraints_off_chain,
    constraints_off_days,
    constraints_staffing,
)
from app.scheduler.domain import SolverInput
from app.scheduler.role_codes import codes_for
from app.scheduler.slack_registry import SlackRegistry


def add_all(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
    registry: SlackRegistry,
) -> None:
    one_status_per_day(model, x, inp)
    respect_approved_off(model, x, inp)
    constraints_off_days.add(model, x, inp, registry)
    constraints_consecutive.add(model, x, inp, registry)
    constraints_off_chain.add(model, x, inp, registry)
    constraints_staffing.add(model, x, inp, registry)
    constraints_comp_days.add(model, x, inp, registry)


def one_status_per_day(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
) -> None:
    """§5.3 #1 — exactly one status per (person, day). HARD.

    Uses each person's role-specific code domain so only valid vars are summed.
    """
    for p in inp.people:
        person_codes = codes_for(p.role)
        for d in inp.days:
            model.AddExactlyOne(x[(p.user_id, d, c)] for c in person_codes)


def respect_approved_off(
    model: cp_model.CpModel,
    x: dict[tuple[int, date, AttendanceCode], cp_model.IntVar],
    inp: SolverInput,
) -> None:
    """§5.3 #5 — approved leave cells are fixed OFF. HARD.

    Modeled as OFF (``X``) in the decision layer; the concrete code (AL/CD)
    is restored from ``approved_off`` when persisting (phase 05). Holidays are
    NOT pinned (decision #5 — they are working days). Guards with ``in x``
    because all roles have an X var, but defensive check is harmless.
    """
    for uid, day_codes in inp.approved_off.items():
        for d in day_codes:
            if (uid, d, AttendanceCode.X) in x:
                model.Add(x[(uid, d, AttendanceCode.X)] == 1)
