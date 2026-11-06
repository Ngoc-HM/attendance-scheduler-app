#!/usr/bin/env bash
# PostgreSQL backup for the Attendance & Auto-Scheduler database (spec §9.5).
#
#   DATABASE_URL=postgresql://user:pass@host:5432/attendance ./scripts/backup_db.sh [dest_dir]
#
# Writes a pg_dump custom-format archive named attendance_<UTC timestamp>.dump
# into dest_dir (default ./backups) and prunes archives older than
# BACKUP_KEEP_DAYS (default 30). Keep the destination inside the EU region and
# encrypted at rest (§9.4). Restore with scripts/restore_db.sh.
set -euo pipefail

: "${DATABASE_URL:?Set DATABASE_URL (postgresql://user:pass@host:port/db)}"
DEST="${1:-./backups}"
KEEP_DAYS="${BACKUP_KEEP_DAYS:-30}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
FILE="$DEST/attendance_${STAMP}.dump"

# SQLAlchemy-style URLs (postgresql+psycopg2://) are not understood by libpq.
PG_URL="${DATABASE_URL/postgresql+psycopg2:\/\//postgresql://}"

mkdir -p "$DEST"
pg_dump --format=custom --no-owner --file="$FILE" "$PG_URL"
echo "Backup written: $FILE ($(du -h "$FILE" | cut -f1))"

find "$DEST" -name 'attendance_*.dump' -mtime +"$KEEP_DAYS" -print -delete | sed 's/^/Pruned: /' || true
