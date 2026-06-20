# NEXT-AI-TASK

任務名稱：v2.5 — 開機自動啟動（macOS LaunchAgent + Windows Startup）+ Windows 版桌面浮動小視窗

目前階段：✅ Codex 複查 + 最小補修完成；已本地 commit；尚未 push

上一棒 AI：Codex

下一棒 AI：使用者（決定是否授權 push；若要補 Windows 實機驗證再交 Codex）

交棒目的：使用者反映「每次開機都要找 AI 修配額守門員 / 控制台」，要求一勞永逸 — macOS 跟 Windows 都做到「登入後自動跳出本地控制台 + 桌面浮動小視窗」，且避開常見 8000 衝突，改走 7000~7999 範圍。

最後更新：2026-06-20 Codex 完成複查、macOS 實機驗證與最小補修

## 必讀檔案（按順序）

1. `scripts/quota_guard_snapshot.py` / `scripts/quota_guard_floating.swift` — 這兩支本輪仍視為禁區；`200K` 寫死、fallback 鏈、wrapper 路徑策略不要動
2. `scripts/autostart_macos_payload.sh` — macOS 登入後實際跑的 payload
3. `scripts/install_macos_autostart.sh` / `scripts/uninstall_macos_autostart.sh`
4. `scripts/autostart_windows_payload.ps1`
5. `scripts/install_windows_autostart.ps1` / `scripts/uninstall_windows_autostart.ps1`
6. `scripts/quota_guard_floating.py` — Tkinter 版浮動小視窗（Windows 用；Mac 仍走 swift）
7. `安裝開機自動啟動 (macOS).command` / `移除開機自動啟動 (macOS).command`
8. `開啟配額守門員.bat` / `更新並開啟控制台.bat` / `開啟控制台與配額守門員.bat`
9. `安裝開機自動啟動 (Windows).bat` / `移除開機自動啟動 (Windows).bat`
10. `.handoff-now.md`（若存在）— 交接時先讀

## 本輪已完成（Claude Code 視角）

### macOS — 開機自動啟動

- `scripts/autostart_macos_payload.sh`：登入後的實際 payload。負責跑 build.py、起 serve_console.py（detached）、等 7000~7999 內的控制台 ready 後開瀏覽器、起 swift 浮動窗（detached）。
  - 已補 LaunchAgent 環境 PATH（`/opt/homebrew/bin` + `/Library/Developer/CommandLineTools/usr/bin` + 標準 PATH），避免找不到 swift / python3。
  - 現已改成避開 8000，改用 `7000~7999` 內可用埠；啟動後會把實際網址寫到 `~/Library/Logs/QuotaGuardian/console-url.txt`。
  - LaunchAgent 不再直接碰 `~/Documents/...`；安裝時會把 runtime 複製到 `~/Library/Application Support/QuotaGuardian/runtime/`，避免 `Operation not permitted`。
  - log 寫到 `~/Library/Logs/QuotaGuardian/autostart.log`，使用者按沒看到視窗時第一手 debug 看那邊。
- `scripts/install_macos_autostart.sh`：寫 `~/Library/LaunchAgents/com.kagenhsu.quota-guardian.autostart.plist`、`launchctl bootstrap gui/$UID`、`launchctl kickstart` 立刻跑一次。已驗證 plist 內容能通過 `plutil -lint`。
- `scripts/uninstall_macos_autostart.sh`：bootout + 刪 plist + 刪 runtime copy + pkill 同 repo 的 serve_console / swift 浮窗。
- 兩個 `.command` 包裝按鈕：`安裝開機自動啟動 (macOS).command` / `移除開機自動啟動 (macOS).command`。

### Windows — Tkinter 浮動小視窗（swift 不能跑 Windows，新做一個對齊版本）

- `scripts/quota_guard_floating.py`：Tkinter always-on-top 視窗。
  - 直接呼叫 `quota_guard_snapshot.py`，吃**同一份 JSON**，行為跟 swift 版對齊（顏色、文字、按鈕、自動複製最終交接提示詞）。
  - 「複製切換提示詞」/「複製最終交接提示詞」按鈕，文案與 swift 版逐字一致（測過 helper：`build_handoff_prompt()` 輸出與 swift `handoffPrompt()` 對得起來）。
  - 30 秒刷一次，跟 swift 版同節奏。
  - Tkinter 在 macOS 上會比 swift 版陽春，所以 **Mac 仍走 swift 版**，Windows 才用這個。

### Windows — 開機自動啟動

