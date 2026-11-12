"""Per-role attendance code domains (owner decision 2026-06-26).

Each person's assignable code set depends on their role:

    Role.A (fixed group)  → {A, D, X, CD}        full flight rules
    Role.T (flexible)     → {AD, X, CD}           full day, no shift split
    Role.M (admin)        → {O/D, X, CD}          office duty
    Role.F (split from T) → {AD, X, CD}           T-like: the weekly rest and the
                                              max-5-consecutive rules apply to F
                                              (owner 2026-07-22)

OFF_CODES are the non-working rest codes; a day is "working" if its assigned
code is not in OFF_CODES (and not a pinned AL/S leave, which is also X).

The automatic solver NEVER creates A/D: that code is reserved for emergency
cover after the roster exists, such as a sudden sickness. CD is in every
role's domain because working a public holiday earns a comp day for every
role (owner decision D1, 2026-11-06); A/D additionally earns one for role A.
The solver only grants CD against carried comp debt (constraints_comp_days).
AD appears in T/F and O/D appears in role M.
"""

from __future__ import annotations

from collections.abc import Iterable

from app.models.enums import AttendanceCode, Role
from app.scheduler.domain import PersonInput

# Maps each role to its EXCLUSIVE assignable code domain.
# These are the ONLY variables the solver creates for that person (§5.1).
ROLE_CODES: dict[Role, tuple[AttendanceCode, ...]] = {
    Role.A: (
        AttendanceCode.A,
        AttendanceCode.D,
        AttendanceCode.X,
        AttendanceCode.CD,
    ),
    Role.T: (
        AttendanceCode.AD,
        AttendanceCode.X,
        AttendanceCode.CD,
    ),
    Role.M: (
        AttendanceCode.O_D,
        AttendanceCode.X,
        AttendanceCode.CD,
    ),
    Role.F: (
        AttendanceCode.AD,
        AttendanceCode.X,
        AttendanceCode.CD,
    ),
}

# Rest codes (non-working): X and CD.  A day whose code is in OFF_CODES does
# NOT count toward the working-day streak or flight staffing.
OFF_CODES: frozenset[AttendanceCode] = frozenset(
    {AttendanceCode.X, AttendanceCode.CD}
)

# Role-A working codes (for clarity in constraints_consecutive / off_chain).
ROLE_A_WORKING: frozenset[AttendanceCode] = frozenset(
    {AttendanceCode.A, AttendanceCode.D}
)


def codes_for(role: Role) -> tuple[AttendanceCode, ...]:
    """Return the assignable code domain for the given role."""
    return ROLE_CODES[role]


def working_codes_for(role: Role) -> tuple[AttendanceCode, ...]:
    """Return the WORKING (non-rest) codes for a role — used for streak logic."""
    return tuple(c for c in ROLE_CODES[role] if c not in OFF_CODES)


def role_groups(people: Iterable[PersonInput]) -> list[list[PersonInput]]:
    """People grouped by role, groups of 2+ only (owner 2026-11-10).

    A role group shares duties, so cover and fair turns are judged inside
    it; a person alone in a role has no one to share with.
    """
    by_role: dict[Role, list[PersonInput]] = {}
    for p in people:
        by_role.setdefault(p.role, []).append(p)
    return [group for group in by_role.values() if len(group) >= 2]
