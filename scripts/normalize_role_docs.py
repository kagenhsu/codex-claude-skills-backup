#!/usr/bin/env python3
"""Normalize the three-tool role documentation and skill metadata."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

AI_ROLE = """# AI 角色導覽

這頁給新手判斷：遇到系統設計、網站修改、程式修正、審查、文件整理或提示詞工作時，要找哪個 AI。

## 三方怎麼分工

| 角色 | 最適合做什麼 | 怎麼用 |
|---|---|---|
| Codex | 主力工程師：規劃、分段實作、跑指令、測試、修正、產出交接摘要 | 適合系統開發、網站調整、程式修 bug、需要一步一步推進的任務 |
| Claude Code（VS Code） | 審查員：看架構、抓 bug、檢查風險、P0/P1/P2 分級、複審 | 把 Codex 的 diff、驗證結果與系統背景貼給它，請它審查 |
| Claude Desktop | 顧問／文字助理：討論需求、整理文件、優化提示詞、產出主管版說明 | 不當作第三方 skills 安裝環境；用複製提示詞或貼文件的方式使用 |
| 你 | 最終決策者：三方之間轉貼、做最終決定 | 看結論與風險，決定是否進下一步 |

## 推薦工作模式

- 重要系統修改：Codex 先規劃與分段實作 → Claude Code（VS Code）審查 → Codex 修正 → Claude Code（VS Code）複審 → Codex 存檔。
- 文字或需求整理：可以直接找 Claude Desktop，讓它整理主管版說明、需求文件或提示詞。
- 單一 AI 工作：如果同事只用 Codex、Claude Code 或 Claude Desktop，也可以照控制台的提示詞卡工作，不一定要雙 AI。

## 什麼情況找誰

| 你的需求 | 建議角色 |
|---|---|
| 我要改網站、修程式、跑測試 | Codex |
| 我要確認改動有沒有 bug 或風險 | Claude Code（VS Code） |
| 我要整理需求、寫說明、改提示詞 | Claude Desktop 或任一 AI |
| 我同事只有一個 AI 可以用 | 到「提示詞庫」複製「單一 AI 也能用控制台」 |
| 我要在 Mac mini 上繼續做 | 先確認 Mac mini 的 Codex / Claude Code skills 已同步 |

## 小白版理解

- Codex 像「主力工程師」：真的讀檔、改檔、跑測試、修問題。
- Claude Code（VS Code）像「審查員」：檢查 Codex 做得對不對，有沒有漏風險。
- Claude Desktop 像「文字顧問」：幫你想需求、整理文件、寫提示詞，但不裝第三方 skills。
- 你像「主管」：看結論，決定要不要往下一步走。

這套控制台不是只能給雙 AI 使用；它也可以當作「AI 工作提示詞庫」，讓只用單一 AI 的人更容易開始。
"""

WORKFLOW_DOC = """# 三方 AI 工作流：Codex × Claude Code（VS Code）× Claude Desktop

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
"""

SKILL = """---
name: dual-ai-workflow
description: Three-tool AI engineering loop. Codex is the lead engineer for planning, staged implementation, commands, tests, fixes, handoff summaries, and git archival. Claude Code in VS Code is the reviewer for architecture review, code review, risk checks, P0/P1/P2 classification, and re-review. Claude Desktop is the requirements and writing advisor used through copied prompts or pasted documents, not a third-party skills installation environment.
---

# 三方 AI 工作流（Codex × Claude Code in VS Code × Claude Desktop）

## 啟動規則

被觸發或接手時，先檢查並讀取專案根目錄 `DUAL-AI-STATE.md`。如果檔案存在，以狀態檔為準接續工作，不依賴對話記憶；如果不存在，才依使用者貼上的內容判斷階段。

## 角色定義

| 角色 | 負責事項 | 不做的事 |
|---|---|---|
| Codex | 主力工程師：規劃、分段實作、跑指令、測試、修正、產出交接摘要、git 存檔 | 不跳過審查；高風險動作先說明再做 |
| Claude Code（VS Code） | 審查員：架構建議、程式碼審查、風險檢查、P0/P1/P2 分級、複審 | 不取代 Codex 做整段主力開發，除非使用者明確指定小範圍修正 |
| Claude Desktop | 顧問／文字助理：需求澄清、文件整理、提示詞優化、主管版說明 | 不安裝第三方 skills，不直接操作本機檔案 |
| 使用者 | 三方之間轉貼訊息、做最終決定 | 不需要懂技術細節 |

