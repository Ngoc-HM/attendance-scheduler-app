"""Roster export in the customer's workbook layout (decision #70)."""

from __future__ import annotations

import io
from datetime import date, time

from fastapi.testclient import TestClient
from openpyxl import load_workbook

from app.core.database import SessionLocal
from app.core.i18n import t
from app.models.enums import AttendanceCode as C
from app.models.enums import LeaveStatus, LeaveType, Role, ScheduleStatus
from app.models.flight import Flight
from app.models.leave import LeaveRequest
from app.models.schedule import MonthlySchedule, ShiftAssignment
from app.models.user import User
from app.scheduler.calendar_utils import month_days
from app.services.roster_sheet import (
    CompRow,
    RosterDay,
    RosterFlightRow,
    RosterPerson,
    RosterSheet,
)
from app.services.roster_xlsx import build_workbook

V = "/api/v1"
SGN = RosterFlightRow("31/30", "0650/1305")
HAN = RosterFlightRow("37/36", "0600/1355")
# The customer's November 2026: 31/30 on Sun, Mon, Wed, Thu, Sat.
SGN_DAYS = {6, 0, 2, 3, 5}


def _people() -> list[RosterPerson]:
    roles = ["M", "M", "T", "T", "A", "A", "A", "A", "F"]
    codes = ["M1", "M2", "T1", "T2", "A1", "A2", "A3", "A4", "F1"]
    return [RosterPerson(i + 1, c, r) for i, (c, r) in enumerate(zip(codes, roles, strict=True))]


def _sheet(year: int = 2026, month: int = 11, *, ad: bool = False) -> RosterSheet:
    people = _people()
    days = [RosterDay(d, [SGN, HAN] if d.weekday() in SGN_DAYS else [HAN])
            for d in month_days(year, month)]
    grid = {}
    for p in people:
        for d in month_days(year, month):
            grid[(p.user_id, d)] = C.X if d.weekday() >= 5 else C.D
    grid[(5, date(year, month, 3))] = C.A_D
    grid[(6, date(year, month, 4))] = C.AL
    if ad:
        grid[(9, date(year, month, 4))] = C.AD
    return RosterSheet(
        year=year, month=month, people=people, days=days, grid=grid,
        comp={p.user_id: CompRow(0, 1, 0, 1) for p in people},
        comp_heading="Compensation Days from October 26 as follows:",
        comp_notes=["A1: 1 - 03OCT A/D duty assigned"], checked_by="M1",
        leave_days={6: {11: 1}}, leave_quota={p.user_id: 25 for p in people},
    )


def _load(data: bytes):
    return load_workbook(io.BytesIO(data))


def test_layout_matches_the_customer_workbook() -> None:
    wb = _load(build_workbook(_sheet()))
    assert wb.sheetnames == ["NOV26", "AL 26"]
    ws = wb["NOV26"]
    assert ws["A1"].value == "WR NOV26 // (TTL 21 WORKING DAYS)"
    assert [ws.cell(2, c).value for c in range(1, 15)] == [
        "Date", "Day", "FLT #", "STA/STD LT FRA", "NOTES",
        "M1", "M2", "T1", "T2", "A1", "A2", "A3", "A4", "F1"]
    widths = {k: v.width for k, v in ws.column_dimensions.items()}
    assert widths["A"] == widths["B"] == 7.7109375 and widths["E"] == 23.7109375
    assert all(widths[c] == 8.7109375 for c in "FGHIJKLMN")
    merged = {str(r) for r in ws.merged_cells.ranges}
    # 1 title + 22 two-row days x 12 + 10 legend rows = the customer's 275.
    assert len(merged) == 275 and "A1:M1" in merged
    assert {"A3:A4", "B3:B4", "E3:E4", "F3:F4", "N3:N4"} <= merged
    assert "A7:A8" not in merged and ws["A7"].value == "3" and ws["C7"].value == "37/36"
    assert (ws["C3"].value, ws["D3"].value, ws["C4"].value) == ("31/30", "0650/1305", "37/36")
    # Same rows below the day block as the customer's file.
    assert ws["A55"].fill.fgColor.rgb == "FF000000" and ws.row_dimensions[55].height == 5.1
    assert ws["A56"].value.startswith("A= ARR duty") and "A56:D56" in merged
    assert "A58:D58" not in merged and ws["A58"].value.startswith("A/D =")
    assert ws["A65"].value == "X = OFF DAY (INCL PH): 09 DAYS"
    assert ws["A66"].value == "TTL DAYS" and ws["J66"].value == 21
    assert ws["A72"].value == "Checked by M1 on:" and ws["J72"].value == "Approved by GM on:"
    assert ws["A74"].value.startswith("Compensation Days from October 26")
    assert ws["A76"].value.startswith("A1: 1")
    # Weekend fill on date/weekday, legend colours on codes, separators.
    assert ws["A3"].fill.fgColor.rgb == "FFC6E0B4" and ws["C3"].fill.fill_type is None
    assert ws["J7"].value == "A/D" and ws["J7"].fill.fgColor.rgb == "FFFF99CC"
    assert ws["H2"].border.left.style == "thick" and ws["J2"].border.left.style == "thick"
    assert ws["N2"].border.left.style == "thick" and ws["N2"].border.right.style == "thick"
    assert ws["G2"].border.left.style == "thin"
    # Counts: A/D row, AL row with its fill.
    assert ws["J58"].value == 1 and ws["K64"].value == 1
    assert ws["K64"].fill.fgColor.rgb == "FFFFFF00"
    assert ws.page_setup.scale == 68 and ws.sheet_view.zoomScale == 80


