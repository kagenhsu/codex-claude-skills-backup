#!/usr/bin/env python3
"""Normalize the two-tool role documentation and skill metadata."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SKILL_DESCRIPTION = "Two-tool AI engineering loop. Codex is the lead engineer for planning, staged implementation, commands, tests, fixes, handoff summaries, and git archival. Claude Code in VS Code is the reviewer for architecture review, code review, risk checks, P0/P1/P2 classification, and re-review."

AI_ROLE = """# AI 角色導覽

這頁給新手判斷：遇到系統設計、網站修改、程式修正、審查、文件整理或提示詞工作時，要找哪個 AI。

## 二刀流怎麼分工

| 角色 | 最適合做什麼 | 怎麼用 |
|---|---|---|
| Codex | 主力工程師：規劃、分段實作、跑指令、測試、修正、產出交接摘要 | 適合系統開發、網站調整、程式修 bug、需要一步一步推進的任務 |
| Claude Code（VS Code） | 審查員：看架構、抓 bug、檢查風險、P0/P1/P2 分級、複審 | 把 Codex 的 diff、驗證結果與系統背景貼給它，請它審查 |
| 你 | 最終決策者：兩邊之間轉貼、做最終決定 | 看結論與風險，決定是否進下一步 |

## 推薦工作模式

- 重要系統修改：Codex 先規劃與分段實作 → Claude Code（VS Code）審查＋修改 → Codex 修正＋開發 → Claude Code（VS Code）複審＋修改 → Codex 存檔。
- 單一 AI 工作：如果同事只用 Codex、Claude Code，也可以照控制台的提示詞卡工作，不一定要二刀流。

## 什麼情況找誰

| 你的需求 | 建議角色 |
|---|---|
| 我要改網站、修程式、跑測試 | Codex |
| 我要確認改動有沒有 bug 或風險 | Claude Code（VS Code） |
| 我要整理需求、寫說明、改提示詞 | Codex 或 Claude Code（VS Code） |
| 我同事只有一個 AI 可以用 | 到「提示詞庫」複製「單一 AI 也能用控制台」 |
| 我要在 Mac mini 上繼續做 | 先確認 Mac mini 的 Codex / Claude Code skills 已同步 |

## 小白版理解

- Codex 像「主力工程師」：真的讀檔、改檔、跑測試、修問題。
- Claude Code（VS Code）像「審查員」：檢查 Codex 做得對不對，有沒有漏風險。
- 你像「主管」：看結論，決定要不要往下一步走。

這套控制台主打二刀流；它也可以當作「AI 工作提示詞庫」，讓只用單一 AI 的人更容易開始。
"""

WORKFLOW_DOC = """# 二刀流工作流：Codex × Claude Code（VS Code）

開發任何專案時，按照這套二刀流分工模式進行。簡單說：Codex 是主力工程師，負責規劃、分段實作、跑指令、測試、修正、延伸開發與交接；Claude Code（VS Code）是審查員，負責架構建議、程式碼審查、風險檢查、修改建議與複審。


## 角色定義

| 角色 | 定位 | 負責事項 | 不做的事 |
|---|---|---|---|
| Codex | 主力工程師 | 讀規劃文件、拆任務、分段寫程式、執行指令、測試、驗證、修正、產出交接摘要 | 不跳過 Claude Code 審查 |
| Claude Code（VS Code） | 審查員 | 架構建議、程式碼審查、風險檢查、P0/P1/P2 分級、複審 | 不取代 Codex 做整段主力開發，除非使用者明確指定小範圍修正 |
| 使用者 | 最終決策者 | 兩邊之間轉貼訊息、做最終決定 | 不需要懂技術細節 |

## 五階段流程

- 第 1 階段：Codex 讀專案結構與文件，不修改，提出方案。
- 第 2 階段：Codex 依確認後的方案分段實作、跑 build、驗證；工作完成後，最後再產出給 Claude Code（VS Code）的交接摘要與 diff。
- 第 3 階段：Claude Code（VS Code）審查＋修改 Codex 的交接摘要、diff 與驗證結果，列出 P0/P1/P2 問題與修改建議；審查完成後，最後再輸出給 Codex 的修正提示詞。
- 第 4 階段：Codex 修正＋開發，逐條判斷審查意見是否成立，只修必要檔案並重新驗證；修正完成後，最後再輸出給 Claude Code（VS Code）的複審提示詞。
- 第 5 階段：Claude Code（VS Code）複審＋修改；通過後，最後再交回 Codex 做 git 存檔。

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
"""

SKILL = """---
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
| Claude Code（VS Code） | 審查員：架構建議、程式碼審查、風險檢查、P0/P1/P2 分級、修改建議、複審 | 不取代 Codex 做整段主力開發，除非使用者明確指定小範圍修正 |
| 使用者 | 兩邊之間轉貼訊息、做最終決定 | 不需要懂技術細節 |

