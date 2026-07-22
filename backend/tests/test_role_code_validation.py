"""Manual writes must preserve the A/D versus AD role boundary."""

import pytest
from fastapi import HTTPException

from app.models.enums import AttendanceCode, Role
from app.services.role_code_validation import validate


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
