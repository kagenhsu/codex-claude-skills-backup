# DUAL-AI-STATE

任務名稱：Loop 提示詞產生器 — 從獨立頁面整合進主控台（`index.html` 新分頁）

目前階段：✅ Maker（Claude Code）實作完成，Checker（子 AI 代打 Codex）獨立審查通過

狀態：使用者前一天做出的「Loop 提示詞產生器」原本是獨立檔案 `loop-prompt-builder.html`，靠導覽列 `↗` 連結在新分頁打開。使用者反映「應該要跟 index.html 綁定在一起才對」，要求把它變成主控台本身的一個分頁，而不是另一個獨立頁面。目前 Codex 不在線，依使用者指示由 Claude Code 同時扮演 Maker（實作）與安排 Checker（子 AI 審查）兩個角色。

最後更新時間：2026-06-24（子 AI Checker 複審通過，待使用者決定 commit / push）

## Checker（子 AI 代打 Codex）獨立審查結論

判定：**通過**

實際查證動作（Checker 自己重新做的，不是只信任 Maker 的自我報告）：
- `git diff HEAD -- scripts/build.py`：確認新增約 175 行純粹是 Loop 提示詞分頁邏輯，沒有偏離任務範圍的改動。
- 逐一 grep 新增的 13 個 DOM id（`loopPainPoint`／`loopTool`／`loopTrigger`／`loopScope`／`loopBudget`／`loopStopCondition`／`loopReport`／`loopMakerChecker`／`loopExtra`／`loopTaskTypeGroup`／`loopPromptOutput`／`loopPromptCopy`／`loopPromptReset`），各自只出現 1 次；對整份檔案 `id="..."` 做 `sort | uniq -c`，無重複，**無 ID 衝突**。
- XSS 檢查：`loopPromptHtml()` 用 `esc()` 跳脫所有使用者輸入；`updateLoopPrompt()` 用 `textContent`（不是 `innerHTML`）寫回即時預覽，**比舊版獨立檔案更安全，無 XSS 風險**。
- 逐行確認 `render()` 裡每個分支都自帶 `return`，`loopPrompt` 分支不會被前面分支提早擋住。
- `grep -rln "loop-prompt-builder.html" .`（排除 `.git/`）只命中 `DUAL-AI-STATE.md`／`index.html`（嵌入的狀態說明 JSON）／`server_test.log`（舊日誌），都是敘述性文字，不是程式碼引用；確認檔案本身已刪除。
- `git status --porcelain` 確認 `.gitignore`／`quota_guard_*`／`serve_console.py`／`install_claude_quota_bridge.py` 等另一條獨立工作的檔案維持原狀，本次整合**沒有誤動**到無關檔案。

保留事項：Checker 受環境暫時性分類器中斷，沒能自己重跑 `python scripts/build.py` 與 Playwright 動態測試，只做了靜態程式碼審查。動態測試（build 成功、`node --check` 語法通過、Playwright headless 實機操作六要素表單＋切換分頁＋複製按鈕，console 零錯誤）已由 Maker（Claude Code）在審查前完成，兩邊合起來視為完整覆蓋。

附帶觀察（與本次無關，不影響本次判定）：
- `scripts/serve_console.py` 的 `_activate_first_available_app()` 在 Windows 上會讓 `/api/wake-ai` 回 500，是既有缺口。
- `loopPromptData()` 對 `localStorage` 內容做了寬容的型別正規化（字串轉陣列），是好的防禦性寫法。

## Checker 通過之後，Maker 自己又抓到並修掉一個從原始檔案帶過來的 P1

Checker 判定通過、寫完上面這段後，Maker（Claude Code）自己跑「預設狀態下的範例輸出」做最後人工核對時，發現 `loopPromptText()` 裡 `d.makerChecker.includes("雙重")` 這個判斷式有 bug：選項「先用最簡單的 Ralph Loop 就好（**不用**雙重把關）」這個字串本身也包含「雙重」兩個字，導致即使使用者選的是「不要雙重把關」，輸出的第四段還是會誤判成「因為我選了雙重把關」，跟使用者實際選擇相反。這個 bug 是從原始獨立檔案 `loop-prompt-builder.html` 逐字搬過來的既有問題，不是這次整合新增的，但這次有機會順手修掉。

