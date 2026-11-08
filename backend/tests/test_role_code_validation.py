"""Manual writes must preserve the A/D versus AD role boundary."""

import pytest
from fastapi import HTTPException

from app.models.enums import AttendanceCode, Role
from app.services.role_code_validation import (
    requestable_codes,
    validate,
    validate_planned,
    validate_requestable,
)


def test_role_a_accepts_a_slash_d_but_rejects_ad() -> None:
    validate(Role.A, AttendanceCode.A_D)
    with pytest.raises(HTTPException) as exc:
        validate(Role.A, AttendanceCode.AD)
    assert exc.value.status_code == 422


@pytest.mark.parametrize("role", [Role.T, Role.F])
def test_t_like_roles_accept_ad_but_reject_a_slash_d(role: Role) -> None:
    validate(role, AttendanceCode.AD)
    with pytest.raises(HTTPException) as exc:
        validate(role, AttendanceCode.A_D)
    assert exc.value.status_code == 422


@pytest.mark.parametrize("role", [Role.A, Role.T, Role.M, Role.F])
def test_cd_is_valid_on_the_planned_schedule_for_every_role(role: Role) -> None:
    """Owner D1 (2026-11-06): holiday work earns CD for every role, so an admin
    may plan the owed CD for any role."""
    validate_planned(role, AttendanceCode.CD)


A, D, X, AD, O_D = (
    AttendanceCode.A, AttendanceCode.D, AttendanceCode.X,
    AttendanceCode.AD, AttendanceCode.O_D,
)


@pytest.mark.parametrize(
    ("role", "expected"),
    [
        (Role.A, {A, D, X}),
        (Role.T, {AD, X}),
        (Role.F, {AD, X}),
        (Role.M, {O_D, X}),
    ],
)
def test_requestable_codes_are_the_solver_domain_without_cd(role, expected) -> None:
    """Employees request only their regular working or off codes."""
    assert requestable_codes(role) == expected
    for code in expected:
        validate_requestable(role, code)


@pytest.mark.parametrize("role", [Role.A, Role.T, Role.M, Role.F])
@pytest.mark.parametrize(
    "code",
    [
        AttendanceCode.AL, AttendanceCode.CD, AttendanceCode.A_D,
        AttendanceCode.T, AttendanceCode.B, AttendanceCode.S,
    ],
)
def test_leave_comp_and_operational_codes_are_not_requestable(role, code) -> None:
    with pytest.raises(HTTPException) as exc:
        validate_requestable(role, code)
    assert exc.value.status_code == 422
    assert exc.value.detail == (
        "Employees may only request their regular working or off codes."
    )
