#!/usr/bin/env bash
# 把「開機自動啟動本地控制台 + 桌面浮動小視窗」裝成 macOS LaunchAgent。
# 使用者只要跑一次：登入完成後，OS 會自動把兩個東西跑起來。
#
# Why LaunchAgent 不用 Login Items：
# - Login Items 一定會經過 Finder/Terminal，會在登入後跳出黑色 Terminal 視窗
# - LaunchAgent 純背景跑，使用者只會看到瀏覽器分頁跟浮動小視窗，乾淨
# - LaunchAgent 可以靠 launchctl 重新觸發、除錯也方便

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PAYLOAD_SOURCE="$REPO_DIR/scripts/autostart_macos_payload.sh"
RUNTIME_DIR="$HOME/Library/Application Support/QuotaGuardian"
REPO_NAME="$(basename "$REPO_DIR")"
RUNTIME_REPO_DIR="$RUNTIME_DIR/runtime/$REPO_NAME"
PAYLOAD="$RUNTIME_DIR/autostart_macos_payload.sh"

if [[ ! -f "$PAYLOAD_SOURCE" ]]; then
  echo "找不到 $PAYLOAD_SOURCE，安裝中止。" >&2
  exit 1
fi
mkdir -p "$RUNTIME_DIR"
cp "$PAYLOAD_SOURCE" "$PAYLOAD"
chmod +x "$PAYLOAD"

# launchd 直接碰 ~/Documents 內的腳本與 Python 檔在部分機器會被 TCC 擋掉，
# 所以安裝時先同步一份 runtime 到 ~/Library/Application Support/QuotaGuardian/runtime。
mkdir -p "$RUNTIME_REPO_DIR"
/usr/bin/rsync -a --delete \
  --exclude '.git/' \
  --exclude '.playwright-cli/' \
  --exclude '.handoff-now.md' \
  --exclude '.handoff-now.bak.md' \
  "$REPO_DIR/" "$RUNTIME_REPO_DIR/"

LABEL="com.kagenhsu.quota-guardian.autostart"
PLIST_PATH="$HOME/Library/LaunchAgents/${LABEL}.plist"
LOG_DIR="$HOME/Library/Logs/QuotaGuardian"
mkdir -p "$LOG_DIR" "$HOME/Library/LaunchAgents"

# 如果已經有同 label 的 LaunchAgent 在跑，先卸載，避免重複註冊。
launchctl bootout "gui/$(id -u)" "$PLIST_PATH" >/dev/null 2>&1 || true

cat >"$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>${PAYLOAD}</string>
        <string>${RUNTIME_REPO_DIR}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>${LOG_DIR}/launchagent.out.log</string>
    <key>StandardErrorPath</key>
    <string>${LOG_DIR}/launchagent.err.log</string>
    <key>ProcessType</key>
    <string>Interactive</string>
</dict>
</plist>
PLIST

# 註冊並立即跑一次，讓使用者馬上看到效果。
launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"
launchctl kickstart -k "gui/$(id -u)/${LABEL}" >/dev/null 2>&1 || true

echo "✅ 已安裝開機自動啟動：${LABEL}"
echo "    plist:  ${PLIST_PATH}"
echo "    log:    ${LOG_DIR}/autostart.log"
echo "    runtime:${RUNTIME_REPO_DIR}"
echo
echo "現在已經為你跑了一次，請看："
echo "  - 瀏覽器是否打開 127.0.0.1:7000~7999 之間的本地控制台網址"
echo "  - 右側是否出現「配額守門員」浮動小視窗"
echo
echo "之後每次登入都會自動跑。要移除請執行："
echo "  ${REPO_DIR}/移除開機自動啟動\\ \\(macOS\\).command"
