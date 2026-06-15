"""F-15 — report assembly (pure) + CSV/XLSX export endpoints."""

from __future__ import annotations

import csv
import io
from datetime import date

from fastapi.testclient import TestClient

from app.models.enums import AttendanceCode
from app.services.report_table import UserRow, build_monthly, build_yearly


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
