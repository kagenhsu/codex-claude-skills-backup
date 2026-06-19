#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
python3 "$SCRIPT_DIR/scripts/install_claude_quota_bridge.py" >/dev/null 2>&1 || true
chmod +x "$SCRIPT_DIR/scripts/claude_quota_statusline.sh" >/dev/null 2>&1 || true
chmod +x "$SCRIPT_DIR/scripts/quota_guard_snapshot.py" >/dev/null 2>&1 || true

# 先收掉先前的浮動窗，避免重複開導致新視窗被擋。
pkill -f "quota_guard_floating.swift" >/dev/null 2>&1 || true
sleep 0.3

# 用 nohup + disown 把 swift 從 Terminal 解綁，
# 這樣使用者關掉自動跳出的 Terminal 視窗，浮動窗也能繼續活著。
nohup swift "$SCRIPT_DIR/scripts/quota_guard_floating.swift" >/tmp/quota-guard.log 2>&1 &
disown

# 給 swift 一點時間把視窗推到前景，再讓 Terminal 視窗自行收掉。
sleep 1
