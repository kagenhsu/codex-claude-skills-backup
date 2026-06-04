# DUAL-AI-STATE

任務名稱：AI 工作流控制台 v1 收尾修正

目前階段：✅ 已完成（v1 收尾修正第 5 階段複審通過）

已完成事項：
- 已讀取並依據本檔實際狀態接續，不沿用舊 MD5 聲明。
- P1-1 已成立並修正：`index.html` 預設頁籤改為「AI 角色導覽」，`backup` 頁籤移到最後；`scripts/build.py` 模板同步改為 `let tab = "guide"`。
- P1-2 已成立並修正：`skills/dual-ai-workflow/SKILL.md`、備份包內版本、`~/.codex` 安裝版、`~/.claude` 安裝版已統一為 LF 行尾。
- 已用 `scripts/update_backup_skill.py` 重打 `codex-skills-backup.tar.gz`，保留原備份包其他內容，只替換 `skills/dual-ai-workflow/SKILL.md`。
- 已同步 LF 版 `SKILL.md` 到 `~/.codex/skills/dual-ai-workflow/SKILL.md` 與 `~/.claude/skills/dual-ai-workflow/SKILL.md`。
- 已處理 P2-3：`.gitignore` 補上 `.DS_Store`、`skills/*`、`!skills/dual-ai-workflow/`。
- 已處理 P2-4：`PRD.md` 的 44 個 skill 改為 45 個（含 1 個自製 dual-ai-workflow）。
- 已處理 P2-5：`AGENTS.md` 專案檔案結構補上 `index.html`、安裝腳本、角色文件、自製 skill 與維護腳本。
- 已處理 P2-6：`data/skills.yaml` 與 `data/prompts.yaml` 改為三方 AI 命名，並重建 `index.html`。
- 已處理 P2-7：`install.sh` 與 `install.ps1` 加入暫存目錄 cleanup，並提供 `--keep-temp` / `-KeepTemp` 保留暫存檔。
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
- P2-2 已成立並修正：`跨地點 / 跨系統接續` 提示詞在 macOS/Linux 與 Windows 指令前補上同步全部 skills 請改用 `restore-skills.sh` / `install.ps1` 的提醒。
- P2-3 已成立並修正：搜尋 placeholder 的「三 AI」改為「三方 AI」。
- P2-4 已成立並修正：全專案舊 build 指令文字統一為 `python3 scripts/build.py`，並重建 `index.html`。
- v1.1 第 5 階段 Claude Code（VS Code）複審通過，無 P0/P1 殘留；6 項 P2 排入 v1.2 backlog。Commit 2422245 為 v1.1 最終存檔。
- v1 收尾修正（commit f0fb601）第 5 階段 Claude Code（VS Code）複審通過，無 P0/P1/P2 殘留。

下一步：
- 等待使用者決定是否 push 到 origin/main；v1.2 backlog 仍在 docs/v1-1-plan.md 或對應 backlog 文件中。

未解決問題：
- v1.2 backlog：
  - P2 #1 sectionAfter lookahead 改用固定 section 名稱白名單
  - P2 #2 state board textarea 拆 oninput 路徑避免 re-render 失焦
  - P2 #3 目前階段正則加入中文數字
  - P2 #4 v1 沿用未修：control 按鈕 search query 對不到 prompts
  - P2 #5 v1 沿用未修：placeholder「三 AI」改「三方 AI」
  - P2 #6 build.py 加 combos 引用 build-time 檢查

最後更新時間：2026-06-04 23:13 +0800
