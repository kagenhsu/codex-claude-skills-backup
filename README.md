# Codex / Claude Skills Console

本專案是一個可攜式的 Codex / Claude Code skills 安裝包，加上一個本機 HTML 控制台。

同事可以直接下載本 repo，或用一行指令把 skills 安裝到自己的電腦。

## 一行安裝

Windows PowerShell：

```powershell
powershell -ExecutionPolicy Bypass -NoProfile -Command "irm https://raw.githubusercontent.com/kagenhsu/codex-claude-skills-backup/main/install.ps1 | iex"
```

不熟 PowerShell/Bash 的同事，請先看下面「比較安全的安裝方式」。

macOS / Linux / Git Bash：

```bash
curl -fsSL https://raw.githubusercontent.com/kagenhsu/codex-claude-skills-backup/main/install.sh | bash
```

不熟 PowerShell/Bash 的同事，請先看下面「比較安全的安裝方式」。

安裝完成後，重新啟動 Codex 和 Claude Code。

## 這個指令做了什麼

| 動作 | 說明 |
|---|---|
| 下載備份包 | 從 GitHub 下載 `codex-skills-backup.tar.gz` |
| 解壓縮 | 把壓縮包展開到暫存資料夾 |
| 安裝 Codex skills | 複製到 `~/.codex/skills` |
| 安裝 Claude Code skills | 複製到 `~/.claude/skills` |
| 保護既有資料 | 如果同名 skill 已存在，會跳過，不覆蓋 |

簡單說：這不是安裝一個大型軟體，只是把整理好的 skills 放到 Codex / Claude Code 會讀取的位置。

## 比較安全的安裝方式

如果你不想直接執行網路上的腳本，可以先下載並檢查：

```powershell
irm https://raw.githubusercontent.com/kagenhsu/codex-claude-skills-backup/main/install.ps1 -OutFile install.ps1
notepad install.ps1
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

macOS / Linux：

```bash
curl -fsSLO https://raw.githubusercontent.com/kagenhsu/codex-claude-skills-backup/main/install.sh
less install.sh
bash install.sh
```

## 本機控制台

安裝後或下載 repo 後，可以直接雙擊：

```text
index.html
```

它是本機 HTML 單頁控制台，用來查詢 skills、複製觸發句、查看提示詞庫和三方 AI 工作流。

## 專案內容

- `index.html` - 本機 Skill 助手控制台，雙擊開啟。
- `codex-skills-backup.tar.gz` - 可攜式 skills 備份包。
- `install.ps1` - Windows 一行安裝腳本。
- `install.sh` - macOS / Linux / Git Bash 一行安裝腳本。
- `restore-skills.sh` - 離線還原腳本，適合已經完整下載 repo 的情境。
- `data/skills.yaml` - 控制台的 skill 目錄資料。
- `data/prompts.yaml` - 控制台的提示詞庫資料。
- `scripts/build.py` - 由 YAML 重建 `index.html`。

## Restore On A New Machine

```bash
git clone https://github.com/kagenhsu/codex-claude-skills-backup.git
cd codex-claude-skills-backup
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
