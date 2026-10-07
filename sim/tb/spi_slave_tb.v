// =============================================================================
// Testbench: SPI Slave Interface Verification
// Project: Custom FPGA-Based GPU — Woxsen University
// Device: Gowin GW2AR-18C (Sipeed Tang Nano 20K)
// Description:
//   Comprehensive testbench verifying the spi_slave module against the
//   ESP32-S3 SPI master protocol.
//
//   Test Matrix:
//     [TEST 1] Single Byte Transmission (MOSI -> rx_data, rx_valid, rx_first)
//     [TEST 2] GPU Packet: CLEAR command [0x01, 0x01, 0x3E]
//     [TEST 3] GPU Packet: DRAW_SPRITE 9-byte stream
//     [TEST 4] Robustness: Incomplete byte rejection on early CS_n abort
//     [TEST 5] Full-Duplex MISO Return Data (FPGA Status -> ESP32)
//     [TEST 6] Tri-state MISO verification when CS_n is deasserted
//
// Usage:
//   iverilog -o sim/build/spi_sim.vvp rtl/spi_slave.v sim/tb/spi_slave_tb.v
//   vvp sim/build/spi_sim.vvp
//   gtkwave sim/waves/spi_slave_sim.vcd
// =============================================================================

`timescale 1ns / 1ps

module spi_slave_tb;

    // =========================================================================
    // Signals
    // =========================================================================
    reg         clk;
    reg         reset;

    // Physical SPI Bus
    reg         spi_sclk;
    reg         spi_cs_n;
    reg         spi_mosi;
    wire        spi_miso;

    // Slave Output Interface
    wire [7:0]  rx_data;
    wire        rx_valid;
    wire        rx_first;
    wire        cs_active;

    // Slave Transmit Interface
    reg  [7:0]  tx_data;
    reg         tx_load;
    wire        tx_ready;

    // Tracking
    integer pass_count = 0;
    integer fail_count = 0;

    // =========================================================================
    // System Clock: 27 MHz (Period = 37.04 ns, Half = 18.52 ns)
    // SPI Clock: ~4.5 MHz (Period = 222.2 ns, Half = 111.1 ns)
    // =========================================================================
    localparam CLK_HALF = 18.52;
    localparam SPI_HALF = 111.1;

    initial clk = 0;
    always #(CLK_HALF) clk = ~clk;

    // =========================================================================
    // Instantiate DUT: SPI Slave
    // =========================================================================
    spi_slave #(
        .SPI_MODE (0)
    ) dut (
        .clk       (clk),
        .reset     (reset),
        .spi_sclk  (spi_sclk),
        .spi_cs_n  (spi_cs_n),
        .spi_mosi  (spi_mosi),
        .spi_miso  (spi_miso),
        .rx_data   (rx_data),
        .rx_valid  (rx_valid),
        .rx_first  (rx_first),
        .cs_active (cs_active),
        .tx_data   (tx_data),
        .tx_load   (tx_load),
        .tx_ready  (tx_ready)
    );

    // =========================================================================
    // Master SPI Driver Tasks (Mode 0: CPOL=0, CPHA=0)
    // =========================================================================

    // Task: Send a single byte via MOSI while reading MISO
    task spi_transfer_byte;
        input  [7:0] mosi_byte;
        output [7:0] miso_byte;
        integer bit_idx;
        begin
            miso_byte = 8'h00;
            for (bit_idx = 7; bit_idx >= 0; bit_idx = bit_idx - 1) begin
                // Mode 0: Data set on falling edge (or before clock starts)
                spi_mosi = mosi_byte[bit_idx];
                #(SPI_HALF);

                // Sample MISO on rising edge of SCLK
                spi_sclk = 1'b1;
                miso_byte[bit_idx] = spi_miso;
                #(SPI_HALF);

                spi_sclk = 1'b0;
            end
        end
    endtask

    // Buffer to capture bytes received by FPGA
    reg [7:0] captured_bytes [0:31];
    reg       captured_first [0:31];
    integer   capture_count = 0;

    // Continuous monitor of FPGA rx_valid
    always @(posedge clk) begin
        if (rx_valid) begin
            captured_bytes[capture_count] = rx_data;
            captured_first[capture_count] = rx_first;
            capture_count = capture_count + 1;
        end
    end

    // =========================================================================
    // Main Verification Sequence
    // =========================================================================
    reg [7:0] dummy_miso;
    reg [7:0] read_miso;
    integer   k;

    initial begin
        $dumpfile("spi_slave_sim.vcd");
        $dumpvars(0, spi_slave_tb);

        $display("");
        $display("========================================================");
        $display("   SPI SLAVE INTERFACE TESTBENCH — Tang Nano 20K       ");
        $display("   ESP32-S3 Master -> FPGA GPU Slave (Mode 0)          ");
        $display("   Custom FPGA GPU — Woxsen University                 ");
        $display("========================================================");

        // Reset
        reset    = 1'b1;
        spi_sclk = 1'b0;
        spi_cs_n = 1'b1;
        spi_mosi = 1'b0;
        tx_data  = 8'h00;
        tx_load  = 1'b0;

        #(CLK_HALF * 10);
        reset = 1'b0;
        #(CLK_HALF * 10);
        $display("[INFO] Reset released, starting SPI tests...\n");

        // =====================================================================
        // [TEST 1] Single Byte Transmission
        // =====================================================================
        $display("--- [TEST 1] Single Byte Transmission ---");
        capture_count = 0;

        // Transaction: CS low -> send 0xA5 -> CS high
        spi_cs_n = 1'b0;
        #(SPI_HALF);
        spi_transfer_byte(8'hA5, dummy_miso);
        #(SPI_HALF);
        spi_cs_n = 1'b1;
        #(CLK_HALF * 10);

        if (capture_count == 1 && captured_bytes[0] === 8'hA5 && captured_first[0] === 1'b1) begin
            $display("    >> PASS: Received byte 0xA5, rx_first=1");
            pass_count = pass_count + 1;
        end else begin
            $display("    >> FAIL: Expected 1 byte (0xA5, first=1), got count=%0d data=0x%02X first=%b",
                     capture_count, captured_bytes[0], captured_first[0]);
            fail_count = fail_count + 1;
        end

        // =====================================================================
        // [TEST 2] GPU Packet: CLEAR Command [0x01, 0x01, 0x3E]
        // =====================================================================
        $display("");
        $display("--- [TEST 2] GPU CLEAR Command Packet [0x01, 0x01, 0x3E] ---");
        capture_count = 0;

        spi_cs_n = 1'b0;
        #(SPI_HALF);
        spi_transfer_byte(8'h01, dummy_miso); // OPCODE: CLEAR
        spi_transfer_byte(8'h01, dummy_miso); // LEN: 1
        spi_transfer_byte(8'h3E, dummy_miso); // COLOR: 0x3E
        #(SPI_HALF);
        spi_cs_n = 1'b1;
        #(CLK_HALF * 10);

        if (capture_count == 3 &&
            captured_bytes[0] === 8'h01 && captured_first[0] === 1'b1 &&
            captured_bytes[1] === 8'h01 && captured_first[1] === 1'b0 &&
            captured_bytes[2] === 8'h3E && captured_first[2] === 1'b0) begin
            $display("    >> PASS: CLEAR packet correctly decoded: Opcode=0x01(first=1), Len=1, Color=0x3E");
            pass_count = pass_count + 1;
        end else begin
            $display("    >> FAIL: CLEAR packet mismatch! count=%0d", capture_count);
            fail_count = fail_count + 1;
        end

        // =====================================================================
        // [TEST 3] GPU Packet: DRAW_SPRITE 9-Byte Burst Stream
        // =====================================================================
        $display("");
        $display("--- [TEST 3] GPU DRAW_SPRITE 9-Byte Burst Stream ---");
        capture_count = 0;

        spi_cs_n = 1'b0;
        #(SPI_HALF);
        spi_transfer_byte(8'h02, dummy_miso); // Opcode: DRAW_SPRITE
        spi_transfer_byte(8'h07, dummy_miso); // Len: 7
        spi_transfer_byte(8'h00, dummy_miso); // X_HI: 0
        spi_transfer_byte(8'h64, dummy_miso); // X_LO: 100
        spi_transfer_byte(8'h00, dummy_miso); // Y_HI: 0
        spi_transfer_byte(8'h32, dummy_miso); // Y_LO: 50
        spi_transfer_byte(8'h00, dummy_miso); // ID_HI: 0
        spi_transfer_byte(8'h05, dummy_miso); // ID_LO: 5 (NPC 5)
        spi_transfer_byte(8'h01, dummy_miso); // Flags: 1 (Flip-X)
        #(SPI_HALF);
        spi_cs_n = 1'b1;
        #(CLK_HALF * 10);

        if (capture_count == 9 && captured_first[0] === 1'b1 && captured_first[1] === 1'b0) begin
            $display("    >> PASS: All 9 bytes received in single burst! Opcode correctly marked as first=1");
            pass_count = pass_count + 1;
        end else begin
            $display("    >> FAIL: DRAW_SPRITE burst mismatch! count=%0d", capture_count);
            fail_count = fail_count + 1;
        end

        // =====================================================================
        // [TEST 4] Robustness: Incomplete Byte Rejection (Early CS_n Abort)
        // =====================================================================
        $display("");
        $display("--- [TEST 4] Incomplete Byte Rejection on Early CS_n Abort ---");
        capture_count = 0;

        // Send only 5 bits of a byte, then abort by raising CS_n
        spi_cs_n = 1'b0;
        #(SPI_HALF);
        for (k = 0; k < 5; k = k + 1) begin
            spi_mosi = 1'b1;
            #(SPI_HALF);
            spi_sclk = 1'b1;
            #(SPI_HALF);
            spi_sclk = 1'b0;
        end
        #(SPI_HALF);
        spi_cs_n = 1'b1; // Abort!
        #(CLK_HALF * 10);

        if (capture_count == 0) begin
            $display("    >> PASS: Incomplete 5-bit transfer was correctly rejected (0 bytes emitted)");
            pass_count = pass_count + 1;
        end else begin
            $display("    >> FAIL: Incomplete transfer erroneously produced a byte! count=%0d", capture_count);
            fail_count = fail_count + 1;
        end

        // Now send a valid byte and ensure slave recovered
        capture_count = 0;
        spi_cs_n = 1'b0;
        #(SPI_HALF);
        spi_transfer_byte(8'h77, dummy_miso);
        #(SPI_HALF);
        spi_cs_n = 1'b1;
        #(CLK_HALF * 10);

        if (capture_count == 1 && captured_bytes[0] === 8'h77 && captured_first[0] === 1'b1) begin
            $display("    >> PASS: Slave fully recovered after abort and received next byte 0x77 cleanly");
            pass_count = pass_count + 1;
        end else begin
            $display("    >> FAIL: Slave failed to recover after abort!");
            fail_count = fail_count + 1;
        end

        // =====================================================================
        // [TEST 5] Full-Duplex MISO Telemetry (FPGA -> ESP32)
        // =====================================================================
        $display("");
        $display("--- [TEST 5] Full-Duplex MISO Return Data ---");

        // Pre-load telemetry status byte: 0x9B into FPGA slave
        @(posedge clk);
        tx_data = 8'h9B;
        tx_load = 1'b1;
        @(posedge clk);
        tx_load = 1'b0;
        @(posedge clk);

        // Master performs transfer and reads MISO
        spi_cs_n = 1'b0;
        #(SPI_HALF);
        spi_transfer_byte(8'h00, read_miso);
        #(SPI_HALF);
        spi_cs_n = 1'b1;
        #(CLK_HALF * 10);

        $display("  MISO Readback: 0x%02X (Expected: 0x9B)", read_miso);
        if (read_miso === 8'h9B) begin
            $display("    >> PASS: MISO transmitted byte 0x9B correctly to master");
            pass_count = pass_count + 1;
        end else begin
            $display("    >> FAIL: MISO byte mismatch! Got 0x%02X, expected 0x9B", read_miso);
            fail_count = fail_count + 1;
        end

        // =====================================================================
        // [TEST 6] Tri-state MISO Verification when CS_n is Inactive
        // =====================================================================
        $display("");
        $display("--- [TEST 6] Tri-state MISO Inactive Check ---");
        spi_cs_n = 1'b1; // CS_n high
        #(CLK_HALF * 10);

        if (spi_miso === 1'bz) begin
            $display("    >> PASS: MISO is high-Z (1'bz) when CS_n is inactive (allows multi-slave bus)");
            pass_count = pass_count + 1;
        end else begin
            $display("    >> FAIL: MISO not high-Z when unselected! Got %b", spi_miso);
            fail_count = fail_count + 1;
        end

        // =====================================================================
        // Grand Summary
        // =====================================================================
        $display("");
        $display("========================================================");
        $display("              SPI SLAVE SIMULATION SUMMARY              ");
        $display("========================================================");
        $display("  Total Tests Passed: %0d", pass_count);
        $display("  Total Tests Failed: %0d", fail_count);
        if (fail_count == 0) begin
            $display("  >> ALL SPI SLAVE TESTS PASSED (100%% SUCCESS)");
        end else begin
            $display("  >> %0d TEST(S) FAILED", fail_count);
        end
        $display("========================================================");
        $display("[INFO] Simulation complete. Waveform saved to spi_slave_sim.vcd\n");

        $finish;
    end

endmodule
