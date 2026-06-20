# 版本紀錄

本文件用繁體中文記錄每次推到 GitHub 的主要變更，方便之後回頭看「這一版增加了什麼功能」。

## 未發布

### 新增

- macOS：新增「開機自動啟動」一鍵安裝。雙擊 `安裝開機自動啟動 (macOS).command` 後，每次登入就會自動跑本地控制台 + 桌面浮動小視窗，不用再手動雙擊任何按鈕。底層是 `~/Library/LaunchAgents/com.kagenhsu.quota-guardian.autostart.plist`，要關掉雙擊 `移除開機自動啟動 (macOS).command` 即可。log 在 `~/Library/Logs/QuotaGuardian/`。
- Windows：新增三個 `.bat` 入口（`開啟配額守門員.bat` / `更新並開啟控制台.bat` / `開啟控制台與配額守門員.bat`）對齊 macOS 上的同名按鈕，第一次讓 Windows 使用者也能雙擊就用。
- Windows：新增「開機自動啟動」一鍵安裝（`安裝開機自動啟動 (Windows).bat`）。底層在 Startup folder 放一個指向 `%APPDATA%\QuotaGuardian\launcher.vbs` 的捷徑，登入後完全不跳黑色 cmd 視窗。
- Windows：新增桌面浮動小視窗 `scripts/quota_guard_floating.py`（Tkinter 版）。資料來源跟 swift 版一樣是 `quota_guard_snapshot.py`，文案、顏色、刷新頻率、「複製切換／最終交接提示詞」按鈕都對齊 swift 版。

### 改善與修正

- v2.5 補修 macOS 開機自動啟動：LaunchAgent 不再直接執行 `~/Documents/...` 內的 repo，改為安裝時同步 runtime 到 `~/Library/Application Support/QuotaGuardian/runtime/` 後再啟動，避開 `Operation not permitted`。
- v2.5 補修本地控制台埠策略：`serve_console.py` 與自動啟動 payload 改為優先使用 `127.0.0.1:7000~7999`，避免撞上其他常見本機開發服務的 8000。
- Windows 自動啟動 payload 修正 `py.exe -w` 啟動方式，避免把 `py.exe -w` 當成單一執行檔路徑。
- 配額守門員補強 Claude Code context proxy：`latest_session_usage_proxy()` 不再只看 3 個最新 session 檔，避免新開多個尚未收到 assistant 回覆的 session 時誤判成沒有可用 context 資料。
- 浮動窗改為依內容自動撐高，避免 Claude Code 視窗從 2 行變 3 行後卡片擠到 footer。

## v2.4.0 — 專案開發分頁說明卡與 plan-progress skill

發布日期：2026-06-16

### 一句話說明

把「專案接續」分頁升級成「專案開發（雙刀／單刀）」：上方新增 Claude Code × Codex 搭配說明卡、下方開發階段卡改成單欄可摺疊版面、並會根據專案資料夾內實際存在的檔案自動告訴你「目前做到哪一階段、下一個小步驟是什麼」。同步新增 `plan-progress` skill，讓 Codex / Claude Code 在終端機也能跑出同樣的進度報告。

### 新增功能

- 「專案接續」分頁重新命名為「**專案開發（雙刀／單刀）**」（連結與頁面標題）。
- 分頁最上方新增「**🗡️ Claude Code × Codex：怎麼搭配開發專案**」可摺疊資訊卡，含：
  - 兩個 AI 各自的角色（Codex 主力工程師 / Claude Code 審查員）
  - 雙刀流 6 棒流程（規劃 → 實作 → 審查 → 修正 → 複審 → 收尾）
  - 單刀流 3 段（釐清 → 分段 → 自審）
  - 何時用雙刀流 vs 單刀流的對照
  - 三條共用紀律
- 「本專案的全部開發階段」資訊卡改為**單欄可摺疊**版面：
  - 點階段標題可展開／收合，目前進行中的階段預設展開
  - 每張卡片含狀態徽章（✓ 已完成 / ⏳ 進行中 / ⏳ 部分完成 / ⭕ 尚未開始 / 參考）
- 新增「**進度看板**」自動偵測：
  - 依專案資料夾內實際存在的關鍵檔案，判斷每個小步驟（如 4.3、6.5）是否完成
  - 顯示「目前階段」「下一個小步驟」「總進度條（N / Total + %）」
  - 每個小步驟旁有獨立狀態：✓ 已完成（綠底劃線）／➤ 目前要做（黃底）／○ 尚未開始
