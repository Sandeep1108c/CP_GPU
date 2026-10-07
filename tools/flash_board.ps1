# =============================================================================
# Script: Flash Tang Nano 20K FPGA Bitstream
# Project: Custom FPGA-Based GPU - Woxsen University
# Usage:
#   powershell -ExecutionPolicy Bypass -File tools/flash_board.ps1 [-Permanent]
# =============================================================================
param (
    [switch]$Permanent
)

$ROOT = (Get-Item $PSScriptRoot).Parent.FullName
$BITSTREAM = Join-Path $ROOT "gowin/impl/pnr/tang_nano_20k_gpu.fs"
$PROGRAMMER = "C:/Gowin/Gowin_V1.9.12.03_x64/Programmer/bin/programmer_cli.exe"

if (-not (Test-Path $BITSTREAM)) {
    Write-Host "Error: Bitstream file not found at: $BITSTREAM" -ForegroundColor Red
    exit 1
}

$OP_INDEX = if ($Permanent) { 9 } else { 2 }
$MODE_NAME = if ($Permanent) { "External SPI Flash (Permanent Non-Volatile)" } else { "SRAM (Instant RAM)" }

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "   FLASHING TANG NANO 20K FPGA BITSTREAM               " -ForegroundColor Cyan
Write-Host "   Target Mode: $MODE_NAME                             " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Bitstream: $BITSTREAM"

& $PROGRAMMER --cable-index 1 --device GW2AR-18C --operation_index $OP_INDEX --fsFile $BITSTREAM

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n>> SUCCESS: Bitstream flashed successfully to Tang Nano 20K!" -ForegroundColor Green
} else {
    Write-Host "`n>> ERROR: Flash failed. Please ensure USB-C cable is connected." -ForegroundColor Red
}
