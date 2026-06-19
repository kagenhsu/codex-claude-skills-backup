#!/usr/bin/env bash
set -euo pipefail

STATE_FILE="${CCTOKMON_STATE_FILE:-$HOME/.claude/cctokmon-state.json}"
TMP_FILE="${STATE_FILE}.tmp"

input="$(cat)"
printf '%s\n' "$input" > "$TMP_FILE"
mv "$TMP_FILE" "$STATE_FILE"

if command -v jq >/dev/null 2>&1; then
  read -r model pct <<< "$(printf '%s' "$input" | jq -r '[
    (.model.display_name // .model.name // "Claude"),
    (.context_window.used_percentage // 0 | tostring)
  ] | @tsv' 2>/dev/null)"
  printf '%s %s%%' "${model:-Claude}" "${pct:-0}"
else
  printf 'quota-guard'
fi
