#!/usr/bin/env bash
# install-skill.sh — install a single skill from the codex-claude-skills-backup archive
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/kagenhsu/codex-claude-skills-backup/main/scripts/install-skill.sh | bash -s <skill-name>
# Example:
#   curl -fsSL https://raw.githubusercontent.com/kagenhsu/codex-claude-skills-backup/main/scripts/install-skill.sh | bash -s dual-ai-workflow

set -euo pipefail

SKILL="${1:-}"
if [ -z "$SKILL" ]; then
  echo "Usage: install-skill.sh <skill-name>" >&2
  echo "Currently bundled skills: dual-ai-workflow, plan-progress" >&2
  exit 1
fi

REPO_RAW_BASE="${REPO_RAW_BASE:-https://raw.githubusercontent.com/kagenhsu/codex-claude-skills-backup/main}"
ARCHIVE_URL="$REPO_RAW_BASE/codex-skills-backup.tar.gz"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

echo "📥 Downloading skill archive..."
if ! curl -fsSL "$ARCHIVE_URL" -o "$TMP_DIR/backup.tar.gz"; then
  echo "❌ Failed to download $ARCHIVE_URL" >&2
  exit 1
fi

echo "📦 Extracting $SKILL ..."
if ! tar -xzf "$TMP_DIR/backup.tar.gz" -C "$TMP_DIR" "skills/$SKILL" 2>/dev/null; then
  echo "❌ Skill '$SKILL' not found in archive." >&2
  echo "   Bundled skills: dual-ai-workflow, plan-progress" >&2
  exit 1
fi

for TARGET in "$HOME/.claude/skills" "$HOME/.codex/skills"; do
  mkdir -p "$TARGET"
  if [ -e "$TARGET/$SKILL" ]; then
    BACKUP="$TARGET/$SKILL.bak.$(date +%Y%m%d-%H%M%S)"
    echo "⏭  Existing skill found at $TARGET/$SKILL — backing up to $BACKUP"
    mv "$TARGET/$SKILL" "$BACKUP"
  fi
  cp -R "$TMP_DIR/skills/$SKILL" "$TARGET/$SKILL"
  echo "✅ Installed: $TARGET/$SKILL"
done

echo
echo "🎉 Done. Restart Codex / Claude Code so it loads the new skill."
