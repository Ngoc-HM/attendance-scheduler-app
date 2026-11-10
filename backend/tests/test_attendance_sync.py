"""B5 — edits to a PUBLISHED roster reach the actuals seeded from it.

Publishing seeds ``AttendanceRecord`` rows (``recorded_by`` NULL) from the
roster. A later admin override or approved shift change must move those
untouched seeded actuals along with the planned cell, but never a cell an
admin recorded by hand.
"""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

V = "/api/v1"


def _admin_headers(client: TestClient) -> dict[str, str]:
    res = client.post(f"{V}/auth/login", data={"username": "admin", "password": "admin123"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _make_user(client: TestClient, admin: dict, username: str, role: str) -> dict:
    res = client.post(
        f"{V}/users",
        headers=admin,
        json={"username": username, "password": "pass123",
              "full_name": username, "role": role},
    )
    assert res.status_code in (200, 201), res.text
    return res.json()


def _login(client: TestClient, username: str) -> dict[str, str]:
    res = client.post(f"{V}/auth/login", data={"username": username, "password": "pass123"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _generate_and_publish(client: TestClient, admin: dict, year: int, month: int) -> dict:
    gen = client.post(
        f"{V}/schedules/generate", headers=admin, json={"year": year, "month": month}
    )
    assert gen.status_code == 200 and gen.json()["feasible"] is True, gen.text
    schedule = gen.json()["schedule"]
    pub = client.post(f"{V}/schedules/{schedule['id']}/publish", headers=admin)
    assert pub.status_code == 200, pub.text
    return schedule


def _actual(client: TestClient, admin: dict, user_id: int, day: str) -> dict:
    d = date.fromisoformat(day)
    rows = client.get(
        f"{V}/attendance", params={"year": d.year, "month": d.month}, headers=admin
    ).json()
    return next(r for r in rows if r["user_id"] == user_id and r["work_date"] == day)


def test_override_on_published_month_updates_seeded_actual(client: TestClient) -> None:
    admin = _admin_headers(client)
    users = [_make_user(client, admin, f"sync_ov_a{i}", "A") for i in (1, 2, 3, 4)]
    u = users[0]["id"]
    schedule = _generate_and_publish(client, admin, 2028, 8)

    seeded = _actual(client, admin, u, "2028-08-15")
    assert seeded["recorded_by"] is None and seeded["code"] != "T"

    res = client.post(
        f"{V}/schedules/{schedule['id']}/override", headers=admin,
        json={"user_id": u, "work_date": "2028-08-15", "code": "T"},
    )
    assert res.status_code == 200, res.text

    actual = _actual(client, admin, u, "2028-08-15")
    assert actual["code"] == "T"
    # Still a seeded cell — later roster edits keep flowing into it.
    assert actual["recorded_by"] is None


def test_override_does_not_touch_admin_recorded_actual(client: TestClient) -> None:
    admin = _admin_headers(client)
    users = [_make_user(client, admin, f"sync_keep_a{i}", "A") for i in (1, 2, 3, 4)]
    u = users[0]["id"]
    schedule = _generate_and_publish(client, admin, 2028, 2)

    put = client.put(
        f"{V}/attendance", headers=admin,
        json={"user_id": u, "work_date": "2028-02-16", "code": "B"},
    )
    assert put.status_code == 200 and put.json()["recorded_by"] is not None, put.text

    res = client.post(
        f"{V}/schedules/{schedule['id']}/override", headers=admin,
        json={"user_id": u, "work_date": "2028-02-16", "code": "T"},
    )
    assert res.status_code == 200, res.text
    planned = next(
        a for a in res.json()["schedule"]["assignments"]
        if a["user_id"] == u and a["work_date"] == "2028-02-16"
    )
    assert planned["code"] == "T"

    assert _actual(client, admin, u, "2028-02-16")["code"] == "B"


def test_approved_shift_change_updates_seeded_actual(client: TestClient) -> None:
    admin = _admin_headers(client)
    users = [_make_user(client, admin, f"sync_sc_a{i}", "A") for i in (1, 2, 3, 4)]
    u = users[0]["id"]
    _generate_and_publish(client, admin, 2028, 4)
    seeded = _actual(client, admin, u, "2028-04-10")["code"]
    # A code role A may request (A, D, X) that differs from the seeded one.
    wanted = "D" if seeded == "A" else "A"

    req = client.post(
        f"{V}/shift-changes", headers=_login(client, "sync_sc_a1"),
        json={"work_date": "2028-04-10", "kind": "change_code", "requested_code": wanted},
    )
    assert req.status_code == 201, req.text
    dec = client.post(
        f"{V}/shift-changes/{req.json()['id']}/decide", headers=admin,
        json={"status": "approved"},
    )
    assert dec.status_code == 200, dec.text

    assert _actual(client, admin, u, "2028-04-10")["code"] == wanted


def test_republish_resyncs_untouched_seeded_actuals(client: TestClient) -> None:
    """Regenerate a published month and publish it again: untouched seeded
    actuals follow the new roster, admin-recorded ones keep their code."""
    admin = _admin_headers(client)
    users = [_make_user(client, admin, f"sync_rp_a{i}", "A") for i in (1, 2, 3, 4)]
    u = users[0]["id"]
    _generate_and_publish(client, admin, 2028, 10)
    put = client.put(
        f"{V}/attendance", headers=admin,
        json={"user_id": u, "work_date": "2028-10-16", "code": "B"},
    )
    assert put.status_code == 200, put.text
    seeded_before = _actual(client, admin, u, "2028-10-15")["code"]
    assert seeded_before != "T"

    # Back to a draft (force: regenerating a published month may require it).
    gen = client.post(
        f"{V}/schedules/generate", headers=admin,
        json={"year": 2028, "month": 10, "force": True},
    )
    assert gen.status_code == 200 and gen.json()["feasible"] is True, gen.text
    sid = gen.json()["schedule"]["id"]
    regenerated = next(
        a["code"] for a in gen.json()["schedule"]["assignments"]
        if a["user_id"] == u and a["work_date"] == "2028-10-15"
    )
    # F11 — the forced regenerate already moved the seeded actual onto the
    # new plan (hidden from the employee until re-published).
    assert _actual(client, admin, u, "2028-10-15")["code"] == regenerated
    for day in ("2028-10-15", "2028-10-16"):
        res = client.post(
            f"{V}/schedules/{sid}/override", headers=admin,
            json={"user_id": u, "work_date": day, "code": "T"},
        )
        assert res.status_code == 200, res.text
    # I1 — a draft edit moves the still-seeded actual at once (the next
    # month's boundary reads it); /attendance/me hides it until re-published.
    # The admin-recorded actual keeps its code.
    assert _actual(client, admin, u, "2028-10-15")["code"] == "T"
    assert _actual(client, admin, u, "2028-10-16")["code"] == "B"

    pub = client.post(f"{V}/schedules/{sid}/publish", headers=admin)
    assert pub.status_code == 200, pub.text

    assert _actual(client, admin, u, "2028-10-15")["code"] == "T"
    assert _actual(client, admin, u, "2028-10-16")["code"] == "B"


# ---------------------------------------------------------------------------
# Decision #39 — deleting an admin must not turn the actuals they recorded
# back into "seeded" rows that the next roster edit would overwrite.
# ---------------------------------------------------------------------------

def test_deleting_an_admin_keeps_their_recorded_actuals_attributed(
    client: TestClient,
) -> None:
    admin = _admin_headers(client)
    me = client.get(f"{V}/users/me", headers=admin).json()["id"]
    other_admin = _make_user(client, admin, "f4_admin2", "M")["id"]
    users = [_make_user(client, admin, f"f4_del_a{i}", "A") for i in (1, 2, 3, 4)]
    u = users[0]["id"]
    schedule = _generate_and_publish(client, admin, 2043, 2)

    put = client.put(
        f"{V}/attendance", headers=_login(client, "f4_admin2"),
        json={"user_id": u, "work_date": "2043-02-10", "code": "T"},
    )
    assert put.status_code == 200 and put.json()["recorded_by"] == other_admin, put.text

    assert client.delete(f"{V}/users/{other_admin}", headers=admin).status_code == 204

    recorded = _actual(client, admin, u, "2043-02-10")
    assert recorded["recorded_by"] == me
    assert recorded["code"] == "T"

    # A later roster edit on that day leaves the recorded actual alone.
    res = client.post(
        f"{V}/schedules/{schedule['id']}/override", headers=admin,
        json={"user_id": u, "work_date": "2043-02-10", "code": "B"},
    )
    assert res.status_code == 200, res.text
    assert _actual(client, admin, u, "2043-02-10")["code"] == "T"


def test_admin_deleting_own_account_hands_recorded_actuals_to_another_admin(
    client: TestClient,
) -> None:
    admin = _admin_headers(client)
    leaving = _make_user(client, admin, "f4_admin3", "M")["id"]
    u = _make_user(client, admin, "f4_self_t1", "T")["id"]
    own = _login(client, "f4_admin3")
    put = client.put(
        f"{V}/attendance", headers=own,
        json={"user_id": u, "work_date": "2043-04-07", "code": "B"},
    )
    assert put.status_code == 200, put.text

    assert client.delete(f"{V}/users/{leaving}", headers=own).status_code == 204

    recorder = _actual(client, admin, u, "2043-04-07")["recorded_by"]
    assert recorder is not None and recorder != leaving
    users = {row["id"]: row for row in client.get(f"{V}/users", headers=admin).json()}
    assert users[recorder]["role"] == "M" and users[recorder]["status"] == "active"


def test_republish_never_overwrites_a_sick_actual(client: TestClient) -> None:
    """An S row with no recorder (e.g. left by the old admin delete) stays S."""
    from app.core.database import SessionLocal
    from app.models.attendance import AttendanceRecord
    from app.models.enums import AttendanceCode

    admin = _admin_headers(client)
    users = [_make_user(client, admin, f"f4_sick_a{i}", "A") for i in (1, 2, 3, 4)]
    u = users[0]["id"]
    schedule = _generate_and_publish(client, admin, 2043, 3)

    db = SessionLocal()
    try:
        row = (
            db.query(AttendanceRecord)
            .filter(
                AttendanceRecord.user_id == u,
                AttendanceRecord.work_date == date(2043, 3, 10),
            )
            .one()
        )
        row.code = AttendanceCode.S
        row.recorded_by = None
        db.commit()
    finally:
        db.close()

    pub = client.post(f"{V}/schedules/{schedule['id']}/publish", headers=admin)
    assert pub.status_code == 200, pub.text
    assert _actual(client, admin, u, "2043-03-10")["code"] == "S"

    res = client.post(
        f"{V}/schedules/{schedule['id']}/override", headers=admin,
        json={"user_id": u, "work_date": "2043-03-10", "code": "B"},
    )
    assert res.status_code == 200, res.text
    assert _actual(client, admin, u, "2043-03-10")["code"] == "S"
