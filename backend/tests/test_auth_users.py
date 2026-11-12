"""End-to-end tests for the auth & user-management flow (F-01, F-02, F-03).

Covers: seed-admin login, JWT-protected /me, admin-created users, the
self-register -> pending -> approve -> login path, and the access-control
guards (bad/pending credentials and non-admin access).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

V = "/api/v1"


def _login(client: TestClient, username: str, password: str):
    return client.post(
        f"{V}/auth/login", data={"username": username, "password": password}
    )


def _token(client: TestClient, username: str, password: str) -> str:
    return _login(client, username, password).json()["access_token"]


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_seed_admin_can_login_and_read_self(client: TestClient) -> None:
    token = _token(client, "admin", "admin123")
    me = client.get(f"{V}/users/me", headers=_bearer(token))
    assert me.status_code == 200
    assert me.json()["role"] == "M"
    assert me.json()["status"] == "active"


def test_wrong_password_rejected(client: TestClient) -> None:
    assert _login(client, "admin", "nope").status_code == 401


def test_admin_creates_active_user_who_can_login(client: TestClient) -> None:
    admin = _bearer(_token(client, "admin", "admin123"))
    created = client.post(
        f"{V}/users",
        headers=admin,
        json={"username": "agne", "full_name": "Agne", "password": "secret1", "role": "A"},
    )
    assert created.status_code == 201
    assert created.json()["status"] == "active"
    assert _login(client, "agne", "secret1").status_code == 200


def test_duplicate_username_conflicts(client: TestClient) -> None:
    admin = _bearer(_token(client, "admin", "admin123"))
    body = {"username": "joachim", "full_name": "J", "password": "secret1", "role": "A"}
    assert client.post(f"{V}/users", headers=admin, json=body).status_code == 201
    assert client.post(f"{V}/users", headers=admin, json=body).status_code == 409


def test_login_ignores_the_case_of_the_username(client: TestClient) -> None:
    """Owner 2026-11-13: staff type their name as they like — "Joachim" was
    stored with a capital and "joachim" was refused. Case and surrounding
    spaces do not matter at login; the password still does."""
    admin = _bearer(_token(client, "admin", "admin123"))
    body = {"username": "Marlene", "full_name": "M", "password": "secret1", "role": "A"}
    assert client.post(f"{V}/users", headers=admin, json=body).status_code == 201
    for typed in ("Marlene", "marlene", "MARLENE", " marlene "):
        assert _login(client, typed, "secret1").status_code == 200, typed
    assert _login(client, "marlene", "Secret1").status_code == 401
    assert _login(client, "marlen", "secret1").status_code == 401
    me = client.get(f"{V}/users/me", headers=_bearer(_token(client, "marlene", "secret1")))
    assert me.json()["username"] == "Marlene"  # stored as entered


def test_username_differing_only_by_case_conflicts(client: TestClient) -> None:
    """Two accounts must never answer to the same typed name."""
    admin = _bearer(_token(client, "admin", "admin123"))
    body = {"username": "helga", "full_name": "H", "password": "secret1", "role": "A"}
    assert client.post(f"{V}/users", headers=admin, json=body).status_code == 201
    again = client.post(f"{V}/users", headers=admin, json={**body, "username": "Helga"})
    assert again.status_code == 409
    registered = client.post(
        f"{V}/auth/register",
        json={"username": "HELGA", "full_name": "H", "password": "secret1"},
    )
    assert registered.status_code == 409


def test_self_register_then_approve_flow(client: TestClient) -> None:
    # Self-registration lands in `pending` and cannot log in yet.
    reg = client.post(
        f"{V}/auth/register",
        json={"username": "longg", "full_name": "Long", "password": "secret1"},
    )
    assert reg.status_code == 201
    assert reg.json()["status"] == "pending"
    assert reg.json()["role"] == "T"
    user_id = reg.json()["id"]
    assert _login(client, "longg", "secret1").status_code == 401

    # Admin approves with a role -> user becomes active and can log in.
    # Keeping the registered role keeps the code (no code is burned).
    admin = _bearer(_token(client, "admin", "admin123"))
    approved = client.post(
        f"{V}/auth/users/{user_id}/approve", json={"role": "T"}, headers=admin
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "active"
    assert approved.json()["role"] == "T"
    assert approved.json()["code"] == reg.json()["code"]
    assert _login(client, "longg", "secret1").status_code == 200


def test_register_ignores_role_and_approve_assigns_role(client: TestClient) -> None:
    # F-03: self-registration cannot pick a role; a smuggled "M" is ignored.
    reg = client.post(
        f"{V}/auth/register",
        json={"username": "x1reg", "full_name": "X", "password": "secret12", "role": "M"},
    )
    assert reg.status_code == 201
    assert reg.json()["role"] == "T"
    assert reg.json()["status"] == "pending"
    uid = reg.json()["id"]

    # Approval must name the role the admin assigns.
    admin = _bearer(_token(client, "admin", "admin123"))
    missing = client.post(f"{V}/auth/users/{uid}/approve", headers=admin)
    assert missing.status_code == 422
    assert _login(client, "x1reg", "secret12").status_code == 401  # still pending

    approved = client.post(
        f"{V}/auth/users/{uid}/approve", json={"role": "A"}, headers=admin
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "active"
    assert approved.json()["role"] == "A"
    assert approved.json()["code"].startswith("A")

    me = client.get(f"{V}/users/me", headers=_bearer(_token(client, "x1reg", "secret12")))
    assert me.json()["role"] == "A"


def test_approve_rejects_accounts_that_are_not_pending(client: TestClient) -> None:
    # Approve only activates pending accounts; it is not a second
    # role-change path (role changes go through PATCH /users/{id}).
    admin = _bearer(_token(client, "admin", "admin123"))
    active = client.post(
        f"{V}/users",
        headers=admin,
        json={"username": "apprv_active", "full_name": "A", "password": "secret1", "role": "A"},
    ).json()
    disabled = client.post(
        f"{V}/users",
        headers=admin,
        json={"username": "apprv_disabled", "full_name": "D", "password": "secret1", "role": "T"},
    ).json()
    assert client.patch(
        f"{V}/users/{disabled['id']}", headers=admin, json={"status": "disabled"}
    ).status_code == 200

    for target in (active, disabled):
        res = client.post(
            f"{V}/auth/users/{target['id']}/approve", json={"role": "M"}, headers=admin
        )
        assert res.status_code == 409
        assert res.json()["detail"] == "Only a pending account can be approved."

    users = {u["id"]: u for u in client.get(f"{V}/users", headers=admin).json()}
    after_active = users[active["id"]]
    after_disabled = users[disabled["id"]]
    assert (after_active["role"], after_active["status"], after_active["code"]) == (
        "A", "active", active["code"]
    )
    assert (after_disabled["role"], after_disabled["status"], after_disabled["code"]) == (
        "T", "disabled", disabled["code"]
    )


def test_non_admin_cannot_list_users(client: TestClient) -> None:
    admin = _bearer(_token(client, "admin", "admin123"))
    client.post(
        f"{V}/users",
        headers=admin,
        json={"username": "thomas", "full_name": "T", "password": "secret1", "role": "A"},
    )
    thomas = _bearer(_token(client, "thomas", "secret1"))
    assert client.get(f"{V}/users", headers=thomas).status_code == 403


def test_directory_lists_active_codes_only(client: TestClient) -> None:
    """Any active user sees the code directory; pending/disabled are hidden."""
    admin = _bearer(_token(client, "admin", "admin123"))

    def _create(username: str, role: str) -> dict:
        r = client.post(
            f"{V}/users",
            headers=admin,
            json={"username": username, "full_name": "Secret Name",
                  "password": "secret1", "role": role},
        )
        assert r.status_code == 201
        return r.json()

    # Created T first, then A: id order differs from code order (A… < T…).
    active = _create("dir_active", "T")
    active_a = _create("dir_active_a", "A")
    disabled = _create("dir_disabled", "A")
    assert client.patch(
        f"{V}/users/{disabled['id']}", headers=admin, json={"status": "disabled"}
    ).status_code == 200
    pending = client.post(
        f"{V}/auth/register",
        json={"username": "dir_pending", "full_name": "Secret Name",
              "password": "secret1", "role": "A"},
    ).json()
    assert pending["status"] == "pending"

    # A plain employee (not admin) can read it.
    employee = _bearer(_token(client, "dir_active", "secret1"))
    r = client.get(f"{V}/users/directory", headers=employee)
    assert r.status_code == 200
    entries = r.json()

    ids = {e["id"] for e in entries}
    assert active["id"] in ids
    assert disabled["id"] not in ids
    assert pending["id"] not in ids
    # Codes only: never the real name.
    assert all(set(e) == {"id", "code", "role"} for e in entries)
    assert "Secret Name" not in r.text
    assert {"id": active["id"], "code": active["code"], "role": "T"} in entries
    # Ordered by code, not by creation: the later A user comes first.
    order = [e["id"] for e in entries]
    assert order.index(active_a["id"]) < order.index(active["id"])
    codes = [e["code"] for e in entries]
    assert codes == sorted(codes)


def test_directory_requires_login(client: TestClient) -> None:
    assert client.get(f"{V}/users/directory").status_code == 401


def test_admin_can_set_quota(client: TestClient) -> None:
    """New users get the default annual leave quota; the admin can change it."""
    from app.core.config import settings

    admin = _bearer(_token(client, "admin", "admin123"))
    created = client.post(
        f"{V}/users",
        headers=admin,
        json={"username": "quota_user", "full_name": "Q", "password": "secret1", "role": "T"},
    )
    assert created.status_code == 201
    assert created.json()["annual_leave_quota"] == settings.ANNUAL_LEAVE_DEFAULT_DAYS == 30
    uid = created.json()["id"]

    r = client.patch(f"{V}/users/{uid}", headers=admin, json={"annual_leave_quota": 25})
    assert r.status_code == 200
    assert r.json()["user"]["annual_leave_quota"] == 25

    for invalid in (-1, 366):
        assert client.patch(
            f"{V}/users/{uid}", headers=admin, json={"annual_leave_quota": invalid}
        ).status_code == 422


def test_admin_create_sets_quota_self_register_cannot(client: TestClient) -> None:
    """POST /users takes the quota in the same request; self-registration
    has no quota field, so a quota sent there is ignored (default applies)."""
    admin = _bearer(_token(client, "admin", "admin123"))
    body = {"full_name": "Q", "password": "secret1", "role": "T"}

    created = client.post(
        f"{V}/users", headers=admin,
        json={**body, "username": "quota_on_create", "annual_leave_quota": 25},
    )
    assert created.status_code == 201
    assert created.json()["annual_leave_quota"] == 25
    assert client.post(
        f"{V}/users", headers=admin,
        json={**body, "username": "quota_too_big", "annual_leave_quota": 366},
    ).status_code == 422

    registered = client.post(
        f"{V}/auth/register",
        json={"username": "quota_self_reg", "full_name": "Q", "password": "secret1",
              "annual_leave_quota": 365},
    )
    assert registered.status_code == 201
    assert registered.json()["annual_leave_quota"] == 30


def test_bare_user_gets_configured_default_quota(client: TestClient, monkeypatch) -> None:
    """The model default reads ANNUAL_LEAVE_DEFAULT_DAYS at insert time, so no
    creation path has to remember to set it."""
    from app.core.config import settings
    from app.core.database import get_db
    from app.models.enums import Role
    from app.models.user import User
    from app.services.user_service import next_user_code

    db = next(get_db())
    try:
        plain = User(
            username="bare_quota_user", full_name="B", hashed_password="x",
            role=Role.T, code=next_user_code(db, Role.T),
        )
        db.add(plain)
        db.commit()
        assert plain.annual_leave_quota == 30

        monkeypatch.setattr(settings, "ANNUAL_LEAVE_DEFAULT_DAYS", 12)
        other = User(
            username="bare_quota_user_12", full_name="B", hashed_password="x",
            role=Role.T, code=next_user_code(db, Role.T),
        )
        db.add(other)
        db.commit()
        assert other.annual_leave_quota == 12

        db.delete(plain)
        db.delete(other)
        db.commit()
    finally:
        db.close()
