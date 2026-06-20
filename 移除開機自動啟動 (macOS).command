#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

bash "$SCRIPT_DIR/scripts/uninstall_macos_autostart.sh"

printf '\n按 Enter 關閉視窗...'
read -r _
