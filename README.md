# Private AI Skills Backup

This repository is a private backup for personal AI assistant skills.

Do not make this repository public.

## Contents

- `codex-skills-backup.tar.gz` - portable backup of user-installed skills.
- `restore-skills.sh` - restores the skills into both Codex and Claude Code.

## Restore On A New Machine

```bash
git clone <your-private-repo-url>
cd skill-portable-installer
./restore-skills.sh
```

The restore script installs skills into:

```bash
~/.codex/skills
~/.claude/skills
```

Restart Codex and Claude Code after restoring.

## Notes

This backup does not include API keys, Codex config, Claude config, MCP settings, or shell environment variables.

Some skills may require separate setup for Node.js, Bun, API keys, browser automation, or service credentials.
