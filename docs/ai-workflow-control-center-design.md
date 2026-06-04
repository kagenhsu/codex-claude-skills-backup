# 三方 AI 協作中控台設計規格

版本：v1.0（2026-06-04）  
狀態：第 1 階段設計修正版，等待使用者確認後進入第 2 階段實作

## 1. 背景

目前控制台已能查詢 skills、複製提示詞、查看三方 AI 工作流與角色導覽。下一步希望把它升級成更完整的「AI 協作中控台」：

- 遇到新的好用 skill 或提示詞時，能用表單收錄，產生 YAML 片段與給 Codex 的完整交辦提示詞。
- 三方 AI 工作流進行中，能用靜態教學與提示詞快速入口提醒使用者下一步該找誰。
- 開新專案時，能更容易找到建立 `AGENTS.md`、PRD、規則文件等專案啟動提示詞。
- 使用者在公司、家裡、Windows 電腦、Mac mini 或其他電腦之間切換時，能用 git 與狀態檔把專案安全接續。

核心原則：AI 可以協助轉交與整理，但不能在使用者看不到的情況下私下互相決定。

## 2. 目標

v1 要做到：

1. 控制台新增 `收錄新內容` 頁籤。
2. 控制台新增 `三方中控` 頁籤，但 v1 僅做靜態教學版。
3. 在既有 `提示詞庫` 中強化 `專案啟動` 快捷篩選，不新增 `專案規劃` 獨立頁籤。
4. 所有自動化動作都先產生「可檢查內容」，再由使用者複製給 Codex。
5. 純 HTML 不能直接安全寫檔，因此 v1 只生成提示詞、生成 YAML、複製，不直接寫入檔案。

## 3. 不做的事

- v1 不直接從瀏覽器寫入 `data/*.yaml`。
- v1 不自動 push GitHub。
- v1 不讓 AI 私下互傳訊息。
- v1 不讀取 `DUAL-AI-STATE.md` 或任何本機狀態檔。
- v1 不建立 `.ai-workflow/` 檔案系統。
- v1 不做 Codex thread、Claude Code（VS Code）或 Claude Desktop 的自動送出。
- v1 不安裝陌生 skill；skill 收錄必須先經過安檢提示。
- v1 不在未經使用者確認時自動 push；跨地點同步必須先顯示本次要同步的內容與風險提醒。

## 4. 功能群一：專案啟動快捷入口

### 4.1 用途

使用者和 AI 討論完新專案方向後，可以從 `提示詞庫` 快速找到建立 `AGENTS.md`、PRD 或專案規則文件的提示詞。v1 不新增 `專案規劃` 獨立頁籤，避免第一版範圍過大。

### 4.2 v1 呈現方式

在既有 `提示詞庫` 中加入或強化 stage / category 篩選快捷鈕：

- 快捷鈕名稱：`專案啟動`
- 篩選目標：`category: 專案啟動`
- 目標使用者：討論完設計方向後，需要建立專案規則、PRD 或初始化文件的人

### 4.3 `AGENTS.md` 提示詞卡

v1 若新增或調整提示詞，應在 `data/prompts.yaml` 中以提示詞卡形式處理，不做獨立表單。

v1 要在 `data/prompts.yaml` 新增或保留以下專案啟動與交接相關卡片：

- `設計方向確認後建立 AGENTS.md`
- `首次上傳 GitHub：繁體中文專案敘述`
- `跨地點 / 跨系統接續`

提示詞用途：

> 討論完設計方向後，請 Codex 建立或更新專案根目錄 `AGENTS.md`，讓後續 AI 接手時知道專案規則、工作方式與注意事項。

提示詞要求 Codex：

1. 建立或更新專案根目錄 `AGENTS.md`。
2. 寫入專案名稱、目標、協作規範、檔案結構、修改與測試注意事項。
3. 不確定的地方列成「待確認問題」，不要自行亂補。
4. 建立文件後回報改了什麼，但不自動 push。

### 4.4 未來獨立頁籤條件

若日後要把 `專案規劃` 獨立成頁籤，至少要有 3 張功能卡，避免只有單一卡片造成頁籤太薄：

