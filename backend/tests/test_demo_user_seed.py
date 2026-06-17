"""Tests for the deterministic demo-user seed tool."""

from __future__ import annotations

from app.core.database import SessionLocal
from app.models.enums import Role
from app.models.user import User
from app.services.demo_user_seed import DEMO_USERS, seed_demo_users


def test_seed_demo_users_is_idempotent(client) -> None:
    db = SessionLocal()
    try:
        first = seed_demo_users(db, "demo12345")
        second = seed_demo_users(db, "demo12345")

        assert first == {"created": 10, "skipped": 0, "total": 10}
        assert second == {"created": 0, "skipped": 10, "total": 10}

        users = (
            db.query(User)
            .filter(User.username.in_([spec.username for spec in DEMO_USERS]))
            .order_by(User.username)
            .all()
        )

        assert [user.username for user in users] == [spec.username for spec in DEMO_USERS]
        assert [user.role for user in users[:4]] == [Role.T] * 4
        assert [user.role for user in users[4:]] == [Role.A] * 6
        assert all(user.status.value == "active" for user in users)
    finally:
        db.close()