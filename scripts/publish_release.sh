#!/usr/bin/env bash
# Build the three desktop clients and publish them as the newest update.
# Run on a Mac from a clean, pushed `main`:
#
#   scripts/publish_release.sh [--min-build N] [--notes "Text shown in the app"]
#
# 1. build number = commit count of HEAD (the same in every build);
# 2. Windows installer + Linux bundle on GitHub Actions (desktop-release.yml),
#    the macOS app here;
# 3. copies them to the server's releases/<build>/ and replaces latest.json
#    last, so a running app never sees a manifest whose files are missing.
# Running apps notice it within an hour (or at their next start) and offer the
# update; with --min-build, older builds must update before they can be used.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVER="${RELEASE_SERVER:-trunggian@160.187.228.64}"
REMOTE_DIR="${RELEASE_DIR:-attendance-scheduler/releases}"
API_URL="${RELEASE_API_URL:-http://160.187.228.64/api/v1}"
MIN_BUILD=0
NOTES=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --min-build) MIN_BUILD="$2"; shift 2 ;;
    --notes) NOTES="$2"; shift 2 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

cd "$ROOT"
[[ -z "$(git status --porcelain)" ]] || { echo "working tree not clean" >&2; exit 1; }
git fetch -q origin main
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]] ||
  { echo "HEAD is not the pushed origin/main" >&2; exit 1; }
BUILD="$(git rev-list --count HEAD)"
OUT="$ROOT/dist/$BUILD"
echo ">> build $BUILD"

gh workflow run desktop-release.yml -f api_base_url="$API_URL" -f build_number="$BUILD"
sleep 8
RUN_ID="$(gh run list --workflow desktop-release.yml --limit 1 --json databaseId -q '.[0].databaseId')"

(cd attendance_scheduler_app && flutter build macos --release \
  --build-name=1.0.0 --build-number="$BUILD" \
  --dart-define=API_BASE_URL="$API_URL" --dart-define=APP_BUILD="$BUILD")

gh run watch "$RUN_ID" --exit-status --interval 30 >/dev/null
rm -rf "$OUT" && mkdir -p "$OUT/ci"
gh run download "$RUN_ID" -D "$OUT/ci"
ditto -c -k --keepParent \
  attendance_scheduler_app/build/macos/Build/Products/Release/attendance_scheduler_app.app \
  "$OUT/attendance-scheduler-macos.zip"
cp "$OUT/ci/attendance-scheduler-windows-setup/RosterFRA-Setup.exe" "$OUT/"
cp "$OUT/ci/attendance-scheduler-linux-x64/attendance-scheduler-linux-x64.tar.gz" "$OUT/"
rm -rf "$OUT/ci"

sha() { shasum -a 256 "$1" | cut -d' ' -f1; }
python3 - "$OUT/latest.json" "$BUILD" "$MIN_BUILD" "$NOTES" \
  "$(sha "$OUT/RosterFRA-Setup.exe")" \
  "$(sha "$OUT/attendance-scheduler-macos.zip")" \
  "$(sha "$OUT/attendance-scheduler-linux-x64.tar.gz")" <<'PY'
import json, sys
path, build, min_build, notes, win, mac, lin = sys.argv[1:]
json.dump({
    "build": int(build), "version": "1.0.0", "min_build": int(min_build),
    "notes": notes,
    "files": {"windows": f"{build}/RosterFRA-Setup.exe",
              "macos": f"{build}/attendance-scheduler-macos.zip",
              "linux": f"{build}/attendance-scheduler-linux-x64.tar.gz"},
    "sha256": {"windows": win, "macos": mac, "linux": lin},
}, open(path, "w"), ensure_ascii=False, indent=2)
PY

ssh "$SERVER" "mkdir -p '$REMOTE_DIR/$BUILD'"
scp -q "$OUT"/RosterFRA-Setup.exe "$OUT"/attendance-scheduler-macos.zip \
  "$OUT"/attendance-scheduler-linux-x64.tar.gz "$SERVER:$REMOTE_DIR/$BUILD/"
scp -q "$OUT/latest.json" "$SERVER:$REMOTE_DIR/latest.json.new"
ssh "$SERVER" "mv '$REMOTE_DIR/latest.json.new' '$REMOTE_DIR/latest.json'"
echo ">> published build $BUILD (files in $OUT)"
curl -s "$API_URL/app/latest"; echo
