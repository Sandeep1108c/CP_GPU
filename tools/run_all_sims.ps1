# =============================================================================
# Script: Run All FPGA GPU Simulations
# Project: Custom FPGA-Based GPU — Woxsen University
# Description:
#   Compiles and runs all testbenches using Icarus Verilog (iverilog + vvp).
#   Stores build artifacts in sim/build/ and waveforms in sim/waves/.
# =============================================================================

$ErrorActionPreference = "Continue"

$ROOT = (Get-Item $PSScriptRoot).Parent.FullName
Set-Location $ROOT

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "   RUNNING ALL GPU FPGA SIMULATIONS (Icarus Verilog)    " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Project Root: $ROOT"

# Ensure build & waves directories exist
New-Item -ItemType Directory -Force -Path "sim/build" | Out-Null
New-Item -ItemType Directory -Force -Path "sim/waves" | Out-Null

$results = @()

function Run-Suite {
    param (
        [string]$Step,
        [string]$Name,
        [string]$VvpFile,
        [string]$CompileCmd,
        [string]$PassPattern,
        [string]$VcdFile
    )

    Write-Host "`n$Step Running $Name..." -ForegroundColor Yellow
    $sw = [System.Diagnostics.Stopwatch]::StartNew()

    Invoke-Expression $CompileCmd | Out-Null
    if ($LASTEXITCODE -ne 0) {
        $sw.Stop()
        Write-Host "  -> COMPILE ERROR ($([math]::Round($sw.Elapsed.TotalSeconds, 1))s)" -ForegroundColor Red
        $script:results += [PSCustomObject]@{ Suite = $Name; Status = "COMPILE_ERR"; Duration = "$([math]::Round($sw.Elapsed.TotalSeconds, 1))s"; File = "N/A" }
        return
    }

    Set-Location "$ROOT/sim/waves"
    $run = & vvp -N "$ROOT/sim/build/$VvpFile" 2>&1
    Set-Location $ROOT
    $sw.Stop()

    $passed = $run -match $PassPattern
    $dur = "$([math]::Round($sw.Elapsed.TotalSeconds, 1))s"
    if ($passed) {
        Write-Host "  -> PASS ($dur)" -ForegroundColor Green
        $script:results += [PSCustomObject]@{ Suite = $Name; Status = "PASS"; Duration = $dur; File = $VcdFile }
    } else {
        Write-Host "  -> FAIL ($dur)" -ForegroundColor Red
        $script:results += [PSCustomObject]@{ Suite = $Name; Status = "FAIL"; Duration = $dur; File = $VcdFile }
    }
}

# 1. TMDS Encoder
Run-Suite -Step "[1/10]" -Name "TMDS Encoder" -VvpFile "tmds_sim.vvp" `
    -CompileCmd "iverilog -o sim/build/tmds_sim.vvp rtl/tmds_encoder.v sim/tb/tmds_encoder_tb.v 2>&1" `
    -PassPattern "ALL TESTS PASSED" -VcdFile "tmds_encoder_sim.vcd"

# 2. Palette LUT & VGA Timing
Run-Suite -Step "[2/10]" -Name "Palette LUT & VGA Timing" -VvpFile "palette_sim.vvp" `
    -CompileCmd "iverilog -o sim/build/palette_sim.vvp rtl/vga_timing.v rtl/palette_lut.v sim/tb/palette_lut_tb.v 2>&1" `
    -PassPattern "ALL TESTS PASSED" -VcdFile "palette_sim.vcd"

# 3. SDRAM Controller Functional
Run-Suite -Step "[3/10]" -Name "SDRAM Controller Functional" -VvpFile "sdram_sim.vvp" `
    -CompileCmd "iverilog -o sim/build/sdram_sim.vvp rtl/sdram_ctrl.v sim/models/sdram_model.v sim/tb/sdram_ctrl_tb.v 2>&1" `
    -PassPattern "ALL TESTS PASSED" -VcdFile "sdram_sim.vcd"

# 4. SDRAM Timing & Stress (546 tests)
Run-Suite -Step "[4/10]" -Name "SDRAM Timing & Stress (546 tests)" -VvpFile "sdram_timing_sim.vvp" `
    -CompileCmd "iverilog -o sim/build/sdram_timing_sim.vvp rtl/sdram_ctrl.v sim/models/sdram_model.v sim/tb/sdram_timing_tb.v 2>&1" `
    -PassPattern "ALL TIMING & STRESS TESTS PASSED" -VcdFile "sdram_timing_sim.vcd"

