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
    ("GET", "/flights/template?year={y}&month={m}", "admin"),
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

# Literal details allowed by (file, exact text) while another fix task still
# owns them. Empty since Task 7 moved the last ones (schedule_service manual
# override) to catalog keys — do not add entries.
KNOWN_LITERAL_OFFENDERS: set[tuple[str, str]] = set()


def _single_assignment(scope: ast.AST | None, name: str) -> ast.AST | None:
    """The value of ``name``'s only assignment inside ``scope``, else None."""
    if scope is None:
        return None
    values = []
    for node in ast.walk(scope):
        if isinstance(node, ast.Assign):
            if any(isinstance(tg, ast.Name) and tg.id == name for tg in node.targets):
                values.append(node.value)
        elif isinstance(node, ast.AnnAssign | ast.AugAssign):
            if isinstance(node.target, ast.Name) and node.target.id == name:
                values.append(node.value)
    return values[0] if len(values) == 1 else None


def _is_literal_text(node: ast.AST | None, scope: ast.AST | None = None) -> bool:
    """A str constant, an f-string, a concatenation / ``.format`` of one, a
    conditional with a literal branch, or a bare name assigned exactly once
    from such a literal in the enclosing function (``scope``)."""
    if isinstance(node, ast.Constant):
        return isinstance(node.value, str)
    if isinstance(node, ast.JoinedStr):
        return True
    if isinstance(node, ast.BinOp):
        return _is_literal_text(node.left, scope) or _is_literal_text(node.right, scope)
    if isinstance(node, ast.IfExp):
        return _is_literal_text(node.body, scope) or _is_literal_text(node.orelse, scope)
    if isinstance(node, ast.Name):
        value = _single_assignment(scope, node.id)
        return value is not None and _is_literal_text(value)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        return node.func.attr == "format" and _is_literal_text(node.func.value, scope)
    return False


def _is_literal_detail(detail: ast.AST | None, scope: ast.AST | None) -> bool:
    if isinstance(detail, ast.Dict):
        return any(_is_literal_text(v, scope) for v in detail.values)
    return _is_literal_text(detail, scope)


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


Detail = tuple[int, ast.AST | None, ast.AST | None]  # (line, detail, enclosing function)


def _scan_source(source: str) -> list[Detail]:
    """Every ``HTTPException(...)`` call in ``source`` with its detail node."""
    tree = ast.parse(source)
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}

    def enclosing_function(node: ast.AST) -> ast.AST | None:
        while node in parents:
            node = parents[node]
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                return node
        return None

    found: list[Detail] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
        if name != "HTTPException":
            continue
        detail = next((k.value for k in node.keywords if k.arg == "detail"), None)
        if detail is None and len(node.args) >= 2:
            detail = node.args[1]
        found.append((node.lineno, detail, enclosing_function(node)))
    return found


def _app_details() -> list[tuple[str, Detail]]:
    return [
        (path.relative_to(APP_DIR).as_posix(), found)
        for path in sorted(APP_DIR.rglob("*.py"))
        for found in _scan_source(path.read_text(encoding="utf-8"))
    ]


def _allow_listed(rel: str, detail: ast.AST | None) -> bool:
    return (
        isinstance(detail, ast.Constant)
        and (rel, detail.value) in KNOWN_LITERAL_OFFENDERS
    )


def test_literal_scanner_catches_indirect_literals() -> None:
    """The scanner itself: literals hidden behind a conditional or a local
    variable are flagged; catalog lookups are not."""
    source = '''
def a(flag):
    raise HTTPException(400, detail="Plain literal.")
def b(flag):
    raise HTTPException(400, detail=t("x.key") if flag else "Fallback text.")
def c():
    msg = "Assigned once."
    raise HTTPException(400, detail=msg)
def d(x):
    raise HTTPException(400, detail=f"Value {x}")
def e():
    msg = t("x.key")
    raise HTTPException(400, detail=msg)
def f(flag):
    raise HTTPException(400, detail=t("x.a") if flag else t("x.b"))
def g():
    raise HTTPException(400, detail={"message": "Literal in dict.", "errors": []})
'''
    flagged = [
        getattr(scope, "name", None)
        for _line, detail, scope in _scan_source(source)
        if _is_literal_detail(detail, scope)
    ]
    assert flagged == ["a", "b", "c", "d", "g"]


def test_every_http_exception_detail_is_catalog_key() -> None:
    details = _app_details()
    assert details, "scanner found no HTTPException at all — broken walk?"

    literals = [
        f"{rel}:{line}"
        for rel, (line, detail, scope) in details
        if _is_literal_detail(detail, scope) and not _allow_listed(rel, detail)
    ]
    assert literals == [], f"hard-coded HTTPException detail(s): {literals}"

    missing = [
        f"{rel}:{line} {key}"
        for rel, (line, detail, _scope) in details
        for key in [_t_key(detail)]
        if key is not None and not (key in MESSAGES["en"] and key in MESSAGES["vi"])
    ]
    assert missing == [], f"t() keys missing from en/vi catalog: {missing}"
