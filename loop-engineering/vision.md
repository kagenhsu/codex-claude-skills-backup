# Vision — 這個 Loop 為什麼存在

## 要解決的痛點

1. AI 每次開發都「忘記前面改過什麼」，結果把已經修好的東西還原回去。
2. 一個系統被改出第二、第三個版本並存，沒人知道哪個是正確的那一份。
3. 開發到一半中斷後，沒人（包括 AI）知道目前卡在哪個階段，導致重新摸索、浪費額度與時間。

這個 Loop 存在的唯一目的：**讓每一輪改動都是「讀過上一輪紀錄之後的小步前進」**，而不是每次重新開始猜。

## 這個 Loop 負責的任務範圍（對應 Budget 的 Action 基礎）

只允許從以下五類任務中挑選，且**每一輪只能挑一類、做一件小事**：

- 自動修 Bug
- Code Review 把關
- 文件 / Changelog 自動更新
- 資料同步或備份
- 開發系統跟網頁（新功能、調整既有功能）

## Scope 邊界（嚴格沙箱）— 不能做的事

- **絕對不能**直接在 `main` / `master` 分支上修改或 commit。所有工作必須在 feature/dev 分支進行。
- **絕對不能**刪除任何既有檔案或資料夾，不能使用 `rm -rf`、`git clean -fd`、批量刪除等指令。如果判斷某個檔案真的該刪，必須停下來在 `progress.txt` 寫明原因並等待人工確認，不能自己動手刪。
- **絕對不能**修改 `.env`、金鑰、憑證（`*.key`、`*.pem`）、CI/CD 設定（`.github/workflows/**`）、資料庫連線設定。
- **絕對不能**在偵測到「同一個系統已經有多個版本並存」時，選擇新增第三個版本來繞過問題；遇到這種情況要停下來回報，由人工決定要留哪一份。
- **絕對不能**略過讀取 `progress.txt` 就直接開始改動 —— 每一輪開始前必須先確認「上一輪做到哪裡、上一輪的結論是什麼」。
- 只能修改允許清單內的路徑（預設：`src/`、`docs/`、`CHANGELOG.md`，依專案調整 `loop.ps1` 的 `-AllowedPaths`）。

## 預算與停止的精神

- 預算用完、或連續犯同一個錯誤達到剎車條件時，**Loop 不能自己延長或重新計算「再給自己一次機會」**，一定要停下來等人工確認後才能重新啟動下一組輪次。
- 任何一輪只要踩到上面的禁區，視為立即觸發 Stop Condition，比輪數/時間預算更高優先。
- **新增的第五種剎車：階段完成強制停**。為了解決「開發到一半忘記卡在哪個階段」的痛點，`progress.txt` 最上面多了一塊「目前開發階段（里程碑）」清單。Maker 每輪結束時要對照這份清單，判斷這一輪是否讓某個階段從未完成變成完成；如果是，要在輪次紀錄寫一行 `STAGE_COMPLETE: yes`，`loop.ps1` 偵測到這個標記就會在這輪 commit 完後立刻停下來，等人工確認要不要接著做下一階段，不會自己接著往下衝。這跟測試 PASS/FAIL 是獨立的判斷——一個階段可能測試還沒全過，但已經是該停下來給人看一眼的時間點。

## Maker 角色：Codex 專用版

這一版 Loop 是「Codex 專用」——平時每一輪動手做事的 Maker 固定是 **Codex**，不是 Claude Code。

- `loop.ps1` 預設 `-AgentCommand "codex"`，備援 `-FallbackAgentCommand "claude"`。
- Codex 額度用完或 CLI 暫時噴錯時，自動換 Claude Code 頂上這一輪，且**一定要在 progress.txt 寫明「這輪是誰頂替」**，不能悄悄發生。

## Maker-Checker 雙重把關（選用升級，目前未啟用）

`final-review.ps1` / `final-checker-prompt.md` 仍保留在這個資料夾裡，但**這一版預設不啟用**——先把單一 Maker（Codex）跑穩，要不要加 Checker 是之後的決定（看是否要升級到 Maker-Checker 模式）。

如果之後決定啟用，角色建議**對調**成：

- **Checker 預設改成 Claude Code**，備援 Codex（`final-review.ps1` 的 `-CheckerCommand` / `-FallbackCheckerCommand` 預設已先改好）。
- 理由：Maker 已經是 Codex，如果 Checker 預設也是 Codex，等於同一個 AI 審查自己做的東西，獨立性打折。換成 Claude Code 收尾，才有真正不同視角的把關。

Checker 的限制不變：只能讀程式碼、寫審查結果（`checker-verdict.txt` 跟 `progress.txt`），**不能修改任何程式碼**，腳本會偵測並擋下違規。Checker 判定 REJECT 時，Maker 在下一組輪次的基礎上補修正，不會回頭撤銷已經 commit 的歷史。主力失敗時自動切備援頂替，同樣要寫明「這次是誰頂替」。
