<#
.SYNOPSIS
    Ralph Loop 最小可行版本（Codex 專用版）— Maker 多輪開發，搭配選用的 final-review.ps1 做收尾把關。

.DESCRIPTION
    跟 final-review.ps1 是互補的兩支腳本：
      loop.ps1（這支）  多輪開發/修補，Maker = Codex，每輪都跑。
      final-review.ps1  選用升級（預設不必跑），只在準備上架前手動跑一次，
                        Checker = Claude Code，審查累積的全部改動。
    角色分工固定，不會因為額度方案互換。

    Loop Contract:
      Trigger        手動執行（每次有新任務/新階段時，你自己打這支腳本啟動一組輪次）
      Scope          嚴格沙箱：只能動 -AllowedPaths 內的檔案，不能碰 main/master 分支，
                      不能碰 -ForbiddenPaths（.env、金鑰、CI 設定等），不能刪檔。
      Budget         輪數上限 (-MaxRounds) 「或」時間上限 (-MaxMinutes)，先到的先停。
      Stop Condition 測試全過 / 連續 N 輪同一個錯誤 / 連續 N 輪沒有任何 diff /
                      踩到禁區或刪檔 / 完成一個開發階段（STAGE_COMPLETE），
                      五種狀況任一發生立刻停。
      Report         終端機輸出 + 寫入 progress.txt 雙軌紀錄（含「目前開發階段」清單）。

.PARAMETER ProjectRoot
    要套用這個 Loop 的目標專案路徑（這個 loop.ps1 本身放在 loop-engineering/ 範本資料夾，
    實際使用時把整個 loop-engineering/ 資料夾複製到目標專案，或用這個參數指過去）。

.PARAMETER AgentCommand
    呼叫的 AI CLI 指令，預設 "codex"。Maker 角色固定是 Codex，這個參數通常不需要改
    （依你實際安裝的 Codex CLI 語法調整，例如可能要改成 codex exec 或加上其他參數）。

.PARAMETER TestCommand
    這個專案的測試指令，例如 "npm test" 或 "pytest"。留空則跳過測試判定（測試結果記為 SKIP）。

.EXAMPLE
    ./loop.ps1 -ProjectRoot "C:\path\to\your-project" -TestCommand "npm test" -MaxRounds 10 -MaxMinutes 120
    # 做完一組輪次、準備上架前，如果決定要啟用 Maker-Checker 選用升級，再跑：
    ./final-review.ps1 -ProjectRoot "C:\path\to\your-project"
#>

param(
    [string]$ProjectRoot = ".",
    [string]$AgentCommand = "codex",
    [string]$FallbackAgentCommand = "claude",
    [string]$PromptFile = "maker-prompt.md",
    [string]$ProgressFile = "progress.txt",
    [string]$TestCommand = "",
    [int]$MaxRounds = 10,
    [int]$MaxMinutes = 120,
    [int]$MaxSameErrorStreak = 3,
    [int]$MaxNoDiffStreak = 5,
    [string[]]$AllowedPaths = @("src", "docs", "CHANGELOG.md"),
    [string[]]$ForbiddenPaths = @(".env", ".env.", "*.key", "*.pem", ".github/workflows")
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

# --- 安全剎車 0：絕對不能在 main / master 上跑 ---
$currentBranch = (git rev-parse --abbrev-ref HEAD).Trim()
if ($currentBranch -eq "main" -or $currentBranch -eq "master") {
    Write-Host "[安全剎車] 目前在 '$currentBranch' 分支。這個 Loop 禁止在主分支上執行。" -ForegroundColor Red
    Write-Host "請先建立並切換到 feature/dev 分支，再重新執行。" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $ProgressFile)) {
    Write-Host "[安全剎車] 找不到 $ProgressFile，這個 Loop 需要先有 progress.txt 才能跑（避免每次重新摸索）。" -ForegroundColor Red
    exit 1
}

