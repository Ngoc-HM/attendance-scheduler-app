"""Alembic on SQLite: fresh upgrade, data-carrying upgrade, ``%`` in the URL.

The migrations run in-process against throwaway SQLite files. The Config has
no ini file, so ``env.py`` skips ``fileConfig`` (which would disable the
``app.*`` loggers of the test process).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from alembic import command
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.enums import Role, UserStatus
from app.models.user import User

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _alembic_config() -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    return cfg


def _point_alembic_at(monkeypatch: pytest.MonkeyPatch, url: str) -> Config:
    # env.py reads the URL from the app settings (single source of truth).
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    return _alembic_config()


def test_sqlite_upgrade_head_then_insert(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A fresh SQLite database built by Alembic accepts ORM inserts: the
    ``created_at`` / ``updated_at`` server defaults must be valid SQLite."""
    url = f"sqlite:///{tmp_path / 'fresh.db'}"
    command.upgrade(_point_alembic_at(monkeypatch, url), "head")

    engine = create_engine(url)
    try:
        with Session(engine) as db:
            db.add(
                User(
                    username="fresh",
                    code="M1",
                    full_name="Fresh Admin",
                    hashed_password=get_password_hash("irrelevant-pw"),
                    role=Role.M,
                    status=UserStatus.active,
                )
            )
            db.commit()
            row = db.execute(
                text("SELECT created_at, updated_at FROM users WHERE username='fresh'")
            ).one()
        assert row[0] is not None and row[1] is not None
    finally:
        engine.dispose()


def test_sqlite_upgrade_with_data_from_0002_to_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Batch migrations (0003, 0008) recreate ``users`` on SQLite. With foreign
    keys enforced, dropping a referenced table fails, so env.py must switch
    them off around the run — existing rows and child rows must survive."""
    url = f"sqlite:///{tmp_path / 'aged.db'}"
    cfg = _point_alembic_at(monkeypatch, url)
    command.upgrade(cfg, "0002")

    engine = create_engine(url)  # the Engine connect hook turns FKs ON
    try:
        with engine.begin() as conn:
            stamp = "'2026-01-01 00:00:00'"
            conn.execute(text(
                "INSERT INTO users (id, username, full_name, hashed_password, role, "
                "status, annual_leave_balance, carry_comp, carry_streak, "
                f"created_at, updated_at) VALUES (1, 'boss', 'Boss', 'x', 'M', "
                f"'active', 0, 0, 0, {stamp}, {stamp}), (2, 'agent', 'Agent', 'x', "
                f"'A2', 'active', 0, 0, 0, {stamp}, {stamp})"
            ))
            conn.execute(text(
                "INSERT INTO monthly_schedules (id, year, month, status, created_at, "
                f"updated_at) VALUES (1, 2026, 1, 'draft', {stamp}, {stamp})"
            ))
            conn.execute(text(
                "INSERT INTO shift_assignments (schedule_id, user_id, work_date, code, "
                f"is_manual_override, created_at, updated_at) VALUES (1, 2, "
                f"'2026-01-05', 'A', 0, {stamp}, {stamp})"
            ))
            conn.execute(text(
                "INSERT INTO leave_requests (user_id, start_date, end_date, leave_type, "
                f"status, created_at, updated_at) VALUES (2, '2026-01-10', "
                f"'2026-01-11', 'monthly', 'approved', {stamp}, {stamp})"
            ))
            conn.execute(text(
                "INSERT INTO audit_logs (actor_id, action, entity, created_at) "
                f"VALUES (1, 'user.create', 'User', {stamp})"
            ))
    finally:
        engine.dispose()

    command.upgrade(cfg, "head")

    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            users = conn.execute(
                text("SELECT id, role, code FROM users ORDER BY id")
            ).all()
            assert [(u[0], u[1]) for u in users] == [(1, "M"), (2, "A")]
            assert all(u[2] for u in users)
            assert conn.execute(text("SELECT count(*) FROM shift_assignments")).scalar() == 1
            assert conn.execute(text("SELECT count(*) FROM leave_requests")).scalar() == 1
            # Nothing dangling after the table rebuilds.
            assert conn.execute(text("PRAGMA foreign_key_check")).all() == []
        assert "annual_leave_quota" in {
            c["name"] for c in inspect(engine).get_columns("users")
        }
    finally:
        engine.dispose()


def test_alembic_url_with_percent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A '%' in DATABASE_URL (URL-encoded password, odd path) must not break
    Alembic: its config is a ConfigParser, where '%' starts an interpolation."""
    folder = tmp_path / "50%off"
    folder.mkdir()
    url = f"sqlite:///{folder / 'pct.db'}"
    command.upgrade(_point_alembic_at(monkeypatch, url), "head")

    engine = create_engine(url)
    try:
        assert inspect(engine).has_table("alembic_version")
        assert inspect(engine).has_table("users")
    finally:
        engine.dispose()
    assert (folder / "pct.db").exists()


def test_0013_backfills_the_colleague_answer_of_existing_swaps(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0013: an approved swap counts as accepted by the colleague, a pending
    one now waits for them; a rejected swap and every code change stay NULL."""
    url = f"sqlite:///{tmp_path / 'swaps.db'}"
    cfg = _point_alembic_at(monkeypatch, url)
    command.upgrade(cfg, "0012")

    engine = create_engine(url)
    try:
        with Session(engine) as db:
            for uid, code in ((1, "A1"), (2, "A2")):
                db.add(User(
                    id=uid, username=f"u{uid}", code=code, full_name=f"U{uid}",
                    hashed_password="x", role=Role.A, status=UserStatus.active,
                ))
            db.commit()
        with engine.begin() as conn:
            stamp = "'2026-01-01 00:00:00'"
            rows = [
                (1, "swap_with", "pending"), (2, "swap_with", "approved"),
                (3, "swap_with", "rejected"), (4, "change_code", "pending"),
            ]
            for rid, kind, status in rows:
                counterpart = "2" if kind == "swap_with" else "NULL"
                requested = "NULL" if kind == "swap_with" else "'X'"
                conn.execute(text(
                    "INSERT INTO shift_change_requests (id, requester_id, work_date, "
                    "kind, requested_code, counterpart_user_id, status, created_at, "
                    f"updated_at) VALUES ({rid}, 1, '2026-01-0{rid}', '{kind}', "
                    f"{requested}, {counterpart}, '{status}', {stamp}, {stamp})"
                ))
    finally:
        engine.dispose()

    command.upgrade(cfg, "head")

    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            got = conn.execute(text(
                "SELECT id, counterpart_status, counterpart_decided_at "
                "FROM shift_change_requests ORDER BY id"
            )).all()
        assert [(r[0], r[1]) for r in got] == [
            (1, "pending"), (2, "approved"), (3, None), (4, None),
        ]
        assert all(r[2] is None for r in got)
    finally:
        engine.dispose()
