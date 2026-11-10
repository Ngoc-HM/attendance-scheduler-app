"""HTTP tests for the monthly flight-plan template (F-04, owner 2026-11).

``GET /flights/template`` → fill ``x`` → ``POST /flights/import``. The test DB
is shared by the whole run, so each test uses its own month (2031) and presets
with FLT numbers nobody else uses (71xx); other active presets only ride along
unchanged in the downloaded file.
"""

from __future__ import annotations

import io
from datetime import date

import openpyxl
import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.i18n import t
from app.models.flight import Flight, FlightDay, FlightPreset

V = "/api/v1"
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _login(client: TestClient, username: str, password: str) -> dict:
    resp = client.post(f"{V}/auth/login", data={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def admin(client: TestClient) -> dict:
    return _login(client, "admin", "admin123")


@pytest.fixture
def preset(client: TestClient, admin: dict):
    """Create active presets for one test and delete them afterwards, so the
    shared DB's later templates (other test files) do not carry them."""
    created: list[int] = []

    def make(arr: int, dep: int) -> dict:
        payload = {
            "label": f"PLAN ({arr}/{dep})", "route": f"R{arr}", "flt_arr": arr,
            "flt_dep": dep, "sta": "06:10:00", "std": "14:20:00", "is_active": True,
        }
        resp = client.post(f"{V}/flights/presets", json=payload, headers=admin)
        assert resp.status_code == 200, resp.text
        created.append(resp.json()["id"])
        return resp.json()

    yield make
    for preset_id in created:
        client.delete(f"{V}/flights/presets/{preset_id}", headers=admin)


def _download(client: TestClient, headers: dict, year: int, month: int):
    resp = client.get(
        f"{V}/flights/template", params={"year": year, "month": month}, headers=headers
    )
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == XLSX_MIME
    assert resp.headers["content-disposition"] == (
        f'attachment; filename="flight-plan-{year}-{month:02d}.xlsx"'
    )
    return openpyxl.load_workbook(io.BytesIO(resp.content))


def _upload(client: TestClient, headers: dict, wb):
    buf = io.BytesIO()
    wb.save(buf)
    files = {"file": ("plan.xlsx", buf.getvalue(), XLSX_MIME)}
    return client.post(f"{V}/flights/import", headers=headers, files=files)


def _row(ws, arr: int, dep: int) -> int:
    for r in range(4, ws.max_row + 1):
        if (ws.cell(row=r, column=2).value, ws.cell(row=r, column=3).value) == (arr, dep):
            return r
    raise AssertionError(f"no row for {arr}/{dep}")


def _mark(ws, arr: int, dep: int, day: int, value: str | None = "x") -> None:
    # .value, not cell(value=None): openpyxl ignores a None there.
    ws.cell(row=_row(ws, arr, dep), column=3 + day).value = value


def _legs(year: int, month: int) -> dict[tuple[int, int], Flight]:
    with SessionLocal() as db:
        rows = db.query(Flight).filter(
            Flight.day >= date(year, month, 1), Flight.day < date(year, month + 1, 1)
        )
        return {(f.day.day, f.flt_number): f for f in rows}


def _flight_days(year: int, month: int) -> dict[int, int]:
    with SessionLocal() as db:
        rows = db.query(FlightDay).filter(
            FlightDay.day >= date(year, month, 1), FlightDay.day < date(year, month + 1, 1)
        )
        return {fd.day.day: fd.flight_pairs for fd in rows}


def _add_leg(day: date, flt: int) -> None:
    with SessionLocal() as db:
        db.add(Flight(day=day, flt_number=flt, route="OTHER"))
        db.commit()


def test_template_lists_presets_and_prefills_existing_flights(client, admin, preset):
    preset(7101, 7102)
    _add_leg(date(2031, 1, 5), 7101)
    _add_leg(date(2031, 1, 5), 7102)
    _add_leg(date(2031, 1, 6), 7101)  # departure missing: not marked
    ws = _download(client, admin, 2031, 1).active
    r = _row(ws, 7101, 7102)
    assert ws.cell(row=r, column=1).value == "PLAN (7101/7102)"
    marked = [d for d in range(1, 32) if ws.cell(row=r, column=3 + d).value == "x"]
    assert marked == [5]
    with SessionLocal() as db:
        active = [p for p in db.query(FlightPreset).all() if p.is_active]
    assert ws.max_row - 3 == len({(p.flt_arr, p.flt_dep) for p in active})


def test_template_is_admin_only(client, admin):
    client.post(
        f"{V}/users", headers=admin,
        json={"username": "plan_emp", "password": "pass1234", "full_name": "P", "role": "A"},
    )
    emp = _login(client, "plan_emp", "pass1234")
    resp = client.get(f"{V}/flights/template", params={"year": 2031, "month": 1}, headers=emp)
    assert resp.status_code == 403


def test_template_without_active_presets_is_422(client, admin):
    with SessionLocal() as db:
        active = db.query(FlightPreset).filter(FlightPreset.is_active.is_(True)).all()
        ids = [p.id for p in active]
        for p in active:
            p.is_active = False
        db.commit()
    try:
        for lang, text in (("en", "Create a flight preset first."),
                           ("vi", "Hãy tạo mẫu chuyến bay trước.")):
            resp = client.get(
                f"{V}/flights/template", params={"year": 2031, "month": 1},
                headers={**admin, "Accept-Language": lang},
            )
            assert resp.status_code == 422
            assert resp.json()["detail"] == text
    finally:
        with SessionLocal() as db:
            for p in db.query(FlightPreset).filter(FlightPreset.id.in_(ids)):
                p.is_active = True
            db.commit()


def test_round_trip_unchanged_is_a_no_op(client, admin, preset):
    preset(7101, 7102)
    _add_leg(date(2031, 2, 3), 7101)
    _add_leg(date(2031, 2, 3), 7102)
    _add_leg(date(2031, 2, 4), 7101)  # lone leg: no mark, but must survive
    before = {k: (f.id, f.route, f.sta, f.std) for k, f in _legs(2031, 2).items()}
    resp = _upload(client, admin, _download(client, admin, 2031, 2))
    assert resp.status_code == 200, resp.text
    after = {k: (f.id, f.route, f.sta, f.std) for k, f in _legs(2031, 2).items()}
    assert set(after) == set(before)
    assert after[(4, 7101)] == before[(4, 7101)]


def test_marking_adds_both_legs_and_sets_pairs(client, admin, preset):
    preset(7101, 7102)
    wb = _download(client, admin, 2031, 3)
    _mark(wb.active, 7101, 7102, 9)
    _mark(wb.active, 7101, 7102, 10, " X ")
    resp = _upload(client, admin, wb)
    assert resp.status_code == 200, resp.text
    assert [(f["day"], f["flt_number"]) for f in resp.json()] == [
        ("2031-03-09", 7101), ("2031-03-09", 7102),
        ("2031-03-10", 7101), ("2031-03-10", 7102),
    ]
    legs = _legs(2031, 3)
    arr, dep = legs[(9, 7101)], legs[(9, 7102)]
    assert (arr.route, str(arr.sta), arr.std) == ("R7101", "06:10:00", None)
    assert (dep.route, dep.sta, str(dep.std)) == ("R7101", None, "14:20:00")
    # 71xx is not a known route pair (§8): the day is recomputed, pairs stay 0.
    assert _flight_days(2031, 3) == {9: 0, 10: 0}


def test_marking_known_route_sets_flight_pairs(client, admin):
    wb = _download(client, admin, 2031, 4)
    _mark(wb.active, 37, 36, 2)
    _mark(wb.active, 31, 30, 2)
    _mark(wb.active, 37, 36, 3)
    resp = _upload(client, admin, wb)
    assert resp.status_code == 200, resp.text
    assert _flight_days(2031, 4) == {2: 2, 3: 1}


def test_unmarking_removes_only_that_presets_legs(client, admin, preset):
    preset(7101, 7102)
    for flt in (7101, 7102, 7199):
        _add_leg(date(2031, 5, 7), flt)
    wb = _download(client, admin, 2031, 5)
    _mark(wb.active, 7101, 7102, 7, None)
    resp = _upload(client, admin, wb)
    assert resp.status_code == 200, resp.text
    assert set(_legs(2031, 5)) == {(7, 7199)}
    # Only the changed day got a FlightDay row; untouched days got none.
    assert _flight_days(2031, 5) == {7: 0}


def _assert_rejected(client, admin, wb, month: int, errors: list[str]) -> None:
    before = set(_legs(2031, month))
    days_before = _flight_days(2031, month)
    resp = _upload(client, admin, wb)
    assert resp.status_code == 422, resp.text
    assert resp.json()["detail"] == {"message": t("flight.import_failed", "en"),
                                     "errors": errors}
    assert set(_legs(2031, month)) == before
    assert _flight_days(2031, month) == days_before


def test_bad_mark_rejects_whole_file(client, admin, preset):
    preset(7101, 7102)
    wb = _download(client, admin, 2031, 6)
    _mark(wb.active, 7101, 7102, 1)  # valid, must not be written
    r = _row(wb.active, 7101, 7102)
    wb.active.cell(row=r, column=8, value="ok")  # H = day 5
    _assert_rejected(client, admin, wb, 6, [
        t("flight.plan_bad_mark", "en").format(cell=f"H{r}", value="ok"),
    ])


def test_changed_header_and_bad_month_reject(client, admin):
    wb = _download(client, admin, 2031, 6)
    _mark(wb.active, 37, 36, 1)
    wb.active["E2"] = 99
    _assert_rejected(client, admin, wb, 6, [t("flight.plan_layout_changed", "en")])
    wb.active["E2"] = 2
    wb.active["B1"] = "2031-13"
    _assert_rejected(client, admin, wb, 6, [
        t("flight.plan_bad_month", "en").format(value="2031-13", min=2000, max=2100),
    ])


def test_unknown_pair_and_duplicate_row_reject(client, admin):
    wb = _download(client, admin, 2031, 6)
    ws = wb.active
    _mark(ws, 37, 36, 1)
    last = ws.max_row
    ws.cell(row=last + 1, column=2, value=7777)
    ws.cell(row=last + 1, column=3, value=7778)
    _assert_rejected(client, admin, wb, 6, [
        t("flight.plan_unknown_preset", "en").format(row=last + 1, arr=7777, dep=7778),
    ])
    ws.cell(row=last + 1, column=2, value=37)
    ws.cell(row=last + 1, column=3, value=36)
    _assert_rejected(client, admin, wb, 6, [
        t("flight.plan_duplicate_pair", "en").format(
            row=last + 1, first_row=_row(ws, 37, 36), arr=37, dep=36
        ),
    ])


def test_three_presets_on_a_day_reject(client, admin, preset):
    for arr in (7111, 7113, 7115):
        preset(arr, arr + 1)
    wb = _download(client, admin, 2031, 7)
    for arr in (7111, 7113, 7115):
        _mark(wb.active, arr, arr + 1, 4)
    _assert_rejected(client, admin, wb, 7, [
        t("flight.plan_too_many_presets", "en").format(day="2031-07-04", max=2),
    ])


def test_shared_flt_on_a_day_rejects(client, admin, preset):
    preset(7121, 7122)
    preset(7121, 7123)
    wb = _download(client, admin, 2031, 8)
    _mark(wb.active, 7121, 7122, 12)
    _mark(wb.active, 7121, 7123, 12)
    _assert_rejected(client, admin, wb, 8, [
        t("flight.plan_shared_flt", "en").format(day="2031-08-12", flt=7121),
    ])


def test_plan_errors_are_vietnamese(client, admin, preset):
    preset(7101, 7102)
    wb = _download(client, admin, 2031, 9)
    r = _row(wb.active, 7101, 7102)
    wb.active.cell(row=r, column=4, value="?")
    buf = io.BytesIO()
    wb.save(buf)
    resp = client.post(
        f"{V}/flights/import", headers={**admin, "Accept-Language": "vi"},
        files={"file": ("plan.xlsx", buf.getvalue(), XLSX_MIME)},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["errors"] == [
        t("flight.plan_bad_mark", "vi").format(cell=f"D{r}", value="?")
    ]


def test_list_format_still_imports(client, admin):
    wb = openpyxl.Workbook()
    wb.active.append(["date", "flt_number", "route", "sta", "std"])
    wb.active.append(["2031-10-02", 7131, "X-Y", "06:30", None])
    resp = _upload(client, admin, wb)
    assert resp.status_code == 200, resp.text
    assert [(f["day"], f["flt_number"]) for f in resp.json()] == [("2031-10-02", 7131)]
