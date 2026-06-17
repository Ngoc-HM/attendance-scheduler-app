"""Seed helpers for deterministic demo users.

The helper is intentionally small and idempotent so it can be reused by a
standalone script or by future admin tooling.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.enums import Role, UserStatus
from app.models.user import User
from app.services.user_service import next_user_code


@dataclass(frozen=True)
class DemoUserSpec:
    username: str
    full_name: str
    role: Role


DEMO_USERS: tuple[DemoUserSpec, ...] = (
    DemoUserSpec("nguyenvana", "Nguyen Van A", Role.T),
    DemoUserSpec("nguyenvanb", "Nguyen Van B", Role.T),
    DemoUserSpec("nguyenvanc", "Nguyen Van C", Role.T),
    DemoUserSpec("nguyenvand", "Nguyen Van D", Role.T),
    DemoUserSpec("nguyenvane", "Nguyen Van E", Role.A),
    DemoUserSpec("nguyenvanf", "Nguyen Van F", Role.A),
    DemoUserSpec("nguyenvang", "Nguyen Van G", Role.A),
    DemoUserSpec("nguyenvanh", "Nguyen Van H", Role.A),
    DemoUserSpec("nguyenvani", "Nguyen Van I", Role.A),
    DemoUserSpec("nguyenvanj", "Nguyen Van J", Role.A),
)


def seed_demo_users(db: Session, password: str) -> dict[str, int]:
    """Create the 10 deterministic demo users if they do not already exist."""

    created = 0
    skipped = 0
    hashed_password = get_password_hash(password)

    for spec in DEMO_USERS:
        existing = db.query(User).filter(User.username == spec.username).one_or_none()
        if existing is not None:
            skipped += 1
            continue

        db.add(
            User(
                username=spec.username,
                full_name=spec.full_name,
                hashed_password=hashed_password,
                role=spec.role,
                status=UserStatus.active,
                code=next_user_code(db, spec.role),
            )
        )
        created += 1

    db.commit()
    return {"created": created, "skipped": skipped, "total": len(DEMO_USERS)}