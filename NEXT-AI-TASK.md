# NEXT-AI-TASK

任務名稱：v1.6 — NEXT-AI-TASK 自動交棒檔與提示詞卡
目前階段：Codex 已完成 v1.6 第 4 階段修正與驗證，等待 Claude Code（VS Code）複審
上一棒 AI：Codex
下一棒 AI：Claude Code（VS Code）
交棒目的：請複審 v1.6 P1/P2 修正是否完整，尤其是備份包與本機安裝版 SKILL.md 是否已同步。
最後更新：2026-06-05 Codex v1.6 第 4 階段修正完成
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
- 以 Claude Code（VS Code）審查員角色複審本輪 diff。
- 確認 P1「codex-skills-backup.tar.gz 未更新」已完全修正。
- 確認 P2「NEXT-AI-TASK.md 最後更新」已處理。
- 確認 build 與四份 MD5 驗證結果可信。
驗證要求：
- 檢查 `git diff -- NEXT-AI-TASK.md skills/dual-ai-workflow/SKILL.md codex-skills-backup.tar.gz data/prompts.yaml index.html DUAL-AI-STATE.md`。
- 確認 build 輸出為 `45 skills / 40 prompts / 3 combos`。
- 確認 `index.html` 內可搜尋到「讀取 NEXT-AI-TASK.md 並接續」與 `NEXT-AI-TASK`。
- 確認四份 `SKILL.md` MD5 皆為 `b7bcf4df2168451ba6486d72723c9c45`。
- 確認本輪已建立本地 commit，但沒有 push。
回報格式：
- 結論：可通過 / 需修正
- P0：不修不能交付
- P1：建議本輪修
- P2：可延後或優化
- 給 Codex 的下一步修正提示詞
注意事項：
- 不要依賴對話記憶，請以 DUAL-AI-STATE.md、NEXT-AI-TASK.md 和目前 git diff 為準。
- 不要自動 push，除非使用者明確要求。
