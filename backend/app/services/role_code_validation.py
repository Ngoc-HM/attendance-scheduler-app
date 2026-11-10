"""Role-aware validation for manual schedule and attendance writes.

Two grids, two rule sets (§9.1):

* **Planned schedule** (``ShiftAssignment`` — admin manual override):
  the role's solver domain plus the operational codes
  X / T / B / AL, and A/D for role A only. Sickness ``S`` is NEVER allowed
  here — the planned roster is visible to every active user, and sickness is
  special-category health data.
* **Actual attendance** (``AttendanceRecord`` — admin-only grid): the same
  set plus ``S``.

What an EMPLOYEE may ask for through a shift-change request is narrower
still: the role's regular working or off codes (solver domain minus CD).
Leave (AL) and comp days (CD) have their own flows, and A/D, T, B are
admin-assigned operational codes.
"""

from __future__ import annotations

from fastapi import HTTPException, status

from app.core.i18n import t
from app.models.enums import AttendanceCode, Role
from app.scheduler.role_codes import ROLE_CODES

# Operational codes any role may carry on the PLANNED grid.
PLANNED_OPERATIONAL_CODES = {
    AttendanceCode.X,
    AttendanceCode.T,
    AttendanceCode.B,
    AttendanceCode.AL,
}

# Actual attendance additionally records sickness (admin-only grid, §9.1).
ACTUAL_OPERATIONAL_CODES = PLANNED_OPERATIONAL_CODES | {AttendanceCode.S}

# Backward-compatible name used by older call sites / tests.
COMMON_OPERATIONAL_CODES = ACTUAL_OPERATIONAL_CODES


def _base(role: Role) -> set[AttendanceCode]:
    allowed = set(ROLE_CODES[role])
    # A/D is valid for role A only as an emergency/manual change after the
    # automatic roster has already been generated.
    if role is Role.A:
        allowed.add(AttendanceCode.A_D)
    return allowed


def allowed_planned_codes(role: Role) -> set[AttendanceCode]:
    """Codes an admin may write into the PLANNED schedule for this role."""
    return _base(role) | PLANNED_OPERATIONAL_CODES


def allowed_codes(role: Role) -> set[AttendanceCode]:
    """Codes an admin may record as ACTUAL attendance for this role."""
    return _base(role) | ACTUAL_OPERATIONAL_CODES


def _reject(role: Role, code: AttendanceCode, allowed: set[AttendanceCode]) -> None:
    listed = ", ".join(sorted(item.value for item in allowed))
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=t("code.not_allowed_for_role").format(
            code=code.value, role=role.value, allowed=listed
        ),
    )


def validate(role: Role, code: AttendanceCode) -> None:
    """Actual-attendance validation (admin grid; S allowed)."""
    allowed = allowed_codes(role)
    if code not in allowed:
        _reject(role, code, allowed)


def validate_planned(role: Role, code: AttendanceCode) -> None:
    """Planned-schedule validation — S is rejected for every role (§9.1)."""
    if code is AttendanceCode.S:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=t("schedule.sick_not_planned"),
        )
    allowed = allowed_planned_codes(role)
    if code not in allowed:
        _reject(role, code, allowed)


def requestable_codes(role: Role) -> set[AttendanceCode]:
    """Codes an employee may request for their own cell (shift change / swap).

    The role's solver domain minus CD: A → {A, D, X}; T, F → {AD, X};
    M → {O/D, X}.
    """
    return set(ROLE_CODES[role]) - {AttendanceCode.CD}


def validate_requestable(role: Role, code: AttendanceCode) -> None:
    """Employee-request validation — 422 ``swap.code_not_requestable``."""
    if code not in requestable_codes(role):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=t("swap.code_not_requestable"),
        )
