# install-all-skills.ps1 — install every bundled skill from the codex-claude-skills-backup archive on Windows.
# Usage:
#   iwr https://raw.githubusercontent.com/kagenhsu/codex-claude-skills-backup/main/scripts/install-all-skills.ps1 -OutFile $env:TEMP\install-all-skills.ps1
#   & $env:TEMP\install-all-skills.ps1

$ErrorActionPreference = 'Stop'

$RepoRawBase = if ($env:REPO_RAW_BASE) { $env:REPO_RAW_BASE } else { 'https://raw.githubusercontent.com/kagenhsu/codex-claude-skills-backup/main' }
$ArchiveUrl = "$RepoRawBase/codex-skills-backup.tar.gz"

$TmpDir = New-Item -ItemType Directory -Force -Path (Join-Path $env:TEMP "skill-install-$([System.Guid]::NewGuid().ToString('N'))")
$ArchivePath = Join-Path $TmpDir 'backup.tar.gz'

try {
  Write-Host "📥 Downloading skill archive..."
  Invoke-WebRequest -Uri $ArchiveUrl -OutFile $ArchivePath -UseBasicParsing

  Write-Host "📦 Extracting bundled skills ..."
  tar -xzf $ArchivePath -C $TmpDir

  $SkillsRoot = Join-Path $TmpDir 'skills'
  if (-not (Test-Path $SkillsRoot)) {
    Write-Error "No skills directory found in archive."
    exit 1
  }

  foreach ($Target in @((Join-Path $HOME '.claude\skills'), (Join-Path $HOME '.codex\skills'))) {
    New-Item -ItemType Directory -Path $Target -Force | Out-Null

    Get-ChildItem -Path $SkillsRoot -Directory | ForEach-Object {
      $SkillName = $_.Name
      if ($SkillName -eq '.system') {
        return
      }

      $SkillTarget = Join-Path $Target $SkillName
      if (Test-Path $SkillTarget) {
        $Backup = "$SkillTarget.bak.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        Write-Host "⏭  Existing skill found at $SkillTarget — backing up to $Backup"
        Move-Item -Path $SkillTarget -Destination $Backup
      }

      Copy-Item -Recurse $_.FullName $SkillTarget
      Write-Host "✅ Installed: $SkillTarget"
    }
  }

  Write-Host ""
  Write-Host "🎉 Done. Restart Codex / Claude Code so they load the bundled skills."
}
finally {
  Remove-Item -Recurse -Force $TmpDir -ErrorAction SilentlyContinue
}
