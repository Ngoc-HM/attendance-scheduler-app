"""Self-arrange off-day check (``_validate_weekly_off``), pure — no DB.

Full 7-day blocks keep exactly 2 X. The leftover days after the 28th have no
quota (owner 2026-11-10): a batch may move a day off within them but must
keep the number of X the person holds there now.
"""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.i18n import t
from app.models.enums import AttendanceCode
from app.scheduler.calendar_utils import month_days
from app.schemas.self_arrange import SelfArrangeChange
from app.services.self_arrange_service import _validate_weekly_off

AD, X = AttendanceCode.AD, AttendanceCode.X
YEAR, MONTH = 2026, 11  # 30 days: four full blocks + 29–30


def _own(tail_x: set[int]) -> dict:
    """X on days 6–7 of every full block; X on the given leftover days."""
    cells = {}
    for d in month_days(YEAR, MONTH):
        if d.day <= 28:
            code = X if d.day % 7 in (6, 0) else AD
        else:
            code = X if d.day in tail_x else AD
        cells[d] = SimpleNamespace(code=code)
    return cells


def _change(day: int, code: AttendanceCode) -> SelfArrangeChange:
    return SelfArrangeChange(work_date=date(YEAR, MONTH, day), code=code)


def _rejected(own, changes) -> None:
    with pytest.raises(HTTPException) as err:
        _validate_weekly_off(own, changes, YEAR, MONTH)
    assert err.value.status_code == 422
    assert err.value.detail == t("selfarrange.breaks_weekly_off")


def test_moving_a_day_off_within_the_leftover_days_is_accepted() -> None:
    own = _own({29})
    _validate_weekly_off(own, [_change(29, AD), _change(30, X)], YEAR, MONTH)


def test_adding_or_removing_a_day_off_in_the_leftover_days_is_rejected() -> None:
    _rejected(_own(set()), [_change(29, X)])          # 0 → 1 X: a free day off
    _rejected(_own({29}), [_change(29, AD)])           # 1 → 0 X: drops the rest day
    _rejected(_own({29, 30}), [_change(30, AD)])       # 2 → 1


def test_leftover_days_with_no_change_count_is_accepted() -> None:
    own = _own({29, 30})
    _validate_weekly_off(own, [_change(29, X), _change(30, X)], YEAR, MONTH)


def test_full_block_still_needs_exactly_two_off_days() -> None:
    own = _own(set())
    # Move block 1's X from the 6th to the 2nd: still 2 → accepted.
    _validate_weekly_off(own, [_change(6, AD), _change(2, X)], YEAR, MONTH)
    _rejected(own, [_change(2, X)])   # 3 X in block 1
    _rejected(own, [_change(6, AD)])  # 1 X in block 1


def test_message_names_both_rules_in_both_languages() -> None:
    assert "7-day block" in t("selfarrange.breaks_weekly_off", "en")
    assert "leftover days" in t("selfarrange.breaks_weekly_off", "en")
    assert "block 7 ngày" in t("selfarrange.breaks_weekly_off", "vi")
    assert "các ngày lẻ cuối tháng" in t("selfarrange.breaks_weekly_off", "vi")
