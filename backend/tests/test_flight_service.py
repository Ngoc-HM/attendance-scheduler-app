"""Tests for F-04 flight schedule service: CRUD, pair derivation, Excel import.

Covers:
- list_days / upsert_day / upsert_flight happy paths
- flight_pairs_map default-0 for unconfigured days
- Pair derivation: 2 routes→2, 1 route→1, 0→0, duplicate arrivals don't double-count
- Excel import happy path (builds workbook in-memory with openpyxl)
- Excel import bad extension rejected (no partial commit)
- Excel import parse error rolls back (no partial commit)
"""

from __future__ import annotations

import io
from datetime import date, time

import openpyxl
import pytest
from fastapi.testclient import TestClient

from app.services.flight_pair_derivation import derive_pairs_for_day

V = "/api/v1"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _login(client: TestClient, username: str, password: str) -> str:
    resp = client.post(
        f"{V}/auth/login", data={"username": username, "password": password}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _admin_headers(client: TestClient) -> dict:
    token = _login(client, "admin", "admin123")
    return {"Authorization": f"Bearer {token}"}


def _make_xlsx(rows: list[tuple]) -> bytes:
    """Build an in-memory .xlsx with a header row followed by data rows."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["date", "flt_number", "route", "sta", "std"])
    for row in rows:
        ws.append(list(row))
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Unit tests: pure pair derivation
# ---------------------------------------------------------------------------


class TestDerivePairsForDay:
    def test_two_routes_gives_two(self):
        # Both HAN-FRA (37+36) and SGN-FRA (31+30) present → 2 pairs.
        assert derive_pairs_for_day([37, 36, 31, 30]) == 2

    def test_one_route_gives_one(self):
        # Only HAN-FRA pair present.
        assert derive_pairs_for_day([37, 36]) == 1

    def test_zero_routes_gives_zero(self):
        assert derive_pairs_for_day([]) == 0
        assert derive_pairs_for_day([99, 100]) == 0  # unknown FLT numbers

    def test_arrival_without_departure_gives_zero(self):
        # FLT 37 (arrival) without FLT 36 (departure) → no complete pair.
        assert derive_pairs_for_day([37]) == 0

    def test_duplicate_arrivals_do_not_double_count(self):
        # Two FLT-37s + one FLT-36 → still only 1 HAN-FRA pair (set semantics).
        assert derive_pairs_for_day([37, 37, 36]) == 1

    def test_duplicate_both_sides_do_not_exceed_one(self):
        # Even if both arrival and departure appear twice → still 1 pair per route.
        assert derive_pairs_for_day([37, 37, 36, 36]) == 1

    def test_cap_at_two(self):
        # Hypothetical: can never exceed 2 even with many FLTs.
        assert derive_pairs_for_day([37, 36, 31, 30, 99, 98]) == 2


# ---------------------------------------------------------------------------
# Integration tests via HTTP client
# ---------------------------------------------------------------------------


class TestFlightDayCrud:
    def test_upsert_and_list_day(self, client: TestClient):
        headers = _admin_headers(client)
        resp = client.put(
            f"{V}/flights/days",
            json={"day": "2026-07-15", "flight_pairs": 2},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["day"] == "2026-07-15"
        assert body["flight_pairs"] == 2

        # Listing that month should include the record.
        list_resp = client.get(
            f"{V}/flights/days", params={"year": 2026, "month": 7}, headers=headers
        )
        assert list_resp.status_code == 200
        days = list_resp.json()
        assert any(d["day"] == "2026-07-15" and d["flight_pairs"] == 2 for d in days)

    def test_upsert_day_idempotent(self, client: TestClient):
        headers = _admin_headers(client)
        for pairs in (1, 0, 2):
            resp = client.put(
                f"{V}/flights/days",
                json={"day": "2026-08-01", "flight_pairs": pairs},
                headers=headers,
            )
            assert resp.status_code == 200
            assert resp.json()["flight_pairs"] == pairs

    def test_non_admin_cannot_upsert_day(self, client: TestClient):
        # Create a regular user.
        admin = _admin_headers(client)
        client.post(
            f"{V}/users",
            headers=admin,
            json={"username": "flt_user", "full_name": "FU", "password": "pass123", "role": "A"},
        )
        token = _login(client, "flt_user", "pass123")
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.put(
            f"{V}/flights/days",
            json={"day": "2026-07-10", "flight_pairs": 1},
            headers=headers,
        )
        assert resp.status_code == 403

    def test_active_user_can_list_days(self, client: TestClient):
        admin = _admin_headers(client)
        client.post(
            f"{V}/users",
            headers=admin,
            json={"username": "flt_reader", "full_name": "FR", "password": "pass234", "role": "A"},
        )
        token = _login(client, "flt_reader", "pass234")
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get(
            f"{V}/flights/days", params={"year": 2026, "month": 7}, headers=headers
        )
        assert resp.status_code == 200


class TestFlightPairsMap:
    def test_default_zero_for_unconfigured_days(self, client: TestClient):
        """flight_pairs_map must return 0 for days with no FlightDay row."""
        from app.core.database import get_db
        from app.services.flight_service import flight_pairs_map

        # Use a fresh DB session via the app's dependency.
        with client as c:  # ensure lifespan ran
            db_gen = get_db()
            db = next(db_gen)
            try:
                result = flight_pairs_map(
                    db,
                    [date(2099, 1, 1), date(2099, 1, 2)],  # far-future, no rows
                )
                assert result[date(2099, 1, 1)] == 0
                assert result[date(2099, 1, 2)] == 0
            finally:
                try:
                    next(db_gen)
                except StopIteration:
                    pass

    def test_empty_list_returns_empty_dict(self, client: TestClient):
        from app.core.database import get_db
        from app.services.flight_service import flight_pairs_map

        with client:
            db = next(get_db())
            assert flight_pairs_map(db, []) == {}


class TestUpsertFlight:
    def test_upsert_flight_recomputes_pairs(self, client: TestClient):
        headers = _admin_headers(client)
        day = "2026-09-10"

        # Add arrival FLT 37.
        resp = client.put(
            f"{V}/flights",
            json={"day": day, "flt_number": 37, "route": "HAN-FRA", "sta": "06:30:00"},
            headers=headers,
        )
        assert resp.status_code == 200

        # Pairs should still be 0 (no departure yet).
        list_resp = client.get(
            f"{V}/flights/days", params={"year": 2026, "month": 9}, headers=headers
        )
        days = {d["day"]: d["flight_pairs"] for d in list_resp.json()}
        assert days.get(day, 0) == 0

        # Add departure FLT 36 — should bump pairs to 1.
        client.put(
            f"{V}/flights",
            json={"day": day, "flt_number": 36, "route": "FRA-HAN", "std": "10:00:00"},
            headers=headers,
        )
        list_resp2 = client.get(
            f"{V}/flights/days", params={"year": 2026, "month": 9}, headers=headers
        )
        days2 = {d["day"]: d["flight_pairs"] for d in list_resp2.json()}
        assert days2.get(day, 0) == 1


class TestImportExcel:
    def test_happy_path_two_routes(self, client: TestClient):
        """Import a workbook with both route pairs on one day → flight_pairs=2."""
        headers = _admin_headers(client)
        day_str = "2026-10-05"
        xlsx_bytes = _make_xlsx([
            (day_str, 37, "HAN-FRA", "06:30", None),
            (day_str, 36, "FRA-HAN", None, "10:00"),
            (day_str, 31, "SGN-FRA", "07:00", None),
            (day_str, 30, "FRA-SGN", None, "11:30"),
        ])
        resp = client.post(
            f"{V}/flights/import",
            headers=headers,
            files={"file": ("flights.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert resp.status_code == 200, resp.text
        flights = resp.json()
        assert len(flights) == 4

        # Verify pairs were recomputed to 2.
        list_resp = client.get(
            f"{V}/flights/days", params={"year": 2026, "month": 10}, headers=headers
        )
        days = {d["day"]: d["flight_pairs"] for d in list_resp.json()}
        assert days.get(day_str) == 2

    def test_happy_path_one_route(self, client: TestClient):
        """Import with only one route pair → flight_pairs=1."""
        headers = _admin_headers(client)
        day_str = "2026-10-06"
        xlsx_bytes = _make_xlsx([
            (day_str, 31, "SGN-FRA", "07:00", None),
            (day_str, 30, "FRA-SGN", None, "11:30"),
        ])
        resp = client.post(
            f"{V}/flights/import",
            headers=headers,
            files={"file": ("flights.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert resp.status_code == 200, resp.text
        list_resp = client.get(
            f"{V}/flights/days", params={"year": 2026, "month": 10}, headers=headers
        )
        days = {d["day"]: d["flight_pairs"] for d in list_resp.json()}
        assert days.get(day_str) == 1

    def test_bad_extension_rejected(self, client: TestClient):
        """Non-.xlsx file must be rejected with 422, no data written."""
        headers = _admin_headers(client)
        resp = client.post(
            f"{V}/flights/import",
            headers=headers,
            files={"file": ("flights.csv", b"date,flt_number\n2026-10-01,37", "text/csv")},
        )
        assert resp.status_code == 422

    def test_parse_error_rolls_back_no_partial_commit(self, client: TestClient):
        """A workbook with a bad row must roll back entirely — no flights saved."""
        headers = _admin_headers(client)
        day_str = "2026-11-01"
        # Row 2 is valid; row 3 has a bad date → entire import rejected.
        xlsx_bytes = _make_xlsx([
            (day_str, 37, "HAN-FRA", "06:30", None),  # valid
            ("NOT-A-DATE", 36, "FRA-HAN", None, "10:00"),  # bad date
        ])
        resp = client.post(
            f"{V}/flights/import",
            headers=headers,
            files={"file": ("flights.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert resp.status_code == 422

        # Verify FLT 37 from this batch was NOT persisted.
        list_resp = client.get(
            f"{V}/flights/days", params={"year": 2026, "month": 11}, headers=headers
        )
        days = {d["day"]: d["flight_pairs"] for d in list_resp.json()}
        # No FlightDay row should exist for this day.
        assert day_str not in days

    def test_empty_workbook_succeeds_with_no_flights(self, client: TestClient):
        """An xlsx with only a header row returns an empty list (no error)."""
        headers = _admin_headers(client)
        xlsx_bytes = _make_xlsx([])  # header only
        resp = client.post(
            f"{V}/flights/import",
            headers=headers,
            files={"file": ("flights.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert resp.status_code == 200
        assert resp.json() == []
