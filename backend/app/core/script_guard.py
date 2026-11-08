"""Guard for the maintenance scripts in ``backend/scripts`` (#33).

``reset_all_passwords.py`` and ``seed_demo_users.py`` rewrite users in bulk.
They run only when ENVIRONMENT is ``dev`` AND the database is local (SQLite,
or a host on the loopback interface): a ``.env`` that says dev while pointing
at a shared/remote Postgres is refused too. ``--allow-non-dev`` overrides on
purpose. The refusal names the environment and the database host — never the
URL itself, which may carry the password.

Also shared by the scripts: ``load_backend_env`` reads ``backend/.env`` by an
absolute path (the settings read ``.env`` relative to the cwd, so a script
started from the repo root silently fell back to the defaults), and
``read_password`` prompts with getpass so the password stays out of the shell
history and the process list.
"""

from __future__ import annotations

import getpass
import sys
from pathlib import Path
from typing import Protocol

from sqlalchemy.engine.url import make_url

LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
# libpq connection parameters that choose the server and win over the URL's
# host when given in the query string (``...@localhost/db?host=remote``).
_HOST_OVERRIDE_PARAMS = frozenset({"host", "hostaddr", "service"})

# Exit code a script returns when the guard refuses.
REFUSED_EXIT_CODE = 2


class _ScriptSettings(Protocol):
    ENVIRONMENT: str
    DATABASE_URL: str


def is_local_database(url: str) -> bool:
    """True for SQLite or a server on this machine (localhost / 127.0.0.1 / ::1).

    A server URL without a host is NOT treated as local: libpq may still take
    the host from ``PGHOST``. Neither is one whose query string names the
    server (``host``, ``hostaddr``, ``service``): libpq connects there instead.
    """
    parsed = make_url(url)
    if parsed.get_backend_name() == "sqlite":
        return True
    if any(key.lower() in _HOST_OVERRIDE_PARAMS for key in parsed.query):
        return False
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
    parsed = make_url(settings.DATABASE_URL)
    query_hosts = [
        f"{key}={value}"
        for key, value in parsed.query.items()
        if key.lower() in _HOST_OVERRIDE_PARAMS
    ]
    host = ", ".join([parsed.host or "(none)", *query_hosts])
    print(
        f"Refusing to run: ENVIRONMENT={settings.ENVIRONMENT}, database host={host}. "
        "These scripts run only against a local database (SQLite, localhost, "
        "127.0.0.1 or ::1) with ENVIRONMENT=dev. Re-run with --allow-non-dev "
        "if this is really intended.",
        file=sys.stderr,
    )
    return REFUSED_EXIT_CODE


def load_backend_env(env_file: Path) -> bool:
    """Load ``env_file`` into ``os.environ`` without overriding variables the
    shell already set (the same precedence as the settings). Call it before
    importing ``app.core.config``. Returns False when the file is missing."""
    if not env_file.is_file():
        return False
    from dotenv import load_dotenv

    load_dotenv(env_file, override=False)
    return True


def read_password(cli_value: str | None) -> str | None:
    """The ``--password`` value, else a getpass prompt (asked twice).

    Returns None (after printing why, never the password) when the two
    entries differ or are empty.
    """
    if cli_value is not None:
        return cli_value
    first = getpass.getpass("New password: ")
    second = getpass.getpass("Repeat password: ")
    if not first:
        print("Refusing to run: the password is empty.", file=sys.stderr)
        return None
    if first != second:
        print("Refusing to run: the two passwords do not match.", file=sys.stderr)
        return None
    return first
