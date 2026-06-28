# Claude Code statusline bridge (Windows).
# 對齊 scripts/claude_quota_statusline.sh 的行為：把 Claude Code 餵進來的 statusline JSON
# 原樣存成 cctokmon-state.json，再印一行簡短文字當 statusline 顯示。
#
# 注意：一定要用 StreamReader 搭配明確的 UTF8 編碼讀 stdin，
# 不能用 [Console]::In.ReadToEnd()（它會用主控台的輸入字碼頁，例如繁體中文 Windows
# 常見的 cp950，把 Claude Code 用 UTF-8 傳進來的中文路徑 / 文字弄成亂碼，
# 連帶讓寫出去的 JSON 壞掉、quota_guard_snapshot.py 讀不到即時資料）。
$ErrorActionPreference = "Stop"

$stateFile = if ($env:CCTOKMON_STATE_FILE) {
    $env:CCTOKMON_STATE_FILE
} else {
    Join-Path $HOME ".claude\cctokmon-state.json"
}
$tmpFile = "$stateFile.tmp"

$stdin = [Console]::OpenStandardInput()
$reader = New-Object System.IO.StreamReader($stdin, [System.Text.Encoding]::UTF8)
$inputText = $reader.ReadToEnd()

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $stateFile) | Out-Null
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($tmpFile, $inputText, $utf8NoBom)
Move-Item -LiteralPath $tmpFile -Destination $stateFile -Force

try {
    $data = $inputText | ConvertFrom-Json
    $model = if ($data.model.display_name) {
        $data.model.display_name
    } elseif ($data.model.name) {
        $data.model.name
    } else {
        "Claude"
    }
    $pct = 0
    if ($null -ne $data.context_window.used_percentage) {
        $pct = [math]::Round([double]$data.context_window.used_percentage, 1)
    }
    Write-Output "$model $pct%"
} catch {
    Write-Output "quota-guard"
}
