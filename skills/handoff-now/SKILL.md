---
name: handoff-now
description: 緊急現場交接檔產生器。當 quota 守門員偵測到本輪剩餘 ≤30%（handoff 階段），或使用者觸發「/handoff-now」「寫現場交接檔」「現在要交棒」「快撞限制了」等指令時，立即把當前對話進度寫到 <cwd>/.handoff-now.md，下一棒 AI 只要讀一個檔就能無痛接手。
---

# handoff-now — 緊急現場交接檔

## 何時觸發

1. 使用者明說：「/handoff-now」、「寫現場交接檔」、「快撞限制了」、「先存一份接手檔」、「現場交接」、「凍結現場」
2. 配額守門員浮動窗顯示「最終交接」訊息（任一 quota window 剩餘 ≤ 10%，alert_stage = `reserve`）
3. 你自己判斷本對話 context 已 ≥ 70%（看最近一次 `python3 scripts/quota_guard_snapshot.py` 輸出的「目前對話 context」百分比）

## 與其他狀態檔的分工

| 檔案 | 性質 | 何時寫 |
|---|---|---|
| `DUAL-AI-STATE.md` | 階段性狀態 | 每階段結束 |
| `NEXT-AI-TASK.md` | 計畫性交棒 | 每棒完成 |
| `.handoff-now.md` | **緊急現場快照** | quota 觸發 / 使用者要求 |

`.handoff-now.md` 是「**當下這 30 分鐘**做了什麼，下一棒從這裡接著做」，不取代上面兩個，但比它們更即時。

## 步驟

1. **抓現場資料**
   - `git -C <cwd> status --short`
   - `git -C <cwd> log --oneline -3`
   - 當前 cwd 絕對路徑
   - 哪個 AI 在寫（Claude Code / Codex）
   - 目前時間（YYYY-MM-DD HH:MM）

2. **由 AI 自己回顧本輪對話**填入 6 欄位（看下方範本）。任一欄位判斷不出來，**寫 `{待補：原因}` 而非省略**。

3. **寫檔順序**
   - 如果 `<cwd>/.handoff-now.md` 已存在 → 先 `mv` 成 `.handoff-now.bak.md`（覆蓋舊備份）
   - 用 `templates/handoff-now.md` 為範本，填入內容，寫到 `<cwd>/.handoff-now.md`
   - 寫完後立刻檢查：檔案內**不得殘留** `{{` 或 `}}`；若有任一欄位無法判斷，改寫成 `{待補：原因}`

4. **回報使用者**
   - 路徑：`<cwd>/.handoff-now.md`
   - 用一句話總結這份 handoff 的關鍵未完成事項
   - 附「給下一棒的最短啟動提示詞」（範本最後一段已內建）

## 觸發後的硬約束

- 寫完 `.handoff-now.md` 後**不要繼續開新大任務**。如果使用者沒明說要繼續做，就停下來等下一棒接手。
- 不要刪 `.handoff-now.bak.md`，那是上一份歷史。
- 不要把 `.handoff-now.md` 加進 git（專案 `.gitignore` 已排除；避免對話內容外流）。

## Codex 對等用法

Codex 沒有 skill 機制，但可以直接讀 `templates/handoff-now.md` 當提示詞範本：當 Codex 看到使用者貼「請寫現場交接檔到 .handoff-now.md」時，就照範本 6 欄位填好寫檔。
