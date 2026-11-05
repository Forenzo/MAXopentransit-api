#!/usr/bin/env bash
# Fetch one or more GTFS feeds. Existing cities continue using GTFS_URL alone.
# When GTFS_SOURCES is defined it contains newline-separated "feedId|https://..." entries.
# Each feed stays an independent OTP feed so its original IDs remain intact and
# future GTFS-Realtime trip IDs can be reconciled against their proper feed.
set -euo pipefail
CITY="${1:?city required}"
SOURCE_FILE="${2:?sources.env required}"
DATA="${3:?output directory required}"
FORCE="${4:-}"
# shellcheck disable=SC1090
source "$SOURCE_FILE"
mkdir -p "$DATA"
download() {
  local id="$1" url="$2" dest="$3" tmp
  if [ -z "$FORCE" ] && [ -s "$dest" ] && [ -z "$(find "$dest" -mtime +1 2>/dev/null)" ]; then
    echo "[gtfs] using cached $id: $dest"
    return
  fi
  tmp="$dest.partial.$$"
  trap 'rm -f "$tmp"' EXIT
  curl -fsSL --retry 3 --connect-timeout 30 -o "$tmp" "$url"
  python3 - "$tmp" <<'PY'
import sys, zipfile
with zipfile.ZipFile(sys.argv[1]) as archive:
    names = {item.filename.lower().rsplit("/", 1)[-1] for item in archive.infolist()}
    missing = {"stops.txt", "routes.txt", "trips.txt", "stop_times.txt"} - names
    if missing:
        raise SystemExit(f"not a usable GTFS ZIP: missing {sorted(missing)}")
    bad = archive.testzip()
    if bad:
        raise SystemExit(f"corrupt GTFS ZIP member: {bad}")
PY
  mv "$tmp" "$dest"
  trap - EXIT
  echo "[gtfs] downloaded $id"
}
if [ -z "${GTFS_SOURCES:-}" ]; then
  download "$CITY" "$GTFS_URL" "$DATA/$CITY-gtfs.zip"
else
  seen=" "
  count=0
  while IFS='|' read -r id url || [ -n "$id" ]; do
    [ -z "$id" ] && continue
    case "$id" in \#*) continue;; esac
    [[ "$id" =~ ^[a-z][a-z0-9_-]*$ ]] || { echo "unsafe GTFS feed ID: $id" >&2; exit 1; }
    [[ "$url" =~ ^https?://[^[:space:]]+$ ]] || { echo "invalid GTFS URL for $id" >&2; exit 1; }
    case "$seen" in *" $id "*) echo "duplicate feed ID: $id" >&2; exit 1;; esac
    seen="$seen$id "
    download "$id" "$url" "$DATA/$id-gtfs.zip"
    count=$((count+1))
  done <<< "$GTFS_SOURCES"
  [ "$count" -gt 0 ] || { echo "GTFS_SOURCES is empty" >&2; exit 1; }
  if [ -n "${PRIMARY_GTFS_FEED:-}" ]; then
    [ -f "$DATA/${PRIMARY_GTFS_FEED}-gtfs.zip" ] || { echo "primary feed missing" >&2; exit 1; }
    cp "$DATA/${PRIMARY_GTFS_FEED}-gtfs.zip" "$DATA/$CITY-gtfs.zip"
  fi
fi