# 5. Top-Level GPU VGA Core (2 Full Frames)
Run-Suite -Step "[5/10]" -Name "GPU Top VGA (2 Frames)" -VvpFile "gpu_sim.vvp" `
    -CompileCmd "iverilog -o sim/build/gpu_sim.vvp -I rtl rtl/gpu_top.v rtl/vga_timing.v rtl/video_scanout.v rtl/color_generator.v rtl/palette_lut.v rtl/sdram_ctrl.v rtl/sdram_arbiter.v rtl/spi_slave.v rtl/cmd_decoder.v rtl/blitter.v rtl/rasterizer.v sim/models/gowin_rpll.v sim/tb/gpu_testbench.v 2>&1" `
    -PassPattern "PASS: At least 2 full frames rendered" -VcdFile "gpu_sim.vcd"

# 6. SPI Slave Interface (Mode 0, 7 tests)
Run-Suite -Step "[6/10]" -Name "SPI Slave (Mode 0, 7 tests)" -VvpFile "spi_sim.vvp" `
    -CompileCmd "iverilog -o sim/build/spi_sim.vvp rtl/spi_slave.v sim/tb/spi_slave_tb.v 2>&1" `
    -PassPattern "ALL SPI SLAVE TESTS PASSED" -VcdFile "spi_slave_sim.vcd"

# 7. Command Decoder FSM (11 tests)
Run-Suite -Step "[7/10]" -Name "Command Decoder (11 tests)" -VvpFile "cmd_sim.vvp" `
    -CompileCmd "iverilog -o sim/build/cmd_sim.vvp rtl/cmd_decoder.v sim/tb/cmd_decoder_tb.v 2>&1" `
    -PassPattern "ALL COMMAND DECODER TESTS PASSED" -VcdFile "cmd_decoder_sim.vcd"

# 8. Blitter Engine (12 tests)
Run-Suite -Step "[8/10]" -Name "Blitter Engine (12 tests)" -VvpFile "blitter_sim.vvp" `
    -CompileCmd "iverilog -o sim/build/blitter_sim.vvp rtl/blitter.v sim/tb/blitter_tb.v 2>&1" `
    -PassPattern "ALL 12 BLITTER ENGINE TESTS PASSED" -VcdFile "blitter_sim.vcd"

# 9. Rasterizer Engine (13 tests)
Run-Suite -Step "[9/10]" -Name "Rasterizer Engine (13 tests)" -VvpFile "rasterizer_sim.vvp" `
    -CompileCmd "iverilog -o sim/build/rasterizer_sim.vvp rtl/rasterizer.v sim/tb/rasterizer_tb.v 2>&1" `
    -PassPattern "ALL 13 RASTERIZER ENGINE TESTS PASSED" -VcdFile "rasterizer_sim.vcd"

# 10. GPU End-to-End System (6 tests)
Run-Suite -Step "[10/10]" -Name "GPU End-to-End System (6 tests)" -VvpFile "gpu_system_sim.vvp" `
    -CompileCmd "iverilog -o sim/build/gpu_system_sim.vvp -I rtl rtl/gpu_top.v rtl/vga_timing.v rtl/video_scanout.v rtl/color_generator.v rtl/palette_lut.v rtl/sdram_ctrl.v rtl/sdram_arbiter.v rtl/spi_slave.v rtl/cmd_decoder.v rtl/blitter.v rtl/rasterizer.v sim/models/gowin_rpll.v sim/models/sdram_model.v sim/tb/gpu_system_tb.v 2>&1" `
    -PassPattern "ALL GPU SYSTEM LEVEL TESTS PASSED" -VcdFile "gpu_system_sim.vcd"

# Dashboard Summary
Write-Host "`n========================================================" -ForegroundColor Cyan
Write-Host "                SIMULATION SUITE DASHBOARD              " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
$results | Format-Table -AutoSize
Write-Host "All waveforms saved to: sim/waves/" -ForegroundColor Green
Write-Host "Open any waveform with: gtkwave sim/waves/<File>`n"
