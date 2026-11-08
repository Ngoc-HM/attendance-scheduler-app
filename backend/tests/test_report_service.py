"""F-15 — report assembly (pure) + CSV/XLSX export endpoints."""

from __future__ import annotations

import csv
import io
from datetime import date

from fastapi.testclient import TestClient
from openpyxl import load_workbook

from app.core.database import SessionLocal
from app.models.enums import AttendanceCode, Role, UserStatus
from app.models.user import User
from app.services import report_service
from app.services.report_serializers import to_csv, to_xlsx
from app.services.report_table import ReportTable, UserRow, build_monthly, build_yearly


def test_build_monthly_totals_count_ad_as_two_workdays() -> None:
    users = [UserRow(1, "Alice", "A")]
    days = [date(2027, 11, d) for d in range(1, 4)]
    grid = {
        (1, days[0]): AttendanceCode.A_D,  # 2 work days
        (1, days[1]): AttendanceCode.A,    # 1
        (1, days[2]): AttendanceCode.X,    # off
    }
    table = build_monthly(users, days, grid)
    row = table.rows[0]
    # headers: User, Role, d1, d2, d3, Work days, A/D, Off (X)
    assert row[0] == "Alice"
    assert row[2:5] == ["A/D", "A", "X"]
    assert row[-3:] == ["3", "1", "1"]  # work=2+1, A/D=1, off=1


def test_build_yearly_sums_workdays_per_month() -> None:
    users = [UserRow(1, "Bob", "A")]
    grids = {
        1: {(1, date(2027, 1, 5)): AttendanceCode.A_D},   # 2
        2: {(1, date(2027, 2, 5)): AttendanceCode.A},     # 1
    }
    table = build_yearly(users, 2027, grids)
    row = table.rows[0]
    assert row[2] == "2" and row[3] == "1"  # M1, M2
    assert row[-1] == "3"  # total


# --- export endpoints ------------------------------------------------------

def _admin(client: TestClient) -> dict[str, str]:
    res = client.post("/api/v1/auth/login", data={"username": "admin", "password": "admin123"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_monthly_csv_export_downloads(client: TestClient) -> None:
    admin = _admin(client)
    res = client.post("/api/v1/users", headers=admin,
                      json={"username": "rep_u1", "password": "pass123",
                            "full_name": "Rep U1", "role": "A"})
    uid = res.json()["id"]
    client.put("/api/v1/attendance", headers=admin,
               json={"user_id": uid, "work_date": "2027-12-01", "code": "A/D"})

    res = client.get("/api/v1/reports/monthly/2027/12?format=csv", headers=admin)
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "attendance_2027_12.csv" in res.headers["content-disposition"]
    rows = list(csv.reader(io.StringIO(res.content.decode("utf-8-sig"))))
    assert rows[0][0] == "User"
    assert any(r[0] == "Rep U1" for r in rows[1:])


def test_monthly_xlsx_export_returns_workbook(client: TestClient) -> None:
    admin = _admin(client)
    res = client.get("/api/v1/reports/monthly/2027/12?format=xlsx", headers=admin)
    assert res.status_code == 200
    assert "spreadsheetml" in res.headers["content-type"]
    assert res.content[:2] == b"PK"  # xlsx is a zip


def test_reports_require_admin(client: TestClient) -> None:
    admin = _admin(client)
    client.post("/api/v1/users", headers=admin,
                json={"username": "rep_nonadmin", "password": "pass123",
                      "full_name": "NA", "role": "T"})
    tok = client.post("/api/v1/auth/login",
                      data={"username": "rep_nonadmin", "password": "pass123"}).json()
    hdr = {"Authorization": f"Bearer {tok['access_token']}"}
    assert client.get("/api/v1/reports/monthly/2027/12", headers=hdr).status_code == 403


# --- R7 (B1): CSV/XLSX formula injection + active users only ---------------

_FORMULA_NAMES = [
    '=HYPERLINK("http://evil.example","x")',
    "+1+2",
    "-3+4",
    "@SUM(A1)",
    "\tTAB",
    "\rCR",
]


def _injection_table() -> ReportTable:
    return ReportTable(
        title="Attendance 2027-12",
        headers=["User", "Role", "Work days"],
        rows=[[name, "A", "3"] for name in _FORMULA_NAMES] + [["Safe Name", "A", "3"]],
    )


def test_csv_formula_cell_is_escaped() -> None:
    rows = list(csv.reader(io.StringIO(to_csv(_injection_table()).decode("utf-8-sig"))))
    names = [r[0] for r in rows[1:]]
    assert names == [f"'{n}" for n in _FORMULA_NAMES] + ["Safe Name"]
    assert names[0] == "'=HYPERLINK(\"http://evil.example\",\"x\")"
    # Plain cells (numbers, roles, headers) are untouched.
    assert rows[0] == ["User", "Role", "Work days"]
    assert rows[1][1:] == ["A", "3"]


def test_xlsx_formula_cell_is_text() -> None:
    ws = load_workbook(io.BytesIO(to_xlsx(_injection_table()))).active
    for idx, name in enumerate(_FORMULA_NAMES, start=2):
        cell = ws.cell(row=idx, column=1)
        assert cell.data_type == "s", (name, cell.data_type)
        # XML stores a bare CR as LF; the escaping is what matters here.
        assert cell.value == f"'{name}".replace("\r", "\n")
    assert ws.cell(row=len(_FORMULA_NAMES) + 2, column=1).value == "Safe Name"


def test_reports_exclude_pending_and_disabled(client: TestClient) -> None:
    db = SessionLocal()
    made: list[User] = []
    try:
        for suffix, user_status in (
            ("act", UserStatus.active),
            ("pen", UserStatus.pending),
            ("dis", UserStatus.disabled),
        ):
            u = User(
                username=f"rep_status_{suffix}",
                code=f"RS{suffix.upper()}",
                full_name=f"Report {suffix}",
                hashed_password="x",
                role=Role.A,
                status=user_status,
            )
            db.add(u)
            made.append(u)
        db.commit()

        monthly_names = {r[0] for r in report_service.monthly(db, 2027, 12).rows}
        yearly_names = {r[0] for r in report_service.yearly(db, 2027).rows}
        for names in (monthly_names, yearly_names):
            assert "Report act" in names
            assert "Report pen" not in names
            assert "Report dis" not in names
    finally:
        for u in made:
            db.delete(u)
        db.commit()
        db.close()
