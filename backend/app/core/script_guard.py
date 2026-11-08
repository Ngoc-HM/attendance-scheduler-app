"""Guard for the maintenance scripts in ``backend/scripts`` (#33).

``reset_all_passwords.py`` and ``seed_demo_users.py`` rewrite users in bulk.
They run only when ENVIRONMENT is ``dev`` AND the database is local (SQLite,
or a host on the loopback interface): a ``.env`` that says dev while pointing
at a shared/remote Postgres is refused too. ``--allow-non-dev`` overrides on
purpose. The refusal names the environment and the database host — never the
URL itself, which may carry the password.
"""

from __future__ import annotations

import sys
from typing import Protocol

from sqlalchemy.engine.url import make_url

LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})

# Exit code a script returns when the guard refuses.
REFUSED_EXIT_CODE = 2


class _ScriptSettings(Protocol):
    ENVIRONMENT: str
    DATABASE_URL: str


def is_local_database(url: str) -> bool:
    """True for SQLite or a server on this machine (localhost / 127.0.0.1 / ::1).

    A server URL without a host is NOT treated as local: libpq may still take
    the host from ``PGHOST``.
    """
    parsed = make_url(url)
    if parsed.get_backend_name() == "sqlite":
        return True
    return parsed.host in LOCAL_HOSTS


def refuse_unless_safe(settings: _ScriptSettings, allow: bool) -> int | None:
    """Return ``REFUSED_EXIT_CODE`` (after printing why) or None to proceed.

    Proceeds when ``allow`` is set (``--allow-non-dev``) or when
    ENVIRONMENT is dev and the database is local.
    """
    if allow or (
        settings.ENVIRONMENT == "dev" and is_local_database(settings.DATABASE_URL)
    ):
        return None
    host = make_url(settings.DATABASE_URL).host or "(none)"
    print(
        f"Refusing to run: ENVIRONMENT={settings.ENVIRONMENT}, database host={host}. "
        "These scripts run only against a local database (SQLite, localhost, "
        "127.0.0.1 or ::1) with ENVIRONMENT=dev. Re-run with --allow-non-dev "
        "if this is really intended.",
        file=sys.stderr,
    )
    return REFUSED_EXIT_CODE
