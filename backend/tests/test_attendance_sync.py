"""B5 — edits to a PUBLISHED roster reach the actuals seeded from it.

Publishing seeds ``AttendanceRecord`` rows (``recorded_by`` NULL) from the
roster. A later admin override, approved shift change or approved
self-arrange batch must move those untouched seeded actuals along with the
planned cell, but never a cell an admin recorded by hand.
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
    assert _actual(client, admin, u, "2028-04-10")["code"] != "T"

    req = client.post(
        f"{V}/shift-changes", headers=_login(client, "sync_sc_a1"),
        json={"work_date": "2028-04-10", "kind": "change_code", "requested_code": "T"},
    )
    assert req.status_code == 201, req.text
    dec = client.post(
        f"{V}/shift-changes/{req.json()['id']}/decide", headers=admin,
        json={"status": "approved"},
    )
    assert dec.status_code == 200, dec.text

    assert _actual(client, admin, u, "2028-04-10")["code"] == "T"


def test_approved_self_arrange_updates_seeded_actuals(client: TestClient) -> None:
    admin = _admin_headers(client)
    for i in (1, 2, 3, 4):
        _make_user(client, admin, f"sync_sa_a{i}", "A")
    t_user = _make_user(client, admin, "sync_sa_t1", "T")["id"]
    schedule = _generate_and_publish(client, admin, 2028, 6)

    # Swap one X and one AD inside the same full 7-day block: the block keeps
    # its weekly-off count, so the batch is valid.
    own = {
        date.fromisoformat(a["work_date"]): a["code"]
        for a in schedule["assignments"] if a["user_id"] == t_user
    }
    off_day = work_day = None
    for start in (1, 8, 15, 22):
        block = [date(2028, 6, d) for d in range(start, start + 7)]
        offs = [d for d in block if own[d] == "X"]
        works = [d for d in block if own[d] == "AD"]
        if offs and works:
            off_day, work_day = offs[0], works[0]
            break
    assert off_day is not None and work_day is not None

    req = client.post(
        f"{V}/self-arrange", headers=_login(client, "sync_sa_t1"),
        json={"year": 2028, "month": 6, "changes": [
            {"work_date": off_day.isoformat(), "code": "AD"},
            {"work_date": work_day.isoformat(), "code": "X"},
        ]},
    )
    assert req.status_code == 201, req.text
    dec = client.post(
        f"{V}/self-arrange/{req.json()['id']}/decide", headers=admin,
        json={"status": "approved"},
    )
    assert dec.status_code == 200, dec.text

    assert _actual(client, admin, t_user, off_day.isoformat())["code"] == "AD"
    assert _actual(client, admin, t_user, work_day.isoformat())["code"] == "X"


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
    for day in ("2028-10-15", "2028-10-16"):
        res = client.post(
            f"{V}/schedules/{sid}/override", headers=admin,
            json={"user_id": u, "work_date": day, "code": "T"},
        )
        assert res.status_code == 200, res.text
    # Draft edits stay out of the actuals until the month is published again.
    assert _actual(client, admin, u, "2028-10-15")["code"] == seeded_before

    pub = client.post(f"{V}/schedules/{sid}/publish", headers=admin)
    assert pub.status_code == 200, pub.text

    assert _actual(client, admin, u, "2028-10-15")["code"] == "T"
    assert _actual(client, admin, u, "2028-10-16")["code"] == "B"
