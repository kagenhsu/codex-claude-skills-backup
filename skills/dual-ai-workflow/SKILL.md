---
name: dual-ai-workflow
description: Two-tool AI engineering loop. Codex is the lead engineer for planning, staged implementation, commands, tests, fixes, handoff summaries, and git archival. Claude Code in VS Code is the reviewer for architecture review, code review, risk checks, P0/P1/P2 classification, and re-review.
---

# 二刀流工作流（Codex × Claude Code in VS Code）

## 啟動規則

被觸發或接手時，先檢查並讀取專案根目錄 `DUAL-AI-STATE.md`。如果檔案存在，以狀態檔為準接續工作，不依賴對話記憶；如果不存在，才依使用者貼上的內容判斷階段。

## 角色定義

| 角色 | 負責事項 | 不做的事 |
|---|---|---|
| Codex | 主力工程師：規劃、分段實作、跑指令、測試、修正、產出交接摘要、git 存檔 | 不跳過審查；高風險動作先說明再做 |
| Claude Code（VS Code） | 審查員：架構建議、程式碼審查、風險檢查、P0/P1/P2 分級、複審 | 不取代 Codex 做整段主力開發，除非使用者明確指定小範圍修正 |
| 使用者 | 在 Codex 與 Claude Code 之間轉貼訊息、做最終決定 | 不需要懂技術細節 |

## 多裝置同步

- Windows 常見安裝目錄：`~/.codex/skills/dual-ai-workflow/`、`~/.claude/skills/dual-ai-workflow/`
- macOS / Mac mini 常見安裝目錄：`~/.codex/skills/dual-ai-workflow/`、`~/.claude/skills/dual-ai-workflow/`
- VS Code 裡的 Claude Code 要確認能讀到同一份 `~/.claude/skills/dual-ai-workflow/SKILL.md`；如果某個環境使用不同 skill 路徑，要同步那一份

## 狀態檔機制

每個階段結束時，自動建立或更新專案根目錄 `DUAL-AI-STATE.md`，固定欄位：任務名稱／目前階段／已完成事項／下一步／未解決問題／最後更新時間。

任務閉環完成時，不刪除 `DUAL-AI-STATE.md`，只把目前階段標記為「✅ 已完成」。

## 主動交棒規則

每個角色要先完成自己這一棒的工作，再主動輸出給下一棒 AI 的交接提示詞；不要在任務尚未做完時提前交棒，也不能只寫「完成」或只依賴目前對話。

交接提示詞應放在回報最後一段，前面先說明實際完成事項、修改檔案、驗證結果與未解決問題。

如果專案根目錄存在 `NEXT-AI-TASK.md`，必須在本棒工作完成後同步更新這份固定交棒檔，讓下一棒 AI 不用翻聊天紀錄也能接續。

`NEXT-AI-TASK.md` 至少要寫清楚：

- 下一棒 AI 是誰
- 下一棒要做什麼
- 必讀檔案
- 驗證要求
- 回報格式

如果因權限、環境或其他原因無法更新 `NEXT-AI-TASK.md`，至少要在回應中完整輸出 `NEXT-AI-TASK.md` 內容，讓使用者可以手動貼入。

## 小步存檔與上傳規則

每完成一個可驗證的小項目，就應該先做一次穩定點，而不是累積到大版本才存檔。

小項目完成時必須：

1. 執行對應的 build / test / lint 或本專案指定驗證。
2. 檢查 `git status --short`，確認只包含本輪相關檔案。
3. 若驗證通過，建立本地 commit，commit message 使用繁體中文並說清楚本輪做了什麼。
4. commit 後主動回報 commit hash、驗證結果、目前 git status。
5. 詢問使用者是否 push；若使用者已明確授權本階段可上傳，才可執行 `git push`。

原則：

- 小步 commit / push 是為了能在開發誤入歧途時回到上一個穩定版本。
- 不要把多個不相干改動塞進同一個 commit。
- 不要自動 push origin/main；任何 push / PR / 寫 origin 的動作都必須先得到使用者明確同意。
- push 後必須再次確認 `git status --short --branch`，並把遠端同步結果寫入 `DUAL-AI-STATE.md` / `NEXT-AI-TASK.md` 或交接提示詞。

## 五階段工作流

### 第一階段：Codex 規劃

Codex 先讀專案結構與文件，不要修改。提出方案：任務目標、要改哪些檔案、可能影響哪些功能、風險與不確定點、修改後如何驗證。等使用者確認後進入第二階段。

### 第二階段：Codex 分段實作

Codex 依確認後的方案分段實作、執行必要指令、跑 build 或測試。工作完成後，先回報改了哪些檔案與驗證結果，最後再輸出「給 Claude Code（VS Code）的完整轉交提示詞」，附上交接摘要、改動檔案、驗證結果、未確認事項與 diff。

### 第三階段：Claude Code（VS Code）審查

Claude Code（VS Code）審查 Codex 的改動、diff 與驗證結果，依 P0／P1／P2 排序，指出檔案與原因。審查完成後，最後再輸出「給 Codex 的完整轉交提示詞」。

### 第四階段：Codex 修正

Codex 逐條判斷審查意見：成立就只改必要檔案並重新驗證，不成立就說明理由。修正完成後，先回報逐條處理結果與重新驗證結果，最後再輸出「給 Claude Code（VS Code）的完整轉交提示詞」，附上新 diff。

### 第五階段：Claude Code（VS Code）複審

Claude Code（VS Code）逐條對照前一輪問題是否已處理，並檢查是否引入新問題。複審完成後，全部通過時先輸出「閉環完成」，最後再輸出「給 Codex 的存檔轉交提示詞」；仍有問題時，最後輸出給 Codex 的修正提示詞，回到第四階段。

## 上下文壓縮觸發規則

當對話上下文估算已達 85%～90% 時，主動執行以下動作：

### 觸發訊號（估算依據）

- 單次對話已讀取 3 個以上大型檔案
- 已跑過多輪工具呼叫加長回應
- 對話中出現過一次「前次對話摘要」區塊（代表已壓縮過一次）
- 感覺到需要截斷早期上下文才能繼續推理

### 動作

1. 主動呼叫對應的 compact / context compression 指令
2. 壓縮完成後，立即輸出以下格式的接續摘要：

```text
【上下文已壓縮】
目前任務：<一行說明>
已完成：
- <條列>
待處理：
- <條列>
重要結論：<若有，否則省略>
```

### 原則

- 估算優先於等待，寧可在 85% 提議，不要等到真的超出才處理
- 如果無法自動觸發壓縮，至少在回應末尾明確提醒使用者：「上下文已接近上限，建議現在執行壓縮」
- 壓縮摘要必須包含足夠資訊讓下一輪無縫繼續，不能只寫「已壓縮」
