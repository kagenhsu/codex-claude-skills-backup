# DUAL-AI-STATE

任務名稱：v1.8 MVP B — 開發進度 tab

目前階段：🔍 v1.8 MVP B 已完成 Codex 排版修正，等待 Claude Code（VS Code）審查後再決定是否 push

已完成事項：
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
- v1.8 MVP B 已新增「開發進度」tab，預設 `let tab = "guide"` 未改。
- v1.8 MVP B 已新增 `progressHtml()`，沿用既有 `parseWorkflowState()` 與 `stateSummaryHtml()`，並從 `NEXT_HTML.raw` 解析「下一棒 AI」。
- v1.8 MVP B 已重建 `index.html`，`python3 scripts/build.py` 輸出仍為 45 skills / 40 prompts / 3 combos。
- v1.8 MVP B 已驗證開發進度 tab 顯示目前階段、下一棒 AI、backlog、最後更新時間，且三方中控 textarea fallback 仍存在。
- v1.8 MVP B 已建立本地 commit，尚未 push `origin/main`。
- v1.8 B1 已清理 `docs/v1-2-backlog.md` P2 #5，補上 ✅ 並標記為 v1.1 已修、backlog 誤留。
- v1.8 B1 已校正 `NEXT-AI-TASK.md`：將 `data/prompts.yaml` schema 限制歸到 v1.8 啟動注意事項，不再混在 v1.7 收尾驗證段。
- 已確認 v1.7 兩個 commit 已 push 至 `origin/main`：`3a99992`、`9ab61fe`。
- 已確認 workflow 小步規則 commit 已 push 至 `origin/main`：`56d13a0`。
- 已修正本機 skill 同步問題：repo 版、備份包內版本、Codex 安裝版、Claude 安裝版四份 `dual-ai-workflow/SKILL.md` MD5 已一致，皆為 `b7bcf4df2168451ba6486d72723c9c45`。
- 已確認本機 Codex / Claude 安裝版現在包含「主動交棒規則」與「上下文壓縮觸發規則」。
- v1.7 收尾已補齊 `docs/v1-2-backlog.md` 的 P2 #2、#3、#6 ✅ 標記。
- v1.7 收尾已在 `README.md` 補上 macOS quarantine 提醒，說明第一次雙擊 `.command` 被擋時可右鍵打開或執行 `xattr -d com.apple.quarantine 更新並開啟控制台.command`。
- v1.7 收尾已更新 `CHANGELOG.md`，記錄 backlog 標記補齊與 README quarantine 提醒。
- v1.8 規劃文件已新增 `docs/v1-8-plan.md`，只做規劃，不提前實作功能程式碼。
- v1.7 已接續開發，目標是清除 v1.2 backlog 剩餘兩項 P2。
- v1.7 已將三方中控按鈕改為優先定位到實際提示詞卡，若找不到才退回階段 section。
- v1.7 已將 `sectionAfter` 改為使用固定欄位白名單 `STATE_SECTION_PATTERN`。
- v1.7 已新增 macOS 中文入口 `更新並開啟控制台.command`，讓使用者不用記 `python3 scripts/build.py`。
- v1.7 已更新 `docs/v1-2-backlog.md`，將 P2 #1 與 P2 #4 標記為已修。
- v1.7 已更新 `README.md`、`CHANGELOG.md` 與 `NEXT-AI-TASK.md`。
- v1.7 已執行 `python3 scripts/build.py`，重建結果為 45 skills / 40 prompts / 3 combos。
- v1.7 目前工作區包含 7 個已修改檔與 1 個新增檔，皆屬本輪修改範圍。
- 第 5 階段 Claude Code（VS Code）複審通過，無 P0/P1/P2 殘留，commit 6278e23 為 v1.6 最終存檔。
- v1.6 第 4 階段已處理 Claude Code（VS Code）審查：P0=0、P1=1、P2=2。
- P1 已成立並修正：已執行 `scripts/update_backup_skill.py` 更新 `codex-skills-backup.tar.gz`，輸出 `replaced=True`，新版 `SKILL.md` MD5 為 `b7bcf4df2168451ba6486d72723c9c45`。
- P1 本機同步已完成：已覆蓋 `~/.codex/skills/dual-ai-workflow/SKILL.md` 與 `~/.claude/skills/dual-ai-workflow/SKILL.md`。
- P1 驗證完成：repo、tar.gz、Codex 安裝版、Claude 安裝版四份 `SKILL.md` MD5 皆為 `b7bcf4df2168451ba6486d72723c9c45`。
- P2 已處理：`NEXT-AI-TASK.md` 已補上「最後更新：2026-06-05 Codex v1.6 實作完成」。
- v1.6 第 4 階段 build 驗證完成：使用 Codex 內建 Python runtime 執行 `scripts/build.py`，輸出 45 skills / 40 prompts / 3 combos。
- v1.6 第 4 階段搜尋驗證完成：`index.html` 內可搜尋到 `NEXT-AI-TASK`。
- v1.6 已新增專案根目錄 `NEXT-AI-TASK.md`，作為固定半自動 AI 交棒檔。
- v1.6 已在 `skills/dual-ai-workflow/SKILL.md` 新增「主動交棒規則」，要求階段完成後主動輸出交接提示詞，並在存在 `NEXT-AI-TASK.md` 時同步更新。
- v1.6 已在 `data/prompts.yaml` 新增提示詞卡「讀取 NEXT-AI-TASK.md 並接續」，分類為三方 AI 協作，`flow: dualai`、`stage: handoff`。
- v1.6 未修改 `scripts/build.py`；原因是既有 `handoff` stage metadata 已可顯示 handoff 提示詞卡。
- v1.6 已使用 Codex 內建 Python runtime 執行 `scripts/build.py`，重建結果為 45 skills / 40 prompts / 3 combos。
- v1.6 已更新 `NEXT-AI-TASK.md`，下一棒指定為 Claude Code（VS Code）審查。
- 已讀取並依據本檔實際狀態接續，不沿用舊 MD5 聲明。
- P1-1 已成立並修正：`index.html` 預設頁籤改為「AI 角色導覽」，`backup` 頁籤移到最後；`scripts/build.py` 模板同步改為 `let tab = "guide"`。
- P1-2 已成立並修正：`skills/dual-ai-workflow/SKILL.md`、備份包內版本、`~/.codex` 安裝版、`~/.claude` 安裝版已統一為 LF 行尾。
- 已用 `scripts/update_backup_skill.py` 重打 `codex-skills-backup.tar.gz`，保留原備份包其他內容，只替換 `skills/dual-ai-workflow/SKILL.md`。
- 已同步 LF 版 `SKILL.md` 到 `~/.codex/skills/dual-ai-workflow/SKILL.md` 與 `~/.claude/skills/dual-ai-workflow/SKILL.md`。
- 已處理 P2-3：`.gitignore` 補上 `.DS_Store`、`skills/*`、`!skills/dual-ai-workflow/`。
- 已處理 P2-4：`PRD.md` 的 44 個 skill 改為 45 個（含 1 個自製 dual-ai-workflow）。
- 已處理 P2-5：`AGENTS.md` 專案檔案結構補上 `index.html`、安裝腳本、角色文件、自製 skill 與維護腳本。
- 已處理 P2-6：`data/skills.yaml` 與 `data/prompts.yaml` 改為三方 AI 命名，並重建 `index.html`。
- 已處理 P2-7：`install.sh` 與 `install.ps1` 加入暫存目錄提示；安裝器基於安全考量不自動刪除暫存資料夾。
- 已處理 P2-8：`README.md` 兩段一行安裝下方補上安全安裝提醒。
- 已處理 P2-9：`index.html` 搜尋 placeholder 補上「角色、分工、導覽」關鍵字。
- 已執行 `python3 scripts/build.py`，重建結果為 45 skills / 33 prompts；本機沒有未帶版本號的 Python 指令可用。
- 已用 macOS `open` 打開本機 `index.html`；生成檔確認 active tab 為 `guide`，第一眼不再落到 backup。
- 搜尋驗證：`角色` 命中 AI 角色導覽內容；`翻譯` 命中 skills 卡片（如 `baoyu-translate`）；`審查` 命中提示詞卡片（如「③ 第三階段：Claude Code（VS Code）審查」）。
- 已依使用者要求逐檔 stage 並建立本地 git commit，commit message 為「修正預設頁籤與三方 AI 命名一致性，統一 SKILL.md 行尾」；未 push 到 origin/main。
- 第 5 階段 Claude Code（VS Code）複審通過，無 P0/P1/P2 殘留，commit d07d61c 為最終存檔。
- 四份 `SKILL.md` MD5 實測一致：
  - 專案版 `skills/dual-ai-workflow/SKILL.md`：`eeee0b5f5b64758e6bd69fc48c714e03`
  - 備份包解壓版 `codex-skills-backup.tar.gz:skills/dual-ai-workflow/SKILL.md`：`eeee0b5f5b64758e6bd69fc48c714e03`
  - Codex 安裝版 `~/.codex/skills/dual-ai-workflow/SKILL.md`：`eeee0b5f5b64758e6bd69fc48c714e03`
  - Claude 安裝版 `~/.claude/skills/dual-ai-workflow/SKILL.md`：`eeee0b5f5b64758e6bd69fc48c714e03`
