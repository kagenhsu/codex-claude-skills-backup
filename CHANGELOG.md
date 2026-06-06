# 版本紀錄

本文件用繁體中文記錄每次推到 GitHub 的主要變更，方便之後回頭看「這一版增加了什麼功能」。

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
