#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$HOME/Library/Logs/QuotaGuardian"
URL_FILE="$LOG_DIR/manual-console-url.txt"
SERVE_LOG="$LOG_DIR/manual-serve.log"

mkdir -p "$LOG_DIR"

pause_on_exit() {
  printf '\n按 Enter 關閉視窗...'
  read -r _
}

cleanup() {
  if [[ -n "${SERVE_PID:-}" ]]; then
    kill "$SERVE_PID" >/dev/null 2>&1 || true
  fi
}

open_console_url() {
  local url="$1"
  local opener="$SCRIPT_DIR/scripts/open_console_browser_macos.sh"
  if [[ -x "$opener" ]]; then
    "$opener" "$url"
    return $?
  fi
  /usr/bin/open "$url"
}

if ! command -v python3 >/dev/null 2>&1; then
  echo "找不到 python3，無法更新控制台。"
  echo "請先安裝 Python 3，或直接雙擊 index.html 開啟舊版控制台。"
  pause_on_exit
  exit 1
fi

echo "正在更新二刀流開發助手控制台..."
if ! python3 "$SCRIPT_DIR/scripts/build.py"; then
  echo
  echo "控制台更新失敗，請確認資料檔案格式是否正確。"
  pause_on_exit
  exit 1
fi

echo "正在啟動本地控制台網址..."
echo "瀏覽器會自動打開 http://127.0.0.1:7000~7999/index.html 的其中一個可用網址。"
echo "這個視窗請先不要關閉；關閉後，本地網址就會停止。"
echo

rm -f "$URL_FILE"
: > "$SERVE_LOG"
trap cleanup EXIT

python3 "$SCRIPT_DIR/scripts/serve_console.py" \
  --root "$SCRIPT_DIR" \
  --write-url-file "$URL_FILE" \
  >>"$SERVE_LOG" 2>&1 &
SERVE_PID=$!

URL=""
for _ in 1 2 3 4 5 6 7 8 9 10; do
  if [[ -f "$URL_FILE" ]]; then
    URL="$(tr -d '\r\n' < "$URL_FILE")"
  fi
  if [[ -n "$URL" ]] && /usr/bin/curl -sf --max-time 1 "$URL" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if [[ -n "$URL" ]] && /usr/bin/curl -sf --max-time 1 "$URL" >/dev/null 2>&1; then
  echo "本地控制台已就緒：$URL"
  if ! open_console_url "$URL"; then
    echo "自動打開瀏覽器失敗，請手動開啟：$URL"
  fi
else
  FILE_URL="file://$SCRIPT_DIR/index.html"
  echo
  echo "本地控制台網址沒在預期時間內就緒，先退回靜態頁面："
  echo "$FILE_URL"
  open_console_url "$FILE_URL" || true
  echo "提醒：靜態頁面只能看內容，像配額守門員這類互動功能仍需要本地網址模式。"
fi

wait "$SERVE_PID"
