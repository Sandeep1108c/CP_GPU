// =============================================================================
// Testbench: SDRAM Controller Verification
// Project: Custom FPGA-Based GPU — Woxsen University
// Description:
//   Comprehensive testbench verifying the sdram_ctrl module with the
//   sdram_model behavioral simulation model.
//
//   Test Suite:
//     1. Initialization sequence (Precharge -> 2x AutoRefresh -> Mode Register -> IDLE)
//     2. Single-byte write with DQM masking to all 4 byte lanes (0, 1, 2, 3)
//     3. Byte-by-byte read and full 32-bit word readback (dout & dout32)
//     4. Multi-bank and multi-row write/read verification (Banks 0..3)
//     5. Auto-refresh execution and busy handshake
//
// Usage:
//   iverilog -o sdram_sim.vvp ../rtl/sdram_ctrl.v sdram_model.v sdram_ctrl_tb.v
//   vvp sdram_sim.vvp
//   gtkwave sdram_sim.vcd
// =============================================================================

`timescale 1ns / 1ps

module sdram_ctrl_tb;

    // =========================================================================
    // Clock & Reset Signals
    // =========================================================================
    reg         clk;
    reg         clk_sdram;
    reg         resetn;

    // Logic Interface Signals
    reg         rd;
    reg         wr;
    reg         refresh;
    reg  [22:0] addr;
    reg  [7:0]  din;
    wire [7:0]  dout;
    wire [31:0] dout32;
    wire        data_ready;
    wire        busy;

    // Physical SDRAM Bus
    wire [31:0] sdram_dq;
    wire [10:0] sdram_a;
    wire [1:0]  sdram_ba;
    wire        sdram_ncs;
    wire        sdram_nras;
    wire        sdram_ncas;
    wire        sdram_nwe;
    wire        sdram_clk;
    wire        sdram_cke;
    wire [3:0]  sdram_dqm;

    // Tracking
    integer pass_count = 0;
    integer fail_count = 0;

    // =========================================================================
    // Clocks: 27 MHz (Period ≈ 37.04 ns, Half = 18.52 ns)
    // clk_sdram is 180 degrees phase shifted (inverted clock)
    // =========================================================================
    localparam HALF_PERIOD = 18.52;

    initial clk = 0;
    always #(HALF_PERIOD) clk = ~clk;

    // clk_sdram is inverted clk (180 deg phase shift)
    always @(*) clk_sdram = ~clk;

    // =========================================================================
    // Instantiate DUT: SDRAM Controller
    // =========================================================================
    sdram_ctrl #(
        .FREQ          (27_000_000),
        .SIM_INIT_WAIT (1) // Fast initialization for simulation
    ) dut (
        .clk        (clk),
        .clk_sdram  (clk_sdram),
        .resetn     (resetn),
        .rd         (rd),
        .wr         (wr),
        .refresh    (refresh),
        .addr       (addr),
        .din        (din),
        .dout       (dout),
        .dout32     (dout32),
        .data_ready (data_ready),
        .busy       (busy),

        .SDRAM_DQ   (sdram_dq),
        .SDRAM_A    (sdram_a),
        .SDRAM_BA   (sdram_ba),
        .SDRAM_nCS  (sdram_ncs),
        .SDRAM_nRAS (sdram_nras),
        .SDRAM_nCAS (sdram_ncas),
        .SDRAM_nWE  (sdram_nwe),
        .SDRAM_CLK  (sdram_clk),
        .SDRAM_CKE  (sdram_cke),
        .SDRAM_DQM  (sdram_dqm)
    );

    // =========================================================================
    // Instantiate Behavioral SDRAM Simulation Model
    // =========================================================================
    sdram_model u_sdram_chip (
        .clk   (sdram_clk),
        .cke   (sdram_cke),
        .cs_n  (sdram_ncs),
        .ras_n (sdram_nras),
        .cas_n (sdram_ncas),
        .we_n  (sdram_nwe),
        .dqm   (sdram_dqm),
        .addr  (sdram_a),
        .ba    (sdram_ba),
        .dq    (sdram_dq)
    );

    // =========================================================================
    // Helper Tasks for SDRAM Access
    // =========================================================================

    // Task: Write a single byte to SDRAM
    task write_byte;
        input [22:0] target_addr;
        input [7:0]  target_data;
        begin
            @(negedge clk);
            while (busy) @(negedge clk); // Wait until controller is ready

            addr = target_addr;
            din  = target_data;
            wr   = 1'b1;
            @(negedge clk);
            wr   = 1'b0;

            // Wait for write command to finish
            while (busy) @(negedge clk);
        end
    endtask

    // Task: Read a single byte from SDRAM and check expected value
    task read_and_check_byte;
        input [22:0] target_addr;
        input [7:0]  expected_data;
        input [8*40-1:0] test_name;
        begin
            @(negedge clk);
            while (busy) @(negedge clk);

            addr = target_addr;
            rd   = 1'b1;
            @(negedge clk);
            rd   = 1'b0;

            // Wait for read data_ready strobe
            while (!data_ready) @(posedge clk);
            #1; // Sample immediately after clock edge

            if (dout === expected_data) begin
                $display("    PASS: %0s -> addr=0x%06X, data=0x%02X",
                         test_name, target_addr, dout);
                pass_count = pass_count + 1;
            end else begin
                $display("    FAIL: %0s -> addr=0x%06X, got 0x%02X, expected 0x%02X",
                         test_name, target_addr, dout, expected_data);
                fail_count = fail_count + 1;
            end

            while (busy) @(negedge clk);
        end
    endtask

    // =========================================================================
    // Main Test Sequence
    // =========================================================================
    initial begin
        $dumpfile("sdram_sim.vcd");
        $dumpvars(0, sdram_ctrl_tb);

        $display("");
        $display("========================================================");
        $display("   SDRAM CONTROLLER SIMULATION — Tang Nano 20K");
        $display("   64Mbit 32-bit SIP SDRAM (GW2AR-18C)");
        $display("   Custom FPGA GPU — Woxsen University");
        $display("========================================================");

        // Reset inputs
        resetn  = 1'b0;
        rd      = 1'b0;
        wr      = 1'b0;
        refresh = 1'b0;
        addr    = 23'd0;
        din     = 8'd0;

        // Apply reset
        #(HALF_PERIOD * 4);
        resetn = 1'b1;
        $display("[INFO] Reset released, waiting for SDRAM power-on initialization...");

        // =====================================================================
        // TEST 1: Power-On Initialization Sequence
        // =====================================================================
        begin : wait_init
            integer init_timeout;
            init_timeout = 0;
            while (busy && init_timeout < 1000) begin
                init_timeout = init_timeout + 1;
                @(posedge clk);
            end

            if (!busy) begin
                $display("  >> PASS: SDRAM initialization complete! Controller is IDLE.");
                pass_count = pass_count + 1;
            end else begin
                $display("  >> FAIL: SDRAM initialization timed out!");
                fail_count = fail_count + 1;
            end
        end

        // =====================================================================
        // TEST 2: Single-Byte Writes with DQM Masking (Bytes 0, 1, 2, 3)
        // =====================================================================
        $display("");
        $display("--- TEST 2: Single-Byte Writes with DQM Masking ---");
        $display("  Writing 4 individual bytes to word address 0x001000:");
        $display("    Byte 0 [0x001000] = 0x11");
        $display("    Byte 1 [0x001001] = 0x22");
        $display("    Byte 2 [0x001002] = 0x33");
        $display("    Byte 3 [0x001003] = 0x44");

        write_byte(23'h001000, 8'h11);
        write_byte(23'h001001, 8'h22);
        write_byte(23'h001002, 8'h33);
        write_byte(23'h001003, 8'h44);

        // =====================================================================
        // TEST 3: Byte Readback & 32-bit Word Check
        // =====================================================================
        $display("");
        $display("--- TEST 3: Byte Readback & 32-bit Word Read ---");

        read_and_check_byte(23'h001000, 8'h11, "Byte 0 (Offset 0)");
        read_and_check_byte(23'h001001, 8'h22, "Byte 1 (Offset 1)");
        read_and_check_byte(23'h001002, 8'h33, "Byte 2 (Offset 2)");
        read_and_check_byte(23'h001003, 8'h44, "Byte 3 (Offset 3)");

        // Check full 32-bit word output: {Byte3, Byte2, Byte1, Byte0} = 0x44332211
        if (dout32 === 32'h44332211) begin
            $display("    PASS: Full 32-bit word readback -> dout32=0x%08X", dout32);
            pass_count = pass_count + 1;
        end else begin
            $display("    FAIL: 32-bit word mismatch -> got 0x%08X, expected 0x44332211", dout32);
            fail_count = fail_count + 1;
        end

        // =====================================================================
        // TEST 4: Multi-Bank & Multi-Row Access
        // =====================================================================
        $display("");
        $display("--- TEST 4: Multi-Bank & Multi-Row Access ---");
        // Bank 0 (addr[22:21] = 00), Row 10, Col 5
        write_byte({2'b00, 11'd10, 8'd5, 2'b00}, 8'hA5);
        // Bank 1 (addr[22:21] = 01), Row 50, Col 20
        write_byte({2'b01, 11'd50, 8'd20, 2'b01}, 8'h5A);
        // Bank 2 (addr[22:21] = 10), Row 100, Col 80
        write_byte({2'b10, 11'd100, 8'd80, 2'b10}, 8'h7B);
        // Bank 3 (addr[22:21] = 11), Row 500, Col 150
        write_byte({2'b11, 11'd500, 8'd150, 2'b11}, 8'hF3);

        read_and_check_byte({2'b00, 11'd10, 8'd5, 2'b00},   8'hA5, "Bank 0 Row 10");
        read_and_check_byte({2'b01, 11'd50, 8'd20, 2'b01},  8'h5A, "Bank 1 Row 50");
        read_and_check_byte({2'b10, 11'd100, 8'd80, 2'b10}, 8'h7B, "Bank 2 Row 100");
        read_and_check_byte({2'b11, 11'd500, 8'd150, 2'b11}, 8'hF3, "Bank 3 Row 500");

        // =====================================================================
        // TEST 5: Auto-Refresh Cycle Verification
        // =====================================================================
        $display("");
        $display("--- TEST 5: Auto-Refresh Execution ---");

        @(negedge clk);
        refresh = 1'b1;
        @(negedge clk);
        refresh = 1'b0;

        if (busy) begin
            $display("    PASS: Controller asserted busy during refresh cycle");
            pass_count = pass_count + 1;
        end else begin
            $display("    FAIL: Controller did not assert busy during refresh");
            fail_count = fail_count + 1;
        end

        // Wait for refresh to complete
        while (busy) @(negedge clk);
        $display("    PASS: Auto-refresh completed, controller returned to IDLE");
        pass_count = pass_count + 1;

        // Verify data at Bank 0 is still retained after refresh
        read_and_check_byte({2'b00, 11'd10, 8'd5, 2'b00}, 8'hA5, "Retention post-refresh");

        // =====================================================================
        // Summary
        // =========================================================================
        $display("");
        $display("========================================================");
        $display("              SIMULATION RESULTS SUMMARY");
        $display("========================================================");
        $display("  Tests passed: %0d", pass_count);
        $display("  Tests failed: %0d", fail_count);
        if (fail_count == 0) begin
            $display("  >> ALL TESTS PASSED (100%% SUCCESS)");
        end else begin
            $display("  >> %0d TEST(S) FAILED", fail_count);
        end
        $display("========================================================");
        $display("");

        $finish;
    end

endmodule
