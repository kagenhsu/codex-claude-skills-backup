# NEXT-AI-TASK

任務名稱：v1.9 — 二刀流開發助手控制台命名統一
目前階段：✅ v1.9 命名統一完成並 push origin/main
上一棒 AI：Codex
下一棒 AI：
交棒目的：v1.9 命名統一已完成並 push origin/main；等待決定下一個任務。
最後更新：2026-06-06 11:50 CST Codex v1.9 命名統一完成並 push origin/main
必讀檔案：
- AGENTS.md
- DUAL-AI-STATE.md
- NEXT-AI-TASK.md
- PRD.md
- docs/skill-console-plan.md
- docs/v1-8-plan.md
- skills/dual-ai-workflow/SKILL.md
- data/prompts.yaml
- scripts/build.py
- index.html
已完成：
- v1.9 已完成 Claude Code（VS Code）複審：P0=0、P1=0，P2=2 + 4 項 v1.8 遺留 backlog，均排入後續優化，不阻擋 push。
- v1.9 已於 2026-06-06 11:50 CST push `origin/main`，遠端已同步至 commit `535021c`。
- v1.9 已依使用者決定，將專案／網頁主標統一為「二刀流開發助手控制台」，副標為「Codex × Claude Code 開發系統」。
- v1.9 已更新 `scripts/build.py` 的瀏覽器 title、頁首 h1、副標與換電腦／同步頁捷徑文案。
- v1.9 已更新 `AGENTS.md`、`PRD.md`、`README.md`、`docs/skill-console-plan.md`、`install.sh`、`install.ps1`、`更新並開啟控制台.command` 的顯示名稱。
- v1.9 已在開發進度「專案版本地圖」補上 v1.9「二刀流命名」階段，讓目前版本可被藍框標出。
- v1.8 MVP B 已依使用者要求完成多頁排版收斂：AI 角色導覽、三方 AI 工作流、開發進度、收錄新內容、安檢 SOP、換電腦／同步等內容卡片寬度已調整為與上方搜尋／導覽區一致。
- v1.8 MVP B Browser comment 已處理：換電腦／同步頁改用 `wide-sop` 版面 class，搬家工具說明與同步指令卡片寬度與上方搜尋／導覽區一致。
- v1.8 MVP B Browser comment 已處理：安檢 SOP 頁改用 `wide-sop` 版面 class，安檢說明與提示詞卡片寬度與上方搜尋／導覽區一致。
- v1.8 MVP B Browser comment 已處理：收錄新內容頁改用 `wide-sop` 版面 class，提示詞／Skill 表單卡片寬度與上方搜尋／導覽區一致。
- v1.8 MVP B Browser comment 已處理：三方 AI 工作流改用獨立 `wide-sop` 版面 class，內容卡片明確撐滿主欄寬度，避免仍受一般 SOP 寬度限制。
- v1.8 MVP B Browser comment 已處理：AI 角色導覽與三方 AI 工作流內容區改用滿寬顯示，資訊卡寬度與上方搜尋／導覽區一致。
- v1.8 MVP B Browser comment 已處理：開發進度新增「必備檔案檢查」，會判斷所選專案資料夾是否缺 DUAL-AI-STATE.md、NEXT-AI-TASK.md、AGENTS.md、PRD.md；缺檔時提供可複製給 AI 的補檔提示詞。
- v1.8 MVP B Browser comment 已處理：開發進度內容區新增 `progress-sop` 版面 class，讓資料夾選擇卡與下方資料卡寬度撐滿主欄，和上方搜尋／導覽區一致。
- v1.8 MVP B Browser comment 已處理：開發進度「目前狀態」摘要移除「下一棒 AI」卡片；交棒資訊仍保留在 NEXT-AI-TASK.md 原檔，不放在主摘要。
- v1.8 MVP B Browser comment 已處理：開發進度上方動作改為「選擇專案資料夾」，使用者主動選取資料夾後，狀態、專案敘述、開發階段與 AGENTS / PRD 卡會改讀該資料夾內的 DUAL-AI-STATE.md、NEXT-AI-TASK.md、AGENTS.md、PRD.md。
- v1.8 MVP B Browser comment 已處理：開發進度「目前狀態」摘要移除「最後更新時間」卡片，改為只顯示目前階段、上一步、下一步與未解決問題；三方中控 `stateSummaryHtml()` 保持不動。
- v1.8 MVP B Browser comment 已處理：開發進度「目前狀態」的地圖改為專案版本地圖，顯示 v1.0～v1.8 各版本標題與簡述，並以藍框標出目前 v1.8。
- v1.8 MVP B Browser comment 已處理：開發進度「目前狀態」移除完整 DUAL-AI-STATE.md / NEXT-AI-TASK.md 檔案卡，保留階段地圖與摘要，避免頁面過長干擾新手。
- v1.8 MVP B Browser comment 已處理：開發進度「目前狀態」新增開發階段地圖，顯示第 1～5 階段標題與簡述，並以藍框標出目前階段。
- v1.8 MVP B Browser comment 已處理：開發進度警示區新增「打開目前專案資料夾」與「複製資料夾路徑」操作，讓使用者可直接進入專案資料夾查 DUAL-AI-STATE.md / NEXT-AI-TASK.md。
- v1.8 MVP B Browser comment 已處理：開發進度 tab 在警示下方新增「目前狀態／專案敘述／開發階段／AGENTS / PRD」切換檢視，可查看專案描述、開發階段與 AGENTS.md / PRD.md 資料。
- v1.8 MVP B 第 5 階段 Claude Code（VS Code）複審完成：P0=0、P1=0、P2=2，P2 均為後續優化建議，不阻擋。
- v1.8 MVP B P2-1 已排入後續優化：`progressHtml()` 未解決問題警示對「全部 ✅」backlog 仍會觸發，後續可加入「全部 ✅ 視為無」判斷。
- v1.8 MVP B P2-2 已排入後續優化：`summary.replace(/<\/div>$/, ...)` 隱性依賴 `stateSummaryHtml()` 結尾，後續可改為參數化或在 `progressHtml()` 直接拼裝。
- v1.8 MVP B 已在 `scripts/build.py` build-time inline `DUAL-AI-STATE.md` 與 `NEXT-AI-TASK.md`，資料格式為 `{raw, html}`，並保留 `</` escape。
- v1.8 MVP B 已新增「開發進度」tab，位置在「AI 角色導覽」後方；預設 `let tab = "guide"` 未改。
- v1.8 MVP B 已新增 `PAGE_INTROS.progress` 新手文案。
- v1.8 MVP B 已新增 `progressHtml()`，沿用既有 `parseWorkflowState()` 與 `stateSummaryHtml()`，並用單行 regex 從 `NEXT_HTML.raw` 解析「下一棒 AI」。
- v1.8 MVP B 已在 `render()` 的 guide 分支後、capture 分支前加入 progress 分支。
- v1.8 MVP B 已執行 `python3 scripts/build.py`，結果仍為 45 skills / 40 prompts / 3 combos。
- v1.8 MVP B 已驗證「開發進度」tab 顯示目前階段、下一棒 AI、backlog、最後更新時間，且三方中控 textarea fallback 仍存在。
- v1.8 MVP B 已建立本地 commit，尚未 push `origin/main`。
- v1.8 B1 已清理 `docs/v1-2-backlog.md` P2 #5，補上 ✅ 並標記為 v1.1 已修、backlog 誤留。
- v1.8 B1 已將 `data/prompts.yaml` schema 限制歸到 v1.8 啟動注意事項，不再混在 v1.7 收尾驗證段。
- 已確認 v1.7 兩個 commit 已 push 至 `origin/main`：`3a99992`、`9ab61fe`。
- 已確認 workflow 小步規則 commit 已 push 至 `origin/main`：`56d13a0`。
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
- 使用者決定下一個任務（MVP A、v1.9 收尾 prompt 命名統一、或 v1.8 backlog 清理）。
- 若選擇 v1.9 收尾，優先處理 `data/prompts.yaml:264`「Skill 助手控制台」命名殘留。
- 若選擇 v1.8 backlog 清理，優先處理 PROJECT_PATH 絕對路徑、死碼、渲染風格落差與 picker warning 樣式。
驗證要求：
- `python3 scripts/build.py` 應成功。
- build 輸出應為 45 skills / 40 prompts / 3 combos。
- `node --check` 抽出的 inline script 應通過。
- 網頁 title 與頁首應顯示「二刀流開發助手控制台」與「Codex × Claude Code 開發系統」。
- 「開發進度」專案版本地圖應顯示 v1.9「二刀流命名」，且目前版本可被藍框標出。
- 「開發進度」tab 可選擇專案資料夾，並檢查 DUAL-AI-STATE.md / NEXT-AI-TASK.md / AGENTS.md / PRD.md 是否存在。
- AI 角色導覽、三方 AI 工作流、收錄新內容、安檢 SOP、換電腦／同步頁的資訊卡寬度應與上方搜尋／導覽區一致。
- 三方中控 tab 的 `workflowStateInput` textarea fallback 應仍可用、未受污染。
- `git status --short --branch` 應顯示本地分支 ahead origin/main，且本輪尚未 push。
v1.8 啟動注意事項：
- 不應修改 `data/prompts.yaml` 既有 schema；新增提示詞請走「收錄新內容」流程。
- MVP B inline `DUAL-AI-STATE.md` / `NEXT-AI-TASK.md` 時，沿用既有 markdown rendering，不 fork 第二份解析邏輯。
回報格式：
- 指定下一個任務。
- 若要 push 後續變更，仍需使用者再次明確授權。
注意事項：
- 不要依賴對話記憶，請以 DUAL-AI-STATE.md、NEXT-AI-TASK.md 和目前 git diff 為準。
- 不要自動 push，除非使用者明確要求。
