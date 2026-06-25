"""Tests for the Flight Preset feature (preset CRUD + day-apply).

Covers:
- GET /presets → 200 for any active user; returns seeded defaults.
- POST /presets (admin) → 200, fields persisted; non-admin → 403.
- PUT /presets/{id} → 200; DELETE /presets/{id} → 204.
- PUT /days/apply with two presets → flight_pairs=2; GET /days returns flights.
- Apply one preset → pairs=1; apply empty → pairs=0 and flights cleared.
- Apply replaces prior legs (overwrite semantics).
- Existing test_flight_service.py compatibility: FlightDayRead has flights=[].
"""

from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient

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


def _create_active_user(client: TestClient, username: str, password: str) -> dict:
    """Create a regular (role=A) active user; return auth headers."""
    admin = _admin_headers(client)
    resp = client.post(
        f"{V}/users",
        headers=admin,
        json={
            "username": username,
            "full_name": username.upper(),
            "password": password,
            "role": "A",
        },
    )
    assert resp.status_code in (200, 201), resp.text
    token = _login(client, username, password)
    return {"Authorization": f"Bearer {token}"}


def _create_preset(client: TestClient, headers: dict, **overrides) -> dict:
    """Helper to POST /presets with sensible defaults."""
    payload = {
        "label": "TEST (99/98)",
        "route": "TEST-ROUTE",
        "flt_arr": 99,
        "flt_dep": 98,
        "sta": "06:00:00",
        "std": "13:55:00",
        "sort_order": 0,
        "is_active": True,
        **overrides,
    }
    resp = client.post(f"{V}/flights/presets", json=payload, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# GET /presets
# ---------------------------------------------------------------------------


class TestListPresets:
    def test_admin_can_list_presets(self, client: TestClient):
        headers = _admin_headers(client)
        resp = client.get(f"{V}/flights/presets", headers=headers)
        assert resp.status_code == 200
        # Seeded defaults should be present.
        labels = [p["label"] for p in resp.json()]
        assert any("HAN" in lbl for lbl in labels)
        assert any("SGN" in lbl for lbl in labels)

    def test_active_user_can_list_presets(self, client: TestClient):
        user_headers = _create_active_user(client, "preset_reader", "pass1234")
        resp = client.get(f"{V}/flights/presets", headers=user_headers)
        assert resp.status_code == 200

    def test_unauthenticated_cannot_list_presets(self, client: TestClient):
        resp = client.get(f"{V}/flights/presets")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /presets
# ---------------------------------------------------------------------------


class TestCreatePreset:
    def test_admin_create_preset_persists_fields(self, client: TestClient):
        headers = _admin_headers(client)
        preset = _create_preset(
            client, headers,
            label="HAN–FRA (37/36) Copy",
            route="HAN-FRA",
            flt_arr=37,
            flt_dep=36,
            sta="06:00:00",
            std="13:55:00",
            sort_order=5,
            is_active=False,
        )
        assert preset["id"] > 0
        assert preset["label"] == "HAN–FRA (37/36) Copy"
        assert preset["route"] == "HAN-FRA"
        assert preset["flt_arr"] == 37
        assert preset["flt_dep"] == 36
        assert preset["sta"] == "06:00:00"
        assert preset["std"] == "13:55:00"
        assert preset["sort_order"] == 5
        assert preset["is_active"] is False

    def test_non_admin_cannot_create_preset(self, client: TestClient):
        user_headers = _create_active_user(client, "non_admin_cp", "pass1234")
        resp = client.post(
            f"{V}/flights/presets",
            json={
                "label": "X",
                "flt_arr": 1,
                "flt_dep": 2,
                "sta": "06:00:00",
                "std": "14:00:00",
            },
            headers=user_headers,
        )
        assert resp.status_code == 403

    def test_preset_appears_in_list_after_create(self, client: TestClient):
        headers = _admin_headers(client)
        preset = _create_preset(client, headers, label="UNIQUE_LABEL_XYZ")
        resp = client.get(f"{V}/flights/presets", headers=headers)
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()]
        assert preset["id"] in ids


# ---------------------------------------------------------------------------
# PUT /presets/{id}
# ---------------------------------------------------------------------------