## 多裝置同步

- Windows 常見安裝目錄：`~/.codex/skills/dual-ai-workflow/`、`~/.claude/skills/dual-ai-workflow/`
- macOS / Mac mini 常見安裝目錄：`~/.codex/skills/dual-ai-workflow/`、`~/.claude/skills/dual-ai-workflow/`
- VS Code 裡的 Claude Code 要確認能讀到同一份 `~/.claude/skills/dual-ai-workflow/SKILL.md`；如果某個環境使用不同 skill 路徑，要同步那一份

## 狀態檔機制

每個階段結束時，自動建立或更新專案根目錄 `DUAL-AI-STATE.md`，固定欄位：任務名稱／目前階段／已完成事項／下一步／未解決問題／最後更新時間。

任務閉環完成時，不刪除 `DUAL-AI-STATE.md`，只把目前階段標記為「✅ 已完成」。

## 五階段工作流

### 第一階段：Codex 規劃

Codex 先讀專案結構與文件，不要修改。提出方案：任務目標、要改哪些檔案、可能影響哪些功能、風險與不確定點、修改後如何驗證。等使用者確認後進入第二階段。

### 第二階段：Codex 分段實作

Codex 依確認後的方案分段實作、執行必要指令、跑 build 或測試。工作完成後，先回報改了哪些檔案與驗證結果，最後再輸出「給 Claude Code（VS Code）的完整轉交提示詞」，附上交接摘要、改動檔案、驗證結果、未確認事項與 diff。

### 第三階段：Claude Code（VS Code）審查＋修改

Claude Code（VS Code）審查 Codex 的改動、diff 與驗證結果，依 P0／P1／P2 排序，指出檔案、原因與修改建議。審查完成後，最後再輸出「給 Codex 的完整轉交提示詞」。

### 第四階段：Codex 修正＋開發

Codex 逐條判斷審查意見：成立就只改必要檔案並重新驗證，不成立就說明理由。若需要補齊相關開發，也在這一階段完成。修正完成後，先回報逐條處理結果與重新驗證結果，最後再輸出「給 Claude Code（VS Code）的完整轉交提示詞」，附上新 diff。

### 第五階段：Claude Code（VS Code）複審＋修改

Claude Code（VS Code）逐條對照前一輪問題是否已處理，並檢查是否引入新問題。若仍有小問題，要補具體修改建議。複審完成後，全部通過時先輸出「閉環完成」，最後再輸出「給 Codex 的存檔轉交提示詞」；仍有問題時，最後輸出給 Codex 的修正提示詞，回到第四階段。
"""


def ensure_skill_description(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---", 4)
    if end == -1:
        return text
    frontmatter = text[4:end].splitlines()
    body = text[end:]
    output = []
    has_description = False
    for line in frontmatter:
        if line.startswith("description:"):
            output.append(f"description: {SKILL_DESCRIPTION}")
            has_description = True
        else:
            output.append(line)
    if not has_description:
        insert_at = 1 if output and output[0].startswith("name:") else len(output)
        output.insert(insert_at, f"description: {SKILL_DESCRIPTION}")
    return "---\n" + "\n".join(output) + body


def main() -> None:
    (ROOT / "docs/ai-role-guide.md").write_text(AI_ROLE, encoding="utf-8")
    (ROOT / "docs/dual-ai-workflow.md").write_text(WORKFLOW_DOC, encoding="utf-8")
    skill_path = ROOT / "skills/dual-ai-workflow/SKILL.md"
    skill_path.write_text(
        ensure_skill_description(skill_path.read_text(encoding="utf-8")),
        encoding="utf-8",
    )

    skills_path = ROOT / "data/skills.yaml"
    skills = yaml.safe_load(skills_path.read_text(encoding="utf-8"))
    for item in skills:
        if item.get("name") == "dual-ai-workflow":
            item["summary"] = "自製 skill：二刀流工作流（Codex＝主力工程師，負責規劃、分段實作、測試、修正與延伸開發；Claude Code（VS Code）＝審查員，負責架構審查、風險檢查、修改建議與複審），並用 DUAL-AI-STATE.md 記錄進度"
    skills_path.write_text(
        yaml.safe_dump(skills, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )

    print("OK: role docs normalized")


if __name__ == "__main__":
    main()
