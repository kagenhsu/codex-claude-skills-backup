#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "正在更新二刀流開發助手控制台..."
python3 scripts/build.py

echo "正在開啟控制台..."
open index.html
