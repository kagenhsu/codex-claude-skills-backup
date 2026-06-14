# NEXT-AI-TASK

任務名稱：v2.2 — 換電腦／同步頁新手安裝入口

目前階段：✅ Claude Code 複核通過，使用者已授權本地 commit；push 尚未授權

上一棒 AI：Claude Code（VS Code）

下一棒 AI：使用者

交棒目的：使用者準備開新專案「人生管理系統」，暫時不會回到 `codex-claude-skills-backup`。本 repo 進入使用週凍結期。

最後更新：2026-06-06 Codex 更新 v2.2 狀態，準備建立本地 commit；等待使用者未來明確授權 push。

必讀檔案：
- `DUAL-AI-STATE.md`
- `NEXT-AI-TASK.md`
- `skills/dual-ai-workflow/SKILL.md`
- `scripts/build.py`
- `index.html`

本輪已完成：
- `skills/dual-ai-workflow/SKILL.md` 已新增「Claude Code 審查閘門」；本地 commit `93b7332` 已完成但尚未 push。
- 「換電腦／同步」頁已改成新手導向的安裝 / 備份入口。
- 頂部新手卡片已補隱私保證：線上 demo 不讀取本機資料、不送任何東西到伺服器。
- 已新增 Windows / macOS 安裝指令卡，按鈕文字為「複製指令」，不是「一鍵安裝」。
- Windows / macOS 安裝卡都補 3 步微引導：打開 PowerShell / Terminal、貼上指令、按 Enter。
- 已新增下載 skills 備份包入口，並說明適用情境。
- 已新增「安裝完成後，你會得到什麼？」三點結果說明。
- 已新增注意事項：線上 demo 不能備份本機、README、macOS Gatekeeper、Issues 留言。
- 進階區已移到頁面最下方，包含 `restore-skills.sh` 與自有 GitHub repo 同步方式。
- 自有版本同步使用 `git remote add mine`，並警告不要使用 `git remote set-url origin`。
- 已同步更新 `PAGE_INTROS.backup` 的 `lead / purpose / first / when`。
- 已修正 `copyText()`，讓按鈕複製後恢復原本的按鈕文字。

驗證要求：
- `python3 scripts/build.py` 應成功，輸出 `45 skills / 41 prompts / 3 combos`。
- `node --check` 抽出的 inline JS 應通過。
- `git status --short --branch` 應顯示本地比 `origin/main` 超前，且 push 尚未執行。
- GitHub Pages 線上 demo 只有在使用者明確授權 push 後才會更新。

凍結期規則：
- 除非使用者明確回報具體不便或真實 bug，否則不開新功能。
- 不主動規劃 v2.3。
- 不主動補 P2。
- 不主動改 README。
- 不主動改 CSS。
- 不主動新增提示詞。
- commit / push / release / GitHub 遠端設定仍須遵守 `dual-ai-workflow` 的 Claude Code 審查閘門。

P2-V22（給未來使用週後評估，不主動修）：
- P2-V22-1：`installSteps` 第 1 步對純新手太簡略，可補「在搜尋列輸入 powershell」。
- P2-V22-2：`.tar.gz` 對 Win10 純新手可能需要解壓工具提醒。
- P2-V22-3：下載備份包按鈕視覺與「複製指令」相似。
- P2-V22-4：`cmdRow` 複製出的指令含 `<...>` placeholder。

下一棒要做：
- 使用者開新專案「人生管理系統」。
- 如果使用者回到本 repo 並明確說「可以 push」，Codex 才能執行 `git push origin main`。
- push 後需確認 `git status --short --branch`，並告知 GitHub Pages 需要等待重新部署。

注意事項：
- 不要依賴對話記憶，請以 `DUAL-AI-STATE.md`、`NEXT-AI-TASK.md` 與目前 git 狀態為準。
- 不要自動 push。
