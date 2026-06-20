# Windows 開機 / 登入後在背景跑這支：
#  1. 更新本地控制台靜態檔（build.py）
#  2. 把 serve_console.py 跑成 detached 背景 process
#  3. 等 127.0.0.1:7000~7999 內挑到的本地網址真的 listen，再打開預設瀏覽器
#  4. 把 quota_guard_floating.py（Tkinter 浮動小視窗）跑成 detached 背景 process
#
# 設計重點：
# - 不出現任何黑色 cmd 視窗 → 全部用 -WindowStyle Hidden 跟 pythonw 啟動
# - 失敗訊息一律寫到 %LOCALAPPDATA%\QuotaGuardian\autostart.log，方便事後 debug
# - 已有 instance 在跑就不重起，避免雙開導致 port 衝突

param(
    [Parameter(Mandatory = $true)]
    [string]$RepoDir
)

$ErrorActionPreference = "Continue"

if (-not (Test-Path -LiteralPath $RepoDir -PathType Container)) {
    Write-Error "RepoDir 不存在：$RepoDir"
    exit 64
}

$logDir = Join-Path $env:LOCALAPPDATA "QuotaGuardian"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir "autostart.log"
$urlFile = Join-Path $logDir "console-url.txt"

function Write-Log([string]$msg) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
    Add-Content -LiteralPath $logFile -Value $line -Encoding UTF8
}

Write-Log "==== autostart 觸發 RepoDir=$RepoDir ===="

# 找 python / pythonw
function Resolve-Python([string]$exeName) {
    $cmd = Get-Command $exeName -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    # py launcher 也算
    $py = Get-Command "py.exe" -ErrorAction SilentlyContinue
    if ($py) {
        return "py.exe"
    }
    return $null
}

$pythonExe = Resolve-Python "python"
$pythonwExe = Resolve-Python "pythonw"
if (-not $pythonExe) {
    Write-Log "找不到 python.exe；請安裝 Python 3 並把它加入 PATH。"
    exit 66
}
if (-not $pythonwExe) {
    # 退而求其次用 python 跑 Tk；會多一個 console 視窗但可動。
    $pythonwExe = $pythonExe
    Write-Log "找不到 pythonw.exe，將用 python 啟動 Tk 浮動視窗（會多一個 console 視窗）。"
}

# 1. 更新控制台靜態檔
$buildScript = Join-Path $RepoDir "scripts\build.py"
if (Test-Path -LiteralPath $buildScript) {
    Write-Log "執行 build.py"
    try {
        & $pythonExe $buildScript *>> $logFile
    } catch {
        Write-Log "build.py 失敗：$_"
    }
} else {
    Write-Log "找不到 build.py：$buildScript（用既有 index.html 繼續）"
}

$portStart = 7000
$portTries = 1000
$serveScript = Join-Path $RepoDir "scripts\serve_console.py"
if (-not (Test-Path -LiteralPath $serveScript)) {
    Write-Log "找不到 serve_console.py：$serveScript"
} else {
    # 先收掉同 repo 的舊 serve_console，避免重複 instance 吃不同 port。
    Get-CimInstance Win32_Process -Filter "Name='python.exe' or Name='py.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -and $_.CommandLine -like "*serve_console.py*" -and $_.CommandLine -like "*$RepoDir*" } |
        ForEach-Object {
            Write-Log "kill 舊 server PID=$($_.ProcessId)"
            try { Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop } catch { Write-Log "kill 舊 server 失敗：$_" }
        }
    Start-Sleep -Milliseconds 300

    Remove-Item -LiteralPath $urlFile -Force -ErrorAction SilentlyContinue
    Write-Log "啟動 serve_console.py（隱藏視窗，port $portStart~$($portStart + $portTries - 1)）"
    $serveLog = Join-Path $logDir "serve_console.log"
    Start-Process -FilePath $pythonExe `
        -ArgumentList @("`"$serveScript`"", "--root", "`"$RepoDir`"", "--host", "127.0.0.1", "--port", "$portStart", "--tries", "$portTries", "--write-url-file", "`"$urlFile`"") `
        -WorkingDirectory $RepoDir `
        -WindowStyle Hidden `
        -RedirectStandardOutput $serveLog `
        -RedirectStandardError "$serveLog.err"
}

# 等 serve_console listen 起來（最多 8 秒）
$url = ""
$ready = $false
for ($i = 1; $i -le 8; $i++) {
    if (Test-Path -LiteralPath $urlFile) {
        $url = (Get-Content -LiteralPath $urlFile -ErrorAction SilentlyContinue | Select-Object -First 1).Trim()
    }
    try {
        $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 1 -ErrorAction Stop
        if ($resp.StatusCode -eq 200) { $ready = $true; break }
    } catch {
        Start-Sleep -Milliseconds 1000
    }
}

if ($ready) {
    Write-Log "serve_console.py 已 ready，打開瀏覽器 $url"
    Start-Process $url
} else {
    Write-Log "serve_console.py 8 秒內沒 ready，跳過瀏覽器自動開啟。"
}

# 3. 桌面浮動小視窗：殘留的先收掉
# Get-Process 的 .CommandLine 在 Windows PowerShell 5 不一定有值，改用 CIM。
Get-CimInstance Win32_Process -Filter "Name='python.exe' or Name='pythonw.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -and $_.CommandLine -like "*quota_guard_floating.py*" } |
    ForEach-Object {
        Write-Log "kill 殘留浮動視窗 PID=$($_.ProcessId)"
        try { Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop } catch { Write-Log "kill 失敗：$_" }
    }
Start-Sleep -Milliseconds 300

$floatingScript = Join-Path $RepoDir "scripts\quota_guard_floating.py"
if (Test-Path -LiteralPath $floatingScript) {
    Write-Log "啟動 quota_guard_floating.py（隱藏視窗）"
    # pythonw 本身就不會跳 console
    $floatingArgs = @("`"$floatingScript`"")
    if ($pythonwExe -ieq "py.exe") {
        $floatingArgs = @("-w", "`"$floatingScript`"")
    }
    Start-Process -FilePath $pythonwExe `
        -ArgumentList $floatingArgs `
        -WorkingDirectory $RepoDir `
        -WindowStyle Hidden
} else {
    Write-Log "找不到 quota_guard_floating.py：$floatingScript"
}

Write-Log "==== autostart 完成 ===="
exit 0
