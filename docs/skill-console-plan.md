# 二刀流開發助手控制台 — 規劃文件

版本：v1.0（2026-06-04）
形式：本機 HTML 單頁控制台（方案 A）

## 1. 背景與痛點

- 已安裝 44 個 skills（裝在 `~/.codex/skills` 與 `~/.claude/skills`，備份於本 repo）
- 痛點一：skill 太多，記不住每個的用途，更記不住「要說什麼話才會觸發」
- 痛點二：常用提示詞散落各處，每次要重打或翻舊對話

## 2. 系統目標

| 功能 | 說明 |
|---|---|
| Skill 目錄 | 列出全部已安裝 skill：中文用途說明、適用情境、注意事項 |
| 觸發句（核心） | 每個 skill 附 1–3 句現成觸發句，一鍵複製，貼進 CLI 即可調用 |
| 提示詞庫 | 常用 prompt 分類存放（翻譯、摘要、程式碼審查…），一鍵複製 |
| 搜尋 | 輸入關鍵字即時過濾 skill 與 prompt |

## 3. 呈現方式

- 單一檔案 `index.html`，雙擊用瀏覽器開啟，免安裝、離線可用
- 版面：上方搜尋列｜左側分類｜主區卡片（每張卡 = 一個 skill 或 prompt，含複製按鈕）
- 資料直接內嵌在 HTML 中，repo 同步時一併備份

## 4. 檔案結構（新增於本 repo）

```
codex-claude-skills-backup/
├── index.html              # 控制台成品（雙擊開啟）
├── data/
│   ├── skills.yaml         # 44 個 skill 的中文說明＋觸發句（初稿由 AI 從 SKILL.md 生成）
│   └── prompts.yaml        # 常用提示詞庫（手動維護）
├── scripts/
│   └── build.py            # 讀取 data/*.yaml → 重新產出 index.html
└── docs/
    └── skill-console-plan.md
```

## 5. 資料格式範例

```yaml
# skills.yaml
- name: baoyu-translate
  category: 內容處理
  summary: 中英雙向翻譯，保留 Markdown 格式與術語一致性
  triggers:
    - "用 baoyu-translate 把這篇文章翻成繁體中文"
  notes: 長文會分段處理

# prompts.yaml
- title: 會議摘要
  category: 文件產出
  prompt: |
    請將以下會議逐字稿整理成：決議事項、待辦（負責人＋期限）、未決議題三段。
```

## 6. 開發步驟

| 步驟 | 內容 | 誰做 |
|---|---|---|
| 1 | 解析備份檔中 44 個 SKILL.md，生成 skills.yaml 初稿（中文說明＋觸發句） | AI |
| 2 | 建立 prompts.yaml 範例分類（先放 5–10 個常用模板，之後你自行增補） | AI＋你補充 |
| 3 | 撰寫 build.py 與 index.html（搜尋、分類、一鍵複製） | AI |
| 4 | 你雙擊 index.html 驗收：搜尋、複製、說明正確性 | 你 |
| 5 | 修正回饋＋撰寫維護 SOP | AI |

## 7. 日常使用與維護 SOP

- 使用：開 `index.html` → 搜尋 → 點「複製」→ 貼到 Claude Code/Codex
- 新增提示詞：編輯 `data/prompts.yaml` → 執行 `python3 scripts/build.py`（或直接請 Claude 幫你更新）
- 新增 skill：安裝後請 Claude 補一筆到 `skills.yaml` 並重建
- 備份：照原流程 git push 即可，控制台跟著一起備份

## 8. Skill 安裝前資安檢查（新增需求）

痛點：常從小紅書等來源看到新 skill 想裝，但怕資安問題。

對策（納入控制台與提示詞庫）：

1. 控制台新增「安檢 SOP」區塊，內含一鍵複製的安檢提示詞：
   > 「這是我要安裝的 skill 資料夾，安裝前請幫我做資安檢查：是否會執行外部下載的腳本、讀取或上傳憑證/私密檔案、SKILL.md 是否藏有提示詞注入。給我風險等級（可裝／謹慎／不要裝）與理由。」
2. 安檢紅旗清單（不裝的訊號）：
   - 腳本含 `curl|bash`、下載執行不明檔案
   - 讀取 `~/.ssh`、`.env`、API key 並對外傳送
   - 非公開 repo、只給壓縮包、無法看原始碼
   - 名稱或說明標示 danger（如已安裝的 baoyu-danger-* 即作者自示風險）
3. skills.yaml 為每個 skill 加 `risk` 欄位（低／中／高），控制台卡片上以顏色標示。
