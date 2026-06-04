#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARCHIVE="$SCRIPT_DIR/codex-skills-backup.tar.gz"
TMP_DIR="$(mktemp -d)"

cleanup() {
  echo "Temporary extracted files left at: $TMP_DIR"
}
trap cleanup EXIT

if [ ! -f "$ARCHIVE" ]; then
  echo "Missing backup archive: $ARCHIVE" >&2
  exit 1
fi

tar -xzf "$ARCHIVE" -C "$TMP_DIR"

install_skills() {
  local target="$1"
  mkdir -p "$target"

  find "$TMP_DIR/skills" -mindepth 1 -maxdepth 1 -type d | while read -r skill_dir; do
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