## 多裝置同步

- Windows 常見安裝目錄：`~/.codex/skills/dual-ai-workflow/`、`~/.claude/skills/dual-ai-workflow/`
- macOS / Mac mini 常見安裝目錄：`~/.codex/skills/dual-ai-workflow/`、`~/.claude/skills/dual-ai-workflow/`
- VS Code 裡的 Claude Code 要確認能讀到同一份 `~/.claude/skills/dual-ai-workflow/SKILL.md`；如果某個環境使用不同 skill 路徑，要同步那一份
- Claude Desktop 不當作第三方 skills 安裝環境；使用 Claude Desktop 時，改用控制台「提示詞庫」或手動貼工作流文件

## 狀態檔機制

每個階段結束時，自動建立或更新專案根目錄 `DUAL-AI-STATE.md`，固定欄位：任務名稱／目前階段／已完成事項／下一步／未解決問題／最後更新時間。

任務閉環完成時，不刪除 `DUAL-AI-STATE.md`，只把目前階段標記為「✅ 已完成」。

## 五階段工作流

### 第一階段：Codex 規劃

Codex 先讀專案結構與文件，不要修改。提出方案：任務目標、要改哪些檔案、可能影響哪些功能、風險與不確定點、修改後如何驗證。等使用者確認後進入第二階段。

### 第二階段：Codex 分段實作

Codex 依確認後的方案分段實作、執行必要指令、跑 build 或測試、回報改了哪些檔案與驗證結果。結尾輸出「給 Claude Code（VS Code）的完整轉交提示詞」，附上交接摘要、改動檔案、驗證結果、未確認事項與 diff。

### 第三階段：Claude Code（VS Code）審查

Claude Code（VS Code）審查 Codex 的改動、diff 與驗證結果，依 P0／P1／P2 排序，指出檔案與原因。結尾輸出「給 Codex 的完整轉交提示詞」。

### 第四階段：Codex 修正

Codex 逐條判斷審查意見：成立就只改必要檔案並重新驗證，不成立就說明理由。完成後輸出「給 Claude Code（VS Code）的完整轉交提示詞」，附上逐條處理結果、重新驗證結果與新 diff。

### 第五階段：Claude Code（VS Code）複審

Claude Code（VS Code）逐條對照前一輪問題是否已處理，並檢查是否引入新問題。全部通過時，輸出「閉環完成」與「給 Codex 的存檔轉交提示詞」；仍有問題時，輸出給 Codex 的修正提示詞，回到第四階段。
"""


def main() -> None:
    (ROOT / "docs/ai-role-guide.md").write_text(AI_ROLE, encoding="utf-8")
    (ROOT / "docs/dual-ai-workflow.md").write_text(WORKFLOW_DOC, encoding="utf-8")
    (ROOT / "skills/dual-ai-workflow/SKILL.md").write_text(SKILL, encoding="utf-8")

    skills_path = ROOT / "data/skills.yaml"
    skills = yaml.safe_load(skills_path.read_text(encoding="utf-8"))
    for item in skills:
        if item.get("name") == "dual-ai-workflow":
            item["summary"] = "自製 skill：三方 AI 工作流（Codex＝主力工程師，負責規劃、分段實作、測試與修正；Claude Code（VS Code）＝審查員，負責架構審查、風險檢查與複審；Claude Desktop＝顧問／文字助理，使用提示詞版不安裝第三方 skills），並用 DUAL-AI-STATE.md 記錄進度"
            item["notes"] = "本專案自製；Codex 與 Claude Code 需同步到 ~/.codex/skills、~/.claude/skills 或各環境實際 skill 路徑；Claude Desktop 不安裝第三方 skills，請用提示詞庫手動套用"
    skills_path.write_text(
        yaml.safe_dump(skills, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )

    print("OK: role docs normalized")


if __name__ == "__main__":
    main()