- `scripts/autostart_windows_payload.ps1`：登入後跑的 PowerShell payload。完全不跳 console 視窗（用 pythonw + `-WindowStyle Hidden`）。
  - 用 `Get-CimInstance Win32_Process` 撈 CommandLine 找殘留 instance（**不是** `Get-Process`，後者在 PS 5 拿不到 CommandLine）。
  - 避開 8000，改從 `7000~7999` 中挑第一個可用埠，與 mac payload 對齊。
- `scripts/install_windows_autostart.ps1`：在 `%APPDATA%\QuotaGuardian\launcher.vbs` 寫一個 VBS（用 wscript 隱藏起 PowerShell），再到 Startup folder 放一個指向那 VBS 的 .lnk 捷徑。**用 VBS 是為了完全不跳黑框**；只用 `-WindowStyle Hidden` 還是會閃一下。
- `scripts/uninstall_windows_autostart.ps1`：刪 .lnk + .vbs + 用 CIM 收掉殘留 instance。
- 三個使用者按鈕：`開啟配額守門員.bat` / `更新並開啟控制台.bat` / `開啟控制台與配額守門員.bat`。
- 兩個安裝按鈕：`安裝開機自動啟動 (Windows).bat` / `移除開機自動啟動 (Windows).bat`。

### 沒動的東西（守 baseline）

- `scripts/quota_guard_snapshot.py`：完全沒動。`CLAUDE_DEFAULT_CONTEXT_TOKENS = 200_000` 沿用；fallback 鏈順序沿用。
- `scripts/quota_guard_floating.swift`：完全沒動。視窗自動撐高、handoffPrompt 文案、mini 模式都保留現狀。
- `~/.claude/cctokmon-bridge.sh` 跟 `scripts/install_claude_quota_bridge.py`：完全沒動。
- 既有的 `開啟配額守門員.command` / `開啟控制台與配額守門員.command` / `更新並開啟控制台.command`：完全沒動，使用者手動按的流程跟以前一模一樣。

## 本輪 Codex 已完成

1. 跑過交棒檔裡列的 bash / Python 驗證指令，全部通過。
2. macOS 真機跑過 install + uninstall：
   - `launchctl print gui/$UID/com.kagenhsu.quota-guardian.autostart` 顯示 `state = running`
   - `~/Library/Logs/QuotaGuardian/autostart.log` 出現 `==== autostart 完成；payload 進入 wait ... ====`
   - `~/Library/Logs/QuotaGuardian/console-url.txt` 寫出 `http://127.0.0.1:7000/index.html`
   - uninstall 後 plist 消失，`launchctl print` 回 `Could not find service`
3. 靜態審過 Windows 五個檔案：
   - VBS here-string 雙引號層疊正確
   - BAT 的 `%~dp0` 尾端反斜線處理正確
   - `Invoke-WebRequest` 8 秒等待目前先保留，但要注意慢機器可能偶發太短
4. 補了一個最小修補：`scripts/uninstall_macos_autostart.sh` 不再整包刪 `QuotaGuardian/runtime/`，只刪本 repo 的 runtime copy。

## 驗證指令

```bash
# 在 codex-claude-skills-backup/ 目錄底下執行
bash -n scripts/autostart_macos_payload.sh
bash -n scripts/install_macos_autostart.sh
bash -n scripts/uninstall_macos_autostart.sh
bash -n "安裝開機自動啟動 (macOS).command"
bash -n "移除開機自動啟動 (macOS).command"
python3 -c "import ast; ast.parse(open('scripts/quota_guard_floating.py').read())"
python3 scripts/quota_guard_snapshot.py | python3 -m json.tool >/dev/null  # 確認沒被弄壞
```

這台 Mac 沒有 `pwsh`，所以 Windows 部分沒有補跑 PowerShell Core；目前結論仍是「靜態審通過、待 Windows 實機驗證」。

## 下一步最小行動

1. 由使用者決定是否授權 push。
2. 若手邊有 Windows 機，再補跑一次 `安裝開機自動啟動 (Windows).bat`，確認瀏覽器與 Tkinter 浮窗都會自動跳出。
3. 本輪新增 commit 已建立；實際 commit hash 以 git 回報為準。

## 注意事項

- 仍在 v2.2 之後的「使用週凍結期」精神內：本輪是回應使用者具體需求才開做，不算自動規劃。
- 不要主動改 README / CSS / 提示詞 / 新增 skill。
- commit / push 仍遵守 `dual-ai-workflow` 的 Claude Code 審查閘門 — 但這一輪審查者就是 Codex，由 Codex 自審。
