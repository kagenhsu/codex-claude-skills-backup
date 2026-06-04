param(
    [string]$RepoRawBase = "https://raw.githubusercontent.com/kagenhsu/codex-claude-skills-backup/main",
    [switch]$KeepTemp
)

$ErrorActionPreference = "Stop"

Write-Host "Codex / Claude skills installer"

$archiveName = "codex-skills-backup.tar.gz"
$localArchive = $null

if ($PSScriptRoot) {
    $candidate = Join-Path $PSScriptRoot $archiveName
    if (Test-Path -LiteralPath $candidate) {
        $localArchive = $candidate
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

    Write-Host ""
    Write-Host "Done. Restart Codex and Claude Code to load the installed skills."
} finally {
    if ($KeepTemp) {
        Write-Host "Temporary files were left at: $tmpRoot"
    } elseif (Test-Path -LiteralPath $tmpRoot) {
        Remove-Item -LiteralPath $tmpRoot -Recurse -Force
    }
}