- v1.1 已新增快速看板與常用組合包，commit `2422245` 為目前 v1.1 實作版本。
- 第 3 階段 Claude Code（VS Code）審查結果：P0=0、P1=1、P2=3；本輪進入第 4 階段逐條修正。
- P1 已成立並修正：三方中控 7 顆按鈕不再把 stage 標題塞進搜尋框，改為切到提示詞庫的三方 AI 協作模式、清空搜尋並嘗試捲到對應 stage section。
- P2-2 已成立並修正：`跨地點 / 跨系統接續` 提示詞在 macOS 與 Windows 指令前補上同步全部 skills 請改用 `restore-skills.sh` / `install.ps1` 的提醒。
- P2-3 已成立並修正：搜尋 placeholder 的「三 AI」改為「三方 AI」。
- P2-4 已成立並修正：全專案舊 build 指令文字統一為 `python3 scripts/build.py`，並重建 `index.html`。
- v1.1 第 5 階段 Claude Code（VS Code）複審通過，無 P0/P1 殘留；6 項 P2 排入 v1.2 backlog。Commit 2422245 為 v1.1 最終存檔。
- v1 收尾修正（commit f0fb601）第 5 階段 Claude Code（VS Code）複審通過，無 P0/P1/P2 殘留。
- v1.2 實作完成（commit 90c6d5b）：combos 引用 build-time 檢查、state board textarea oninput 修正游標失焦、目前階段正則支援中文數字、命名統一。P2 #2/#3/#6 已清除。
- v1.3 實作完成（待 commit）：Windows/macOS 桌面捷徑、移除 Linux 支援說法、禁止安裝腳本自動刪除暫存。Claude Code（VS Code）複審通過，無 P0/P1。
- v1.4 實作完成（待 commit）：移除 KeepTemp 參數、`.gitignore` 加入 `server-*.log`、`STATE_SECTIONS` 加維護注釋、重建 `index.html`。Claude Code（VS Code）複審通過，無 P0/P1。
- v1.5 實作進行中：`skills/dual-ai-workflow/SKILL.md` 已加入「上下文壓縮觸發規則」。
- v1.5 提示詞卡已新增：`data/prompts.yaml` 加入「上下文壓縮接續摘要」，`flow: dualai`、`stage: context-compact`。
- v1.5 控制台顯示已同步：`scripts/build.py` 新增 `context-compact` stage metadata 與排序，並重建 `index.html`。
- v1.5 build 驗證完成：`scripts/build.py` 成功輸出 45 skills / 39 prompts / 3 combos。
- v1.5 P1 已修正：已執行 `scripts/update_backup_skill.py` 更新 `codex-skills-backup.tar.gz`，備份包內 `skills/dual-ai-workflow/SKILL.md` 已包含「上下文壓縮觸發規則」。
- v1.5 本機 skill 已同步：`~/.codex/skills/dual-ai-workflow/SKILL.md` 與 `~/.claude/skills/dual-ai-workflow/SKILL.md` 已覆蓋為新版。
- v1.5 四份 `SKILL.md` MD5 實測一致：repo 版、備份包內版本、Codex 安裝版、Claude 安裝版皆為 `b5ba5093bd1af782a51049cc72660709`。
- v1.5 Claude Code（VS Code）P1 修正後複審通過，無 P0/P1，允許 commit。

