"""Shift time frames (owner 2026-11-18, decision #71): store and display only.

The admin sets the start and end of shifts A and D. The frame of a double
shift (``A/D`` earns a comp day, ``AD`` does not; both work both shifts) is
derived as the earliest start to the latest end and never stored. Nothing
here judges a punch as late or early.
"""

from __future__ import annotations

import re
from datetime import time

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.business_time import business_today
from app.core.i18n import t
from app.models.attendance import AttendanceRecord
from app.models.enums import AttendanceCode, ScheduleStatus
from app.models.schedule import MonthlySchedule, ShiftAssignment
from app.models.shift_time import ShiftTime
from app.schemas.shift_time import ShiftTimeRead, ShiftTimesUpdate, ShiftToday

# The owner's defaults; also seeded by migration 0014. A database built by
# create_all (dev, tests) has no rows and reads these.
DEFAULTS: dict[str, tuple[time, time]] = {
    "A": (time(5, 30), time(13, 5)),
    "D": (time(6, 20), time(13, 55)),
}
DOUBLE = AttendanceCode.A_D.value
_HHMM = re.compile(r"([01]\d|2[0-3]):([0-5]\d)")


def _hm(value: time) -> str:
    return value.strftime("%H:%M")


def _parse(value: str) -> time:
    match = _HHMM.fullmatch(value)
    if match is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=t("shift_time.invalid_time"))
    return time(int(match.group(1)), int(match.group(2)))


def frames(db: Session) -> dict[str, tuple[time, time]]:
    """Stored frames of A and D, the default for a missing row."""
    stored = {r.code: (r.start_time, r.end_time) for r in db.query(ShiftTime).all()}
    return {code: stored.get(code, default) for code, default in DEFAULTS.items()}


def double_frame(single: dict[str, tuple[time, time]]) -> tuple[time, time]:
    """A/D works from the earliest start to the latest end."""
    return (min(s for s, _ in single.values()), max(e for _, e in single.values()))


def frame_for_code(
    single: dict[str, tuple[time, time]], code: AttendanceCode | None
) -> tuple[time, time] | None:
    """The frame shown for a day code: A, D, or the derived one for A/D and
    AD; None for every other code."""
    if code in (AttendanceCode.A, AttendanceCode.D):
        return single[code.value]
    if code in (AttendanceCode.A_D, AttendanceCode.AD):
        return double_frame(single)
    return None


def list_frames(db: Session) -> list[ShiftTimeRead]:
    single = frames(db)
    start, end = double_frame(single)
    return [
        *(ShiftTimeRead(code=c, start=_hm(s), end=_hm(e)) for c, (s, e) in single.items()),
        ShiftTimeRead(code=DOUBLE, start=_hm(start), end=_hm(end), derived=True),
    ]


def update(db: Session, payload: ShiftTimesUpdate) -> list[ShiftTimeRead]:
    """Admin sets A and/or D; each start must come before its end."""
    parsed = {f.code: (_parse(f.start), _parse(f.end)) for f in payload.frames}
    for start, end in parsed.values():
        if start >= end:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, detail=t("shift_time.start_not_before_end")
            )
    rows = {r.code: r for r in db.query(ShiftTime).all()}
    for code, (start, end) in parsed.items():
        row = rows.get(code)
        if row is None:
            db.add(ShiftTime(code=code, start_time=start, end_time=end))
        else:
            row.start_time, row.end_time = start, end
    db.commit()
    return list_frames(db)


def _today_code(db: Session, user_id: int) -> AttendanceCode | None:
    """Today's code: the recorded one, else the published roster's cell."""
    day = business_today()
    actual = (
        db.query(AttendanceRecord.code)
        .filter(AttendanceRecord.user_id == user_id, AttendanceRecord.work_date == day)
        .scalar()
    )
    if actual is not None:
        return actual
    return (
        db.query(ShiftAssignment.code)
        .join(MonthlySchedule, ShiftAssignment.schedule_id == MonthlySchedule.id)
        .filter(
            MonthlySchedule.status == ScheduleStatus.published,
            ShiftAssignment.user_id == user_id,
            ShiftAssignment.work_date == day,
        )
        .scalar()
    )


def today_for_user(db: Session, user_id: int) -> ShiftToday:
    code = _today_code(db, user_id)
    frame = frame_for_code(frames(db), code)
    if code is None or frame is None:
        return ShiftToday(code=code.value if code else None)
    return ShiftToday(code=code.value, start=_hm(frame[0]), end=_hm(frame[1]))
