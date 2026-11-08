"""Out-of-range input returns 4xx, never 500 (review 2026-11-08, section E).

* Every year/month query or path parameter is bounded: month 1..12, year
  2000..2100 (same range as ``GenerateScheduleRequest``) → 422 otherwise.
* Every ``HTTPException`` detail is a catalog message (``t("key")``), never a
  hard-coded English literal.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.i18n import MESSAGES

V = "/api/v1"

# (method, url template, who) — {y}/{m} are filled in by each test.
MONTH_ENDPOINTS: list[tuple[str, str, str]] = [
    ("GET", "/attendance?year={y}&month={m}", "admin"),
    ("GET", "/attendance/me?year={y}&month={m}", "employee"),
    ("POST", "/attendance/seed?year={y}&month={m}", "admin"),
    ("GET", "/attendance/clock/me?year={y}&month={m}", "employee"),
    ("GET", "/flights/days?year={y}&month={m}", "employee"),
    ("GET", "/schedules/{y}/{m}", "employee"),
    ("GET", "/schedules/{y}/{m}", "admin"),
    ("GET", "/reports/monthly/{y}/{m}", "admin"),
    ("POST", "/calculations/{y}/{m}/close", "admin"),
]
YEAR_ENDPOINTS: list[tuple[str, str, str]] = [
    ("GET", "/holidays?year={y}", "employee"),
    ("GET", "/reports/yearly/{y}", "admin"),
    ("GET", "/leaves/balance?year={y}", "employee"),
]


def _login(client: TestClient, username: str, password: str) -> dict[str, str]:
    res = client.post(f"{V}/auth/login", data={"username": username, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture
def headers(client: TestClient) -> dict[str, dict[str, str]]:
    admin = _login(client, "admin", "admin123")
    res = client.post(
        f"{V}/users", headers=admin,
        json={"username": "bounds_emp", "password": "pass123",
              "full_name": "bounds_emp", "role": "A"},
    )
    assert res.status_code in (201, 409), res.text  # 409: created by an earlier case
    return {"admin": admin, "employee": _login(client, "bounds_emp", "pass123")}


def _call(client: TestClient, method: str, url: str, hdrs: dict[str, str]):
    return client.request(method, f"{V}{url}", headers=hdrs)


@pytest.mark.parametrize("month", [0, 13])
@pytest.mark.parametrize(("method", "template", "who"), MONTH_ENDPOINTS)
def test_month_13_returns_422(
    client: TestClient, headers: dict, method: str, template: str, who: str, month: int
) -> None:
    res = _call(client, method, template.format(y=2026, m=month), headers[who])
    assert res.status_code == 422, (template, month, res.status_code, res.text)


@pytest.mark.parametrize("year", [0, 1999, 2101])
@pytest.mark.parametrize(
    ("method", "template", "who"), MONTH_ENDPOINTS + YEAR_ENDPOINTS
)
def test_year_out_of_range_422(
    client: TestClient, headers: dict, method: str, template: str, who: str, year: int
) -> None:
    res = _call(client, method, template.format(y=year, m=6), headers[who])
    assert res.status_code == 422, (template, year, res.status_code, res.text)


# --- i18n: no hard-coded HTTPException detail ------------------------------

APP_DIR = Path(__file__).resolve().parents[1] / "app"

# Files still holding literal details that belong to OTHER fix tasks of the
# 2026-11-08 review (they own those files). The coordinator empties this list
# once those tasks are merged — do not add new entries.
KNOWN_LITERAL_OFFENDERS: set[str] = {
    "services/schedule_service.py",  # Task 7 (lines ~151/169) + Task 2 (~228)
}


def _is_literal_text(node: ast.AST | None) -> bool:
    """A str constant, an f-string, or a concatenation / %-format of one."""
    if isinstance(node, ast.Constant):
        return isinstance(node.value, str)
    if isinstance(node, ast.JoinedStr):
        return True
    if isinstance(node, ast.BinOp):
        return _is_literal_text(node.left) or _is_literal_text(node.right)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        return node.func.attr == "format" and _is_literal_text(node.func.value)
    return False


def _t_key(node: ast.AST | None) -> str | None:
    """The literal key of ``t("key")`` / ``t("key").format(...)``, else None."""
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "format"
    ):
        node = node.func.value
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "t"
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and isinstance(node.args[0].value, str)
    ):
        return node.args[0].value
    return None


def _http_exception_details() -> list[tuple[str, int, ast.AST | None]]:
    found = []
    for path in sorted(APP_DIR.rglob("*.py")):
        rel = path.relative_to(APP_DIR).as_posix()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
            if name != "HTTPException":
                continue
            detail = next((k.value for k in node.keywords if k.arg == "detail"), None)
            if detail is None and len(node.args) >= 2:
                detail = node.args[1]
            found.append((rel, node.lineno, detail))
    return found


def test_every_http_exception_detail_is_catalog_key() -> None:
    details = _http_exception_details()
    assert details, "scanner found no HTTPException at all — broken walk?"

    literals = [
        f"{rel}:{line}"
        for rel, line, detail in details
        if rel not in KNOWN_LITERAL_OFFENDERS
        and (_is_literal_text(detail) or (
            isinstance(detail, ast.Dict)
            and any(_is_literal_text(v) for v in detail.values)
        ))
    ]
    assert literals == [], f"hard-coded HTTPException detail(s): {literals}"

    missing = [
        f"{rel}:{line} {key}"
        for rel, line, detail in details
        for key in [_t_key(detail)]
        if key is not None and not (key in MESSAGES["en"] and key in MESSAGES["vi"])
    ]
    assert missing == [], f"t() keys missing from en/vi catalog: {missing}"