- `建立 AGENTS.md`
- `建立 PRD`
- `建立 .gitignore + 種子 DUAL-AI-STATE`

### 4.5 草稿保存

如果未來 `專案規劃` 做成表單，表單草稿使用瀏覽器 LocalStorage 暫存，純本機、不上傳。

### 4.6 GitHub 首次上傳與專案敘述規範

專案啟動提示詞必須加入 GitHub 首次上傳規則：

- 第一版 GitHub repo 名稱、repo description、README 摘要、commit message、release / changelog 摘要，預設都採用繁體中文。
- 除非使用者明確要求，或網友／協作者建議需要多語言版本，才增加英文或其他語言。
- v1 新增獨立提示詞卡 `首次上傳 GitHub：繁體中文專案敘述`；上傳 GitHub 前，AI 必須詢問開發者：「這個版本主要做了哪些動作？」用來整理 commit message、README 摘要或 release note。
- 若開發者沒有補充，AI 可以根據 git diff、已完成事項與 `DUAL-AI-STATE.md` 自動整理繁體中文版本摘要，但必須讓使用者確認後再 push。
- push 前仍要提醒檢查是否包含敏感資料，例如 API key、`.env`、SSH key、私人對話或不該公開的壓縮包內容。

### 4.7 跨地點與跨系統接續

專案啟動與三方工作流提示詞應支援「跨地點、跨系統接續」情境；v1 新增獨立提示詞卡 `跨地點 / 跨系統接續`。

- 使用者下班、休息、換到家裡 Windows 電腦、公司 Windows 電腦、Mac mini 或其他電腦前，可以請 Codex 做「接續存檔」。
- 接續存檔流程包含：
  1. 檢查 `git status`。
  2. 更新 `DUAL-AI-STATE.md`，寫清楚目前做到哪裡、下一步要做什麼、未解決問題。
  3. 根據本次實際變更整理繁體中文 commit message。
  4. 建立本地 commit。
  5. 詢問使用者是否要 push 到 GitHub，不能自動 push。
  6. push 前提醒檢查敏感資料與大檔案。
- 使用者到另一台電腦接續時，提示詞要引導：
  1. 先執行 `git pull --ff-only`。
  2. 讀取 `DUAL-AI-STATE.md`。
  3. 用三行摘要回報目前階段、上一步、下一步。
  4. 再詢問是否繼續設計、實作或複審。
- 這個功能不等於自動備份所有檔案；它只用 git 同步已 commit 的專案狀態。
- 若工作樹有未 commit 內容，AI 必須提醒使用者先決定要 commit、暫存、還是放棄本次修改。
- Windows 與 macOS / Linux 要分開顯示指令：
  - Windows PowerShell：`git status`、`git pull --ff-only`、`git push origin main`。
  - macOS / Linux / Git Bash：同樣使用 `git status`、`git pull --ff-only`、`git push origin main`。
