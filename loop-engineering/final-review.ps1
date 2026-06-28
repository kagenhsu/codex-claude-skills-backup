<#
.SYNOPSIS
    收尾把關（Final Gate）— 在準備 push / 上架前，跑一次 Codex 審查整段累積改動。

.DESCRIPTION
    跟 loop.ps1 是互補的兩支腳本，不是取代關係（Codex 專用版，Maker-Checker 為選用升級，預設未啟用）：
      loop.ps1         多輪開發/修補，Maker = Codex，每輪都跑，預算用輪數+時間控制。
      final-review.ps1 只在你覺得「這組輪次做完了、準備上架」時手動跑一次，
                        Checker = Claude Code，審查範圍是「從分支分歧點到現在累積的全部 diff」，
                        不是某一輪而已。

    角色分工固定，不會因為額度方案（PRO X5 / Max X5）互換：
      Maker（每輪）  = Codex
      Checker（收尾）= Claude Code
    （理由：Maker 已經是 Codex，Checker 換成 Claude Code 才有獨立視角，不是同一個 AI 審查自己。）

    安全規則跟 loop.ps1 一致：不能在 main/master 上跑、Checker 不能改程式碼（只能寫
    checker-verdict.txt 跟 progress.txt）、不 push、不刪檔。

.PARAMETER BaseRef
    審查範圍的起點。留空的話，腳本會自動找目前分支跟 main（或 master）的分歧點
    (`git merge-base HEAD main`)，從那裡到 HEAD 的累積 diff 就是這次要審查的全部範圍。

.EXAMPLE
    ./final-review.ps1 -ProjectRoot "C:\path\to\your-project"
#>

param(
    [string]$ProjectRoot = ".",
    [string]$CheckerCommand = "claude",
    [string]$FallbackCheckerCommand = "codex",
    [string]$CheckerPromptFile = "final-checker-prompt.md",
    [string]$ProgressFile = "progress.txt",
    [string]$VerdictFile = "checker-verdict.txt",
    [string]$BaseRef = "",
    [string[]]$AllowedPaths = @("src", "docs", "CHANGELOG.md")
)

$ErrorActionPreference = "Stop"
Set-Location $ProjectRoot

function Write-Log {
    param([string]$Text)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$timestamp] $Text"
    Write-Host $line
    Add-Content -Path $ProgressFile -Value $line
}

# --- 安全剎車 0：不能在 main / master 上跑 ---
$currentBranch = (git rev-parse --abbrev-ref HEAD).Trim()
if ($currentBranch -eq "main" -or $currentBranch -eq "master") {
    Write-Host "[安全剎車] 目前在 '$currentBranch' 分支。收尾審查必須在 feature/dev 分支上對著 main 的差異跑，不能直接在 main 上跑。" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $ProgressFile)) {
    Write-Host "[安全剎車] 找不到 $ProgressFile。" -ForegroundColor Red
    exit 1
}

# --- 工作目錄必須乾淨，否則沒法正確圈出「累積 diff」的範圍 ---
$dirtyStatus = git status --porcelain
if ($dirtyStatus) {
    Write-Host "[安全剎車] 工作目錄不乾淨，有未 commit 的變更：" -ForegroundColor Red
    Write-Host $dirtyStatus
    Write-Host "請先用 loop.ps1 跑完一輪讓它 commit，或自行確認後再執行收尾審查。" -ForegroundColor Red
    exit 1
}

# --- 自動找分歧點 ---
if ($BaseRef -eq "") {
    $resolved = $null
    foreach ($candidate in @("main", "master")) {
        git rev-parse --verify $candidate *> $null
        if ($LASTEXITCODE -eq 0) {
            $resolved = (git merge-base HEAD $candidate).Trim()
            break
        }
    }
    if (-not $resolved) {
        Write-Host "[安全剎車] 找不到 main 或 master 分支，無法自動判斷審查起點。請用 -BaseRef 手動指定一個 commit。" -ForegroundColor Red
        exit 1
    }
    $BaseRef = $resolved
}

Write-Log "===== 收尾審查啟動：分支=$currentBranch, 審查範圍=$BaseRef..HEAD, Checker=$CheckerCommand ====="

$diffStat = git diff --stat $BaseRef
if (-not $diffStat) {
    Write-Host "[提醒] 累積 diff 是空的（目前分支跟 $BaseRef 沒有差異），沒有東西需要審查。" -ForegroundColor Yellow
    exit 0
}
Write-Log "累積變更範圍：`n$diffStat"

