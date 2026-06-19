# AGENTS.md — 專案頂層規則文件

專案名稱：二刀流開發助手控制台（Codex × Claude Code 開發系統）
專案簡介：本機 HTML 單頁控制台，管理已安裝的 Codex / Claude Code skills（中文說明＋觸發句一鍵複製）、常用提示詞庫，以及 skill 安裝前的資安檢查 SOP。

## 開發協作規範（AI 必須遵守）

0. **接手第一動**：如果專案根目錄存在 `.handoff-now.md`，**先 `cat` 讀完再做任何修改**。那是上一棒 AI 在撞配額限制前寫的現場交接快照，避免你重做已完成的事或漏掉未完成的事。讀完後若內容仍有效，從「下一步」第 1 點開始；若已不適用，回報使用者並請示新方向。
1. 每個任務先看規劃文件（docs/skill-console-plan.md、PRD.md）再執行
2. 一個對話只做一個明確任務
3. 不要刪除文件，除非用戶明確要求
4. 需求不清楚時，先提出關鍵問題，不要直接猜著做
5. 任務有風險時，先明說風險，再執行
6. 修改完成後，總結：改了哪些內容、如何檢查、下一步建議
7. 每次回答盡可能用小白能聽懂的話解釋
8. 遇到技術專有名詞時，用一句簡單的話解釋它是什麼意思、邏輯是什麼

## 專案檔案結構

```
codex-claude-skills-backup/
├── AGENTS.md                  # 本文件（頂層規則）
├── PRD.md                     # 需求文檔
├── index.html                 # 控制台成品（雙擊開啟）
├── install.sh                 # macOS 一行安裝腳本
├── install.ps1                # Windows PowerShell 一行安裝腳本
├── data/
│   ├── skills.yaml            # skill 目錄資料
│   └── prompts.yaml           # 提示詞庫資料
├── scripts/
│   ├── build.py               # 由 yaml 重建 index.html
│   ├── normalize_role_docs.py # 正規化角色導覽文件內容
│   └── update_backup_skill.py # 更新備份包內自製 workflow skill
├── docs/
│   ├── skill-console-plan.md  # 規劃文件
│   ├── ai-role-guide.md       # AI 角色導覽
│   └── dual-ai-workflow.md    # 二刀流工作流說明
├── skills/
│   └── dual-ai-workflow/      # 自製二刀流工作流 skill
├── codex-skills-backup.tar.gz # 原有 skills 備份（不可刪）
└── restore-skills.sh          # 原有還原腳本（不可刪）