# 工作目錄必須乾淨，否則沒法正確切每一輪的 diff 基準（每輪結束都會自動本地 commit）
$dirtyStatus = git status --porcelain
if ($dirtyStatus) {
    Write-Host "[安全剎車] 工作目錄不乾淨，有未 commit 的變更：" -ForegroundColor Red
    Write-Host $dirtyStatus
    Write-Host "請先手動確認這些變更要保留、commit 或捨棄，再重新執行 Loop。" -ForegroundColor Red
    exit 1
}

Write-Log "===== Loop 啟動：分支=$currentBranch, MaxRounds=$MaxRounds, MaxMinutes=$MaxMinutes ====="

$startTime = Get-Date
$lastErrorSignature = ""
$sameErrorStreak = 0
$noDiffStreak = 0
$stopReason = ""

for ($round = 1; $round -le $MaxRounds; $round++) {

    # --- Budget 剎車：時間上限 ---
    $elapsedMinutes = (New-TimeSpan -Start $startTime -End (Get-Date)).TotalMinutes
    if ($elapsedMinutes -ge $MaxMinutes) {
        $stopReason = "達到時間上限（$MaxMinutes 分鐘），目前已過 $([Math]::Round($elapsedMinutes,1)) 分鐘"
        break
    }

    Write-Log "----- Round $round 開始（已耗時 $([Math]::Round($elapsedMinutes,1)) 分鐘）-----"

    $beforeCommit = (git rev-parse HEAD).Trim()

    # --- 執行這一輪：把 prompt.md 整份內容餵給 AI agent ---
    # 容錯規則：Maker（預設 Codex）暫時不能用時（額度用完、CLI 噴錯等），
    # 自動換成 -FallbackAgentCommand（預設 Claude Code）頂上去，並把「這輪是誰頂替」清楚寫進 progress.txt，
    # 不能悄悄發生。這個情況常發生（額度互有空檔），所以這不是例外處理，是常態設計。
    $promptContent = Get-Content $PromptFile -Raw
    $usedAgent = $AgentCommand
    try {
        $output = & $AgentCommand -p $promptContent 2>&1
    } catch {
        Write-Log "[頂替] $AgentCommand 無法執行（$($_.Exception.Message)），改用備援 $FallbackAgentCommand 頂上這一輪 Maker"
        try {
            $output = & $FallbackAgentCommand -p $promptContent 2>&1
            $usedAgent = $FallbackAgentCommand
        } catch {
            $stopReason = "Maker 主力 $AgentCommand 跟備援 $FallbackAgentCommand 都無法執行，停止等待人工確認"
            Write-Log $stopReason
            break
        }
    }
    Write-Log "Round $round 實際執行 Maker 的是: $usedAgent$(if ($usedAgent -ne $AgentCommand) { '（頂替）' })"
    $outputText = $output | Out-String
    $outputText | Add-Content -Path $ProgressFile

    # --- 階段性剎車：Maker 是否在這一輪回報完成了一個開發階段 ---
    # 對應 progress.txt 最上面的「目前開發階段（里程碑）」清單，由 maker-prompt.md 規定
    # Maker 每輪都要寫 STAGE_COMPLETE: yes/no。偵測到 yes 時，這一輪仍會走完正常的
    # commit/測試流程，但結束後會強制停下來等人工確認，不會自動接著做下一階段。
    $stageComplete = $outputText -match "STAGE_COMPLETE:\s*yes"

    # --- Scope 剎車 1：是否刪除了既有檔案 ---
    $deletedFiles = git diff --diff-filter=D --name-only $beforeCommit
    if ($deletedFiles) {
        $stopReason = "偵測到本輪刪除了既有檔案：`n$deletedFiles`n立即停止，等待人工確認"
        Write-Log $stopReason
        break
    }

    # --- Scope 剎車 2：是否動到禁區檔案 ---
    $changedFiles = git diff --name-only $beforeCommit
    $hitForbidden = $null
    foreach ($pattern in $ForbiddenPaths) {
        foreach ($file in $changedFiles) {
            if ($file -like $pattern -or $file -like "*$pattern*") {
                $hitForbidden = $file
                break
            }
        }
        if ($hitForbidden) { break }
    }
    if ($hitForbidden) {
        $stopReason = "偵測到變更碰到禁區檔案：$hitForbidden，立即停止，等待人工確認"
        Write-Log $stopReason
        break
    }

    # --- Scope 剎車 3：是否動到允許清單以外的檔案 ---
    $outOfScope = @()
    foreach ($file in $changedFiles) {
        $inScope = $false
        foreach ($allowed in $AllowedPaths) {
            if ($file -like "$allowed*") { $inScope = $true; break }
        }
        if (-not $inScope) { $outOfScope += $file }
    }
    if ($outOfScope.Count -gt 0) {
        $stopReason = "偵測到變更超出允許範圍（-AllowedPaths）：$($outOfScope -join ', ')，立即停止，等待人工確認"
        Write-Log $stopReason
        break
    }

    # --- 記錄 diff 規模，判斷是否「這輪完全沒動作」 ---
    $diffStat = git diff --stat $beforeCommit
    if (-not $diffStat) {
        $noDiffStreak++
        Write-Log "本輪沒有任何 diff（連續第 $noDiffStreak 次）"
    } else {
        $noDiffStreak = 0
        Write-Log "本輪變更：`n$diffStat"
    }
    if ($noDiffStreak -ge $MaxNoDiffStreak) {
        $stopReason = "連續 $MaxNoDiffStreak 輪沒有任何 diff，可能卡住了，停止等待人工確認"
        break
    }

    # --- 通過所有 Scope 檢查後，本地 commit 這一輪（只 commit，不 push）---
    # 這一步是必要的：下一輪的 diff 偵測、以及之後 final-review.ps1 的累積審查，
    # 都需要每一輪有明確的 commit 邊界，否則沒辦法正確切出「這一輪到底改了什麼」。
    if ($diffStat) {
        git add -A -- $AllowedPaths $ProgressFile 2>$null
        git commit -m "loop round $round (maker=$usedAgent)" --quiet
        $afterCommit = (git rev-parse HEAD).Trim()
        Write-Log "Round $round 已本地 commit：$afterCommit（尚未 push）"
    }

    # --- 跑測試，判斷 Stop Condition：測試全過 / 連續同一錯誤 ---
    $testResult = "SKIP"
    if ($TestCommand -ne "") {
        cmd /c $TestCommand
        $exitCode = $LASTEXITCODE
        if ($exitCode -eq 0) {
            $testResult = "PASS"
            $sameErrorStreak = 0
            $lastErrorSignature = ""
        } else {
            $testResult = "FAIL"
            $errorSignature = "exitcode_$exitCode"
            if ($errorSignature -eq $lastErrorSignature) {
                $sameErrorStreak++
            } else {
                $sameErrorStreak = 1
                $lastErrorSignature = $errorSignature
            }
        }
    }
    Write-Log "Round $round 測試結果: $testResult"

    if ($testResult -eq "PASS") {
        $stopReason = "測試全過，正常結束"
        break
    }

    if ($sameErrorStreak -ge $MaxSameErrorStreak) {
        $stopReason = "連續 $MaxSameErrorStreak 輪同一個錯誤（$lastErrorSignature），強制停止，等待人工確認"
        break
    }

    if ($stageComplete) {
        $stopReason = "Round $round 回報完成一個開發階段（STAGE_COMPLETE: yes），依設定強制停下等人工確認，再開下一組輪次"
        break
    }

    Write-Log "----- Round $round 結束 -----`n"
}

if (-not $stopReason) {
    $stopReason = "達到輪數上限（$MaxRounds 輪）"
}

Write-Log "===== Loop 結束。原因：$stopReason ====="
Write-Host ""
Write-Host "=== Loop 結束 ===" -ForegroundColor Yellow
Write-Host "原因: $stopReason" -ForegroundColor Yellow
Write-Host "詳細紀錄請看 $ProgressFile，每輪 commit 都還在本地分支上，沒有 push。"
Write-Host "下一步：覺得這組輪次做完了就跑 ./final-review.ps1 讓 Codex 收尾把關；還沒做完就再跑一次這支腳本繼續開新一組輪次。" -ForegroundColor Cyan
