"""Rule violations reach the client in the request's language (en / vi).

The solver and the re-check hand over a rule, a message key and parameters;
``schedule_violation_text`` renders them through the i18n catalog and names a
person by roster code and name — never ``User <id>``.
"""

from __future__ import annotations

import dataclasses
import re
import string
from datetime import date

from fastapi.testclient import TestClient
from ortools.sat.python import cp_model

from app.core.i18n import MESSAGES, t
from app.models.enums import AttendanceCode, Role
from app.models.user import User
from app.scheduler import constraints
from app.scheduler.calendar_utils import month_days
from app.scheduler.domain import PersonInput, SolverInput, Violation
from app.scheduler.engine import SchedulerEngine
from app.scheduler.role_codes import codes_for
from app.scheduler.slack_registry import SlackRegistry
from app.services import schedule_input_builder
from app.services.schedule_violation_checker import recheck
from app.services.schedule_violation_text import render, render_all

V = "/api/v1"
A, D, X, CD, AD = (
    AttendanceCode.A, AttendanceCode.D, AttendanceCode.X, AttendanceCode.CD,
    AttendanceCode.AD,
)
LEFTOVER = re.compile(r"\{[a-z_]+\}")
RAW_ID = re.compile(r"\bUser \d+\b")


def _people() -> dict[int, User]:
    return {
        uid: User(id=uid, code=code, full_name=name)
        for uid, code, name in (
            (1, "A1", "Nguyễn Văn An"),
            (2, "A2", "Trần Thị Bình"),
            (3, "T1", "Lê Văn Cường"),
            (4, "M1", "Phạm Thị Dung"),
        )
    }


