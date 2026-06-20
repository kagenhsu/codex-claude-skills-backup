# 安裝「開機自動啟動」到 Windows 的 Startup folder。
#
# 做法：
#  1. 在 %APPDATA%\QuotaGuardian\ 裡放一個 launcher.vbs，
#     負責用 wscript 隱藏跑 PowerShell 的 autostart_windows_payload.ps1。
#  2. 在 Startup folder（%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup）
#     放一個指向那支 .vbs 的捷徑（.lnk）。
#  3. 安裝完立刻跑一次，使用者馬上看到效果。
#
# 為什麼用 .vbs：因為它呼叫 PowerShell 時可以完全不跳任何視窗，
#   .bat / .ps1 用 -WindowStyle Hidden 還是會閃一下黑框。

param(
    [string]$RepoDir = ""
)

$ErrorActionPreference = "Stop"

if (-not $RepoDir) {
    # 從本檔位置往上推一層
    $RepoDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
if (-not (Test-Path -LiteralPath $RepoDir -PathType Container)) {
    throw "RepoDir 不存在：$RepoDir"
}

$payload = Join-Path $RepoDir "scripts\autostart_windows_payload.ps1"
if (-not (Test-Path -LiteralPath $payload)) {
    throw "找不到 autostart payload：$payload"
}

$appDir = Join-Path $env:APPDATA "QuotaGuardian"
New-Item -ItemType Directory -Force -Path $appDir | Out-Null

# 1. 寫 launcher.vbs（用 wscript 隱藏起 PowerShell）
$vbsPath = Join-Path $appDir "launcher.vbs"
$vbsContent = @"
' 由 install_windows_autostart.ps1 產生。
' 任務：靜默啟動 autostart_windows_payload.ps1，不顯示任何視窗。
Option Explicit
Dim sh, cmd
Set sh = CreateObject("WScript.Shell")
cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ""$payload"" -RepoDir ""$RepoDir"""
sh.Run cmd, 0, False
"@

# 把雙引號處理好
$vbsContent | Set-Content -LiteralPath $vbsPath -Encoding UTF8
Write-Host "✅ 寫入 launcher：$vbsPath"

# 2. 在 Startup folder 放 .lnk 指向 launcher.vbs
$startup = [Environment]::GetFolderPath("Startup")
$lnkPath = Join-Path $startup "QuotaGuardianAutostart.lnk"

$wshell = New-Object -ComObject WScript.Shell
$shortcut = $wshell.CreateShortcut($lnkPath)
$shortcut.TargetPath = "wscript.exe"
$shortcut.Arguments = '"' + $vbsPath + '"'
$shortcut.WorkingDirectory = $RepoDir
$shortcut.WindowStyle = 7  # Minimized
$shortcut.Description = "Codex × Claude 配額守門員 + 本地控制台 開機自動啟動"
$shortcut.Save()
Write-Host "✅ 建立 Startup 捷徑：$lnkPath"

# 3. 立刻跑一次
Write-Host ""
Write-Host "現在先跑一次，讓你馬上看到效果..."
Start-Process "wscript.exe" -ArgumentList ('"' + $vbsPath + '"') -WindowStyle Hidden

Write-Host ""
Write-Host "完成。之後每次登入 Windows，這兩個會自動出現："
Write-Host "  - 瀏覽器分頁  127.0.0.1:7000~7999 之間的本地控制台網址"
Write-Host "  - 桌面浮動小視窗（Tkinter 版的配額守門員）"
Write-Host ""
Write-Host "log 位置：$env:LOCALAPPDATA\QuotaGuardian\autostart.log"
Write-Host "要移除：請執行同層的 '移除開機自動啟動 (Windows).bat'"
