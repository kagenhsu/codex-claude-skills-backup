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
$localArchive = $null
$localIndex = $null

if ($PSScriptRoot) {
    $candidate = Join-Path $PSScriptRoot $archiveName
    if (Test-Path -LiteralPath $candidate) {
        $localArchive = $candidate
    }

    $indexCandidate = Join-Path $PSScriptRoot $indexName
    if (Test-Path -LiteralPath $indexCandidate) {
        $localIndex = $indexCandidate
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

    if ($localIndex) {
        Copy-Item -LiteralPath $localIndex -Destination $consoleIndex -Force
        Write-Host "Console copied: $consoleIndex"
    } else {
        $indexUrl = "$RepoRawBase/$indexName"
        Write-Host "Downloading console: $indexUrl"
        Invoke-WebRequest -Uri $indexUrl -OutFile $consoleIndex
        Write-Host "Console downloaded: $consoleIndex"
    }

    $desktopDir = [Environment]::GetFolderPath("DesktopDirectory")
    if (-not $desktopDir) {
        $desktopDir = Join-Path $HOME "Desktop"
    }
    New-Item -ItemType Directory -Force -Path $desktopDir | Out-Null

    $shortcutBaseName = "二刀流開發助手控制台"
    $shortcutPath = Join-Path $desktopDir ($shortcutBaseName + ".lnk")
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $consoleIndex
    $shortcut.WorkingDirectory = $ConsoleDir
    $shortcut.Description = "Open local Codex x Claude Code development console"
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
