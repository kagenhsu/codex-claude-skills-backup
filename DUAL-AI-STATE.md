# DUAL-AI-STATE

任務名稱：v2.2 — 換電腦／同步頁新手安裝入口

目前階段：✅ 已完成，等待本地 commit；push origin/main 尚未授權

狀態：使用週凍結期 + 使用者準備開新專案「人生管理系統」

已完成事項：
- v2.1 已完成並推上 GitHub Pages：首頁新增新手分工提示、二刀流分工細節說明、雙 AI 新專案討論提示詞、README 新手版與客製化說明。
- 已新增 GitHub repo About website 連結，指向 `https://kagenhsu.github.io/codex-claude-skills-backup/`。
- 已將 `skills/dual-ai-workflow/SKILL.md` 加入「Claude Code 審查閘門」，並同步到本機 Codex / Claude Code 全域 skill；本地 commit `93b7332` 已完成但尚未 push。
- v2.2 已將「換電腦／同步」頁改成新手導向的「把二刀流控制台裝到自己的電腦」入口。
- v2.2 頂部新手卡片已補隱私保證：網頁不讀取本機資料、不送任何東西到伺服器，按鈕只複製指令或開啟下載連結。
- v2.2 已新增三個主要入口：Windows 安裝指令、macOS 安裝指令、下載 skills 備份包。
- Windows / macOS 安裝卡已配 3 步微引導：打開 PowerShell / Terminal、貼上指令、按 Enter 等待完成。
- 已新增「安裝完成後，你會得到什麼？」三點結果說明。
- 已新增注意事項：線上 demo 不能備份本機、README、macOS Gatekeeper、GitHub Issues 留言。
- 進階區已移到頁面最下方，標題明示「不是新手第一步該按」。
- 進階區已新增「給已下載整個 repo 的人」與「已安裝後，想擁有自己的版本？」。
- 自有版本同步路徑使用 `git remote add mine`，並提醒不要用 `git remote set-url origin`。
- 已同步更新 `PAGE_INTROS.backup` 的 `lead / purpose / first / when`。
- 已新增 CSS：`install-hero`、`install-grid`、`install-card`、`install-steps`、`install-result-grid`、`advanced-section`、`advanced-grid`。
- 已新增 helper：`installSteps(system)`。
- 已修正 `copyText()`：複製後恢復原按鈕文字，不再 hardcode 成「複製」。

驗證結果：
- `python3 scripts/build.py` 通過，輸出 `45 skills / 41 prompts / 3 combos`。
- `node --check` 檢查 `index.html` inline JS 通過。
- 產生後 HTML 關鍵文案檢查通過。
- 受保護函式 0 行 diff：
  `progressHtml / controlHtml / stateBoardHtml / parseWorkflowState / stateSummaryHtml / bindControl / bindStateBoard / captureHtml / skillForm / skillCapturePrompt / renderOnlineBanner / renderLaunchTip`
- Claude Code 已完成 v2.2 複核：P0=0、P1=0，P2=4 條不阻擋；使用者已授權本地 commit，但尚未授權 push。

本輪 P2-V22（凍結期只記錄，不主動修）：
- P2-V22-1：`installSteps` 第 1 步對純新手太簡略，可補「在搜尋列輸入 powershell」。
- P2-V22-2：`.tar.gz` 對 Win10 純新手可能需要解壓工具提醒。
- P2-V22-3：下載備份包按鈕視覺與「複製指令」相似。
- P2-V22-4：`cmdRow` 複製出的指令含 `<...>` placeholder。

下一步：
- Codex 依 Claude Code 授權建立本地 commit，commit message：
  `v2.2：換電腦／同步頁改寫為新手安裝入口`
- commit 後回報 commit hash 與 `git status --short --branch`。
- 不要 push；只有使用者明確說「可以 push」才執行 `git push origin main`。
- 凍結期繼續：不要主動規劃 v2.3、不要主動補 P2、不要主動改 README。
- 使用者接下來會開新專案「人生管理系統」，暫時不會回到 `codex-claude-skills-backup`。

未解決問題：
- v2.2 尚未 push，因此 GitHub Pages 線上 demo 仍是舊版。push 並等待 GitHub Pages 部署後，`https://kagenhsu.github.io/codex-claude-skills-backup/` 才會更新。
- 使用週凍結期內，只有使用者回報具體不便或真實 bug 時才進入規劃；不要主動開新功能。

最後更新時間：2026-06-06 由 Codex 更新，準備建立 v2.2 本地 commit
