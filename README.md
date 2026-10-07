# Custom FPGA-Based GPU — "Find the Thief" Game Console
**Institution**: Woxsen University — School of Technology  
**Supervisor**: Dr. Bhanu Prakash  
**Hardware Target**: Sipeed Tang Nano 20K (Gowin GW2AR-LV18QN88C8/I7) + ESP32-S3-DevKitC-1  

---

## 📁 Project Directory Structure

```
d:/CP GPU/
├── rtl/                      # Synthesizable Verilog Hardware Modules
│   ├── top_board.v           # Board top wrapper with LED diagnostics & buttons
│   ├── gpu_top.v             # GPU core top-level module
│   ├── vga_timing.v          # 640x480 @ 60Hz timing generator (registered)
│   ├── color_generator.v     # 8-bar test pattern generator
│   ├── palette_lut.v         # 256 x 24-bit RGB Color Lookup Table (BRAM)
│   ├── tmds_encoder.v        # DVI 1.0 3-Channel 8b->10b encoder
│   ├── sdram_ctrl.v          # 8MB 32-bit SDRAM controller (adapted nand2mario)
│   └── gowin_rpll.v          # Gowin rPLL primitive (27 MHz -> 25.2 MHz)
│
├── constraints/              # Physical FPGA Pin Constraints
│   └── tang_nano_20k.cst     # Clock (Pin 4), Button (Pin 88), LEDs (Pins 15-18), VGA
│
├── gowin/                    # Gowin EDA Project Files
│   └── tang_nano_20k_gpu.gprj # Gowin IDE project file
│
├── sim/                      # Verification & Simulation Suite
│   ├── tb/                   # Verilog testbenches
│   │   ├── tmds_encoder_tb.v # TMDS 8b->10b & DC balance tests
│   │   ├── palette_lut_tb.v  # 256-color CLUT & timing tests
│   │   ├── sdram_ctrl_tb.v   # SDRAM controller tests
│   │   └── gpu_testbench.v   # Full 2-frame VGA render test
│   ├── models/               # Behavioral simulation models
│   │   ├── sdram_model.v     # 64Mbit SDR SDRAM chip behavioral model
│   │   └── gowin_rpll.v      # PLL simulation clock stub
│   ├── reference/            # External open-source references
│   │   ├── nand2mario_sdram.v
│   │   └── src_sdram_top.v
│   ├── waves/                # Simulation waveform dumps (*.vcd, *.gtkw)
│   └── build/                # Compiled simulation binaries (*.vvp)
│
├── firmware/                 # ESP32-S3 Dual-Core Firmware
│   └── main/                 # Game loop, nanoGPT inference, SPI master, USB gamepad
│
├── ai/                       # Custom nanoGPT Model (4.8M parameters)
│   ├── data/                 # 500+ NPC dialogue training samples & vocab
│   └── scripts/              # Training & INT8 quantization pipelines
│
├── assets/                   # Art Assets & Converters
│   ├── raw/                  # PNG sprites, tilesets, Aseprite files
│   └── bin/                  # Indexed binary assets for SD card / SDRAM upload
│
├── docs/                     # Project Specifications & Documentation
│   ├── Custom_FPGA_GPU_Project_Document.pdf
│   └── Custom_FPGA_GPU_Project_Document.docx
│
└── tools/                    # Automated Scripts & Utilities
    ├── run_all_sims.ps1      # One-click test runner (runs all 4 test suites)
    ├── generate_docx.py      # Documentation generator
    └── generate_pdf.py       # PDF build tool
```

---

## 🚀 Quick Start Commands

### 1. Run All Simulations (1 Second)
To compile and test all hardware modules with a full test report:
```powershell
powershell -ExecutionPolicy Bypass -File tools/run_all_sims.ps1
```

### 2. View Waveforms in GTKWave
```powershell
gtkwave sim/waves/sdram_sim.vcd
gtkwave sim/waves/tmds_encoder_sim.vcd
gtkwave sim/waves/palette_sim.vcd
gtkwave sim/waves/gpu_sim.vcd
```

### 3. Open in Gowin EDA
Open Gowin EDA and load:
`d:\CP GPU\gowin\tang_nano_20k_gpu.gprj` (or `d:\CP GPU\tang_nano_20k_gpu.gprj`)
