#!/usr/bin/env bash
set -euo pipefail

URL="${1:-}"
if [[ -z "$URL" ]]; then
  exit 64
fi

CHROME_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PROFILE_DIR="$HOME/Library/Application Support/QuotaGuardian/chrome-local-console-profile"

if [[ -x "$CHROME_BIN" ]]; then
  mkdir -p "$PROFILE_DIR"
  "$CHROME_BIN" \
    --user-data-dir="$PROFILE_DIR" \
    --new-window \
    "$URL" \
    --disable-extensions \
    --no-first-run \
    --no-default-browser-check \
    >/dev/null 2>&1 &
  /usr/bin/osascript -e 'tell application "Google Chrome" to activate' >/dev/null 2>&1 || true
  exit 0
fi

if /usr/bin/osascript -e "tell application \"Safari\" to open location \"$URL\"" >/dev/null 2>&1; then
  exit 0
fi

/usr/bin/open "$URL"
