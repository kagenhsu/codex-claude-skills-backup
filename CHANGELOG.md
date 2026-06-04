# 版本紀錄

本文件用繁體中文記錄每次推到 GitHub 的主要變更，方便之後回頭看「這一版增加了什麼功能」。

## v1.1.0 — AI 工作流控制台與收錄流程強化

發布日期：2026-06-04

### 新增功能

- 新增「收錄新內容」頁籤，可選擇收錄「提示詞」或「Skill」。
- 收錄表單會同時產生兩塊內容：
  - 推薦複製：給 Codex 的完整交辦提示詞
  - 進階檢查：YAML 片段
- Skill 收錄表單加入安檢 gating：未勾選「已跑過 Skill 安裝前資安檢查」時，不啟用 Codex 交辦提示詞。
- 新增「三方中控」頁籤，提供五階段流程卡與快速複製入口。
- 新增 `DUAL-AI-STATE` 快速看板，可貼上狀態檔並在本機瀏覽器解析目前階段、上一步、下一步與未解決問題。
- 新增「常用組合包」功能，用 `data/combos.yaml` 把常用提示詞組成一包複製。
- 新增 3 組初始組合包：
  - 開新專案起手包
  - 三方審查修正包
  - 跨地點接續包
- 提示詞庫新增「專案啟動」快捷篩選。
- 新增「首次上傳 GitHub：繁體中文專案敘述」提示詞卡。
- 新增「跨地點 / 跨系統接續」提示詞卡，支援 macOS / Linux / Windows 接續流程。

### 改善與修正

- 預設落地頁改為「AI 角色導覽」，避免新手第一眼落到「換電腦／同步」。
- 三方中控按鈕改為切到提示詞庫的三方 AI 協作模式，不再把 stage 標題塞進搜尋框，避免出現空列表。
- 搜尋 placeholder 統一使用「三方 AI」。
- 全專案 build 指令統一為 `python3 scripts/build.py`。
- `skills/dual-ai-workflow/SKILL.md` 統一 LF 行尾，並同步備份包與本機安裝版。
- 多裝置同步提醒補上：
  - macOS / Linux 使用 `./restore-skills.sh`
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
