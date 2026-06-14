#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

pause_on_exit() {
  printf '\n按 Enter 關閉視窗...'
  read -r _
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
echo "瀏覽器會自動打開 http://127.0.0.1:8000/index.html（若 8000 被占用，會改用其他可用連接埠）。"
echo "這個視窗請先不要關閉；關閉後，本地網址就會停止。"
echo
if ! python3 "$SCRIPT_DIR/scripts/serve_console.py" --root "$SCRIPT_DIR" --open-browser; then
  echo
  echo "無法啟動本地控制台網址。"
  echo "你可以先手動執行：python3 \"$SCRIPT_DIR/scripts/serve_console.py\" --root \"$SCRIPT_DIR\" --open-browser"
  pause_on_exit
  exit 1
fi