- 如果涉及 skill 同步，要提醒 Windows 與 macOS 的 skills 路徑可能不同：
  - Windows 常見路徑：`$HOME\.codex\skills\`、`$HOME\.claude\skills\`
  - macOS / Linux 常見路徑：`~/.codex/skills/`、`~/.claude/skills/`
- 若跨系統造成行尾差異，`skills/dual-ai-workflow/SKILL.md` 以 LF 為標準，重新打包或同步前要確認不要變成 CRLF。

## 5. 功能群二：收錄新內容

### 5.1 用途

使用者看到新的好用 skill 或提示詞時，不需要懂 YAML。只要填表單，控制台會產生：

- 推薦複製：給 Codex 的完整交辦提示詞
- 進階檢查：YAML 片段

### 5.2 頁籤名稱

`收錄新內容`

### 5.3 內容類型

表單第一步先選：

- `提示詞`
- `Skill`

### 5.4 提示詞表單欄位

- 標題：控制台卡片名稱
- 分類：下拉選單 + `其他` 自由填
- 用途：什麼時候使用
- 適用流程：`common` / `dualai` / `solo`
- 階段：例如 `entry`、`3`、`4`、`5`、`archive`、空白
- 提示詞原文

分類下拉預設選項使用目前 `data/prompts.yaml` 已存在的 category：

- `專案啟動`
- `開發過程`
- `版本控制`
- `整合串接`
- `上線部署`
- `三方 AI 協作`
- `Skill 管理`
- `安全檢查`
- `三方 AI 工作流`
- `單AI精簡`
- `其他`

### 5.5 Skill 表單欄位

Skill 表單頂端必須有 checkbox：

> 我已對 skill 跑過「Skill 安裝前資安檢查」提示詞。

規則：

- checkbox 預設未勾。
- 未勾時，不顯示或停用「產生 Codex 交辦提示詞」按鈕。
- 未勾時仍可顯示 YAML 片段預覽，但要加上醒目提醒：尚未安檢，不建議收錄或安裝。
- 風險等級預設為 `中`，使用者可改為 `低` 或 `高`。

Skill 表單欄位：

- skill 名稱
- 來源：GitHub URL、資料夾路徑或來源描述
- 分類
- 風險等級：低 / 中 / 高，預設中
- 用途摘要
- 觸發句，支援多行
- 注意事項

Skill 表單要顯示安全提醒：

> 陌生來源的 skill 請先做安檢。不要直接安裝會讀取金鑰、執行不明腳本或要求忽略規則的 skill。

### 5.6 產出的 Codex 交辦提示詞

表單產生的交辦提示詞採完整模式：

1. 請 Codex 檢查內容格式與風險。
2. 寫入 `data/prompts.yaml` 或 `data/skills.yaml`。
3. 執行 `python3 scripts/build.py` 重建 `index.html`。
4. 驗證 `index.html` 搜尋得到新卡片。
5. 建立本地 git commit。
6. 明確不要 push `origin/main`。

### 5.7 第一批內建提示詞狀態

以下三張提示詞已實作於 commit `0d95854`，本版不再新增：

- `給 Codex 的存檔收尾提示詞`
- `給 Codex 的逐條修正轉交提示詞`
- `設計方向確認後建立 AGENTS.md`

本設計文件只規範後續如何在控制台收錄新內容，不把這三張卡列入 v1 實作範圍。

### 5.8 草稿保存

`收錄新內容` 表單草稿使用瀏覽器 LocalStorage 暫存，純本機、不上傳。草稿只用來避免使用者填到一半關頁後遺失內容，不作為正式資料來源。

## 6. 功能群三：三方中控

### 6.1 用途

把三方 AI 工作流從「手動轉貼」升級成更清楚的「透明中控」。v1 不做動態狀態或自動送出，只做靜態五階段教學與提示詞快速入口。

### 6.2 頁籤名稱

`三方中控`

### 6.3 核心規則

每個交接入口都要顯示：

- 要交給誰：Codex / Claude Code（VS Code）/ Claude Desktop
- 為什麼交給它：規劃、實作、審查、修正、複審、文件整理、存檔收尾
- 使用者下一步要做什麼：跳到提示詞庫、複製提示詞、貼到對應 AI

v1 不顯示「自動送出」字樣，不暗示控制台能直接送訊息給其他 AI。

### 6.4 三方通道策略

v1 全部走複製貼上或交接包檔，不做自動送出。v4 才探索自動送出，且不承諾時程。

| 角色 | v1 策略 | 未來探索 |
|---|---|---|
| Codex | 產生或導向可複製給 Codex 的提示詞 | v4 才探索 Codex thread 自動送出 |
| Claude Code（VS Code） | 產生或導向可貼到 VS Code Claude Code 的提示詞 | v4 才探索可用通道 |
| Claude Desktop | 產生或導向可貼到 Claude Desktop 的提示詞 | v4 才探索可用通道 |

### 6.5 狀態資料

v1 保留 `DUAL-AI-STATE.md` 作為人類可讀狀態，但控制台不讀取它。

未來可新增 `.ai-workflow/`：

```text
.ai-workflow/
├── state.json
├── outbox/
│   ├── 2026-06-04-to-claude-code-review.md
│   └── 2026-06-04-to-codex-fix.md
└── history/
    └── 2026-06-04-events.jsonl
