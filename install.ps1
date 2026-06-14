param(
    [string]$RepoRawBase = "https://raw.githubusercontent.com/kagenhsu/codex-claude-skills-backup/main",
    [string]$ConsoleDir = ""
)

$ErrorActionPreference = "Stop"

Write-Host "Codex / Claude skills installer"

if (-not $ConsoleDir) {
    $ConsoleDir = Join-Path ([Environment]::GetFolderPath("MyDocuments")) "CodexClaudeSkillsConsole"
}

$archiveName = "codex-skills-backup.tar.gz"
$indexName = "index.html"
$serveScriptRel = "scripts/serve_console.py"
$localArchive = $null
$localIndex = $null
$localServeScript = $null

if ($PSScriptRoot) {
    $candidate = Join-Path $PSScriptRoot $archiveName
    if (Test-Path -LiteralPath $candidate) {
        $localArchive = $candidate
    }

    $indexCandidate = Join-Path $PSScriptRoot $indexName
    if (Test-Path -LiteralPath $indexCandidate) {
        $localIndex = $indexCandidate
    }

    $serveCandidate = Join-Path $PSScriptRoot $serveScriptRel
    if (Test-Path -LiteralPath $serveCandidate) {
        $localServeScript = $serveCandidate
    }
}

$tmpRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("codex-claude-skills-" + [System.Guid]::NewGuid().ToString("N"))
$extractDir = Join-Path $tmpRoot "extract"
New-Item -ItemType Directory -Force -Path $tmpRoot, $extractDir | Out-Null

try {
    if ($localArchive) {
        $archive = $localArchive
        Write-Host "Using local archive: $archive"
    } else {
        $archive = Join-Path $tmpRoot $archiveName
        $archiveUrl = "$RepoRawBase/$archiveName"
        Write-Host "Downloading archive: $archiveUrl"
        Invoke-WebRequest -Uri $archiveUrl -OutFile $archive
    }

    tar -xzf $archive -C $extractDir

    $sourceSkills = Join-Path $extractDir "skills"
    if (-not (Test-Path -LiteralPath $sourceSkills)) {
        throw "Archive does not contain a skills directory."
    }

    function Install-Skills {
        param(
            [string]$Target
        )

        New-Item -ItemType Directory -Force -Path $Target | Out-Null

        Get-ChildItem -LiteralPath $sourceSkills -Directory | ForEach-Object {
            if ($_.Name -eq ".system") {
                return
            }

            $dest = Join-Path $Target $_.Name
            if (Test-Path -LiteralPath $dest) {
                Write-Host "Skip existing: $dest"
                return
            }

            Copy-Item -LiteralPath $_.FullName -Destination $dest -Recurse
            Write-Host "Installed: $dest"
        }
    }

    Install-Skills (Join-Path $HOME ".codex\skills")
    Install-Skills (Join-Path $HOME ".claude\skills")

    New-Item -ItemType Directory -Force -Path $ConsoleDir | Out-Null
    $consoleIndex = Join-Path $ConsoleDir $indexName
    $consoleScriptDir = Join-Path $ConsoleDir "scripts"
    $consoleServeScript = Join-Path $ConsoleDir $serveScriptRel
    New-Item -ItemType Directory -Force -Path $consoleScriptDir | Out-Null

    if ($localIndex) {
        Copy-Item -LiteralPath $localIndex -Destination $consoleIndex -Force
        Write-Host "Console copied: $consoleIndex"
    } else {
        $indexUrl = "$RepoRawBase/$indexName"
        Write-Host "Downloading console: $indexUrl"
        Invoke-WebRequest -Uri $indexUrl -OutFile $consoleIndex
        Write-Host "Console downloaded: $consoleIndex"
    }

    if ($localServeScript) {
        Copy-Item -LiteralPath $localServeScript -Destination $consoleServeScript -Force
        Write-Host "Console launcher copied: $consoleServeScript"
    } else {
        $serveUrl = "$RepoRawBase/$serveScriptRel"
        Write-Host "Downloading console launcher: $serveUrl"
        Invoke-WebRequest -Uri $serveUrl -OutFile $consoleServeScript
        Write-Host "Console launcher downloaded: $consoleServeScript"
    }

    $launcherPs1 = Join-Path $ConsoleDir "啟動控制台.ps1"
    @"
`$ErrorActionPreference = "Stop"

function Resolve-Python {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @("py", "-3")
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @("python")
    }
    if (Get-Command python3 -ErrorAction SilentlyContinue) {
        return @("python3")
    }
    throw "找不到 Python，無法啟動本地控制台網址。"
}

try {
    `$pythonCmd = Resolve-Python
    Write-Host "正在啟動本地控制台網址..."
    Write-Host "瀏覽器會自動打開 http://127.0.0.1:8000/index.html（若 8000 被占用，會改用其他可用連接埠）。"
    Write-Host "這個視窗請先不要關閉；關閉後，本地網址就會停止。"
    Write-Host ""
    if (`$pythonCmd.Count -gt 1) {
        & `$pythonCmd[0] `$pythonCmd[1..(`$pythonCmd.Count - 1)] "$consoleServeScript" --root "$ConsoleDir" --open-browser
    } else {
        & `$pythonCmd[0] "$consoleServeScript" --root "$ConsoleDir" --open-browser
    }
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Read-Host "按 Enter 關閉視窗"
    exit 1
}
"@ | Set-Content -LiteralPath $launcherPs1 -Encoding UTF8
    Write-Host "Console launcher created: $launcherPs1"

    $desktopDir = [Environment]::GetFolderPath("DesktopDirectory")
    if (-not $desktopDir) {
        $desktopDir = Join-Path $HOME "Desktop"
    }
    New-Item -ItemType Directory -Force -Path $desktopDir | Out-Null

    $shortcutBaseName = "二刀流開發助手控制台"
    $shortcutPath = Join-Path $desktopDir ($shortcutBaseName + ".lnk")
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = "powershell.exe"
    $shortcut.Arguments = "-ExecutionPolicy Bypass -NoProfile -File `"$launcherPs1`""
    $shortcut.WorkingDirectory = $ConsoleDir
    $shortcut.Description = "Start local Codex x Claude Code development console"
    $shortcut.Save()
    Write-Host "Desktop shortcut created: $shortcutPath"

    Write-Host ""
    Write-Host "Done. Restart Codex and Claude Code to load the installed skills."
    Write-Host "Open the console from your desktop shortcut: $shortcutBaseName"
} finally {
    if (Test-Path -LiteralPath $tmpRoot) {
        Write-Host "Temporary files were left at: $tmpRoot"
        Write-Host "For safety, this installer does not delete temporary folders automatically."
    }
}
