# DUAL-AI-STATE

任務名稱：v2.5 — 開機自動啟動 + Windows 版桌面浮動小視窗

目前階段：✅ Claude Code 第一版完成；等 Codex 複查 + 補修 + 本地 commit；尚未 push

狀態：使用者明確要求修補「每次開機都要找 AI 修配額守門員」的痛點，並要求避開 8000 與其他本機開發服務衝突

最後更新時間：2026-06-20 Claude Code 完成檔案落地

## 本輪已完成事項

### macOS — 開機自動啟動（LaunchAgent）

- 新增 `scripts/autostart_macos_payload.sh`：登入後實際跑的腳本。負責 build.py、起 serve_console.py、等 `7000~7999` 內的控制台 ready 後開瀏覽器、起 swift 浮動窗。
- 新增 `scripts/install_macos_autostart.sh`：寫 `~/Library/LaunchAgents/com.kagenhsu.quota-guardian.autostart.plist` 並 bootstrap，立即 kickstart 跑一次。安裝時會同步一份 runtime 到 `~/Library/Application Support/QuotaGuardian/runtime/codex-claude-skills-backup`，避開 `launchd` 直接讀取 `~/Documents/...` 時的 `Operation not permitted`。
- 新增 `scripts/uninstall_macos_autostart.sh`：bootout、刪 plist、刪 runtime copy、pkill 同 repo 的 swift 浮窗與 serve_console。
- 新增使用者按鈕 `安裝開機自動啟動 (macOS).command` / `移除開機自動啟動 (macOS).command`。

### Windows — Tkinter 浮動小視窗（swift 版不能跑 Win）

- 新增 `scripts/quota_guard_floating.py`：always-on-top Tk 視窗。
  - 資料來源跟 swift 版完全相同（`quota_guard_snapshot.py`）。
  - 顏色映射：normal → 綠、prepare → 黃、handoff → 橘、reserve → 紅、unavailable → 灰，與 swift `barColor()` 對齊。
  - 「複製切換提示詞」/「複製最終交接提示詞」按鈕文案逐字對齊 swift `handoffPrompt()`。
  - reserve 階段自動複製最終交接提示詞，UI 行為跟 swift 一致。
  - 30 秒刷新一次。
  - **Mac 仍走 swift 版**，這支只給 Win 用。

### Windows — 三個對齊 Mac 的 .bat 入口

- `開啟配額守門員.bat`：起 pythonw 浮動視窗，先用 CIM kill 殘留 instance。
- `更新並開啟控制台.bat`：python build.py + serve_console.py --open-browser。
- `開啟控制台與配額守門員.bat`：浮動視窗丟背景跑，控制台 exec 風格在當前視窗跑。

### Windows — 開機自動啟動

- `scripts/autostart_windows_payload.ps1`：登入後背景跑的 PowerShell payload。
  - pythonw + `-WindowStyle Hidden` 啟動，完全不跳 console。
  - 避開 8000，改從 `7000~7999` 中挑第一個可用埠，跟 mac 對齊。
  - 殘留 instance 用 `Get-CimInstance Win32_Process` 撈 CommandLine 找（避免 Get-Process 在 PS 5 拿不到 CommandLine 的陷阱）。
- `scripts/install_windows_autostart.ps1`：寫 `%APPDATA%\QuotaGuardian\launcher.vbs`，再到 Startup folder 放 .lnk 指向 wscript + 那支 vbs。VBS 是為了完全不跳黑框（只用 `-WindowStyle Hidden` 還是會閃）。
- `scripts/uninstall_windows_autostart.ps1`：刪 .lnk + .vbs + CIM 收掉殘留 instance。
- 使用者按鈕 `安裝開機自動啟動 (Windows).bat` / `移除開機自動啟動 (Windows).bat`。

### 沒動的禁區（按 `memory/project_quota_guardian_baseline.md` 守 baseline）

- `scripts/quota_guard_snapshot.py`：**0 行變動**。
- `scripts/quota_guard_floating.swift`：**0 行變動**。
- `~/.claude/cctokmon-bridge.sh`：**0 行變動**。
- `scripts/install_claude_quota_bridge.py`：**0 行變動**。
- 既有的 `.command` 三個按鈕：**0 行變動**，使用者手動雙擊的流程跟以前一模一樣。

### 文件更新

- `CHANGELOG.md`「未發布」加上四條新增條目。
- `NEXT-AI-TASK.md` 改寫成 v2.5 給 Codex 複查的版本。
- 本檔（`DUAL-AI-STATE.md`）更新為當前狀態。

## 驗證結果（Claude Code 自驗）

- `bash -n` 通過：autostart_macos_payload.sh / install_macos_autostart.sh / uninstall_macos_autostart.sh / 安裝開機自動啟動 (macOS).command / 移除開機自動啟動 (macOS).command。
- `python3 -c "import ast; ast.parse(...)"` 通過：scripts/quota_guard_floating.py。
- 模擬 plist 內容 `plutil -lint` 通過：路徑含中文 + 空格無 escape 問題。
- helper 邏輯抽出測試：`color_for_stage('reserve')` → `#E63946`、`build_handoff_prompt()` 對齊 swift 版開頭文案、`final_handoff_needed()` 在 reserve stage 觸發 True、`next_ai_name()` 挑 percent 最高的。

## 已知尚未驗證（請 Codex 補）

- macOS install + uninstall 已在真機 launchctl 流程實跑；仍要確認不同機器上 `7000~7999` 與 runtime copy 行為是否一致。
- Windows 全部檔案沒實機跑（這台是 Mac）。Codex 如果手上有 Win 機可實機驗一次最好；不然請靜態審 PowerShell here-string / VBS 雙引號 / .bat unicode 路徑三件事。

## 下一步

- Codex 跑 `NEXT-AI-TASK.md` 裡的「驗證指令」+ 視 baseline 守則修補。
- 沒問題就建本地 commit：`v2.5：開機自動啟動 + Windows 版桌面浮動小視窗`。
- 回報 commit hash 與 `git status --short --branch`。
- **不要 push**，等使用者明確授權。

## 未解決問題

- v2.2 的 commit 仍未 push（GitHub Pages 線上 demo 還是 v2.1）。本輪 v2.5 不主動補 push v2.2 — 由使用者一次決定要不要 push v2.2 + v2.5。
- Codex 若實機驗證後發現需要把 swift 版改成支援「也偵測 Tkinter 同行 process」之類的整合，請先回報，**不要自動動 swift**（baseline 禁區）。

## 凍結期規則（沿用 v2.2）

- 除非使用者明確回報具體不便或真實 bug，否則不開新功能。
- 不主動規劃 v2.6。
- 不主動補 P2。
- 不主動改 README / CSS。
- commit / push / release / GitHub 遠端設定仍須遵守 `dual-ai-workflow` 的 Claude Code 審查閘門 — 本輪由 Codex 自審。