```

第三期若新增 `.ai-workflow/state.json`，它與 `DUAL-AI-STATE.md` 並存：

- `DUAL-AI-STATE.md`：人類可讀，供使用者與 AI 快速理解目前狀態。
- `.ai-workflow/state.json`：機器可讀，供控制台或工具自動產生交接包。

第三期不取代 `DUAL-AI-STATE.md`。若未來要取代，必須同步修改 `skills/dual-ai-workflow/SKILL.md` 與 `docs/dual-ai-workflow.md`。

### 6.6 中控台顯示

v1 不讀取 `DUAL-AI-STATE.md`，只顯示靜態五階段教學與對應提示詞快速入口。動態狀態顯示延到 v2，等 `.ai-workflow/state.json` 規格定下來再做。

頁面顯示：

- 五階段流程卡：第 1 階段到第 5 階段
- 每階段負責角色
- 每階段目的
- 每階段對應提示詞入口
- 小白版說明：現在這一步是在做什麼

範例快速入口：

- `第 1 階段：Codex 規劃`：跳到提示詞庫 `stage: 1` 並複製對應 prompt
- `第 2 階段：Codex 分段實作`：跳到提示詞庫 `stage: 2` 並複製對應 prompt
- `第 3 階段：Claude Code 審查`：跳到提示詞庫 `stage: 3` 並複製對應 prompt
- `第 4 階段：Codex 修正`：跳到提示詞庫 `stage: 4` 並複製對應 prompt
- `第 5 階段：Claude Code 複審`：跳到提示詞庫 `stage: 5` 並複製對應 prompt
- `存檔收尾`：跳到提示詞庫 `stage: archive` 並複製對應 prompt
- `Claude Desktop 整理主管版說明`：跳到提示詞庫 `stage: desktop-summary` 並複製對應 prompt

點按鈕的含義是「跳到提示詞庫對應 stage + 複製對應 prompt」，不是自動送出，也不是讀取目前狀態後決定下一步。

### 6.7 stage 命名規範

以下列表是前端下拉選單與 `STAGE_META` 的唯一來源。新增 stage 前要先更新本節。

| stage | 說明 |
|---|---|
| `entry` | 啟動或接續某個流程的入口提示詞 |
| `1` | 第 1 階段：Codex 規劃 |
| `2` | 第 2 階段：Codex 分段實作 |
| `3` | 第 3 階段：Claude Code（VS Code）審查 |
| `4` | 第 4 階段：Codex 逐條修正 |
| `5` | 第 5 階段：Claude Code（VS Code）複審 |
| `handoff` | 一方 AI 產出後，轉交給另一方接續 |
| `status` | 讀取或更新 `DUAL-AI-STATE.md` 的狀態提示詞 |
| `archive` | 第 5 階段通過後，交給 Codex 做驗證、狀態檔、commit、push 決策的存檔收尾 |
| `desktop-summary` | 交給 Claude Desktop 整理需求、主管版說明、文件或提示詞 |

## 7. UI 設計原則

- 不要求使用者懂 YAML。
- 新手推薦複製「給 Codex 的完整交辦提示詞」。
- YAML 片段標為進階檢查用。
- 每個欄位都要有一句白話說明。
- 危險或不可逆動作要明確提醒，例如安裝陌生 skill、commit、push。
- 頁面文字要短，避免把使用者淹沒在規則裡。
- 所有草稿只存在瀏覽器 LocalStorage，純本機、不上傳。
- 涉及 GitHub 專案敘述、版本摘要、README、release note 時，預設用繁體中文，除非使用者明確要求多語言。
- 跨地點同步提示詞要用白話說明：「現在是把這台電腦的進度存到 GitHub，讓公司、家裡、Windows 或 Mac 電腦可以 pull 下來接著做。」

## 8. 技術設計

現有 `scripts/build.py` 已把 YAML 資料與 Markdown 文件編譯成單一 `index.html`。v1 可直接擴充這個模板：

- 新增 `capture` tab：`收錄新內容`。
- 新增 `control` tab：`三方中控` 靜態教學版。
- 強化 `prompts` tab：加入 `專案啟動` 快捷篩選。
- 在前端 JavaScript 中加入表單狀態、LocalStorage 草稿、YAML 字串生成、Codex 交辦提示詞生成。
- 不新增外部依賴。
- 不需要後端服務。

資料仍由使用者或 Codex 寫入 `data/*.yaml`，控制台只負責產生內容與複製。

## 9. 驗證方式

實作完成後至少驗證：

1. `python3 scripts/build.py` 成功。
2. 雙擊 `index.html` 可看到新增 `收錄新內容` 與 `三方中控` 頁籤。
3. 既有六個頁籤功能與搜尋未被打破：`Skills`、`提示詞庫`、`三方 AI 工作流`、`AI 角色導覽`、`安檢 SOP`、`換電腦／同步`。
4. `提示詞庫` 能用 `專案啟動` 快捷篩選找到建立 `AGENTS.md` 類提示詞。
5. `收錄新內容` 選提示詞時，能產生 prompt YAML 與 Codex 交辦提示詞。
6. `收錄新內容` 選 Skill 時，預設風險為中，未勾安檢 checkbox 時不能產生 Codex 交辦提示詞。
7. `收錄新內容` 的表單草稿可用 LocalStorage 暫存，重新整理後不遺失。
8. `三方中控` 只顯示靜態五階段教學與提示詞快速入口，不讀取 `DUAL-AI-STATE.md`。
9. `三方中控` 快速入口的按鈕語意是跳到提示詞庫對應 stage 並複製 prompt，不暗示自動送出。
10. 專案啟動或 GitHub 上傳相關提示詞會要求版本敘述使用繁體中文，並在 push 前詢問或自動整理「這個版本做了哪些動作」。
11. 跨地點 / 跨系統接續提示詞會要求更新 `DUAL-AI-STATE.md`、commit、詢問是否 push，並在另一台 Windows 或 macOS 電腦以 `git pull --ff-only` 接續。
12. 搜尋「角色」「翻譯」「審查」仍能命中既有對應內容。

## 10. 分期建議

### 第一期：v1 範圍鎖定

只做：

- `收錄新內容` tab。
- Skill 收錄的安檢 gating：必勾「我已對 skill 跑過『Skill 安裝前資安檢查』提示詞」才顯示或啟用 Codex 交辦提示詞按鈕。
- 雙產出區塊：
  - 推薦複製：Codex 交辦提示詞。
  - 進階檢查：YAML 片段。
- 表單草稿 LocalStorage 暫存，純本機、不上傳。
- `三方中控` tab 靜態教學版。
- `提示詞庫` 加 `專案啟動` 快捷篩選。
- 新增 2 張提示詞卡：`首次上傳 GitHub：繁體中文專案敘述`、`跨地點 / 跨系統接續`；更新 `data/prompts.yaml` 後執行 `python3 scripts/build.py` 重建 `index.html`。

不做：

- `專案規劃` 獨立 tab。
- 自動送出。
- 寫 YAML 的後端。
- `.ai-workflow/` 檔案系統。
- 動態讀取 `DUAL-AI-STATE.md`。

### 第二期：三方中控動態狀態

- 定義 `.ai-workflow/state.json` 規格。
- `三方中控` 才開始讀取機器可讀狀態。
- `DUAL-AI-STATE.md` 繼續保留為人類可讀狀態。

### 第三期：半自動交接檔

- 新增 `.ai-workflow/outbox/` 與 `.ai-workflow/history/`。
- 讓 Codex 可產生交接檔並記錄歷史。
- `.ai-workflow/state.json` 與 `DUAL-AI-STATE.md` 並存，不取代。

### 第四期：工具通道整合

- 才探索 Codex thread、Claude Code（VS Code）、Claude Desktop 的自動送出能力。
- 所有自動送出都必須先顯示內容並由使用者確認。
- 不承諾時程；若工具通道不可用，永久保留複製貼上模式。

## 11. 開放問題

- `archive` 與 `desktop-summary` 是否要立即補入 `data/prompts.yaml` 的提示詞卡，或等 v1 實作時一起補？
- `專案啟動` 快捷篩選要做成 flow switch、category chip，還是提示詞庫上方固定快捷按鈕？
- `收錄新內容` 產生 YAML 時，要採用最少欄位，還是顯示所有欄位供進階檢查？
- README 是否要補一段「如何收錄新內容」？
