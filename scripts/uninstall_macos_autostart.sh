#!/usr/bin/env bash
set -euo pipefail

LABEL="com.kagenhsu.quota-guardian.autostart"
PLIST_PATH="$HOME/Library/LaunchAgents/${LABEL}.plist"
RUNTIME_DIR="$HOME/Library/Application Support/QuotaGuardian"
RUNTIME_REPO_DIR="$RUNTIME_DIR/runtime/codex-claude-skills-backup"

if [[ -f "$PLIST_PATH" ]]; then
  launchctl bootout "gui/$(id -u)" "$PLIST_PATH" >/dev/null 2>&1 || true
  rm -f "$PLIST_PATH"
  echo "✅ 已移除開機自動啟動：${LABEL}"
else
  echo "ℹ️  本機沒有安裝 ${LABEL}，不需要移除。"
fi

# 把目前還活著的桌面浮動小視窗也收掉，恢復「乾淨狀態」。
/usr/bin/pkill -f "quota_guard_floating.swift" >/dev/null 2>&1 || true
/usr/bin/pkill -f "serve_console.py.*codex-claude-skills-backup" >/dev/null 2>&1 || true
rm -f "$RUNTIME_DIR/autostart_macos_payload.sh"
rm -rf "$RUNTIME_REPO_DIR"
if [[ -d "$RUNTIME_DIR/runtime" ]] && [[ -z "$(find "$RUNTIME_DIR/runtime" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
  rmdir "$RUNTIME_DIR/runtime" >/dev/null 2>&1 || true
fi

echo
echo "提醒：本地控制台網址（serve_console.py）若還在背景跑，"
echo "可以用：lsof -nP -iTCP -sTCP:LISTEN | grep 127.0.0.1 找到對應 port / PID 後 kill。"
