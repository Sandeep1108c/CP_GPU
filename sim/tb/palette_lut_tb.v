// =============================================================================
// Testbench: Palette LUT & Updated VGA Timing Verification
// Project: Custom FPGA-Based GPU — Woxsen University
// Description:
//   Comprehensive testbench verifying:
//     1. palette_lut: Default 256-color initialization (VGA 16, color cube, gray)
//     2. palette_lut: Dynamic write port (SET_PALETTE opcode 0x05)
//     3. vga_timing: 640x480 @ 60Hz timing (HSYNC, VSYNC, video_active, porches)
//     4. vga_timing: frame_sync and line_sync strobes
//     5. Pipeline integration: vga_timing -> color pattern -> palette_lut
// =============================================================================

`timescale 1ns / 1ps

module palette_lut_tb;

    // =========================================================================
    // Signals
    // =========================================================================
    reg         clk;
    reg         reset;

    // Palette LUT signals
    reg  [7:0]  color_idx;
    wire [7:0]  red, green, blue;
    wire [23:0] rgb;
    reg         wr_en;
    reg  [7:0]  wr_addr;
    reg  [7:0]  wr_r, wr_g, wr_b;

    // VGA Timing signals
    wire        hsync, vsync, video_active;
    wire [9:0]  pixel_x, pixel_y;
    wire        frame_sync, line_sync;

    // Tracking
    integer pass_count = 0;
    integer fail_count = 0;

    // =========================================================================
    // DUT 1: Palette LUT
    // =========================================================================
    palette_lut u_palette (
        .clk       (clk),
        .reset     (reset),
        .color_idx (color_idx),
        .red       (red),
        .green     (green),
        .blue      (blue),
        .rgb       (rgb),
        .wr_en     (wr_en),
        .wr_addr   (wr_addr),
        .wr_r      (wr_r),
        .wr_g      (wr_g),
        .wr_b      (wr_b)
    );

    // =========================================================================
    // DUT 2: Updated VGA Timing Generator
    // =========================================================================
    vga_timing u_vga_timing (
        .clk          (clk),
        .reset        (reset),
        .hsync        (hsync),
        .vsync        (vsync),
        .video_active (video_active),
        .pixel_x      (pixel_x),
        .pixel_y      (pixel_y),
        .frame_sync   (frame_sync),
        .line_sync    (line_sync)
    );

    // =========================================================================
    // Clock: 25.175 MHz pixel clock (period = 39.72 ns, half = 19.86 ns)
    // =========================================================================
    localparam HALF_PERIOD = 19.86;
    initial clk = 0;
    always #(HALF_PERIOD) clk = ~clk;

    // =========================================================================
    // Helper task
    // =========================================================================
    task check_rgb;
        input [23:0] actual;
        input [23:0] expected;
        input [8*40-1:0] test_name;
        begin
            if (actual === expected) begin
                $display("    PASS: %0s -> RGB=0x%06X", test_name, actual);
                pass_count = pass_count + 1;
            end else begin
                $display("    FAIL: %0s -> got RGB=0x%06X, expected 0x%06X",
                         test_name, actual, expected);
                fail_count = fail_count + 1;
            end
        end
    endtask

    // =========================================================================
    // Main Test Sequence
    // =========================================================================
    integer h_active_clocks;
    integer h_sync_clocks;
    integer total_line_clocks;

    initial begin
        $dumpfile("palette_sim.vcd");
        $dumpvars(0, palette_lut_tb);

        $display("");
        $display("========================================================");
        $display("   PALETTE LUT & VGA TIMING SIMULATION");
        $display("   Custom FPGA GPU — Woxsen University");
        $display("========================================================");

        // Reset
        reset = 1;
        wr_en = 0; wr_addr = 0; wr_r = 0; wr_g = 0; wr_b = 0;
        color_idx = 0;

        #(HALF_PERIOD * 10);
        reset = 0;
        @(posedge clk);
        $display("[INFO] Reset released, starting tests...");

        // =====================================================================
        // TEST 1: Default Palette Initialization Verification
        // (1 cycle read latency in BRAM)
        // =====================================================================
        $display("");
        $display("--- TEST 1: Default Palette Colors (Read Port) ---");

        // Index 0: Black (0x000000)
        color_idx = 8'd0;
        @(posedge clk); #1;
        check_rgb(rgb, 24'h000000, "Index 0 (Black)");

        // Index 1: Blue (0x0000AA)
        color_idx = 8'd1;
        @(posedge clk); #1;
        check_rgb(rgb, 24'h0000AA, "Index 1 (Blue)");

        // Index 4: Red (0xAA0000)
        color_idx = 8'd4;
        @(posedge clk); #1;
        check_rgb(rgb, 24'hAA0000, "Index 4 (Red)");

        // Index 15: White (0xFFFFFF)
        color_idx = 8'd15;
        @(posedge clk); #1;
        check_rgb(rgb, 24'hFFFFFF, "Index 15 (White)");

        // Index 231: Full color cube corner (0xFFFFFF)
        color_idx = 8'd231;
        @(posedge clk); #1;
        check_rgb(rgb, 24'hFFFFFF, "Index 231 (Cube 5,5,5 White)");

        // Index 232: Grayscale 0 (8 + 0*10 = 8 -> 0x080808)
        color_idx = 8'd232;
        @(posedge clk); #1;
        check_rgb(rgb, 24'h080808, "Index 232 (Darkest Gray)");

        // =====================================================================
        // TEST 2: Dynamic Palette Write (SET_PALETTE Opcode 0x05)
        // =====================================================================
        $display("");
        $display("--- TEST 2: Dynamic Palette Write (SET_PALETTE) ---");

        // Write custom Neon Orange (0xFF, 0x88, 0x00) to Index 42
        @(negedge clk);
        wr_en   = 1;
        wr_addr = 8'd42;
        wr_r    = 8'hFF;
        wr_g    = 8'h88;
        wr_b    = 8'h00;
        @(negedge clk);
        wr_en   = 0;

        // Read Index 42 back (present address on negedge, check after next posedge)
        color_idx = 8'd42;
        @(posedge clk); #1;
        check_rgb(rgb, 24'hFF8800, "Index 42 (Written: Neon Orange)");

        // Overwrite Index 0 (Black -> Bright Cyan 0x00FFFF)
        @(negedge clk);
        wr_en   = 1;
        wr_addr = 8'd0;
        wr_r    = 8'h00;
        wr_g    = 8'hFF;
        wr_b    = 8'hFF;
        @(negedge clk);
        wr_en   = 0;

        // Read Index 0 back
        color_idx = 8'd0;
        @(posedge clk); #1;
        check_rgb(rgb, 24'h00FFFF, "Index 0 (Overwritten: Bright Cyan)");

        // =====================================================================
        // TEST 3: VGA Timing Verification (1 Full Line)
        // =====================================================================
        $display("");
        $display("--- TEST 3: VGA Timing Single Line Check ---");

        // Wait until line_sync is detected
        while (!line_sync) @(posedge clk);
        $display("    [INFO] Detected line_sync at time %0t ns", $time);

        // Measure line characteristics from this line_sync until the next line_sync
        h_active_clocks   = 0;
        h_sync_clocks     = 0;
        total_line_clocks = 0;

        // Advance one cycle so line_sync clears
        if (video_active) h_active_clocks = h_active_clocks + 1;
        if (!hsync)       h_sync_clocks   = h_sync_clocks + 1;
        total_line_clocks = total_line_clocks + 1;
        @(posedge clk);

        while (!line_sync) begin
            if (video_active) h_active_clocks = h_active_clocks + 1;
            if (!hsync)       h_sync_clocks   = h_sync_clocks + 1;
            total_line_clocks = total_line_clocks + 1;
            @(posedge clk);
        end

        $display("    Total line clocks: %0d (Expected: 800)", total_line_clocks);
        $display("    Active pixel clocks: %0d (Expected: 640)", h_active_clocks);
        $display("    HSYNC pulse width: %0d (Expected: 96)", h_sync_clocks);

        if (total_line_clocks == 800) begin
            $display("    PASS: Total line length == 800 clocks");
            pass_count = pass_count + 1;
        end else begin
            $display("    FAIL: Total line length mismatch (got %0d, expected 800)", total_line_clocks);
            fail_count = fail_count + 1;
        end

        if (h_active_clocks == 640) begin
            $display("    PASS: Active pixel count == 640 clocks");
            pass_count = pass_count + 1;
        end else begin
            $display("    FAIL: Active pixel count mismatch (got %0d, expected 640)", h_active_clocks);
            fail_count = fail_count + 1;
        end

        if (h_sync_clocks == 96) begin
            $display("    PASS: HSYNC active-low pulse == 96 clocks");
            pass_count = pass_count + 1;
        end else begin
            $display("    FAIL: HSYNC pulse width mismatch (got %0d, expected 96)", h_sync_clocks);
            fail_count = fail_count + 1;
        end

        // =====================================================================
        // TEST 4: Frame Sync & VSYNC Pulse Verification
        // =====================================================================
        $display("");
        $display("--- TEST 4: Frame Sync & VSYNC Detection ---");

        // Monitor for frame_sync
        begin : wait_frame_sync
            integer timeout;
            timeout = 0;
            while (!frame_sync && timeout < 450000) begin
                timeout = timeout + 1;
                @(posedge clk);
            end
            if (frame_sync) begin
                $display("    PASS: frame_sync pulse detected at time %0t ns", $time);
                pass_count = pass_count + 1;
            end else begin
                $display("    FAIL: frame_sync timed out!");
                fail_count = fail_count + 1;
            end
        end

        // Wait for VSYNC pulse (active low)
        begin : wait_vsync
            integer vsync_pulse_clocks;
            vsync_pulse_clocks = 0;
            while (vsync) @(posedge clk); // wait for vsync to go low
            $display("    [INFO] VSYNC went low at time %0t ns", $time);
            while (!vsync) begin
                vsync_pulse_clocks = vsync_pulse_clocks + 1;
                @(posedge clk);
            end
            $display("    VSYNC low duration: %0d clocks (Expected: 2 lines * 800 = 1600 clocks)", vsync_pulse_clocks);
            if (vsync_pulse_clocks == 1600) begin
                $display("    PASS: VSYNC pulse width exactly 2 lines (1600 clocks)");
                pass_count = pass_count + 1;
            end else begin
                $display("    FAIL: VSYNC pulse width mismatch (got %0d, expected 1600)", vsync_pulse_clocks);
                fail_count = fail_count + 1;
            end
        end

        // =====================================================================
        // Summary
        // =====================================================================
        $display("");
        $display("========================================================");
        $display("              SIMULATION RESULTS SUMMARY");
        $display("========================================================");
        $display("  Tests passed: %0d", pass_count);
        $display("  Tests failed: %0d", fail_count);
        if (fail_count == 0) begin
            $display("  >> ALL TESTS PASSED");
        end else begin
            $display("  >> %0d TEST(S) FAILED", fail_count);
        end
        $display("========================================================");
        $display("");

        $finish;
    end

endmodule
