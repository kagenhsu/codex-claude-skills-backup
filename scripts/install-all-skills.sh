#!/usr/bin/env bash
# install-all-skills.sh — install every bundled skill from the codex-claude-skills-backup archive
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/kagenhsu/codex-claude-skills-backup/main/scripts/install-all-skills.sh | bash

set -euo pipefail

REPO_RAW_BASE="${REPO_RAW_BASE:-https://raw.githubusercontent.com/kagenhsu/codex-claude-skills-backup/main}"
ARCHIVE_URL="$REPO_RAW_BASE/codex-skills-backup.tar.gz"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

echo "📥 Downloading skill archive..."
if ! curl -fsSL "$ARCHIVE_URL" -o "$TMP_DIR/backup.tar.gz"; then
  echo "❌ Failed to download $ARCHIVE_URL" >&2
  exit 1
fi

echo "📦 Extracting bundled skills ..."
tar -xzf "$TMP_DIR/backup.tar.gz" -C "$TMP_DIR"

if [ ! -d "$TMP_DIR/skills" ]; then
  echo "❌ No skills directory found in archive." >&2
  exit 1
fi

install_target() {
  local target="$1"
  mkdir -p "$target"

  find "$TMP_DIR/skills" -mindepth 1 -maxdepth 1 -type d | while read -r skill_dir; do
    local skill_name backup_path
    skill_name="$(basename "$skill_dir")"

    if [ "$skill_name" = ".system" ]; then
      continue
    fi

    if [ -e "$target/$skill_name" ]; then
      backup_path="$target/$skill_name.bak.$(date +%Y%m%d-%H%M%S)"
      echo "⏭  Existing skill found at $target/$skill_name — backing up to $backup_path"
      mv "$target/$skill_name" "$backup_path"
    fi

    cp -R "$skill_dir" "$target/$skill_name"
    echo "✅ Installed: $target/$skill_name"
  done
}

install_target "$HOME/.claude/skills"
install_target "$HOME/.codex/skills"

echo
echo "🎉 Done. Restart Codex / Claude Code so they load the bundled skills."
