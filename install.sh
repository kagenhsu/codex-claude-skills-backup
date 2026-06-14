#!/usr/bin/env bash
set -euo pipefail

REPO_RAW_BASE="${REPO_RAW_BASE:-https://raw.githubusercontent.com/kagenhsu/codex-claude-skills-backup/main}"
ARCHIVE_NAME="codex-skills-backup.tar.gz"
INDEX_NAME="index.html"
SERVE_SCRIPT_REL="scripts/serve_console.py"

if [ "$(uname -s)" != "Darwin" ]; then
  echo "This installer supports macOS only." >&2
  exit 1
fi

if [ "$#" -gt 0 ]; then
  echo "Usage: $0" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_ARCHIVE="$SCRIPT_DIR/$ARCHIVE_NAME"
LOCAL_INDEX="$SCRIPT_DIR/$INDEX_NAME"
LOCAL_SERVE_SCRIPT="$SCRIPT_DIR/$SERVE_SCRIPT_REL"
TMP_DIR="$(mktemp -d)"
EXTRACT_DIR="$TMP_DIR/extract"
mkdir -p "$EXTRACT_DIR"

cleanup() {
  echo "Temporary files were left at: $TMP_DIR"
  echo "For safety, this installer does not delete temporary folders automatically."
}
trap cleanup EXIT

echo "Codex / Claude skills installer"

if [ -f "$LOCAL_ARCHIVE" ]; then
  ARCHIVE="$LOCAL_ARCHIVE"
  echo "Using local archive: $ARCHIVE"
else
  ARCHIVE="$TMP_DIR/$ARCHIVE_NAME"
  ARCHIVE_URL="$REPO_RAW_BASE/$ARCHIVE_NAME"
  echo "Downloading archive: $ARCHIVE_URL"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$ARCHIVE_URL" -o "$ARCHIVE"
  elif command -v wget >/dev/null 2>&1; then
    wget -qO "$ARCHIVE" "$ARCHIVE_URL"
  else
    echo "Missing curl or wget. Please install one of them and retry." >&2
    exit 1
  fi
fi

tar -xzf "$ARCHIVE" -C "$EXTRACT_DIR"

SOURCE_SKILLS="$EXTRACT_DIR/skills"
if [ ! -d "$SOURCE_SKILLS" ]; then
  echo "Archive does not contain a skills directory." >&2
  exit 1
fi

install_skills() {
  local target="$1"
  mkdir -p "$target"

  find "$SOURCE_SKILLS" -mindepth 1 -maxdepth 1 -type d | while read -r skill_dir; do
    local skill_name
    skill_name="$(basename "$skill_dir")"

    if [ "$skill_name" = ".system" ]; then
      continue
    fi

    if [ -e "$target/$skill_name" ]; then
      echo "Skip existing: $target/$skill_name"
      continue
    fi

    cp -R "$skill_dir" "$target/$skill_name"
    echo "Installed: $target/$skill_name"
  done
}

install_skills "$HOME/.codex/skills"
install_skills "$HOME/.claude/skills"

CONSOLE_DIR="$HOME/Documents/CodexClaudeSkillsConsole"
CONSOLE_INDEX="$CONSOLE_DIR/$INDEX_NAME"
CONSOLE_SCRIPT_DIR="$CONSOLE_DIR/scripts"
CONSOLE_SERVE_SCRIPT="$CONSOLE_DIR/$SERVE_SCRIPT_REL"
mkdir -p "$CONSOLE_DIR"
mkdir -p "$CONSOLE_SCRIPT_DIR"

if [ -f "$LOCAL_INDEX" ]; then
  cp "$LOCAL_INDEX" "$CONSOLE_INDEX"
  echo "Console copied: $CONSOLE_INDEX"
else
  INDEX_URL="$REPO_RAW_BASE/$INDEX_NAME"
  echo "Downloading console: $INDEX_URL"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$INDEX_URL" -o "$CONSOLE_INDEX"
  else
    echo "Missing curl. Please install curl and retry." >&2
    exit 1
  fi
  echo "Console downloaded: $CONSOLE_INDEX"
fi

if [ -f "$LOCAL_SERVE_SCRIPT" ]; then
  cp "$LOCAL_SERVE_SCRIPT" "$CONSOLE_SERVE_SCRIPT"
  echo "Console launcher copied: $CONSOLE_SERVE_SCRIPT"
else
  SERVE_URL="$REPO_RAW_BASE/$SERVE_SCRIPT_REL"
  echo "Downloading console launcher: $SERVE_URL"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$SERVE_URL" -o "$CONSOLE_SERVE_SCRIPT"
  else
    echo "Missing curl. Please install curl and retry." >&2
    exit 1
  fi
  echo "Console launcher downloaded: $CONSOLE_SERVE_SCRIPT"
fi

DESKTOP_DIR="$HOME/Desktop"
LAUNCHER="$DESKTOP_DIR/二刀流開發助手控制台.command"
mkdir -p "$DESKTOP_DIR"
cat > "$LAUNCHER" <<EOF
#!/usr/bin/env bash
set -euo pipefail

if ! command -v python3 >/dev/null 2>&1; then
  echo "找不到 python3，無法啟動本地控制台網址。"
  echo "請先安裝 Python 3，再重新雙擊此檔案。"
  echo
  printf '按 Enter 關閉視窗...'
  read -r _
  exit 1
fi

echo "正在啟動本地控制台網址..."
echo "瀏覽器會自動打開 http://127.0.0.1:8000/index.html（若 8000 被占用，會改用其他可用連接埠）。"
echo "這個視窗請先不要關閉；關閉後，本地網址就會停止。"
echo
python3 "$CONSOLE_SERVE_SCRIPT" --root "$CONSOLE_DIR" --open-browser
EOF
chmod +x "$LAUNCHER"
echo "Desktop launcher created: $LAUNCHER"

echo
echo "Done. Restart Codex and Claude Code to load the installed skills."
echo "Open the console from your desktop launcher: 二刀流開發助手控制台.command"
