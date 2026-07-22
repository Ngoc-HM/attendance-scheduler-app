"""Role-aware validation for manual schedule and attendance writes."""

from __future__ import annotations

from fastapi import HTTPException, status

from app.models.enums import AttendanceCode, Role
from app.scheduler.role_codes import ROLE_CODES

# Operational codes can be recorded manually for any role. Flight/office/double
# shift codes remain exclusive to their scheduler role domains.
COMMON_OPERATIONAL_CODES = {
    AttendanceCode.X,
    AttendanceCode.T,
    AttendanceCode.B,
    AttendanceCode.S,
    AttendanceCode.AL,
}


def allowed_codes(role: Role) -> set[AttendanceCode]:
    allowed = set(ROLE_CODES[role]) | COMMON_OPERATIONAL_CODES
    # A/D is valid for role A only as an emergency/manual change after the
    # automatic roster has already been generated.
    if role is Role.A:
        allowed.add(AttendanceCode.A_D)
    return allowed


def validate(role: Role, code: AttendanceCode) -> None:
    if code not in allowed_codes(role):
        allowed = ", ".join(sorted(item.value for item in allowed_codes(role)))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"Code {code.value} is not valid for role {role.value}; "
                f"allowed: {allowed}"
            ),
        )
