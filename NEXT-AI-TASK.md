# NEXT-AI-TASK

任務名稱：v1.6 — NEXT-AI-TASK 自動交棒檔與提示詞卡
目前階段：✅ v1.6 閉環完成
上一棒 AI：Codex
下一棒 AI：使用者決定是否 push 到 origin/main
交棒目的：v1.6 已完成本地存檔，等待使用者決定是否同步到 GitHub。
最後更新：2026-06-05 Codex v1.6 閉環完成
必讀檔案：
- AGENTS.md
- DUAL-AI-STATE.md
- NEXT-AI-TASK.md
- PRD.md
- docs/skill-console-plan.md
- skills/dual-ai-workflow/SKILL.md
- data/prompts.yaml
- scripts/build.py
- index.html
已完成：
- 第 5 階段 Claude Code（VS Code）複審通過，無 P0/P1/P2 殘留，commit 6278e23 為 v1.6 最終存檔。
- 新增專案根目錄 `NEXT-AI-TASK.md` 固定交棒檔。
- `skills/dual-ai-workflow/SKILL.md` 新增「主動交棒規則」section。
- `data/prompts.yaml` 新增「讀取 NEXT-AI-TASK.md 並接續」提示詞卡，`flow: dualai`、`stage: handoff`。
- 未修改 `scripts/build.py`，因既有 `handoff` stage 已能顯示。
- 已重建 `index.html`，build 結果為 45 skills / 40 prompts / 3 combos。
- 已更新 `DUAL-AI-STATE.md` 記錄 v1.6 進行中與下一步。
- 已執行 `scripts/update_backup_skill.py` 更新 `codex-skills-backup.tar.gz`，輸出 `replaced=True`。
- 已同步 `SKILL.md` 到 `~/.codex/skills/dual-ai-workflow/SKILL.md` 與 `~/.claude/skills/dual-ai-workflow/SKILL.md`。
- repo、tar.gz、Codex 安裝版、Claude 安裝版四份 `SKILL.md` MD5 皆為 `b7bcf4df2168451ba6486d72723c9c45`。
- 已補上 `NEXT-AI-TASK.md` 的最後更新欄位。
下一棒要做：
- 使用者決定是否 push 到 origin/main。
- 如要同步到 GitHub，push 前先確認 commit 不含敏感資料。
驗證要求：
- `git status` 應乾淨。
- `git log --oneline -3` 應顯示收尾 commit 在最上方，且 v1.6 功能 commit `6278e23` 在其後。
回報格式：
- 選擇 (a) 只保留本地，或 (b) 同步 GitHub。
注意事項：
- 不要依賴對話記憶，請以 DUAL-AI-STATE.md、NEXT-AI-TASK.md 和目前 git diff 為準。
- 不要自動 push，除非使用者明確要求。
