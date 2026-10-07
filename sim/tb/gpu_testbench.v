// =============================================================================
// Testbench: GPU Top-Level Simulation
// Project: Custom FPGA-Based GPU — Woxsen University
// Description:
//   Comprehensive testbench that simulates the GPU rendering pipeline.
//   - Drives a 27 MHz crystal clock (matching Tang Nano 20K hardware)
//   - PLL stub generates 25.175 MHz pixel clock internally
//   - Applies reset, then lets the GPU run for 2 full frames
//   - Dumps all signals to a VCD file for GTKWave visualization
//   - Prints timing verification messages to the console
//
// Usage:
//   iverilog -o gpu_sim.vvp ../rtl/vga_timing.v ../rtl/color_generator.v ../rtl/gpu_top.v gowin_rpll.v gpu_testbench.v
//   vvp gpu_sim.vvp
//   gtkwave gpu_sim.vcd
// =============================================================================

`timescale 1ns / 1ps

module gpu_testbench;

    // =========================================================================
    // Testbench Signals
    // =========================================================================
    reg         clk_27m;      // 27 MHz crystal oscillator
    reg         reset;
    wire        hsync;
    wire        vsync;
    wire        video_active;
    wire [9:0]  pixel_x;
    wire [9:0]  pixel_y;
    wire [7:0]  red;
    wire [7:0]  green;
    wire [7:0]  blue;
    wire        pixel_clk;

    // SPI & SDRAM wires for testbench
    wire [31:0] sdram_dq;
    wire [10:0] sdram_a;
    wire [1:0]  sdram_ba;
    wire        sdram_ncs, sdram_nras, sdram_ncas, sdram_nwe, sdram_clk, sdram_cke;
    wire [3:0]  sdram_dqm;

    // =========================================================================
    // Instantiate the Design Under Test (DUT)
    // =========================================================================
    gpu_top dut (
        .clk_27m       (clk_27m),
        .reset         (reset),

        .spi_sclk      (1'b0),
        .spi_cs_n      (1'b1),
        .spi_mosi      (1'b0),
        .spi_miso      (),

        .SDRAM_DQ      (sdram_dq),
        .SDRAM_A       (sdram_a),
        .SDRAM_BA      (sdram_ba),
        .SDRAM_nCS     (sdram_ncs),
        .SDRAM_nRAS    (sdram_nras),
        .SDRAM_nCAS    (sdram_ncas),
        .SDRAM_nWE     (sdram_nwe),
        .SDRAM_CLK     (sdram_clk),
        .SDRAM_CKE     (sdram_cke),
        .SDRAM_DQM     (sdram_dqm),

        .hsync         (hsync),
        .vsync         (vsync),
        .video_active  (video_active),
        .pixel_x       (pixel_x),
        .pixel_y       (pixel_y),
        .red           (red),
        .green         (green),
        .blue          (blue),

        .clk_pixel     (pixel_clk),
        .clk_serial    (),
        .pll_lock      (),
        .gpu_busy      (),
        .cmd_busy      (),
        .cmd_error     (),
        .buf_front_idx ()
    );

    // =========================================================================
    // Clock Generation: 27 MHz crystal → period = 37.037 ns → half ≈ 18.518 ns
    // The PLL inside gpu_top converts this to 25.175 MHz pixel clock
    // =========================================================================
    localparam HALF_PERIOD_27M = 18.518;  // nanoseconds (27 MHz)

    initial clk_27m = 0;
    always #(HALF_PERIOD_27M) clk_27m = ~clk_27m;

    // =========================================================================
    // Frame & Line Counters for Verification
    // (Triggered on the internal 25.175 MHz pixel clock domain)
    // =========================================================================
    integer frame_count   = 0;
    integer line_count    = 0;
    integer pixel_count   = 0;
    reg     prev_vsync;
    reg     prev_hsync;

    // Use the PLL output clock for counting

    always @(posedge pixel_clk) begin
        prev_vsync <= vsync;
        prev_hsync <= hsync;

        // Detect VSYNC falling edge (start of new frame)
        if (prev_vsync && !vsync) begin
            frame_count <= frame_count + 1;
            $display("====================================================");
            $display("[FRAME %0d COMPLETE] at time %0t ns", frame_count, $time);
            $display("====================================================");
        end

        // Detect HSYNC falling edge (start of new line)
        if (prev_hsync && !hsync) begin
            line_count <= line_count + 1;
        end

        // Count active pixels
        if (video_active) begin
            pixel_count <= pixel_count + 1;
        end
    end

    // =========================================================================
    // Simulation Control
    // =========================================================================
    initial begin
        // --- VCD Dump Setup for GTKWave ---
        $dumpfile("gpu_sim.vcd");
        $dumpvars(1, gpu_testbench);

        // --- Console Header ---
        $display("");
        $display("========================================================");
        $display("   CUSTOM FPGA GPU SIMULATION - Woxsen University");
        $display("   VGA 640x480 @ 60Hz | Crystal: 27 MHz + PLL");
        $display("   Hardware: ESP32-S3 + Tang Nano 20K (GW2AR-18)");
        $display("========================================================");
        $display("");
        $display("[INFO] Starting simulation...");
        $display("[INFO] Crystal clock: 27 MHz (period: %.2f ns)", HALF_PERIOD_27M * 2);
        $display("[INFO] PLL output: 25.175 MHz pixel clock");
        $display("[INFO] Expected H total: 800 pixels per line");
        $display("[INFO] Expected V total: 525 lines per frame");
        $display("[INFO] Expected frame time: %0d pixel clock cycles", 800 * 525);
        $display("");

        // --- Apply Reset ---
        reset = 1;
        #500;           // Hold reset for ~500ns (covers PLL lock time of ~200ns)
        reset = 0;
        $display("[INFO] Reset de-asserted at time %0t ns", $time);
        $display("[INFO] GPU pipeline running...");
        $display("");

        // --- Run for 2 full frames ---
        // 1 frame = 800 * 525 = 420,000 pixel clock cycles
        // At 25.175 MHz: 1 frame = 420,000 * 39.72 ns = ~16.68 ms
        // 2 frames = ~33.36 ms, add margin
        #35000000;      // 35 ms — covers 2+ full frames


        // --- Final Verification ---
        $display("");
        $display("========================================================");
        $display("            SIMULATION RESULTS SUMMARY");
        $display("========================================================");
        $display("  Frames completed    : %0d", frame_count);
        $display("  Total lines drawn   : %0d", line_count);
        $display("  Active pixels drawn : %0d", pixel_count);
        $display("  Expected pixels/frame: %0d (640 x 480)", 640 * 480);
        $display("");

        if (frame_count >= 2) begin
            $display("  >> PASS: At least 2 full frames rendered!");
        end else begin
            $display("  >> FAIL: Expected 2 frames, got %0d", frame_count);
        end

        $display("");
        $display("[INFO] Simulation complete. Open gpu_sim.vcd in GTKWave.");
        $display("");

        $finish;
    end

    // =========================================================================
    // Optional: Monitor first few pixels for debugging
    // =========================================================================
    initial begin
        // Wait for reset to release
        @(negedge reset);
        // Wait a bit for PLL to settle
        #100;
        // Print first 10 active pixels
        repeat(10) begin
            @(posedge pixel_clk);
            if (video_active) begin
                $display("[PIXEL] x=%0d y=%0d | R=0x%02h G=0x%02h B=0x%02h",
                         pixel_x, pixel_y, red, green, blue);
            end
        end
    end

endmodule
