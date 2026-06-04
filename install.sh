#!/usr/bin/env bash
set -euo pipefail

REPO_RAW_BASE="${REPO_RAW_BASE:-https://raw.githubusercontent.com/kagenhsu/codex-claude-skills-backup/main}"
ARCHIVE_NAME="codex-skills-backup.tar.gz"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_ARCHIVE="$SCRIPT_DIR/$ARCHIVE_NAME"
TMP_DIR="$(mktemp -d)"
EXTRACT_DIR="$TMP_DIR/extract"
mkdir -p "$EXTRACT_DIR"

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

echo
echo "Done. Restart Codex and Claude Code to load the installed skills."
echo "Temporary files were left at: $TMP_DIR"
