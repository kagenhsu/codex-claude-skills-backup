#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_REPO_DIR="$HOME/Library/Application Support/QuotaGuardian/runtime/codex-claude-skills-backup"
cd "$SCRIPT_DIR"
python3 "$SCRIPT_DIR/scripts/install_claude_quota_bridge.py" >/dev/null 2>&1 || true
chmod +x "$SCRIPT_DIR/scripts/claude_quota_statusline.sh" >/dev/null 2>&1 || true
chmod +x "$SCRIPT_DIR/scripts/quota_guard_snapshot.py" >/dev/null 2>&1 || true

# 如果這台 Mac 已經裝了開機自動啟動版本，先把關鍵腳本同步到 runtime，
# 避免手動開啟與自動啟動讀到不同版本的浮動窗邏輯。
if [[ -d "$RUNTIME_REPO_DIR/scripts" ]]; then
  /usr/bin/rsync -a \
    "$SCRIPT_DIR/scripts/quota_guard_floating.swift" \
    "$SCRIPT_DIR/scripts/quota_guard_snapshot.py" \
    "$RUNTIME_REPO_DIR/scripts/" >/dev/null 2>&1 || true
fi

# 先收掉先前的浮動窗，避免重複開導致新視窗被擋。
pkill -f "quota_guard_floating.swift" >/dev/null 2>&1 || true
sleep 0.3

# 用 nohup + disown 把 swift 從 Terminal 解綁，
# 這樣使用者關掉自動跳出的 Terminal 視窗，浮動窗也能繼續活著。
if [[ -f "$RUNTIME_REPO_DIR/scripts/quota_guard_floating.swift" ]]; then
  nohup swift "$RUNTIME_REPO_DIR/scripts/quota_guard_floating.swift" >/tmp/quota-guard.log 2>&1 &
else
  nohup swift "$SCRIPT_DIR/scripts/quota_guard_floating.swift" >/tmp/quota-guard.log 2>&1 &
fi
disown

# 給 swift 一點時間把視窗推到前景，再讓 Terminal 視窗自行收掉。
sleep 1

# 某些多螢幕 / Space 座標下，Swift 視窗會真的啟動但落在畫面外。
# 這裡用 System Events 做最後一道保險，把它拉回主畫面可視區。
/usr/bin/osascript <<'APPLESCRIPT' >/dev/null 2>&1 || true
tell application "System Events"
  tell process "swift-frontend"
    set frontmost to true
    try
      set position of window "配額守門員" to {900, 80}
    end try
  end tell
end tell
APPLESCRIPT
