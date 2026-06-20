# NEXT-AI-TASK

任務名稱：v2.5 — 開機自動啟動（macOS LaunchAgent + Windows Startup）+ Windows 版桌面浮動小視窗

目前階段：✅ Claude Code 第一版完成；等 Codex 複查 + 視情況補修；尚未 commit / push

上一棒 AI：Claude Code（VS Code）

下一棒 AI：Codex（複查 + 修補 + 本地 commit）

交棒目的：使用者反映「每次開機都要找 AI 修配額守門員 / 控制台」，要求一勞永逸 — macOS 跟 Windows 都做到「登入後自動跳出本地控制台 + 桌面浮動小視窗」，且避開常見 8000 衝突，改走 7000~7999 範圍。

最後更新：2026-06-20 Claude Code 完成檔案落地，待 Codex 複查

## 必讀檔案（按順序）

1. `memory/project_quota_guardian_baseline.md` — 守門員 baseline，**禁區清單**（200K 寫死、fallback 鏈、wrapper 路徑策略不要動）
2. `scripts/autostart_macos_payload.sh` — macOS 登入後實際跑的 payload
3. `scripts/install_macos_autostart.sh` / `scripts/uninstall_macos_autostart.sh`
4. `scripts/autostart_windows_payload.ps1`
5. `scripts/install_windows_autostart.ps1` / `scripts/uninstall_windows_autostart.ps1`
6. `scripts/quota_guard_floating.py` — Tkinter 版浮動小視窗（Windows 用；Mac 仍走 swift）
7. `安裝開機自動啟動 (macOS).command` / `移除開機自動啟動 (macOS).command`
8. `開啟配額守門員.bat` / `更新並開啟控制台.bat` / `開啟控制台與配額守門員.bat`
9. `安裝開機自動啟動 (Windows).bat` / `移除開機自動啟動 (Windows).bat`

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

## Codex 複查請務必做的事

1. **跑得起來嗎**
   - macOS：在自己機器執行 `bash 'scripts/install_macos_autostart.sh'`，確認：
     - `launchctl print gui/$UID/com.kagenhsu.quota-guardian.autostart` 列得到
     - `~/Library/Logs/QuotaGuardian/autostart.log` 有 `==== autostart 完成 ====`
     - 瀏覽器確實打開 `127.0.0.1:7000~7999` 之間的本地控制台網址
     - 桌面右上出現 swift 浮動窗
   - macOS 確認後執行 `bash 'scripts/uninstall_macos_autostart.sh'`，確認 plist 移除、launchctl 找不到。
2. **plist 路徑含中文 + 空格**會不會被 launchd 拆爛？payload 已經把 `REPO_DIR` 用 `${REPO_DIR}` 帶進去並 `cd "$REPO_DIR"`，但請確認 launchd 真實環境下 `cd` 成功。
3. **Windows 部分先靜態複查**：不一定要實機跑（你目前是 Mac），請看：
   - install_windows_autostart.ps1 的 VBS 內容 — PowerShell `@"..."@` here-string 對雙引號的處理是否符合 VBS 期望（VBS 用 `""` 表示一個 `"`）。
   - autostart_windows_payload.ps1 的 `Invoke-WebRequest` 8 秒等待夠不夠？
4. **守 baseline 確認**：對照 `memory/project_quota_guardian_baseline.md` 的禁區清單，確認本輪沒誤動到 snapshot fallback / 200K 寫死 / wrapper 路徑策略。
5. **`memory/feedback_read_handoff_now_first.md`**：本檔案就是這套機制的延伸（交接時要先讀 `.handoff-now.md`），請保持這個準則。

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

PowerShell 部分如果 Codex 也在 Mac，可以先用 `pwsh -NoProfile -Command 'Get-Command Get-CimInstance'` 跳過實機驗證；只要在 Windows 上裝完跑一次能看到瀏覽器 + Tkinter 視窗，就算驗證通過。

## Codex 接手要做的下一步

1. 跑上面的驗證指令，確認沒語法問題。
2. macOS 在自己機器跑 install + uninstall 一回，確認流程乾淨。
3. 看 Windows 那五個檔靜態審：VBS / PowerShell / BAT 三種引號層疊有沒有問題。
4. 沒問題就建本地 commit（**不要 push**）：
   - commit message 建議：`v2.5：開機自動啟動 + Windows 版桌面浮動小視窗`
5. 把 commit hash 跟 `git status --short --branch` 回報給使用者，請使用者確認是否授權 push。
6. 如果發現問題：用最小修補丁，不要重做整套；對 swift / snapshot.py 仍是禁區。

## 注意事項

- 仍在 v2.2 之後的「使用週凍結期」精神內：本輪是回應使用者具體需求才開做，不算自動規劃。
- 不要主動改 README / CSS / 提示詞 / 新增 skill。
- commit / push 仍遵守 `dual-ai-workflow` 的 Claude Code 審查閘門 — 但這一輪審查者就是 Codex，由 Codex 自審。
- 完成 commit 後請更新 `DUAL-AI-STATE.md` 跟 `CHANGELOG.md` 的「未發布」區塊。
