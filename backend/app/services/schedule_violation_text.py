"""Turn rule violations into client text in the request's language.

The solver (``app.scheduler``) and the re-check
(``schedule_violation_checker``) both hand over a ``Violation``: the rule, a
message ``key`` (empty → the rule name) and ``params``. This module is the one
place that renders them, through the catalog key
``schedule.violation.<key>``, so a rule reads the same after Generate and in
the re-check. The engine stays free of i18n and PII (only ``user_id``); the
person is named here, by roster code and name.

Formatting: dates are ``YYYY-MM-DD`` (the other catalog messages, e.g. the
flight-plan and leave warnings, use the same); ``{person}`` is
``schedule.violation.person``; ``{shift}`` "A"/"D" is the app's ARR/DEP.
An unknown rule, or params that do not fill its template, give the generic
``schedule.violation.unknown`` — never the engine's English line.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date

from app.core.i18n import t
from app.models.user import User
from app.scheduler.domain import Violation
from app.schemas.schedule import ConstraintViolation

KEY_PREFIX = "schedule.violation."


def format_day(day: date) -> str:
    return day.isoformat()


def person_label(
    user_id: int, people: Mapping[int, User], lang: str | None = None
) -> str:
    """Roster code and full name; a translated "user #id" once the row is gone."""
    user = people.get(user_id)
    if user is None:
        return t(f"{KEY_PREFIX}person_unknown", lang).format(id=user_id)
    name = (user.full_name or "").strip()
    if not name or name == user.code:
        return user.code
    return t(f"{KEY_PREFIX}person", lang).format(code=user.code, name=name)


def _value(name: str, value: object, lang: str | None) -> object:
    if isinstance(value, date):
        return format_day(value)
    if name == "shift":
        return t(f"{KEY_PREFIX}shift_{value}", lang)
    return value


def render(
    v: Violation, people: Mapping[int, User], lang: str | None = None
) -> str:
    """The violation as one sentence in ``lang`` (default: the request's)."""
    values: dict[str, object] = {
        name: _value(name, value, lang) for name, value in v.params.items()
    }
    if v.day is not None:
        values.setdefault("day", format_day(v.day))
    if v.user_id is not None:
        values["person"] = person_label(v.user_id, people, lang)

    key = f"{KEY_PREFIX}{v.key or v.rule}"
    template = t(key, lang)
    if template != key:
        try:
            return template.format(**values)
        except (KeyError, IndexError, ValueError):
            pass  # params do not fit the template: generic text below
    fallback = t(f"{KEY_PREFIX}unknown", lang)
    return f"{format_day(v.day)}: {fallback}" if v.day is not None else fallback


def render_all(
    violations: Iterable[Violation],
    people: Mapping[int, User],
    lang: str | None = None,
) -> list[ConstraintViolation]:
    """API shape (``day``, ``user_id``, ``rule``, ``message``) with the text
    rendered in ``lang``."""
    return [
        ConstraintViolation(
            day=v.day, user_id=v.user_id, rule=v.rule, message=render(v, people, lang)
        )
        for v in violations
    ]
