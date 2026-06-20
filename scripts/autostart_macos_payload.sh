#!/usr/bin/env bash
# 由 LaunchAgent 在使用者登入時呼叫。負責：
# 1. 更新本地控制台靜態檔
# 2. 把本地控制台網址 (serve_console.py) 跑成 detached daemon
# 3. 把桌面浮動小視窗 (quota_guard_floating.swift) 跑成 detached daemon
# 4. 等本地網址真的 listen 起來，再打開瀏覽器分頁
#
# 重點設計：完全不依賴 Terminal.app，所以開機後不會跳 Terminal 視窗。
# 失敗訊息一律寫進 ~/Library/Logs/QuotaGuardian/autostart.log，
# 使用者按 launcher 沒看到視窗時，第一手 debug 看那個檔案。

set -u

REPO_DIR="${1:-}"
if [[ -z "$REPO_DIR" || ! -d "$REPO_DIR" ]]; then
  echo "[autostart] missing or invalid REPO_DIR: $REPO_DIR" >&2
  exit 64
fi

LOG_DIR="$HOME/Library/Logs/QuotaGuardian"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/autostart.log"
URL_FILE="$LOG_DIR/console-url.txt"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$LOG_FILE"
}

# LaunchAgent 環境通常只有 /usr/bin:/bin:/usr/sbin:/sbin，先補上 Homebrew 常見路徑與
# CommandLineTools，避免 swift / python3 找不到。
export PATH="/opt/homebrew/bin:/usr/local/bin:/Library/Developer/CommandLineTools/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"

log "==== autostart 觸發，REPO_DIR=$REPO_DIR ===="

cd "$REPO_DIR" || { log "cd 失敗"; exit 65; }

PYTHON_BIN="$(command -v python3 || true)"
SWIFT_BIN="$(command -v swift || true)"

if [[ -z "$PYTHON_BIN" ]]; then
  log "找不到 python3，無法啟動本地控制台。"
  exit 66
fi

# 1. 更新控制台靜態檔（失敗不擋；之前產出的舊 index.html 還是能用）
if ! "$PYTHON_BIN" "$REPO_DIR/scripts/build.py" >>"$LOG_FILE" 2>&1; then
  log "build.py 失敗，繼續用舊版 index.html。"
fi

# 2. 控制台：固定避開常見 8000，改從 7000~7999 內挑第一個可用埠。
PORT_START=7000
PORT_TRIES=1000

# 舊的同 repo serve_console 先收掉，避免重複 instance 搶不同 port。
/usr/bin/pkill -f "$REPO_DIR/scripts/serve_console.py" >/dev/null 2>&1 || true
sleep 0.3

log "啟動 serve_console.py（背景，port ${PORT_START}~$((PORT_START + PORT_TRIES - 1))）"
rm -f "$URL_FILE"
nohup "$PYTHON_BIN" "$REPO_DIR/scripts/serve_console.py" \
  --root "$REPO_DIR" \
  --host 127.0.0.1 \
  --port "$PORT_START" \
  --tries "$PORT_TRIES" \
  --write-url-file "$URL_FILE" \
  >> "$LOG_DIR/serve_console.log" 2>&1 &
disown

# 等 serve_console 真的把 URL 寫出來且 listen 起來，最多等 8 秒。
URL=""
for i in 1 2 3 4 5 6 7 8; do
  if [[ -f "$URL_FILE" ]]; then
    URL="$(tr -d '\r\n' < "$URL_FILE")"
  fi
  if [[ -n "$URL" ]] && /usr/bin/curl -sf --max-time 1 "$URL" >/dev/null 2>&1; then
    log "serve_console.py 已 ready (try=$i, url=$URL)"
    break
  fi
  sleep 1
done

if [[ -n "$URL" ]] && /usr/bin/curl -sf --max-time 1 "$URL" >/dev/null 2>&1; then
  log "打開瀏覽器：$URL"
  /usr/bin/open "$URL" >>"$LOG_FILE" 2>&1 || log "open 瀏覽器失敗"
else
  log "serve_console.py 8 秒內沒 ready；不開瀏覽器以免出現錯誤分頁。"
fi

# 3. 桌面浮動小視窗：之前殘留的先收掉再重啟一次，確保資料是新的。
if [[ -n "$SWIFT_BIN" ]]; then
  /usr/bin/pkill -f "quota_guard_floating.swift" >/dev/null 2>&1 || true
  sleep 0.3
  log "啟動 quota_guard_floating.swift（背景）"
  nohup "$SWIFT_BIN" "$REPO_DIR/scripts/quota_guard_floating.swift" \
    >> "$LOG_DIR/floating.log" 2>&1 &
  disown
else
  log "找不到 swift，跳過桌面浮動小視窗。請執行 xcode-select --install。"
fi

log "==== autostart 完成 ===="
exit 0