下一步：
- 請 Claude Code（VS Code）審查本輪排版與開發進度功能修改，依 P0/P1/P2 回報。
- 若 Claude Code（VS Code）審查 OK，使用者再決定是否讓 Codex push `origin/main`。
- 後續若繼續 v1.8，可把 2 項 P2 與下一個任務（MVP A 或 v1.8 收尾）一併處理。

未解決問題：
- v1.8 後續優化：
  - P2-1：`progressHtml()` 未解決問題警示對「全部 ✅」backlog 仍會觸發；建議後續加入「全部 ✅ 視為無」判斷。
  - P2-2：`summary.replace(/<\/div>$/, ...)` 隱性依賴 `stateSummaryHtml()` 結尾；建議後續改為將 `nextCard` 作為參數或在 `progressHtml()` 直接拼裝。
- v1.2 backlog（已清除項目以 ✅ 標記）：
  - ✅ P2 #1 sectionAfter lookahead 改用固定 section 名稱白名單（v1.7 已修）
  - ✅ P2 #2 state board textarea 拆 oninput 路徑（v1.2 commit 90c6d5b 已修）
  - ✅ P2 #3 目前階段正則加入中文數字（v1.2 commit 90c6d5b 已修）
  - ✅ P2 #4 v1 沿用未修：control 按鈕 search query 對不到 prompts（v1.7 已修）
  - ✅ P2 #5 placeholder「三 AI」改「三方 AI」（v1.1 已修，backlog 條目為誤留）
  - ✅ P2 #6 build.py 加 combos 引用 build-time 檢查（v1.2 commit 90c6d5b 已修）

最後更新時間：2026-06-06 Codex v1.8 MVP B 排版修正完成，已交給 Claude Code（VS Code）審查後再決定是否 push