def _placeholders(text: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


# --- every rule the solver can emit -----------------------------------------


class _AllSlackPositive:
    """Stands in for a solved CpSolver: every slack var is 1."""

    def value(self, _var) -> int:
        return 1


def _solver_violations(inp: SolverInput) -> list[Violation]:
    model = cp_model.CpModel()
    x = {
        (p.user_id, d, c): model.new_bool_var(f"x_{p.user_id}_{d}_{c.name}")
        for p in inp.people
        for d in inp.days
        for c in codes_for(p.role)
    }
    registry = SlackRegistry()
    constraints.add_all(model, x, inp, registry)
    return registry.violations(_AllSlackPositive())  # type: ignore[arg-type]


def _full_month_input(people: list[PersonInput]) -> SolverInput:
    days = month_days(2026, 11)
    return SolverInput(
        year=2026,
        month=11,
        people=people,
        days=days,
        flight_pairs={d: 2 for d in days},
    )


def _all_solver_violations() -> list[Violation]:
    with_role_a = _full_month_input(
        [
            PersonInput(1, Role.A, carry_comp=2, carry_streak=3),
            PersonInput(3, Role.T),
            PersonInput(4, Role.M),
        ]
    )
    without_role_a = _full_month_input([PersonInput(3, Role.T)])
    infeasible = SchedulerEngine._no_schedule(cp_model.INFEASIBLE).violations
    return (
        _solver_violations(with_role_a)
        + _solver_violations(without_role_a)
        + infeasible
    )


SOLVER_TEXTS = {
    ("flight_staffing", "flight_staffing"),
    ("flight_staffing", "flight_staffing_no_role_a"),
    ("rolling_seven_min_two_rest", "rolling_seven_min_two_rest"),
    ("max_consecutive_working", "max_consecutive_working"),
    ("max_consecutive_working_carry", "max_consecutive_working_carry"),
    ("max_consecutive_off", "max_consecutive_off"),
    ("role_a_minimum_a_days", "role_a_minimum_a_days"),
    ("comp_day_shortfall", "comp_day_shortfall"),
    ("comp_day_excess", "comp_day_excess"),
    ("infeasible", "infeasible"),
}


# --- every rule the checker can emit ----------------------------------------


def _all_checker_violations() -> list[Violation]:
    days = month_days(2026, 11)
    grid: dict[tuple[int, date], AttendanceCode] = {}
    for d in days:
        # 1 (role A): works D every day → consecutive, rolling rest, no pure
        #   A, owed comp not granted, staffing short of ARR.
        grid[(1, d)] = D
        # 3 (role T): off every day → off chain, CD excess.
        grid[(3, d)] = X
    grid[(3, days[-1])] = CD
    with_role_a = recheck(
        grid=grid,
        roles={1: Role.A, 3: Role.T},
        carry_streaks={1: 3},
        days=days,
        flight_pairs={d: 2 for d in days},
        carry_comps={1: 2},
    )
    without_role_a = recheck(
        grid={(3, d): AD for d in days},
        roles={3: Role.T},
        carry_streaks={},
        days=days,
        flight_pairs={days[0]: 1},
    )
    return with_role_a + without_role_a


CHECKER_TEXTS = {
    ("flight_staffing", "flight_staffing"),
    ("flight_staffing", "flight_staffing_no_role_a"),
    ("rolling_seven_min_two_rest", "rolling_seven_min_two_rest"),
    ("max_consecutive_working", "max_consecutive_working"),
    ("max_consecutive_off", "max_consecutive_off"),
    ("role_a_minimum_a_days", "role_a_minimum_a_days"),
    ("comp_day_shortfall", "comp_day_shortfall"),
    ("comp_day_excess", "comp_day_excess"),
}

DISABLED_DUTY = Violation(
    rule="disabled_user_duty",
    message="",
    day=date(2026, 11, 13),
    user_id=2,
    params={"code": "A/D"},
)


def _assert_rendered_in_both(violations: list[Violation]) -> None:
    people = _people()
    for v in violations:
        en = render(v, people, "en")
        vi = render(v, people, "vi")
        for text in (en, vi):
            assert text, v
            assert not LEFTOVER.search(text), (v, text)
            assert not RAW_ID.search(text), (v, text)
            assert "shortfall:" not in text, (v, text)
        assert en != vi, (v, en)
        if v.user_id is not None:
            person = people[v.user_id]
            assert person.code in en and person.full_name in vi, (v, en, vi)
        dates = [p for p in v.params.values() if isinstance(p, date)]
        if v.rule in ("flight_staffing", "disabled_user_duty"):
            dates.append(v.day)
        for day in dates:
            assert day.isoformat() in en and day.isoformat() in vi, (v, en, vi)


def test_every_solver_rule_renders_in_en_and_vi() -> None:
    violations = _all_solver_violations()
    assert {(v.rule, v.key or v.rule) for v in violations} == SOLVER_TEXTS
    _assert_rendered_in_both(violations)


def test_every_checker_rule_renders_in_en_and_vi() -> None:
    violations = _all_checker_violations()
    assert {(v.rule, v.key or v.rule) for v in violations} == CHECKER_TEXTS
    _assert_rendered_in_both(violations)


def test_disabled_user_duty_names_the_person() -> None:
    _assert_rendered_in_both([DISABLED_DUTY])
    assert render(DISABLED_DUTY, _people(), "vi").startswith("2026-11-13: ")
    assert "A/D" in render(DISABLED_DUTY, _people(), "vi")


def test_every_message_key_has_a_catalog_entry() -> None:
    keys = {f"schedule.violation.{key}" for _, key in SOLVER_TEXTS | CHECKER_TEXTS}
    keys |= {
        "schedule.violation.disabled_user_duty",
        "schedule.violation.unknown",
        "schedule.violation.person",
        "schedule.violation.person_unknown",
        "schedule.violation.shift_A",
        "schedule.violation.shift_D",
    }
    for lang in ("en", "vi"):
        missing = keys - MESSAGES[lang].keys()
        assert not missing, (lang, missing)


def test_solver_and_checker_read_the_same_for_the_same_rule() -> None:
    """Same rule, same parameters → the same sentence after Generate and in
    the re-check (here: D shift short by 1 on a 2-pair day)."""
    people = _people()
    day = date(2026, 11, 13)
    inp = dataclasses.replace(
        _full_month_input([PersonInput(1, Role.A)]),
        flight_pairs={day: 2},
    )
    engine = next(
        v for v in _solver_violations(inp)
        if v.rule == "flight_staffing" and v.params.get("shift") == "D"
    )
    days = month_days(2026, 11)
    checker = next(
        v
        for v in recheck(
            grid={(1, d): (D if d == day else X) for d in days},
            roles={1: Role.A, 2: Role.A},
            carry_streaks={},
            days=days,
            flight_pairs={day: 2},
        )
        if v.rule == "flight_staffing" and v.params.get("shift") == "D"
    )
    for lang in ("en", "vi"):
        assert render(engine, people, lang) == render(checker, people, lang)
    assert render(engine, people, "vi") == (
        "2026-11-13: thiếu 1 người ca DEP (cần ít nhất 2); "
        "lịch tự động không xếp ca kép A/D."
    )


# --- people, fallback, catalog ----------------------------------------------


def test_person_is_named_by_roster_code_and_name() -> None:
    v = Violation(
        rule="role_a_minimum_a_days", message="", user_id=1,
        params={"minimum": 2},
    )
    people = _people()
    for lang in ("en", "vi"):
        text = render(v, people, lang)
        assert text.startswith("A1 (Nguyễn Văn An): "), text
        assert "User 1" not in text


def test_missing_user_falls_back_to_translated_number() -> None:
    v = Violation(
        rule="role_a_minimum_a_days", message="", user_id=77,
        params={"minimum": 2},
    )
    en, vi = render(v, {}, "en"), render(v, {}, "vi")
    assert en.startswith(t("schedule.violation.person_unknown", "en").format(id=77))
    assert vi.startswith(t("schedule.violation.person_unknown", "vi").format(id=77))
    assert "#77" in en and "#77" in vi and en != vi


def test_unknown_rule_gets_a_translated_fallback() -> None:
    v = Violation(
        rule="brand_new_rule", message="English text that must not leak",
        day=date(2026, 11, 2),
    )
    en, vi = render(v, {}, "en"), render(v, {}, "vi")
    assert en != vi
    assert "must not leak" not in en + vi
    assert en.startswith("2026-11-02: ") and vi.startswith("2026-11-02: ")


def test_render_all_maps_to_api_violations() -> None:
    v = Violation(
        rule="max_consecutive_off", message="", day=date(2026, 11, 3), user_id=1,
        params={"start": date(2026, 11, 3)},
    )
    [api] = render_all([v], _people(), "vi")
    assert (api.rule, api.day, api.user_id) == (v.rule, v.day, v.user_id)
    assert api.message == render(v, _people(), "vi")


def test_catalog_languages_have_same_keys_and_placeholders() -> None:
    en, vi = MESSAGES["en"], MESSAGES["vi"]
    assert en.keys() == vi.keys()
    mismatched = [k for k in en if _placeholders(en[k]) != _placeholders(vi[k])]
    assert mismatched == []


# --- HTTP: generate + violations endpoint in the request's language ----------


def _admin_headers(client: TestClient) -> dict[str, str]:
    res = client.post(
        f"{V}/auth/login", data={"username": "admin", "password": "admin123"}
    )
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_generate_and_violations_follow_accept_language(
    client: TestClient, monkeypatch
) -> None:
    """One role-A person and a 2-pair day: the D shift is short by design.

    Only this test's user is planned (the DB holds other tests' users), so the
    staffing shortfall is certain whatever ran before.
    """
    year, month, short_day = 2071, 4, date(2071, 4, 14)
    admin = _admin_headers(client)
    res = client.post(
        f"{V}/users", headers=admin,
        json={"username": "vt_a1", "password": "pass123",
              "full_name": "Hoàng Văn Tâm", "role": "A"},
    )
    assert res.status_code in (200, 201), res.text
    user = res.json()
    res = client.put(
        f"{V}/flights/days", headers=admin,
        json={"day": short_day.isoformat(), "flight_pairs": 2},
    )
    assert res.status_code in (200, 201), res.text

    real_build = schedule_input_builder.build

    def only_this_user(db, y, m):
        inp = real_build(db, y, m)
        return dataclasses.replace(
            inp,
            people=[p for p in inp.people if p.user_id == user["id"]],
            max_solve_seconds=10,
        )

    monkeypatch.setattr(schedule_input_builder, "build", only_this_user)

    def staffing_on_short_day(items: list[dict]) -> list[str]:
        return [
            v["message"] for v in items
            if v["rule"] == "flight_staffing" and v["day"] == short_day.isoformat()
        ]

    vi = {**admin, "Accept-Language": "vi"}
    en = {**admin, "Accept-Language": "en"}
    res = client.post(
        f"{V}/schedules/generate", headers=vi, json={"year": year, "month": month}
    )
    assert res.status_code == 200, res.text
    body = res.json()
    generated = staffing_on_short_day(body["violations"])
    assert any("ca DEP (cần ít nhất 2)" in m for m in generated), generated
    assert all(m.startswith(f"{short_day.isoformat()}: thiếu") for m in generated)
    assert not any("shortfall" in v["message"] for v in body["violations"])
    schedule_id = body["schedule"]["id"]

    checked_vi = client.get(f"{V}/schedules/{schedule_id}/violations", headers=vi)
    assert checked_vi.status_code == 200, checked_vi.text
    rechecked = staffing_on_short_day(checked_vi.json())
    assert any("ca DEP" in m for m in rechecked), rechecked
    assert all("thiếu" in m for m in rechecked)

    checked_en = client.get(f"{V}/schedules/{schedule_id}/violations", headers=en)
    english = staffing_on_short_day(checked_en.json())
    assert any("DEP" in m for m in english), english
    assert all("short on the" in m for m in english)
    assert set(english).isdisjoint(rechecked)

    res = client.post(
        f"{V}/schedules/generate", headers=en,
        json={"year": year, "month": month, "force": True},
    )
    assert res.status_code == 200, res.text
    assert all("short" in m for m in staffing_on_short_day(res.json()["violations"]))

    # A per-person breach names the person by roster code and name.
    for day in range(1, 8):
        res = client.post(
            f"{V}/schedules/{schedule_id}/override", headers=vi,
            json={"user_id": user["id"], "work_date": f"{year}-04-{day:02d}",
                  "code": "D"},
        )
        assert res.status_code == 200, res.text
    items = res.json()["violations"]
    mine = [v for v in items if v["user_id"] == user["id"]]
    assert any(v["rule"] == "max_consecutive_working" for v in mine), items
    for v in mine:
        assert v["message"].startswith(f"{user['code']} (Hoàng Văn Tâm): "), v
    assert not any(f"User {user['id']}" in v["message"] for v in items)
