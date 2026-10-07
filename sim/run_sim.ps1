# =============================================================================
#  Custom FPGA GPU Simulation Script (PowerShell)
#  Project: Custom FPGA-Based GPU — Woxsen University
# =============================================================================

$ROOT = (Get-Item $PSScriptRoot).Parent.FullName
& "$ROOT/tools/run_all_sims.ps1"
