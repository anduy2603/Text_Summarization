# run_overnight_benchmark.ps1
# Chay TODO-3 va TODO-4 noi tiep nhau, log ra file.
# Cach dung: .\run_overnight_benchmark.ps1

$ErrorActionPreference = "Stop"
$ROOT = $PSScriptRoot
$LogFile = "$ROOT\overnight_benchmark.log"

function Log($msg) {
    $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $line = "[$ts] $msg"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
}

Log "=== OVERNIGHT BENCHMARK STARTED ==="
Log "Log file: $LogFile"

# ----------------------------------------------------------------
# TODO-3: ViT5 vs TextRank tren validation set, n=200
# ----------------------------------------------------------------
Log ""
Log "--- TODO-3: ViT5 benchmark (validation, n=200) ---"
$t3Start = Get-Date

python "$ROOT\scripts\benchmark_abstractive_vit5.py" `
    --n 200 `
    --max-sentences 2 `
    --warmup-vit5 `
    --out-dir "$ROOT\notebooks\results\official\validation" `
    2>&1 | Tee-Object -Append -FilePath $LogFile

$t3End = Get-Date
$t3Min = [math]::Round(($t3End - $t3Start).TotalMinutes, 1)
Log "TODO-3 xong trong $t3Min phut."

# ----------------------------------------------------------------
# TODO-4: Test set benchmark, tat ca 5 engines, n=200
# ----------------------------------------------------------------
Log ""
Log "--- TODO-4: Test set benchmark (5 engines, n=200) ---"
$t4Start = Get-Date

python "$ROOT\scripts\benchmark_test_set.py" `
    --n 200 `
    --max-sentences 2 `
    --warmup-vit5 `
    2>&1 | Tee-Object -Append -FilePath $LogFile

$t4End = Get-Date
$t4Min = [math]::Round(($t4End - $t4Start).TotalMinutes, 1)
Log "TODO-4 xong trong $t4Min phut."

# ----------------------------------------------------------------
Log ""
Log "=== TAT CA BENCHMARK HOAN THANH ==="
Log "Xem ket qua tai:"
Log "  notebooks/results/official/validation/  (TODO-3)"
Log "  notebooks/results/official/test/        (TODO-4)"
Log "Log day du: $LogFile"
