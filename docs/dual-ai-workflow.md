# 二刀流工作流：Codex × Claude Code（VS Code）

開發任何專案時，按照這套二刀流分工模式進行。簡單說：Codex 是主力工程師，負責規劃、分段實作、跑指令、測試、修正與交接；Claude Code（VS Code）是審查員，負責架構建議、程式碼審查、風險檢查與複審。


## 角色定義

| 角色 | 定位 | 負責事項 | 不做的事 |
|---|---|---|---|
| Codex | 主力工程師 | 讀規劃文件、拆任務、分段寫程式、執行指令、測試、驗證、修正、產出交接摘要 | 不跳過 Claude Code 審查 |
| Claude Code（VS Code） | 審查員 | 架構建議、程式碼審查、風險檢查、P0/P1/P2 分級、複審 | 不取代 Codex 做整段主力開發，除非使用者明確指定小範圍修正 |
| 使用者 | 最終決策者 | 兩邊之間轉貼訊息、做最終決定 | 不需要懂技術細節 |

## 五階段流程

- 第 1 階段：Codex 讀專案結構與文件，不修改，提出方案。
- 第 2 階段：Codex 依確認後的方案分段實作、跑 build、驗證；工作完成後，最後再產出給 Claude Code（VS Code）的交接摘要與 diff。
- 第 3 階段：Claude Code（VS Code）審查 Codex 的交接摘要、diff 與驗證結果；預設使用「5 子代理深度同行評審」，依專案類型分別檢查安全性、程式品質、bug、效能與架構，列出 P0/P1/P2 問題；審查完成後，最後再輸出給 Codex 的修正提示詞。
- 第 4 階段：Codex 逐條判斷審查意見是否成立，只修必要檔案並重新驗證；修正完成後，最後再輸出給 Claude Code（VS Code）的複審提示詞。
- 第 5 階段：Claude Code（VS Code）複審；通過後，最後再交回 Codex 做 git 存檔。

## 深度同行評審觸發規則

當第 2 階段完成，或任何功能新增、UI 調整、安裝腳本修改、release、commit、push、PR 觸發審查閘門時，Codex 給 Claude Code（VS Code）的交接提示詞應自動帶入「5 子代理深度同行評審」要求。

5 個子代理依專案類型調整檢查重點：

| 子代理 | 核心檢查 |
|---|---|
| Security Agent | 權限、機密資料、輸入驗證、注入攻擊、上傳、部署與依賴風險 |
| Quality Agent | 可讀性、命名、重複邏輯、錯誤處理、測試缺口、既有風格一致性 |
| Bug Hunter Agent | 明顯 bug、邊界情況、空值、日期/時區、資料狀態與回歸風險 |
| Concurrency & Perf Agent | 效能瓶頸、併發衝突、重複查詢、I/O、快取、資源釋放 |
| Architecture Agent | 模組邊界、資料流、責任切分、技術選型、擴充性與 PRD 對齊 |

如果某個維度沒有問題，Claude Code（VS Code）只需回覆「該維度未發現明顯異常」。如果有問題，必須給出具體修改建議或可套用的程式片段，並標註 P0/P1/P2。

## 交棒節奏

- 每個 AI 都先完成自己這一棒，再把下一棒提示詞放在回報最後。
- 不在工作尚未完成時提前交棒。
- 交棒前先寫清楚：完成事項、修改檔案、驗證結果、未解決問題與目前 git 狀態。
- 若專案有 `NEXT-AI-TASK.md`，完成後同步更新，讓下一棒不用翻對話紀錄。

## 多裝置同步

- 這套工作流可能在 Windows、Mac mini、VS Code 裡的 Claude Code 使用。
- Codex 與 Claude Code 是可安裝 skills 的主要環境，要保持同一份 `dual-ai-workflow`。
- 每次修改 `skills/dual-ai-workflow/SKILL.md` 後，要同步到所有會使用 Codex / Claude Code 且支援 skills 的裝置與執行環境。
- Windows 與 macOS 常見安裝位置相同：`~/.codex/skills/dual-ai-workflow/`、`~/.claude/skills/dual-ai-workflow/`。
- VS Code 裡的 Claude Code 要確認讀到同一份 `~/.claude/skills/dual-ai-workflow/SKILL.md`；如果設定了不同 skill 路徑，也要同步那一份。

## 單一 AI 也能使用

如果同事只用一個 AI，也可以用這個控制台：

1. 到「提示詞庫」複製「單一 AI 也能用控制台」。
2. 貼給手上的 AI。
3. 要求它先釐清任務，再提出方案，不要一開始就修改。
4. 如果是系統或程式修改，完成後再提醒是否需要找另一個 AI 做審查。
