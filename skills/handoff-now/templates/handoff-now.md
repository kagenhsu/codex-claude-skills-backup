# 現場交接檔 — {{專案名稱或目錄名}}

> 寫入前檢查：本檔所有 `{{...}}` 佔位符都必須替換完成；若有任一欄無法判斷，改寫成 `{待補：原因}`，不要原樣保留範本變數。

> 由 **{{Claude Code | Codex}}** 在 **{{YYYY-MM-DD HH:MM}}** 寫入
> 觸發原因：{{quota 撞 handoff / 使用者主動觸發 / context 高}}
> 工作目錄：`{{絕對路徑}}`
> 當前分支 / 最後 3 commit：
> ```
> {{git status --short 輸出}}
>
> {{git log --oneline -3 輸出}}
> ```

## 目前做到哪裡
{{1-3 句白話總結。例：正在改 scripts/quota_guard_snapshot.py 的 fallback 邏輯，已加 context_window_proxy，正在驗證新文案。}}

## 已完成
- {{條列具體可驗證的事，含檔名/行號}}
- {{例：scripts/install_claude_quota_bridge.py 改 wrapper（已驗證 cctokmon-state.json 會寫出）}}

## 未完成
- {{條列。含「為什麼還沒做完」}}
- {{例：swift 視窗只測 swiftc -parse 沒實測視覺，因為這個 session 沒辦法開 UI}}

## 下一步
1. {{下一棒第一個動作。要具體，例「跑 X 指令、改 Y 檔的 Z 函數」}}
2. {{第二個動作（若有）}}
3. {{若需要使用者決策才能繼續，明寫「等使用者回答 OOO」}}

## 下次開工提示詞
> {{給下一棒 AI 直接複製貼上的提示詞。範例：}}
>
> 接續 `{{專案名稱}}` 的「{{當前任務}}」。請先：
> 1. `cat .handoff-now.md` 讀完現場
> 2. `cat NEXT-AI-TASK.md`（若存在）對齊計畫
> 3. 不要重做已完成項
> 4. 從「下一步」第 1 點開始，做完先回報，再繼續
> 5. 全程繁體中文，遇到不確定先問再做

## 風險
- {{例：未提交變更在 X 檔}}
- {{例：某個改動跨平台未驗證}}
- {{例：上一棒 quota 已撞 reserve，這份 handoff 是趕著寫的，可能漏細節}}

---

_此檔由 `skills/handoff-now/` 產生，覆寫前舊版會存在 `.handoff-now.bak.md`。專案 `.gitignore` 已排除，不會被 commit。_