修法：把判斷字串從 `"雙重"` 改成更精確的 `"雙重確認"`（只有「我要 Maker-Checker 雙重確認」這個選項含有這個字串，「不用雙重把關」不含），已修正並重新跑過 `python scripts/build.py` + `node --check` + Playwright 預設狀態輸出核對，確認修好後輸出邏輯正確（選「不用雙重把關」時走「第四段：之後要不要升級」分支，不再誤判）。

## 本輪已完成事項

- 把 `loop-prompt-builder.html`（336 行獨立檔案，含自己的 `<head>`/CSS/`<script>`）整段邏輯改寫成 `scripts/build.py` 裡的一個分頁模組，套用控制台既有的設計語言（`.workflow-guide`/`.guide-item`、`.form-grid`/`.field`、`.builder-preview`、`optionsHtml()`、`copyText()`），不再有自己獨立的 CSS/modal。
- 新增：`PAGE_INTROS.loopPrompt`、`LOOP_*` 常數（任務類型/工具/Trigger/Budget/Stop Condition/Report/Maker-Checker 選項）、`loopPromptData()`／`loopPromptRead()`（沿用原本 `localStorage` key `loop-prompt-builder`，使用者原本存的設定不會跑掉）、`loopAskLine()`／`loopPromptText()`（提示詞組字邏輯逐字保留原版）、`loopPromptHtml()`／`updateLoopPrompt()`／`bindLoopPrompt()`，並在 `render()` 加上 `tab==="loopPrompt"` 分支。
- 導覽列原本的 `<a href="loop-prompt-builder.html" target="_blank">Loop 提示詞 ↗</a>` 改成 `<button data-tab="loopPrompt">Loop 提示詞</button>`；首頁（`guide` 分頁）原本的「建立 Loop 提示詞 ↗」外部連結按鈕也改成 `data-home-tab="loopPrompt"`，點擊後用既有的 `setTab()` 切分頁，不再開新視窗。
- 刪除已變成重複內容的獨立檔案 `loop-prompt-builder.html`（已徵得使用者同意保持刪除狀態，不恢復）。
- 順手修掉前一版的 P2：原獨立頁用 `innerHTML` 插入使用者填的「痛點敘述」（自我 XSS 風險）；新版的即時預覽改用 `textContent` 寫入，表單欄位值一律經過 `esc()` 跳脫，這個風險已不存在。

## 本輪驗證

- `python scripts/build.py` 成功：`OK: ... built with 50 skills / 51 prompts / 4 combos`。
- 抽出 `index.html` 內嵌的整段 `<script>`，跑 `node --check` 確認無語法錯誤。
- 啟動本機 `serve_console.py`，用 Playwright（headless Chromium）實機操作：點「Loop 提示詞」分頁 → 確認概念卡片／六要素卡片／表單欄位／即時預覽／複製按鈕／清空按鈕全部存在 → 在痛點欄位輸入文字，確認預覽即時更新含該文字 → 勾選任務類型 checkbox，確認預覽同步更新 → 點複製按鈕，按鈕文字從「複製提示詞」變成「已複製」沒有報錯 → 切到 `guide`／`installGuide`／`skills` 分頁再切回 `loopPrompt`，確認沒有任何 regression、瀏覽器 console 全程零錯誤（`CONSOLE_ERRORS []`）。

## 已知尚未驗證 / 未解決問題

- `/api/wake-ai` 在 Windows 上回 500（`activate_unsupported`）：既有功能既有缺口，與本次整合無關，未變動。
- 工作目錄裡仍有另一條獨立進行中、跟 Loop 提示詞無關的工作（`scripts/quota_guard_snapshot.py` 等 Windows 相容性 + 即時用量 API），本次整合刻意不動它，`git status` 因此不會是乾淨狀態。
- macOS 上的人工視覺確認（雙擊打開、肉眼看排版）尚未做，這台是 Windows 機器；建議使用者自己開一次確認排版／字體在 macOS 上沒有跑掉。

## 下一步

- Checker 已複審通過，等使用者決定是否要把這次整合（`scripts/build.py` + `index.html` + 刪除 `loop-prompt-builder.html`）建立成一個新的收尾 commit，以及是否 push。

## 凍結期規則（沿用既有專案慣例）

- 除非使用者明確回報具體不便或真實 bug，否則不開新功能。
- commit / push / release / GitHub 遠端設定仍須遵守 `dual-ai-workflow` 的 Claude Code 審查閘門。
