# NEXT-AI-TASK

任務名稱：v1.7 收尾完成 + v1.8 規劃啟動
目前階段：✅ v1.7 收尾完成，v1.8 僅完成規劃文件；本機 workflow skill 已同步
上一棒 AI：Codex
下一棒 AI：使用者決定是否啟動 v1.8
交棒目的：v1.7 已完成本地收尾；v1.8 只建立規劃文件；本機 dual-ai-workflow skill 已同步到 Codex / Claude 安裝版，等待使用者確認是否進入實作或 push。
最後更新：2026-06-05 Codex 補記本機 dual-ai-workflow skill 同步驗證完成
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
- 已修正本機 skill 同步問題：repo 版、備份包內版本、Codex 安裝版、Claude 安裝版四份 `dual-ai-workflow/SKILL.md` MD5 已一致，皆為 `b7bcf4df2168451ba6486d72723c9c45`。
- 已確認本機 Codex / Claude 安裝版現在包含「主動交棒規則」與「上下文壓縮觸發規則」。
- v1.7 收尾已補齊 `docs/v1-2-backlog.md` 的 P2 #2、#3、#6 ✅ 標記。
- v1.7 收尾已在 `README.md` 補上 macOS quarantine 提醒，說明第一次雙擊 `.command` 被擋時可右鍵打開或執行 `xattr -d com.apple.quarantine 更新並開啟控制台.command`。
- v1.7 收尾已更新 `CHANGELOG.md`，記錄 backlog 標記補齊與 README quarantine 提醒。
- v1.8 規劃文件已新增 `docs/v1-8-plan.md`，只做規劃，不提前實作功能程式碼。
- v1.7 已將三方中控按鈕改為優先定位到實際提示詞卡，找不到卡片時才退回階段 section。
- v1.7 已將 `sectionAfter` 改為使用固定欄位白名單 `STATE_SECTION_PATTERN`。
- v1.7 已新增 macOS 中文入口 `更新並開啟控制台.command`，讓使用者不用記 `python3 scripts/build.py`。
- v1.7 已更新 `README.md`、`docs/v1-2-backlog.md` 與 `CHANGELOG.md`。
- v1.7 已執行 `python3 scripts/build.py`，結果為 45 skills / 40 prompts / 3 combos。
- v1.7 目前工作區包含 7 個已修改檔與 1 個新增檔，皆屬本輪修改範圍。
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
- 使用者決定是否啟動 v1.8；若啟動，先讀 `docs/v1-8-plan.md`，確認「我要做什麼」與「開發進度」兩個 MVP 的實作順序。
- 使用者決定是否 push 目前本地 commit；不要自動 push origin/main。
驗證要求：
- `python3 scripts/build.py` 應成功。
- 四份 `dual-ai-workflow/SKILL.md` MD5 應一致：repo、備份包、`~/.codex`、`~/.claude`。
- README 與 CHANGELOG 中關於 `.command` 的描述應一致。
- v1.8 本輪只新增 `docs/v1-8-plan.md`，不應修改 `data/prompts.yaml` 既有 schema，也不應提前寫 v1.8 功能程式碼。
回報格式：
- 回報 v1.7 commit hash、build 結果、目前 `git status --short`，並提醒不要自動 push。
注意事項：
- 不要依賴對話記憶，請以 DUAL-AI-STATE.md、NEXT-AI-TASK.md 和目前 git diff 為準。
- 不要自動 push，除非使用者明確要求。
