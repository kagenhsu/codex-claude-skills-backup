# install-skill.ps1 — install a single skill from the codex-claude-skills-backup archive on Windows.
# Usage:
#   iwr https://raw.githubusercontent.com/kagenhsu/codex-claude-skills-backup/main/scripts/install-skill.ps1 -OutFile $env:TEMP\install-skill.ps1
#   & $env:TEMP\install-skill.ps1 -Skill dual-ai-workflow
#
# Or as a single line:
#   $s='dual-ai-workflow'; iwr https://raw.githubusercontent.com/kagenhsu/codex-claude-skills-backup/main/scripts/install-skill.ps1 -OutFile $env:TEMP\install-skill.ps1; & $env:TEMP\install-skill.ps1 -Skill $s

param(
  [Parameter(Mandatory = $true)]
  [string]$Skill
)

$ErrorActionPreference = 'Stop'

$RepoRawBase = if ($env:REPO_RAW_BASE) { $env:REPO_RAW_BASE } else { 'https://raw.githubusercontent.com/kagenhsu/codex-claude-skills-backup/main' }
$ArchiveUrl = "$RepoRawBase/codex-skills-backup.tar.gz"

$TmpDir = New-Item -ItemType Directory -Force -Path (Join-Path $env:TEMP "skill-install-$([System.Guid]::NewGuid().ToString('N'))")
$ArchivePath = Join-Path $TmpDir 'backup.tar.gz'

try {
  Write-Host "📥 Downloading skill archive..."
  Invoke-WebRequest -Uri $ArchiveUrl -OutFile $ArchivePath -UseBasicParsing

  Write-Host "📦 Extracting $Skill ..."
  tar -xzf $ArchivePath -C $TmpDir "skills/$Skill" 2>$null
  $ExtractedDir = Join-Path $TmpDir "skills/$Skill"
  if (-not (Test-Path $ExtractedDir)) {
    Write-Error "Skill '$Skill' not found in archive. Bundled skills: dual-ai-workflow, plan-progress"
    exit 1
  }

  foreach ($Target in @((Join-Path $HOME '.claude\skills'), (Join-Path $HOME '.codex\skills'))) {
    New-Item -ItemType Directory -Path $Target -Force | Out-Null
    $SkillTarget = Join-Path $Target $Skill
    if (Test-Path $SkillTarget) {
      $Backup = "$SkillTarget.bak.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
      Write-Host "⏭  Existing skill found at $SkillTarget — backing up to $Backup"
      Move-Item -Path $SkillTarget -Destination $Backup
    }
    Copy-Item -Recurse $ExtractedDir $SkillTarget
    Write-Host "✅ Installed: $SkillTarget"
  }

  Write-Host ""
  Write-Host "🎉 Done. Restart Codex / Claude Code so it loads the new skill."
}
finally {
  Remove-Item -Recurse -Force $TmpDir -ErrorAction SilentlyContinue
}