- 新增 `plan-progress` **skill**（規劃與協作分類）：
  - 讀 `專案規劃表.md` 後對照資料夾檔案，輸出進度報告
  - 第一次跑會推論並寫進 `.plan-rules.yaml` 快取，第二次起無需重推
  - 不修改任何原始檔（除規則快取），不執行 git 寫操作
- 新增專案根目錄 `**專案規劃表.md**`：7 個階段（第 0–6 階段）×「要做什麼／細項開發步驟／會產出什麼／完成判斷」四段式格式。

### 技術變更

- `build.py` 新增 `collect_console_paths()`：掃描 ROOT 內檔案內嵌為 `CONSOLE_FILE_PATHS`，供前端進度偵測；跳過 `.git/` 內檔避免 HTML 過肥，僅保留標記路徑供「2.3 初始化 Git」偵測。
- `progressSource()` 與 `loadProjectFolder()` 新增 `filePaths` 欄位。
- `parseProjectPlanStages()` 改為輸出含小步驟 ID 的 bullets（`{id, text}`）。
- 新增 `PLAN_DETECTION_RULES`（31 條規則）與 `detectPlanDone()` 偵測 helper。
- 新增 CSS：`.plan-progress-banner`、`.plan-list`、`.plan-stage`、`.plan-step` 等單欄摺疊卡片所需樣式。
- `.gitignore` 加 `!skills/plan-progress/` 例外，讓新 skill 進得了版控。

### 驗證結果

- `python3 scripts/build.py` 成功輸出：`50 skills / 50 prompts / 3 combos`
- `node --check` 抽出的 inline script 通過語法檢查。
- 偵測規則對本控制台 13 個關鍵小步驟全數命中（含 `.git`、`AGENTS.md`、`PRD.md`、`README.md`、`install.sh/ps1`、`build.py`、`data/skills.yaml`、`data/prompts.yaml`、`codex-skills-backup.tar.gz`、`CHANGELOG.md`、`restore-skills.sh`、`index.html`）。

## v2.1.0 — 新手分工提示與雙 AI 專案討論

發布日期：2026-06-06

### 新增功能

- 首頁「二刀流最簡單分工」新增可直接複製的分工說明、Codex 開工、Claude Code 審查與單一 AI 提示詞。
- 「新手先按：複製分工細節說明」按鈕獨立置中顯示，讓第一次使用的人先理解 Codex / Claude Code 分工。
- 提示詞庫新增「二刀流分工細節說明」，用來向新手或同事說明兩個 AI 的角色、交接方式與注意事項。
- 日常提示詞「開發系統」新增「雙 AI 討論新專案方向」，可從模糊想法開始，透過 Codex 工程視角與 Claude Code 審查視角互動討論出專案規劃。
- README 開頭新增線上試用版（demo）連結，讓 GitHub repo 首頁能直接進入 GitHub Pages demo。

### 驗證結果

- `python3 scripts/build.py` 成功輸出：`45 skills / 41 prompts / 3 combos`
- `node --check` 抽出的 inline script 通過語法檢查。

## v2.0.0 — 日常提示詞新手版與 GitHub Pages demo

發布日期：2026-06-06

### 新增功能

- 新增「日常提示詞」頁籤，提供新手可直接複製的日常 AI 交辦提示詞。
- 新增開發系統、找資料 / 做比對、整理資料、整理電腦檔案等分類。
- 首頁調整為「首頁 / 快速開始」，更適合第一次使用的人理解二刀流流程。
- 加入 GitHub Pages demo banner，線上試用版會提醒使用者這是 demo。
- 新增 `robots.txt`，避免 demo 頁被搜尋引擎收錄本機開發狀態內容。

### 驗證結果

- `python3 scripts/build.py` 成功輸出：`45 skills / 40 prompts / 3 combos`
- `node --check` 抽出的 inline script 通過語法檢查。

## v1.9.0 — 二刀流命名統一

發布日期：2026-06-06

### 改善與修正

