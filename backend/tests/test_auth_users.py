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
        json={"username": "agne", "full_name": "Agne", "password": "secret1", "role": "A1"},
    )
    assert created.status_code == 201
    assert created.json()["status"] == "active"
    assert _login(client, "agne", "secret1").status_code == 200


def test_duplicate_username_conflicts(client: TestClient) -> None:
    admin = _bearer(_token(client, "admin", "admin123"))
    body = {"username": "joachim", "full_name": "J", "password": "secret1", "role": "A2"}
    assert client.post(f"{V}/users", headers=admin, json=body).status_code == 201
    assert client.post(f"{V}/users", headers=admin, json=body).status_code == 409


def test_self_register_then_approve_flow(client: TestClient) -> None:
    # Self-registration lands in `pending` and cannot log in yet.
    reg = client.post(
        f"{V}/auth/register",
        json={"username": "longg", "full_name": "Long", "password": "secret1", "role": "A3"},
    )
    assert reg.status_code == 201
    assert reg.json()["status"] == "pending"
    user_id = reg.json()["id"]
    assert _login(client, "longg", "secret1").status_code == 401

    # Admin approves -> user becomes active and can log in.
    admin = _bearer(_token(client, "admin", "admin123"))
    approved = client.post(f"{V}/auth/users/{user_id}/approve", headers=admin)
    assert approved.status_code == 200
    assert approved.json()["status"] == "active"
    assert _login(client, "longg", "secret1").status_code == 200


def test_non_admin_cannot_list_users(client: TestClient) -> None:
    admin = _bearer(_token(client, "admin", "admin123"))
    client.post(
        f"{V}/users",
        headers=admin,
        json={"username": "thomas", "full_name": "T", "password": "secret1", "role": "A4"},
    )
    thomas = _bearer(_token(client, "thomas", "secret1"))
    assert client.get(f"{V}/users", headers=thomas).status_code == 403