class TestUpdatePreset:
    def test_update_preset_changes_fields(self, client: TestClient):
        headers = _admin_headers(client)
        preset = _create_preset(client, headers, label="Original Label")

        resp = client.put(
            f"{V}/flights/presets/{preset['id']}",
            json={
                "label": "Updated Label",
                "route": "NEW-ROUTE",
                "flt_arr": 55,
                "flt_dep": 54,
                "sta": "07:00:00",
                "std": "15:00:00",
                "sort_order": 3,
                "is_active": False,
            },
            headers=headers,
        )
        assert resp.status_code == 200
        updated = resp.json()
        assert updated["label"] == "Updated Label"
        assert updated["route"] == "NEW-ROUTE"
        assert updated["flt_arr"] == 55
        assert updated["flt_dep"] == 54
        assert updated["is_active"] is False

    def test_update_nonexistent_preset_returns_404(self, client: TestClient):
        headers = _admin_headers(client)
        resp = client.put(
            f"{V}/flights/presets/99999",
            json={
                "label": "X",
                "flt_arr": 1,
                "flt_dep": 2,
                "sta": "06:00:00",
                "std": "14:00:00",
            },
            headers=headers,
        )
        assert resp.status_code == 404

    def test_non_admin_cannot_update_preset(self, client: TestClient):
        admin = _admin_headers(client)
        preset = _create_preset(client, admin)
        user_headers = _create_active_user(client, "non_admin_up", "pass1234")
        resp = client.put(
            f"{V}/flights/presets/{preset['id']}",
            json={
                "label": "X",
                "flt_arr": 1,
                "flt_dep": 2,
                "sta": "06:00:00",
                "std": "14:00:00",
            },
            headers=user_headers,
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /presets/{id}
# ---------------------------------------------------------------------------


class TestDeletePreset:
    def test_delete_preset_returns_204(self, client: TestClient):
        headers = _admin_headers(client)
        preset = _create_preset(client, headers, label="To Delete")
        resp = client.delete(
            f"{V}/flights/presets/{preset['id']}", headers=headers
        )
        assert resp.status_code == 204

        # Should no longer appear in list.
        list_resp = client.get(f"{V}/flights/presets", headers=headers)
        ids = [p["id"] for p in list_resp.json()]
        assert preset["id"] not in ids

    def test_delete_nonexistent_returns_404(self, client: TestClient):
        headers = _admin_headers(client)
        resp = client.delete(
            f"{V}/flights/presets/99999", headers=headers
        )
        assert resp.status_code == 404

    def test_non_admin_cannot_delete_preset(self, client: TestClient):
        admin = _admin_headers(client)
        preset = _create_preset(client, admin)
        user_headers = _create_active_user(client, "non_admin_del", "pass1234")
        resp = client.delete(
            f"{V}/flights/presets/{preset['id']}", headers=user_headers
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# PUT /days/apply
# ---------------------------------------------------------------------------


class TestApplyPresetsToDay:
    def _get_seeded_preset_ids(self, client: TestClient, headers: dict) -> list[int]:
        """Return ids of the two seeded presets (HAN-FRA and SGN-FRA)."""
        resp = client.get(f"{V}/flights/presets", headers=headers)
        presets = resp.json()
        # Bootstrap seeds exactly these two; pick by route.
        han = next(p for p in presets if p.get("route") == "HAN-FRA")
        sgn = next(p for p in presets if p.get("route") == "SGN-FRA")
        return [han["id"], sgn["id"]]

    def test_apply_two_presets_gives_pairs_2(self, client: TestClient):
        headers = _admin_headers(client)
        ids = self._get_seeded_preset_ids(client, headers)
        day = "2026-07-20"

        resp = client.put(
            f"{V}/flights/days/apply",
            json={"day": day, "preset_ids": ids},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["day"] == day
        assert body["flight_pairs"] == 2
        # Response must include flights list with 4 legs (2 per preset).
        assert len(body["flights"]) == 4

    def test_apply_two_presets_flights_have_correct_sta_std(self, client: TestClient):
        headers = _admin_headers(client)
        ids = self._get_seeded_preset_ids(client, headers)
        day = "2026-07-21"

        resp = client.put(
            f"{V}/flights/days/apply",
            json={"day": day, "preset_ids": ids},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        flights = {f["flt_number"]: f for f in resp.json()["flights"]}

        # HAN-FRA: arrival flt 37 → sta=06:00, std=None
        assert flights[37]["sta"] == "06:00:00"
        assert flights[37]["std"] is None
        # HAN-FRA: departure flt 36 → sta=None, std=13:55
        assert flights[36]["sta"] is None
        assert flights[36]["std"] == "13:55:00"
        # SGN-FRA: arrival flt 31 → sta=06:30, std=None
        assert flights[31]["sta"] == "06:30:00"
        assert flights[31]["std"] is None
        # SGN-FRA: departure flt 30 → sta=None, std=13:35
        assert flights[30]["sta"] is None
        assert flights[30]["std"] == "13:35:00"

    def test_get_days_returns_flights_after_apply(self, client: TestClient):
        headers = _admin_headers(client)
        ids = self._get_seeded_preset_ids(client, headers)
        day = "2026-07-22"

        client.put(
            f"{V}/flights/days/apply",
            json={"day": day, "preset_ids": ids},
            headers=headers,
        )

        list_resp = client.get(
            f"{V}/flights/days",
            params={"year": 2026, "month": 7},
            headers=headers,
        )
        assert list_resp.status_code == 200
        day_rows = {d["day"]: d for d in list_resp.json()}
        assert day in day_rows
        assert day_rows[day]["flight_pairs"] == 2
        assert len(day_rows[day]["flights"]) == 4

    def test_apply_one_preset_gives_pairs_1(self, client: TestClient):
        headers = _admin_headers(client)
        ids = self._get_seeded_preset_ids(client, headers)
        day = "2026-07-23"

        resp = client.put(
            f"{V}/flights/days/apply",
            json={"day": day, "preset_ids": [ids[0]]},  # only HAN-FRA
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["flight_pairs"] == 1
        assert len(body["flights"]) == 2

    def test_apply_empty_preset_ids_clears_day(self, client: TestClient):
        headers = _admin_headers(client)
        ids = self._get_seeded_preset_ids(client, headers)
        day = "2026-07-24"

        # First apply two presets.
        client.put(
            f"{V}/flights/days/apply",
            json={"day": day, "preset_ids": ids},
            headers=headers,
        )

        # Then clear with empty list.
        resp = client.put(
            f"{V}/flights/days/apply",
            json={"day": day, "preset_ids": []},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["flight_pairs"] == 0
        assert body["flights"] == []

    def test_apply_replaces_prior_legs(self, client: TestClient):
        """Applying a different preset set fully replaces prior legs."""
        headers = _admin_headers(client)
        ids = self._get_seeded_preset_ids(client, headers)
        day = "2026-07-25"

        # Apply both presets first.
        client.put(
            f"{V}/flights/days/apply",
            json={"day": day, "preset_ids": ids},
            headers=headers,
        )

        # Now apply only the SGN-FRA preset.
        resp = client.put(
            f"{V}/flights/days/apply",
            json={"day": day, "preset_ids": [ids[1]]},  # SGN-FRA only
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["flight_pairs"] == 1

        flt_numbers = {f["flt_number"] for f in body["flights"]}
        # HAN-FRA legs (37, 36) should be gone; SGN-FRA legs (31, 30) remain.
        assert 31 in flt_numbers
        assert 30 in flt_numbers
        assert 37 not in flt_numbers
        assert 36 not in flt_numbers

    def test_non_admin_cannot_apply_presets(self, client: TestClient):
        user_headers = _create_active_user(client, "non_admin_apply", "pass1234")
        resp = client.put(
            f"{V}/flights/days/apply",
            json={"day": "2026-07-26", "preset_ids": []},
            headers=user_headers,
        )
        assert resp.status_code == 403

    def test_apply_ignores_nonexistent_preset_ids(self, client: TestClient):
        """Silently skip unknown preset IDs; result depends on valid ones only."""
        headers = _admin_headers(client)
        ids = self._get_seeded_preset_ids(client, headers)
        day = "2026-07-27"

        # Mix one valid + one non-existent ID.
        resp = client.put(
            f"{V}/flights/days/apply",
            json={"day": day, "preset_ids": [ids[0], 999999]},
            headers=headers,
        )
        assert resp.status_code == 200
        # Only the valid preset processed → pairs=1.
        assert resp.json()["flight_pairs"] == 1


# ---------------------------------------------------------------------------
# PUT /days/apply-batch
# ---------------------------------------------------------------------------


class TestApplyBatch:
    def _seeded_ids(self, client: TestClient, headers: dict) -> list[int]:
        resp = client.get(f"{V}/flights/presets", headers=headers)
        presets = resp.json()
        han = next(p for p in presets if p.get("route") == "HAN-FRA")
        sgn = next(p for p in presets if p.get("route") == "SGN-FRA")
        return [han["id"], sgn["id"]]

    def test_batch_two_days_returns_correct_pairs_and_flights(self, client: TestClient):
        """Apply two items (different days, different preset combos) → 200 with 2 FlightDayRead."""
        headers = _admin_headers(client)
        ids = self._seeded_ids(client, headers)
        day1 = "2026-09-01"
        day2 = "2026-09-02"

        resp = client.put(
            f"{V}/flights/days/apply-batch",
            json={
                "items": [
                    {"day": day1, "preset_ids": [ids[0]]},       # HAN-FRA only → pairs=1
                    {"day": day2, "preset_ids": [ids[0], ids[1]]}, # both → pairs=2
                ]
            },
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert len(body) == 2

        row1 = next(r for r in body if r["day"] == day1)
        row2 = next(r for r in body if r["day"] == day2)

        assert row1["flight_pairs"] == 1
        assert len(row1["flights"]) == 2  # arr + dep for HAN-FRA

        assert row2["flight_pairs"] == 2
        assert len(row2["flights"]) == 4  # 2 legs × 2 presets

    def test_batch_empty_preset_ids_clears_day(self, client: TestClient):
        """Item with empty preset_ids clears that day → pairs=0, flights=[]."""
        headers = _admin_headers(client)
        ids = self._seeded_ids(client, headers)
        day = "2026-09-03"

        # Seed some flights first.
        client.put(
            f"{V}/flights/days/apply",
            json={"day": day, "preset_ids": ids},
            headers=headers,
        )

        resp = client.put(
            f"{V}/flights/days/apply-batch",
            json={"items": [{"day": day, "preset_ids": []}]},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert len(body) == 1
        assert body[0]["flight_pairs"] == 0
        assert body[0]["flights"] == []

    def test_batch_is_atomic_both_days_persisted(self, client: TestClient):
        """Atomicity check: both days written in one commit are visible via GET /days."""
        headers = _admin_headers(client)
        ids = self._seeded_ids(client, headers)
        day1 = "2026-09-15"
        day2 = "2026-09-16"

        client.put(
            f"{V}/flights/days/apply-batch",
            json={
                "items": [
                    {"day": day1, "preset_ids": [ids[0]]},
                    {"day": day2, "preset_ids": [ids[1]]},
                ]
            },
            headers=headers,
        )

        list_resp = client.get(
            f"{V}/flights/days",
            params={"year": 2026, "month": 9},
            headers=headers,
        )
        assert list_resp.status_code == 200
        day_map = {d["day"]: d for d in list_resp.json()}
        assert day1 in day_map
        assert day2 in day_map
        assert day_map[day1]["flight_pairs"] == 1
        assert day_map[day2]["flight_pairs"] == 1

    def test_non_admin_cannot_apply_batch(self, client: TestClient):
        """Non-admin user receives 403."""
        user_headers = _create_active_user(client, "non_admin_batch", "pass1234")
        resp = client.put(
            f"{V}/flights/days/apply-batch",
            json={"items": [{"day": "2026-09-20", "preset_ids": []}]},
            headers=user_headers,
        )
        assert resp.status_code == 403

    def test_batch_empty_items_returns_empty_list(self, client: TestClient):
        """Empty items list → 200 with []."""
        headers = _admin_headers(client)
        resp = client.put(
            f"{V}/flights/days/apply-batch",
            json={"items": []},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json() == []


# ---------------------------------------------------------------------------
# Compatibility: existing FlightDayRead shape still works
# ---------------------------------------------------------------------------


class TestFlightDayReadBackwardCompat:
    def test_list_days_returns_flights_field(self, client: TestClient):
        """GET /days must include flights key (empty list when no flights set)."""
        headers = _admin_headers(client)
        # Upsert a day via the old endpoint.
        client.put(
            f"{V}/flights/days",
            json={"day": "2026-08-10", "flight_pairs": 1},
            headers=headers,
        )
        resp = client.get(
            f"{V}/flights/days",
            params={"year": 2026, "month": 8},
            headers=headers,
        )
        assert resp.status_code == 200
        for day_row in resp.json():
            assert "flights" in day_row  # field always present