- 將專案與網頁主標統一為「二刀流開發助手控制台」，副標為「Codex × Claude Code 開發系統」。
- 將控制台頁籤、提示詞分類、角色導覽、工作流說明與 Skill 目錄說明統一為「二刀流」命名。
- 移除控制台內容中的第三角色描述，二刀流流程只保留 Codex 與 Claude Code（VS Code）。
- 補上開發進度「專案版本地圖」中的 v1.9 階段，讓目前版本可被藍框標出。
- 清除「單一 AI 也能用控制台」提示詞中的舊產品名稱。
- 調整二刀流交棒節奏：每個 AI 先完成自己這一棒，再於回報最後輸出給下一棒的提示詞。
- 收錄新內容頁新增「填上方表單 → 下方自動產生」連結帶，讓提示詞／Skill 表單與下方交辦提示詞、YAML 卡片的關係更清楚。
- 修正 Claude Code（VS Code）複核提出的 v1.9 修正包：`normalize_role_docs.py` 保留 SKILL description 與交棒節奏、`dual-ai-workflow` trigger 去重，並重新同步備份包與本機安裝版。
- 簡化 Skill 收錄表單：改成只貼 Skill 網址或資料夾路徑，下方自動產生「安檢流程 → 安全才安裝 → 同步 Codex / Claude Code → 收錄控制台」提示詞。
- 移除獨立安檢頁籤；安檢流程已整合進「收錄新內容」的 Skill 收錄提示詞。

### 驗證結果

- `python3 scripts/build.py` 成功輸出：`45 skills / 40 prompts / 3 combos`
- `node --check` 抽出的 inline script 通過語法檢查。

## v1.7.0 — 二刀流中控與狀態解析收尾

發布日期：2026-06-05

### 改善與修正

- 二刀流中控按鈕改為記住目標提示詞卡，跳到提示詞庫後優先捲到該卡片；若找不到才退回階段 section。
- `sectionAfter` 狀態解析改用固定欄位白名單，避免被非狀態欄位文字誤截斷。
- 新增 macOS 中文入口 `更新並開啟控制台.command`，可一鍵重建並開啟本機控制台。
- `docs/v1-2-backlog.md` 標記剩餘 P2 已於 v1.7 清除。
- 補齊 v1.2 backlog #2、#3、#6 的 ✅ 標記，避免下一輪 AI 誤判未修。
- README 補上 macOS quarantine 提醒：第一次雙擊 `.command` 被擋時，可右鍵打開或移除 quarantine 屬性。

### 驗證結果

- `python3 scripts/build.py` 成功輸出：`45 skills / 40 prompts / 3 combos`
- `更新並開啟控制台.command` 已設為可執行檔。

## v1.1.0 — AI 工作流控制台與收錄流程強化

發布日期：2026-06-04

### 新增功能

- 新增「收錄新內容」頁籤，可選擇收錄「提示詞」或「Skill」。
- 收錄表單會同時產生兩塊內容：
  - 推薦複製：給 Codex 的完整交辦提示詞
  - 進階檢查：YAML 片段
- Skill 收錄表單加入安檢 gating：未勾選「已跑過 Skill 安裝前資安檢查」時，不啟用 Codex 交辦提示詞。
- 新增「二刀流中控」頁籤，提供五階段流程卡與快速複製入口。
- 新增 `DUAL-AI-STATE` 快速看板，可貼上狀態檔並在本機瀏覽器解析目前階段、上一步、下一步與未解決問題。
- 新增「常用組合包」功能，用 `data/combos.yaml` 把常用提示詞組成一包複製。
- 新增 3 組初始組合包：
  - 開新專案起手包
  - 二刀流審查修正包
  - 跨地點接續包
- 提示詞庫新增「專案啟動」快捷篩選。
- 新增「首次上傳 GitHub：繁體中文專案敘述」提示詞卡。
- 新增「跨地點 / 跨系統接續」提示詞卡，支援 macOS / Windows 接續流程。

### 改善與修正

- 預設落地頁改為「AI 角色導覽」，避免新手第一眼落到「換電腦／同步」。
- 二刀流中控按鈕改為切到提示詞庫的二刀流協作模式，不再把 stage 標題塞進搜尋框，避免出現空列表。
- 搜尋 placeholder 統一使用「二刀流」。
- 全專案 build 指令統一為 `python3 scripts/build.py`。
- `skills/dual-ai-workflow/SKILL.md` 統一 LF 行尾，並同步備份包與本機安裝版。
- 多裝置同步提醒補上：
  - macOS 使用 `./restore-skills.sh`
  - Windows 使用 `install.ps1`
- `DUAL-AI-STATE.md` 與文件路徑避免暴露本機絕對路徑，改用 `~/` 或相對路徑。

### 驗證結果

- `python3 scripts/build.py` 成功輸出：`45 skills / 38 prompts / 3 combos`
- GitHub push 前已做敏感資料快篩。
- Claude Code（VS Code）已完成第 5 階段複審。

### 後續 v1.2 Backlog

- `sectionAfter` 改用固定 section 名稱白名單。
- state board textarea 避免輸入時 re-render 造成游標失焦。
- 目前階段解析支援中文數字。
- `build.py` 增加 combos 引用 build-time 檢查。
