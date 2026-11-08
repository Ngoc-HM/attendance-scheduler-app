#!/usr/bin/env bash
# Restore a pg_dump archive produced by scripts/backup_db.sh.
#
#   DATABASE_URL=postgresql://user:pass@host:5432/attendance \
#     ./scripts/restore_db.sh [--age-identity KEYFILE] backups/attendance_20260903T020000Z.dump[.age|.gpg]
#
# Drops and recreates every object in the archive (--clean --if-exists), then
# prints the Alembic revision so you can confirm the schema matches the code
# (`alembic current` in backend/ should report the same head).
# Rehearse this on a staging database before relying on it (§9.5 recovery).
#
# Credentials: the password is taken from DATABASE_URL and handed to
# pg_restore/psql through the PGPASSWORD environment variable, never on the
# command line, and the URL is only ever printed with the password masked.
#
# Encrypted archives (see backup_db.sh --encrypt-age / --encrypt-gpg):
#   *.dump.age  decrypted with `age -d -i KEYFILE`; pass --age-identity KEYFILE
#               (or set AGE_IDENTITY)
#   *.dump.gpg  decrypted with `gpg --decrypt` using the local keyring
# The decrypted dump is streamed into pg_restore and never written to disk.
set -euo pipefail

usage() {
  echo "Usage: $0 [--age-identity KEYFILE] <archive.dump[.age|.gpg]>" >&2
  exit 2
}

AGE_KEY="${AGE_IDENTITY:-}"
ARCHIVE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --age-identity) [ $# -ge 2 ] && [ -n "$2" ] || usage; AGE_KEY="$2"; shift 2 ;;
    -h|--help) usage ;;
    -*) usage ;;
    *) [ -z "$ARCHIVE" ] || usage; ARCHIVE="$1"; shift ;;
  esac
done
[ -n "$ARCHIVE" ] || usage
[ -f "$ARCHIVE" ] || { echo "Archive not found: $ARCHIVE" >&2; exit 1; }

: "${DATABASE_URL:?Set DATABASE_URL (postgresql://user:pass@host:port/db)}"

# --- Split DATABASE_URL into a password-free libpq URL + PGPASSWORD ---------
urldecode() {
  local s="${1//\\/\\\\}"
  printf '%b' "${s//%/\\x}"
}

case "$DATABASE_URL" in
  postgres://*|postgresql://*|postgresql+*://*) ;;
  *) echo "DATABASE_URL must be a PostgreSQL URL (postgresql://...)" >&2; exit 1 ;;
esac
url_rest="${DATABASE_URL#*://}"
# A password in the query string would end up on the pg tools' command line.
if [[ "$url_rest" == *\?* ]] && [[ "&${url_rest#*\?}" == *"&password="* ]]; then
  echo "DATABASE_URL must not carry password= in its query string; put the password in user:password@host" >&2
  exit 1
fi
url_user=""
url_pass=""
if [[ "$url_rest" == *@* ]]; then
  url_creds="${url_rest%@*}"
  url_rest="${url_rest##*@}"
  url_user="${url_creds%%:*}"
  [[ "$url_creds" == *:* ]] && url_pass="${url_creds#*:}"
fi
# libpq does not understand SQLAlchemy driver suffixes (postgresql+psycopg2).
PG_URL="postgresql://${url_user:+${url_user}@}${url_rest}"
# Shown to the operator: no password and no query string (it may carry password=).
SAFE_URL="postgresql://${url_user:+${url_user}${url_pass:+:***}@}${url_rest%%\?*}"
if [ -n "$url_pass" ]; then
  PGPASSWORD="$(urldecode "$url_pass")"
  export PGPASSWORD
fi
unset url_pass url_creds

# --- Restore ----------------------------------------------------------------
case "$ARCHIVE" in
  *.age)
    command -v age >/dev/null || { echo "age is not installed" >&2; exit 1; }
    [ -n "$AGE_KEY" ] || { echo "Encrypted archive: pass --age-identity KEYFILE (or set AGE_IDENTITY)" >&2; exit 1; }
    ;;
  *.gpg)
    command -v gpg >/dev/null || { echo "gpg is not installed" >&2; exit 1; }
    ;;
esac

read -r -p "This REPLACES the data in $SAFE_URL with $ARCHIVE. Type 'restore' to continue: " answer
[ "$answer" = "restore" ] || { echo "Aborted."; exit 1; }

case "$ARCHIVE" in
  *.age) age -d -i "$AGE_KEY" "$ARCHIVE" | pg_restore --clean --if-exists --no-owner --dbname="$PG_URL" ;;
  *.gpg) gpg --batch --decrypt "$ARCHIVE" | pg_restore --clean --if-exists --no-owner --dbname="$PG_URL" ;;
  *)     pg_restore --clean --if-exists --no-owner --dbname="$PG_URL" "$ARCHIVE" ;;
esac
echo "Restore complete. Alembic revision in the restored database:"
psql "$PG_URL" -Atc "SELECT version_num FROM alembic_version" || echo "(no alembic_version table)"
