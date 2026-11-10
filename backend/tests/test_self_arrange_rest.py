"""Self-arrange rest check (``check_rest_batch``), pure — no DB.

Owner 2026-11-10: the 7-day blocks are gone. A batch must keep the month's
number of X and must not create a new rolling-7-day or 5-in-a-row breach
for the requester, history included.
"""

from __future__ import annotations

from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.i18n import t
from app.models.enums import AttendanceCode, Role
from app.scheduler.calendar_utils import month_days
from app.schemas.self_arrange import SelfArrangeChange
from app.services.self_arrange_service import check_rest_batch

AD, X = AttendanceCode.AD, AttendanceCode.X
YEAR, MONTH = 2026, 11  # 1 Nov 2026 is a Sunday; Fri+Sat = 6/7, 13/14, …
DAYS = month_days(YEAR, MONTH)
ME = SimpleNamespace(id=7, role=Role.T)


def _own(off_days: set[int]) -> dict:
    return {d: SimpleNamespace(code=X if d.day in off_days else AD) for d in DAYS}


FRI_SAT = {6, 7, 13, 14, 20, 21, 27, 28}


def _change(day: int, code: AttendanceCode) -> SelfArrangeChange:
    return SelfArrangeChange(work_date=date(YEAR, MONTH, day), code=code)


def _check(own, changes, *, carry=0, previous=None) -> None:
    check_rest_batch(
        ME, own, changes, DAYS, carry_streak=carry, previous_working=previous or {}
    )


def _rejected(own, changes, **kw) -> None:
    with pytest.raises(HTTPException) as err:
        _check(own, changes, **kw)
    assert err.value.status_code == 422
    assert err.value.detail == t("selfarrange.breaks_weekly_off")


def test_moving_a_pair_is_accepted() -> None:
    # Fri+Sat 27/28 → Thu+Fri 26/27: same count, no 6-day run.
    _check(_own(FRI_SAT), [_change(28, AD), _change(26, X)])


def test_adding_or_removing_a_day_off_is_rejected() -> None:
    _rejected(_own(FRI_SAT), [_change(29, X)])   # 8 → 9 X: a free day off
    _rejected(_own(FRI_SAT), [_change(6, AD)])   # 8 → 7 X


def test_a_move_that_makes_six_working_days_in_a_row_is_rejected() -> None:
    # Fri+Sat 13/14 → Sun+Mon 15/16: works 8–14, seven days in a row.
    _rejected(
        _own(FRI_SAT),
        [_change(13, AD), _change(14, AD), _change(15, X), _change(16, X)],
    )


def test_history_counts_at_the_start_of_the_month() -> None:
    # Off on 1 Nov; moving that X to 2 Nov is fine without history …
    own = _own(FRI_SAT | {1})
    batch = [_change(1, AD), _change(2, X)]
    _check(own, batch)
    # … but after 5 worked days ending 31 Oct, working 1 Nov makes six.
    history = {date(YEAR, MONTH, 1) - timedelta(days=n): n <= 5 for n in range(1, 7)}
    _rejected(own, batch, carry=5, previous=history)


def test_an_existing_breach_does_not_block_an_unrelated_move() -> None:
    # Already 6 working days 8–13 (only 14 off that week); moving 27/28 is ok.
    own = _own(FRI_SAT - {13} | {12})
    own[date(YEAR, MONTH, 12)] = SimpleNamespace(code=AD)
    own[date(YEAR, MONTH, 29)] = SimpleNamespace(code=X)
    _check(own, [_change(28, AD), _change(26, X)])


def test_message_in_both_languages() -> None:
    assert "same number of days off" in t("selfarrange.breaks_weekly_off", "en")
    assert "7 consecutive days" in t("selfarrange.breaks_weekly_off", "en")
    assert t("selfarrange.breaks_weekly_off", "vi") == (
        "Sắp xếp phải giữ nguyên số ngày nghỉ trong tháng và không làm quá "
        "5 ngày trong 7 ngày liên tiếp bất kỳ."
    )
