#!/usr/bin/env bash
# PostgreSQL backup for the Attendance & Auto-Scheduler database (spec §9.5).
#
#   DATABASE_URL=postgresql://user:pass@host:5432/attendance \
#     ./scripts/backup_db.sh [--encrypt-age RECIPIENT | --encrypt-gpg RECIPIENT] [dest_dir]
#
# Writes a pg_dump custom-format archive named attendance_<UTC timestamp>.dump
# into dest_dir (default ./backups) and prunes archives older than
# BACKUP_KEEP_DAYS (default 30). Restore with scripts/restore_db.sh.
#
# Credentials: the password is taken from DATABASE_URL and handed to pg_dump
# through the PGPASSWORD environment variable, never on the command line, and
# the URL is only ever printed with the password masked.
#
# Encryption (optional, recommended when the archive leaves this machine; keep
# the destination inside the EU region and encrypted at rest, spec §9.4):
#   --encrypt-age RECIPIENT  pipe the dump through `age -r RECIPIENT`
#                            (an age public key, age1...); writes *.dump.age
#   --encrypt-gpg RECIPIENT  pipe the dump through `gpg --encrypt -r RECIPIENT`
#                            (a key id or e-mail in the local keyring); writes *.dump.gpg
# The unencrypted dump never touches the disk when one of these is used.
set -euo pipefail

usage() {
  echo "Usage: $0 [--encrypt-age RECIPIENT | --encrypt-gpg RECIPIENT] [dest_dir]" >&2
  exit 2
}

ENCRYPT=""
RECIPIENT=""
DEST="./backups"
while [ $# -gt 0 ]; do
  case "$1" in
    --encrypt-age|--encrypt-gpg)
      [ -z "$ENCRYPT" ] || usage
      [ $# -ge 2 ] && [ -n "$2" ] || usage
      ENCRYPT="${1#--encrypt-}"
      RECIPIENT="$2"
      shift 2
      ;;
    -h|--help) usage ;;
    -*) usage ;;
    *) DEST="$1"; shift ;;
  esac
done

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
# Shown in logs: no password and no query string (it may carry password=).
SAFE_URL="postgresql://${url_user:+${url_user}${url_pass:+:***}@}${url_rest%%\?*}"
if [ -n "$url_pass" ]; then
  PGPASSWORD="$(urldecode "$url_pass")"
  export PGPASSWORD
fi
unset url_pass url_creds

# --- Dump -------------------------------------------------------------------
KEEP_DAYS="${BACKUP_KEEP_DAYS:-30}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
FILE="$DEST/attendance_${STAMP}.dump"

case "$ENCRYPT" in
  age) command -v age >/dev/null || { echo "age is not installed" >&2; exit 1; }; FILE="$FILE.age" ;;
  gpg) command -v gpg >/dev/null || { echo "gpg is not installed" >&2; exit 1; }; FILE="$FILE.gpg" ;;
esac

mkdir -p "$DEST"
umask 077
trap 'rm -f "$FILE"' ERR

echo "Backing up $SAFE_URL"
case "$ENCRYPT" in
  age) pg_dump --format=custom --no-owner "$PG_URL" | age -r "$RECIPIENT" -o "$FILE" ;;
  gpg) pg_dump --format=custom --no-owner "$PG_URL" \
         | gpg --batch --yes --encrypt --recipient "$RECIPIENT" --output "$FILE" ;;
  *)   pg_dump --format=custom --no-owner --file="$FILE" "$PG_URL" ;;
esac
trap - ERR
echo "Backup written: $FILE ($(du -h "$FILE" | cut -f1))"

find "$DEST" -name 'attendance_*.dump*' -mtime +"$KEEP_DAYS" -print -delete | sed 's/^/Pruned: /' || true