def test_ad_gets_the_double_shift_fill_and_a_legend_line() -> None:
    ws = _load(build_workbook(_sheet(ad=True)))["NOV26"]
    cell = next(c for row in ws.iter_rows(min_row=3, max_row=54) for c in row if c.value == "AD")
    assert cell.fill.fgColor.rgb == "FFFF99CC"
    assert ws["A59"].value.startswith("AD = ") and ws["N59"].value == 1
    assert ws["A67"].value == "TTL DAYS"  # everything below moved one row


def test_leave_sheet() -> None:
    ws = _load(build_workbook(_sheet()))["AL 26"]
    assert ws["C4"].value == "Urlaubstageübersicht 2026"
    assert ws["C6"].value == "M1" and ws["K6"].value == "F1"
    assert ws["B8"].value == "Januar" and ws["B19"].value == "Dezember"
    assert ws["H18"].value == 1 and ws["H20"].value == 24 and ws["C20"].value == 25


def test_day_without_flights_keeps_one_empty_row() -> None:
    sheet = _sheet(2026, 2)
    sheet.days[0] = RosterDay(sheet.days[0].day, [])
    ws = _load(build_workbook(sheet))["FEB26"]
    assert ws["A3"].value == "1" and ws["C3"].value is None and ws["A4"].value == "2"


# --- endpoint ----------------------------------------------------------------

def _login(client: TestClient, username: str, password: str) -> dict[str, str]:
    res = client.post(f"{V}/auth/login", data={"username": username, "password": password})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _employee(client: TestClient, admin: dict[str, str], username: str, name: str) -> int:
    res = client.post(f"{V}/users", headers=admin, json={
        "username": username, "password": "pass123", "full_name": name, "role": "A"})
    if res.status_code == 409:
        with SessionLocal() as db:
            return db.query(User.id).filter(User.username == username).scalar()
    assert res.status_code == 201, res.text
    return res.json()["id"]


def test_roster_route_needs_admin_and_a_roster(client: TestClient) -> None:
    admin = _login(client, "admin", "admin123")
    _employee(client, admin, "roster_emp", "Roster Employee")
    emp = _login(client, "roster_emp", "pass123")
    assert client.get(f"{V}/reports/roster/2076/5", headers=emp).status_code == 403
    res = client.get(f"{V}/reports/roster/2076/5", headers={**admin, "Accept-Language": "vi"})
    assert res.status_code == 404
    assert res.json()["detail"] == t("report.roster_no_schedule", "vi")


def test_roster_route_exports_codes_never_names(client: TestClient) -> None:
    admin = _login(client, "admin", "admin123")
    uid = _employee(client, admin, "roster_secret", "Roster Secret Name")
    year, month = 2077, 3
    with SessionLocal() as db:
        schedule = MonthlySchedule(year=year, month=month, status=ScheduleStatus.draft)
        db.add(schedule)
        db.flush()
        for d in month_days(year, month):
            db.add(ShiftAssignment(schedule_id=schedule.id, user_id=uid, work_date=d,
                                   code=C.A_D if d.day == 2 else C.D))
        db.add(Flight(day=date(year, month, 2), flt_number=37, sta=time(6, 0)))
        db.add(Flight(day=date(year, month, 2), flt_number=36, std=time(13, 55)))
        db.add(LeaveRequest(user_id=uid, start_date=date(year, 1, 5), end_date=date(year, 1, 7),
                            leave_type=LeaveType.monthly, status=LeaveStatus.approved))
        db.commit()
        # Other tests leave users named like a day code ("A"); those short
        # names cannot be told apart from codes, so only longer ones count.
        names = [n for (n,) in db.query(User.full_name).all() if len(n) >= 4]
        code = db.get(User, uid).code
        admin_code = db.query(User.code).filter(User.username == "admin").scalar()
        assert db.get(User, uid).role is Role.A

    res = client.get(f"{V}/reports/roster/{year}/{month}", headers=admin)
    assert res.status_code == 200, res.text
    assert 'filename="WR MAR77.xlsx"' in res.headers["content-disposition"]
    wb = _load(res.content)
    assert wb.sheetnames == ["MAR77", "AL 77"]
    values = [str(c.value) for ws in wb.worksheets for row in ws.iter_rows() for c in row
              if c.value is not None]
    assert not any("Roster Secret Name" in v for v in values)
    assert not set(values) & set(names)
    ws = wb["MAR77"]
    col = next(c.column for c in ws[2] if c.value == code)
    assert ws["C4"].value == "37/36" and ws["D4"].value == "0600/1355"
    assert ws.cell(4, col).value == "A/D"
    assert any(v == f"Checked by {admin_code} on:" for v in values)
    al = wb["AL 77"]
    col = next(c.column for c in al[6] if c.value == code)
    assert al.cell(8, col).value == 3  # January
