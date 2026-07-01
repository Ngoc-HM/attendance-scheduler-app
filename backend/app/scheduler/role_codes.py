"""Per-role attendance code domains (owner decision 2026-06-26).

Each person's assignable code set depends on their role:

    Role.A (fixed group)  → {A, D, A/D, X, CD}   full flight rules
    Role.T (flexible)     → {AD, X}               full day, no shift split
    Role.M (admin)        → {O/D, X}              office duty

OFF_CODES are the non-working rest codes; a day is "working" if its assigned
code is not in OFF_CODES (and not a pinned AL/S leave, which is also X).

The CD code (comp-day off) appears only in the role-A domain; the constraint
``constraints_comp_days`` enforces it role-A only.  AD (two shifts, no comp)
appears only in the role-T domain.  O/D (office) appears only in role-M.
"""

from __future__ import annotations

from app.models.enums import AttendanceCode, Role

# Maps each role to its EXCLUSIVE assignable code domain.
# These are the ONLY variables the solver creates for that person (§5.1).
ROLE_CODES: dict[Role, tuple[AttendanceCode, ...]] = {
    Role.A: (
        AttendanceCode.A,
        AttendanceCode.D,
        AttendanceCode.A_D,
        AttendanceCode.X,
        AttendanceCode.CD,
    ),
    Role.T: (
        AttendanceCode.AD,
        AttendanceCode.X,
    ),
    Role.M: (
        AttendanceCode.O_D,
        AttendanceCode.X,
    ),
}

# Rest codes (non-working): X and CD.  A day whose code is in OFF_CODES does
# NOT count toward the working-day streak or flight staffing.
OFF_CODES: frozenset[AttendanceCode] = frozenset(
    {AttendanceCode.X, AttendanceCode.CD}
)

# Role-A working codes (for clarity in constraints_consecutive / off_chain).
ROLE_A_WORKING: frozenset[AttendanceCode] = frozenset(
    {AttendanceCode.A, AttendanceCode.D, AttendanceCode.A_D}
)


def codes_for(role: Role) -> tuple[AttendanceCode, ...]:
    """Return the assignable code domain for the given role."""
    return ROLE_CODES[role]


def working_codes_for(role: Role) -> tuple[AttendanceCode, ...]:
    """Return the WORKING (non-rest) codes for a role — used for streak logic."""
    return tuple(c for c in ROLE_CODES[role] if c not in OFF_CODES)
