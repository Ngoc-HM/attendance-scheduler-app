#!/usr/bin/env bash
# Restore a pg_dump archive produced by scripts/backup_db.sh.
#
#   DATABASE_URL=postgresql://user:pass@host:5432/attendance ./scripts/restore_db.sh backups/attendance_20260903T020000Z.dump
#
# Drops and recreates every object in the archive (--clean --if-exists), then
# prints the Alembic revision so you can confirm the schema matches the code
# (`alembic current` in backend/ should report the same head).
# Rehearse this on a staging database before relying on it (§9.5 recovery).
set -euo pipefail

: "${DATABASE_URL:?Set DATABASE_URL (postgresql://user:pass@host:port/db)}"
ARCHIVE="${1:?Usage: restore_db.sh <archive.dump>}"
[ -f "$ARCHIVE" ] || { echo "Archive not found: $ARCHIVE" >&2; exit 1; }

PG_URL="${DATABASE_URL/postgresql+psycopg2:\/\//postgresql://}"

read -r -p "This REPLACES the data in $PG_URL with $ARCHIVE. Type 'restore' to continue: " answer
[ "$answer" = "restore" ] || { echo "Aborted."; exit 1; }

pg_restore --clean --if-exists --no-owner --dbname="$PG_URL" "$ARCHIVE"
echo "Restore complete. Alembic revision in the restored database:"
psql "$PG_URL" -Atc "SELECT version_num FROM alembic_version" || echo "(no alembic_version table)"
