#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

"$SCRIPT_DIR/開啟配額守門員.command" >/tmp/quota-guard.log 2>&1 &
exec "$SCRIPT_DIR/更新並開啟控制台.command"
