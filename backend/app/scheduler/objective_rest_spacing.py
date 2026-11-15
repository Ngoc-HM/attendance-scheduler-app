"""Prefer ordinary rest in pairs; use three-day breaks only when necessary."""

from datetime import timedelta

from app.models.enums import AttendanceCode
from app.scheduler.role_codes import OFF_CODES, codes_for


def terms(model, x, inp):
    days = sorted(inp.days)
    if not days:
        return []
    penalties = []
    for person in inp.people:
        uid = person.user_id
        leave = {
            day for day, code in inp.approved_off.get(uid, {}).items() if code is AttendanceCode.AL
        } | inp.long_leave_off.get(uid, set())
        previous = list(person.prev_codes)[-2:]
        timeline = [
            (days[0] - timedelta(days=len(previous) - i), code) for i, code in enumerate(previous)
        ] + [(day, None) for day in days]
        rest = [code for code in codes_for(person.role) if code in OFF_CODES]
        for i in range(len(timeline) - 2):
            window = timeline[i : i + 3]
            if any(code is AttendanceCode.AL or day in leave for day, code in window):
                continue
            fixed = [code for _, code in window if code is not None]
            if any(code.is_working for code in fixed):
                continue
            current = [day for day, code in window if code is None]
            triple = model.new_bool_var(f"ordinary_rest_triple_{uid}_{window[0][0]}")
            model.add(
                triple
                >= len(fixed) + sum(x[uid, day, code] for day in current for code in rest) - 2
            )
            penalties.append(triple)
    return penalties
