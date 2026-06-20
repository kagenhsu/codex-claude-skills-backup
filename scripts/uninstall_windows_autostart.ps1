# 移除 Windows Startup folder 裡的 QuotaGuardian 自動啟動捷徑，
# 並把目前還在跑的 serve_console.py / quota_guard_floating.py 都收掉。

$ErrorActionPreference = "Continue"

$startup = [Environment]::GetFolderPath("Startup")
$lnkPath = Join-Path $startup "QuotaGuardianAutostart.lnk"

if (Test-Path -LiteralPath $lnkPath) {
    Remove-Item -LiteralPath $lnkPath -Force
    Write-Host "✅ 已移除 Startup 捷徑：$lnkPath"
} else {
    Write-Host "ℹ️  本機沒有 Startup 捷徑：$lnkPath"
}

$appDir = Join-Path $env:APPDATA "QuotaGuardian"
$vbsPath = Join-Path $appDir "launcher.vbs"
if (Test-Path -LiteralPath $vbsPath) {
    Remove-Item -LiteralPath $vbsPath -Force
    Write-Host "✅ 已移除 launcher：$vbsPath"
}

# 收掉浮動視窗 / 本地網址 server（用 CIM 才拿得到 CommandLine）
Get-CimInstance Win32_Process -Filter "Name='python.exe' or Name='pythonw.exe'" -ErrorAction SilentlyContinue |
    Where-Object {
        $_.CommandLine -and (
            $_.CommandLine -like "*quota_guard_floating.py*" -or
            $_.CommandLine -like "*serve_console.py*"
        )
    } |
    ForEach-Object {
        Write-Host "kill PID=$($_.ProcessId)  $($_.CommandLine)"
        try { Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop } catch { Write-Host "kill 失敗：$_" }
    }

Write-Host ""
Write-Host "完成。之後登入不會再自動跑配額守門員與本地控制台。"
Write-Host "log 檔保留：$env:LOCALAPPDATA\QuotaGuardian\autostart.log（要的話可手動刪）"