$preCheckerCommit = (git rev-parse HEAD).Trim()
if (Test-Path $VerdictFile) { Remove-Item $VerdictFile -Force }

$promptTemplate = Get-Content $CheckerPromptFile -Raw
$prompt = $promptTemplate.Replace("{{BASE_REF}}", $BaseRef)

# 容錯規則：Checker（預設 Claude Code）暫時不能用時，自動換成 -FallbackCheckerCommand（預設 Codex）
# 頂上去做收尾審查，並把「這次是誰頂替」清楚寫進 progress.txt，不能悄悄發生。
$usedChecker = $CheckerCommand
try {
    # 注意：依你實際安裝的 CLI 語法調整這一行（例如 Codex 要改成 codex exec、或加上其他必要參數）
    $checkerOutput = & $CheckerCommand -p $prompt 2>&1
} catch {
    Write-Log "[頂替] $CheckerCommand 無法執行（$($_.Exception.Message)），改用備援 $FallbackCheckerCommand 頂上這次收尾審查"
    try {
        $checkerOutput = & $FallbackCheckerCommand -p $prompt 2>&1
        $usedChecker = $FallbackCheckerCommand
    } catch {
        Write-Log "Checker 主力 $CheckerCommand 跟備援 $FallbackCheckerCommand 都無法執行"
        Write-Host "[失敗] 兩個 AI CLI 都無法執行，請確認安裝狀態與額度。" -ForegroundColor Red
        exit 1
    }
}
Write-Log "本次收尾審查實際執行的是: $usedChecker$(if ($usedChecker -ne $CheckerCommand) { '（頂替，注意：原本固定分工是 Claude Code 做收尾審查，這次換人審查，結果可信度請自行評估）' })"
$checkerOutput | Out-String | Add-Content -Path $ProgressFile

# --- Checker 不能改程式碼，只能動 VerdictFile 跟 ProgressFile ---
$checkerChangedFiles = git diff --name-only $preCheckerCommit | Where-Object {
    $_ -ne $VerdictFile -and $_ -ne $ProgressFile
}
if ($checkerChangedFiles) {
    Write-Log "[Checker 違規] Codex 不應該修改程式碼，但偵測到它改了：$($checkerChangedFiles -join ', ')"
    Write-Host "[安全剎車] Codex 動了不該動的檔案，請人工檢查，不要直接採用這次審查結果。" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $VerdictFile)) {
    Write-Log "Codex 沒有產出 $VerdictFile，無法判斷收尾審查結果"
    Write-Host "[安全剎車] 沒有拿到合法的審查結果，不能視為已通過。" -ForegroundColor Red
    exit 1
}

$verdictContent = Get-Content $VerdictFile -Raw
$verdictMatch = [Regex]::Match($verdictContent, "VERDICT:\s*(APPROVE|REJECT)", "IgnoreCase")
if (-not $verdictMatch.Success) {
    Write-Log "$VerdictFile 格式不合法，找不到 VERDICT: APPROVE/REJECT"
    Write-Host "[安全剎車] 審查結果格式不合法，不能視為已通過。" -ForegroundColor Red
    exit 1
}
$verdict = $verdictMatch.Groups[1].Value.ToUpper()

# --- 本地 commit 這次審查紀錄（只 commit，不 push，不動程式碼）---
git add -- $ProgressFile $VerdictFile 2>$null
git commit -m "final-review: checker=$usedChecker verdict=$verdict (base $BaseRef)" --quiet --allow-empty
$reviewCommit = (git rev-parse HEAD).Trim()

Write-Log "===== 收尾審查結束：判定=$verdict（已本地 commit $reviewCommit，尚未 push）====="
Write-Host ""
if ($verdict -eq "APPROVE") {
    Write-Host "=== Codex 核准，可以準備 push / 上架 ===" -ForegroundColor Green
} else {
    Write-Host "=== Codex 打回，先別 push ===" -ForegroundColor Yellow
    Write-Host "請看 $VerdictFile 的 REQUIRED_FIXES，回去用 loop.ps1 跑下一組輪次修正，修完再跑一次本腳本。" -ForegroundColor Yellow
}
Write-Host "詳細內容看 $ProgressFile 最下面的「收尾把關紀錄」與 $VerdictFile。"
