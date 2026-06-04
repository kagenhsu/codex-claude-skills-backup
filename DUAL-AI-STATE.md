# DUAL-AI-STATE

任務名稱：新增 AI 角色導覽並修正 Claude Desktop 使用方式

目前階段：✅ 已完成

已完成事項：
- 新增 `docs/ai-role-guide.md`，說明 Codex、Claude Code（VS Code）、Claude Desktop 的角色與適用情境。
- `index.html` 新增「AI 角色導覽」頁籤，並保留「三方 AI 工作流」「提示詞庫」「安檢 SOP」等原功能。
- 修正網站可見文字，避免新手看到 `????` 或舊版 `Claude@VSCode`、`Claude@桌面` 命名。
- `skills/dual-ai-workflow/SKILL.md` 已修正為新版分工：Codex 是主力工程師，負責第 1、2、4 階段；Claude Code（VS Code）是審查員，負責第 3、5 階段；Claude Desktop 是顧問／文字助理，不安裝第三方 skills。
- `data/skills.yaml` 與 `data/prompts.yaml` 已補上 Claude Desktop 提示詞版、單一 AI 使用與三方角色說明。
- 已執行 `scripts/build.py`，重建結果為 45 skills / 33 prompts。
- 已用 `scripts/update_backup_skill.py` 保留原備份包內容，更新 `codex-skills-backup.tar.gz` 內的 `skills/dual-ai-workflow/SKILL.md`。
- 已同步 `skills/dual-ai-workflow/SKILL.md` 到 `C:\Users\User\.codex\skills\dual-ai-workflow\SKILL.md` 與 `C:\Users\User\.claude\skills\dual-ai-workflow\SKILL.md`。
- 專案版、備份包版、`.codex` 安裝版、`.claude` 安裝版的 `SKILL.md` MD5 皆為 `a45e7469fcb50ca42a25af69de8cb477`。

下一步：
- 可交給 Claude Code（VS Code）複查角色分工與網站文案。
- 複查通過後，可進入 git 存檔。
- 若 Mac mini 也使用 Codex 或 Claude Code，請把新版 `SKILL.md` 同步到 Mac mini 的 `~/.codex/skills/dual-ai-workflow/` 與 `~/.claude/skills/dual-ai-workflow/`。

未解決問題：
- 尚未由 Claude Code（VS Code）做最終複審。
- 尚未執行 git commit。

最後更新時間：2026-06-04 10:55 +08:00
