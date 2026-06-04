# 三方 AI 工作流：Codex × Claude Code（VS Code）× Claude Desktop

開發任何專案時，按照這套三方分工模式進行。簡單說：Codex 是主力工程師，負責規劃、分段實作、跑指令、測試、修正與交接；Claude Code（VS Code）是審查員，負責架構建議、程式碼審查、風險檢查與複審；Claude Desktop 是顧問／文字助理，負責需求討論、文件整理與提示詞優化。

> Claude Desktop 不當作第三方 skills 安裝環境。使用 Claude Desktop 時，請從控制台「提示詞庫」複製提示詞，或手動貼上工作流文件。

## 角色定義

| 角色 | 定位 | 負責事項 | 不做的事 |
|---|---|---|---|
| Codex | 主力工程師 | 讀規劃文件、拆任務、分段寫程式、執行指令、測試、驗證、修正、產出交接摘要 | 不跳過 Claude Code 審查 |
| Claude Code（VS Code） | 審查員 | 架構建議、程式碼審查、風險檢查、P0/P1/P2 分級、複審 | 不取代 Codex 做整段主力開發，除非使用者明確指定小範圍修正 |
| Claude Desktop | 顧問／文字助理 | 需求澄清、文件整理、提示詞優化、主管版說明 | 不安裝第三方 skills，不直接操作本機檔案 |
| 使用者 | 最終決策者 | 三方之間轉貼訊息、做最終決定 | 不需要懂技術細節 |

## 五階段流程

- 第 1 階段：Codex 讀專案結構與文件，不修改，提出方案。
- 第 2 階段：Codex 依確認後的方案分段實作、跑 build、驗證、產出交接摘要與 diff。
- 第 3 階段：Claude Code（VS Code）審查 Codex 的交接摘要、diff 與驗證結果，列出 P0/P1/P2 問題。
- 第 4 階段：Codex 逐條判斷審查意見是否成立，只修必要檔案並重新驗證。
- 第 5 階段：Claude Code（VS Code）複審；通過後交回 Codex 做 git 存檔。

Claude Desktop 可以在任一階段協助整理需求、轉寫主管版說明或優化提示詞，但不直接改檔。

## 多裝置同步

- 這套工作流可能在 Windows、Mac mini、VS Code 裡的 Claude Code 使用。
- Codex 與 Claude Code 是可安裝 skills 的主要環境，要保持同一份 `dual-ai-workflow`。
- Claude Desktop 不當作第三方 skills 安裝環境；在 Claude Desktop 使用時，改用控制台「提示詞庫」或手動貼工作流文件。
- 每次修改 `skills/dual-ai-workflow/SKILL.md` 後，要同步到所有會使用 Codex / Claude Code 且支援 skills 的裝置與執行環境。
- Windows 與 macOS 常見安裝位置相同：`~/.codex/skills/dual-ai-workflow/`、`~/.claude/skills/dual-ai-workflow/`。
- VS Code 裡的 Claude Code 要確認讀到同一份 `~/.claude/skills/dual-ai-workflow/SKILL.md`；如果設定了不同 skill 路徑，也要同步那一份。

## 單一 AI 也能使用

如果同事只用一個 AI，也可以用這個控制台：

1. 到「提示詞庫」複製「單一 AI 也能用控制台」。
2. 貼給手上的 AI。
3. 要求它先釐清任務，再提出方案，不要一開始就修改。
4. 如果是系統或程式修改，完成後再提醒是否需要找另一個 AI 做審查。
