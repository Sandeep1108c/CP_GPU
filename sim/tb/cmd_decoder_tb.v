// =============================================================================
// Testbench: GPU Command Decoder Verification (cmd_decoder_tb.v)
// Project: Custom FPGA-Based GPU — Woxsen University
// Device: Gowin GW2AR-18C (Sipeed Tang Nano 20K)
// Description:
//   Comprehensive verification suite for cmd_decoder.v covering:
//     [TEST 1]  NOP (0x00) - No-op and error clearance
//     [TEST 2]  CLEAR (0x01) - Framebuffer clear with 8-bit color
//     [TEST 3]  DRAW_SPRITE (0x02) - 7-byte blit descriptor
//     [TEST 4]  DRAW_LINE (0x03) - 9-byte Bresenham line descriptor
//     [TEST 5]  DRAW_RECT (0x04) - 9-byte filled rectangle descriptor
//     [TEST 6]  SET_PALETTE (0x05) - 4-byte palette entry update
//     [TEST 7]  SWAP_BUFFER (0x06) - Double-buffering & VSYNC synchronization
//     [TEST 8]  LOAD_SPRITE (0x07) - Streaming pixel write into SDRAM address
//     [TEST 9]  Error Recovery: Early CS abort during multi-byte payload
//     [TEST 10] Error Recovery: Invalid/unknown opcode handling
// =============================================================================

`timescale 1ns / 1ps

module cmd_decoder_tb;

    // -------------------------------------------------------------------------
    // DUT Signals
    // -------------------------------------------------------------------------
    reg         clk;
    reg         reset;

    // SPI Slave Interface
    reg  [7:0]  rx_data;
    reg         rx_valid;
    reg         rx_first;
    reg         cs_active;

    // Telemetry
    wire [7:0]  tx_data;
    wire        tx_load;
    reg         tx_ready;

    // Video Timing
    reg         vsync;
    reg         in_vblank;
    wire        buf_front_idx;
    wire        buf_back_idx;
    wire        swap_pending;

    // Palette LUT
    wire        palette_wr_en;
    wire [7:0]  palette_addr;
    wire [7:0]  palette_r;
    wire [7:0]  palette_g;
    wire [7:0]  palette_b;

    // Clear Engine
    wire        clear_start;
    wire [7:0]  clear_color;
    reg         clear_done;
    reg         clear_busy;

    // Blitter Engine
    wire        sprite_start;
    wire [15:0] sprite_x;
    wire [15:0] sprite_y;
    wire [15:0] sprite_id;
    wire [7:0]  sprite_flags;
    reg         sprite_done;
    reg         sprite_busy;

    // Rasterizer Engine
    wire        line_start;
    wire [15:0] line_x0;
    wire [15:0] line_y0;
    wire [15:0] line_x1;
    wire [15:0] line_y1;
    wire [7:0]  line_color;
    reg         line_done;
    reg         line_busy;

    wire        rect_start;
    wire [15:0] rect_x;
    wire [15:0] rect_y;
    wire [15:0] rect_w;
    wire [15:0] rect_h;
    wire [7:0]  rect_color;
    reg         rect_done;
    reg         rect_busy;

    // SDRAM Loader
    wire        sdram_load_start;
    wire [23:0] sdram_load_addr;
    wire [7:0]  sdram_load_data;
    wire        sdram_load_valid;
    reg         sdram_load_ready;

    // Diagnostics
    wire        gpu_busy;
    wire        cmd_busy;
    wire        cmd_error;

    // Test Tracking
    integer pass_count = 0;
    integer fail_count = 0;

    // -------------------------------------------------------------------------
    // System Clock: 27 MHz (Period = 37.04 ns, Half = 18.52 ns)
    // -------------------------------------------------------------------------
    localparam CLK_HALF = 18.52;
    initial clk = 0;
    always #(CLK_HALF) clk = ~clk;

    // -------------------------------------------------------------------------
    // Instantiate DUT
    // -------------------------------------------------------------------------
    cmd_decoder dut (
        .clk              (clk),
        .reset            (reset),
        .rx_data          (rx_data),
        .rx_valid         (rx_valid),
        .rx_first         (rx_first),
        .cs_active        (cs_active),
        .tx_data          (tx_data),
        .tx_load          (tx_load),
        .tx_ready         (tx_ready),
        .vsync            (vsync),
        .in_vblank        (in_vblank),
        .buf_front_idx    (buf_front_idx),
        .buf_back_idx     (buf_back_idx),
        .swap_pending     (swap_pending),
        .palette_wr_en    (palette_wr_en),
        .palette_addr     (palette_addr),
        .palette_r        (palette_r),
        .palette_g        (palette_g),
        .palette_b        (palette_b),
        .clear_start      (clear_start),
        .clear_color      (clear_color),
        .clear_done       (clear_done),
        .clear_busy       (clear_busy),
        .sprite_start     (sprite_start),
        .sprite_x         (sprite_x),
        .sprite_y         (sprite_y),
        .sprite_id        (sprite_id),
        .sprite_flags     (sprite_flags),
        .sprite_done      (sprite_done),
        .sprite_busy      (sprite_busy),
        .line_start       (line_start),
        .line_x0          (line_x0),
        .line_y0          (line_y0),
        .line_x1          (line_x1),
        .line_y1          (line_y1),
        .line_color       (line_color),
        .line_done        (line_done),
        .line_busy        (line_busy),
        .rect_start       (rect_start),
        .rect_x           (rect_x),
        .rect_y           (rect_y),
        .rect_w           (rect_w),
        .rect_h           (rect_h),
        .rect_color       (rect_color),
        .rect_done        (rect_done),
        .rect_busy        (rect_busy),
        .sdram_load_start (sdram_load_start),
        .sdram_load_addr  (sdram_load_addr),
        .sdram_load_data  (sdram_load_data),
        .sdram_load_valid (sdram_load_valid),
        .sdram_load_ready (sdram_load_ready),
        .gpu_busy         (gpu_busy),
        .cmd_busy         (cmd_busy),
        .cmd_error        (cmd_error)
    );

    // -------------------------------------------------------------------------
    // Helper Tasks for Byte Stream Injection
    // -------------------------------------------------------------------------
    task send_byte;
        input [7:0] b;
        input       is_first;
        begin
            @(posedge clk);
            rx_data  <= b;
            rx_valid <= 1'b1;
            rx_first <= is_first;
            @(posedge clk);
            rx_valid <= 1'b0;
            rx_first <= 1'b0;
            #(CLK_HALF * 2);
        end
    endtask

    // -------------------------------------------------------------------------
    // Main Verification Sequence
    // -------------------------------------------------------------------------
    initial begin
        $dumpfile("cmd_decoder_sim.vcd");
        $dumpvars(0, cmd_decoder_tb);

        $display("");
        $display("========================================================");
        $display("   GPU COMMAND DECODER FSM TESTBENCH — Tang Nano 20K   ");
        $display("   Custom FPGA GPU — Woxsen University                 ");
        $display("========================================================");

        // Initialize signals
        reset            = 1'b1;
        rx_data          = 8'h00;
        rx_valid         = 1'b0;
        rx_first         = 1'b0;
        cs_active        = 1'b0;
        tx_ready         = 1'b1;
        vsync            = 1'b0;
        in_vblank        = 1'b0;
        clear_done       = 1'b0;
        clear_busy       = 1'b0;
        sprite_done      = 1'b0;
        sprite_busy      = 1'b0;
        line_done        = 1'b0;
        line_busy        = 1'b0;
        rect_done        = 1'b0;
        rect_busy        = 1'b0;
        sdram_load_ready = 1'b1;

        #(CLK_HALF * 10);
        reset = 1'b0;
        #(CLK_HALF * 10);
        $display("[INFO] Reset released, starting Command Decoder verification...\n");

        // =====================================================================
        // [TEST 1] NOP Command (0x00, Len 0)
        // =====================================================================
        $display("--- [TEST 1] NOP Command (0x00, Len 0) ---");
        cs_active = 1'b1;
        send_byte(8'h00, 1'b1); // CMD: NOP
        send_byte(8'h00, 1'b0); // LEN: 0
        cs_active = 1'b0;
        #(CLK_HALF * 6);

        if (cmd_error === 1'b0 && cmd_busy === 1'b0) begin
            $display("    >> PASS: NOP executed cleanly with no error");
            pass_count = pass_count + 1;
        end else begin
            $display("    >> FAIL: NOP caused unexpected state: cmd_error=%b, cmd_busy=%b", cmd_error, cmd_busy);
            fail_count = fail_count + 1;
        end

        // =====================================================================
        // [TEST 2] CLEAR Command (0x01, Len 1, Color 0x3E)
        // =====================================================================
        $display("");
        $display("--- [TEST 2] CLEAR Command (0x01, Len 1, Color 0x3E) ---");
        cs_active = 1'b1;
        send_byte(8'h01, 1'b1); // CMD: CLEAR
        send_byte(8'h01, 1'b0); // LEN: 1
        send_byte(8'h3E, 1'b0); // COLOR: 0x3E
        cs_active = 1'b0;

        // Wait for clear_start strobe
        @(posedge clear_start);
        if (clear_color === 8'h3E) begin
            $display("    >> Captured clear_start strobe with clear_color = 0x%02X", clear_color);
            clear_busy = 1'b1;
            #(CLK_HALF * 6);
            clear_busy = 1'b0;
            clear_done = 1'b1;
            @(posedge clk);
            clear_done = 1'b0;
            #(CLK_HALF * 6);

            if (cmd_busy === 1'b0 && cmd_error === 1'b0) begin
                $display("    >> PASS: CLEAR command executed and handshake completed");
                pass_count = pass_count + 1;
            end else begin
                $display("    >> FAIL: CLEAR did not return to idle after clear_done");
                fail_count = fail_count + 1;
            end
        end else begin
            $display("    >> FAIL: clear_color mismatch! Got 0x%02X, expected 0x3E", clear_color);
            fail_count = fail_count + 1;
        end

        // =====================================================================
        // [TEST 3] DRAW_SPRITE Command (0x02, Len 7)
        // =====================================================================
        $display("");
        $display("--- [TEST 3] DRAW_SPRITE (0x02, Len 7: x=100, y=50, id=5, flags=1) ---");
        cs_active = 1'b1;
        send_byte(8'h02, 1'b1); // CMD: DRAW_SPRITE
        send_byte(8'h07, 1'b0); // LEN: 7
        send_byte(8'h00, 1'b0); // X_HI: 0
        send_byte(8'h64, 1'b0); // X_LO: 100
        send_byte(8'h00, 1'b0); // Y_HI: 0
        send_byte(8'h32, 1'b0); // Y_LO: 50
        send_byte(8'h00, 1'b0); // ID_HI: 0
        send_byte(8'h05, 1'b0); // ID_LO: 5
        send_byte(8'h01, 1'b0); // FLAGS: 1 (Flip-X)
        cs_active = 1'b0;

        @(posedge sprite_start);
        if (sprite_x === 16'd100 && sprite_y === 16'd50 && sprite_id === 16'd5 && sprite_flags === 8'd1) begin
            $display("    >> Deserialized params: x=%0d, y=%0d, id=%0d, flags=0x%02X",
                     sprite_x, sprite_y, sprite_id, sprite_flags);
            sprite_busy = 1'b1;
            #(CLK_HALF * 6);
            sprite_busy = 1'b0;
            sprite_done = 1'b1;
            @(posedge clk);
            sprite_done = 1'b0;
            #(CLK_HALF * 6);

            $display("    >> PASS: DRAW_SPRITE parsed and triggered correctly");
            pass_count = pass_count + 1;
        end else begin
            $display("    >> FAIL: DRAW_SPRITE parameters corrupted! x=%0d y=%0d id=%0d flags=%b",
                     sprite_x, sprite_y, sprite_id, sprite_flags);
            fail_count = fail_count + 1;
        end

        // =====================================================================
        // [TEST 4] DRAW_LINE Command (0x03, Len 9)
        // =====================================================================
        $display("");
        $display("--- [TEST 4] DRAW_LINE (0x03, Len 9: (10,20)->(80,90), color=0x0C) ---");
        cs_active = 1'b1;
        send_byte(8'h03, 1'b1); // CMD: DRAW_LINE
        send_byte(8'h09, 1'b0); // LEN: 9
        send_byte(8'h00, 1'b0); // X0_HI
        send_byte(8'h0A, 1'b0); // X0_LO: 10
        send_byte(8'h00, 1'b0); // Y0_HI
        send_byte(8'h14, 1'b0); // Y0_LO: 20
        send_byte(8'h00, 1'b0); // X1_HI
        send_byte(8'h50, 1'b0); // X1_LO: 80
        send_byte(8'h00, 1'b0); // Y1_HI
        send_byte(8'h5A, 1'b0); // Y1_LO: 90
        send_byte(8'h0C, 1'b0); // COLOR: 0x0C
        cs_active = 1'b0;

        @(posedge line_start);
        if (line_x0 === 16'd10 && line_y0 === 16'd20 &&
            line_x1 === 16'd80 && line_y1 === 16'd90 && line_color === 8'h0C) begin
            $display("    >> Deserialized line: (%0d,%0d) -> (%0d,%0d), color=0x%02X",
                     line_x0, line_y0, line_x1, line_y1, line_color);
            line_done = 1'b1;
            @(posedge clk);
            line_done = 1'b0;
            #(CLK_HALF * 6);

            $display("    >> PASS: DRAW_LINE parameters and trigger verified");
            pass_count = pass_count + 1;
        end else begin
            $display("    >> FAIL: DRAW_LINE parameters corrupted!");
            fail_count = fail_count + 1;
        end

        // =====================================================================
        // [TEST 5] DRAW_RECT Command (0x04, Len 9)
        // =====================================================================
        $display("");
        $display("--- [TEST 5] DRAW_RECT (0x04, Len 9: (50,50, 100,80), color=0x15) ---");
        cs_active = 1'b1;
        send_byte(8'h04, 1'b1); // CMD: DRAW_RECT
        send_byte(8'h09, 1'b0); // LEN: 9
        send_byte(8'h00, 1'b0); // X_HI
        send_byte(8'h32, 1'b0); // X_LO: 50
        send_byte(8'h00, 1'b0); // Y_HI
        send_byte(8'h32, 1'b0); // Y_LO: 50
        send_byte(8'h00, 1'b0); // W_HI
        send_byte(8'h64, 1'b0); // W_LO: 100
        send_byte(8'h00, 1'b0); // H_HI
        send_byte(8'h50, 1'b0); // H_LO: 80
        send_byte(8'h15, 1'b0); // COLOR: 0x15
        cs_active = 1'b0;

        @(posedge rect_start);
        if (rect_x === 16'd50 && rect_y === 16'd50 &&
            rect_w === 16'd100 && rect_h === 16'd80 && rect_color === 8'h15) begin
            $display("    >> Deserialized rect: pos=(%0d,%0d), size=%0dx%0d, color=0x%02X",
                     rect_x, rect_y, rect_w, rect_h, rect_color);
            rect_done = 1'b1;
            @(posedge clk);
            rect_done = 1'b0;
            #(CLK_HALF * 6);

            $display("    >> PASS: DRAW_RECT parameters and trigger verified");
            pass_count = pass_count + 1;
        end else begin
            $display("    >> FAIL: DRAW_RECT parameters corrupted!");
            fail_count = fail_count + 1;
        end

        // =====================================================================
        // [TEST 6] SET_PALETTE Command (0x05, Len 4)
        // =====================================================================
        $display("");
        $display("--- [TEST 6] SET_PALETTE (0x05, Len 4: idx=42, RGB=(255,128,64)) ---");
        cs_active = 1'b1;
        send_byte(8'h05, 1'b1); // CMD: SET_PALETTE
        send_byte(8'h04, 1'b0); // LEN: 4
        send_byte(8'd42,  1'b0); // IDX: 42
        send_byte(8'd255, 1'b0); // R: 255
        send_byte(8'd128, 1'b0); // G: 128
        send_byte(8'd64,  1'b0); // B: 64
        cs_active = 1'b0;

        @(posedge palette_wr_en);
        if (palette_addr === 8'd42 && palette_r === 8'd255 &&
            palette_g === 8'd128 && palette_b === 8'd64) begin
            $display("    >> Captured palette write: addr=%0d, R=%0d, G=%0d, B=%0d",
                     palette_addr, palette_r, palette_g, palette_b);
            #(CLK_HALF * 6);

            $display("    >> PASS: SET_PALETTE strobe and RGB components verified");
            pass_count = pass_count + 1;
        end else begin
            $display("    >> FAIL: SET_PALETTE values corrupted! addr=%0d R=%0d G=%0d B=%0d",
                     palette_addr, palette_r, palette_g, palette_b);
            fail_count = fail_count + 1;
        end

        // =====================================================================
        // [TEST 7] SWAP_BUFFER Command (0x06, Len 0) & VSYNC Flip
        // =====================================================================
        $display("");
        $display("--- [TEST 7] SWAP_BUFFER (0x06, Len 0) & VSYNC Flip ---");
        $display("    Initial Buffer State: Front=%0d, Back=%0d, swap_pending=%b",
                 buf_front_idx, buf_back_idx, swap_pending);

        cs_active = 1'b1;
        send_byte(8'h06, 1'b1); // CMD: SWAP_BUFFER
        send_byte(8'h00, 1'b0); // LEN: 0
        cs_active = 1'b0;
        #(CLK_HALF * 6);

        if (swap_pending === 1'b1 && buf_front_idx === 1'b0) begin
            $display("    >> Swap request registered, waiting for VSYNC edge...");
            #(CLK_HALF * 4);
            vsync = 1'b1;
            #(CLK_HALF * 4);
            vsync = 1'b0;
            #(CLK_HALF * 4);

            if (buf_front_idx === 1'b1 && buf_back_idx === 1'b0 && swap_pending === 1'b0) begin
                $display("    >> Buffer flipped on VSYNC: Front=%0d, Back=%0d, swap_pending=%b",
                         buf_front_idx, buf_back_idx, swap_pending);
                $display("    >> PASS: Double-buffering tear-free swap verified");
                pass_count = pass_count + 1;
            end else begin
                $display("    >> FAIL: Buffer failed to flip on VSYNC!");
                fail_count = fail_count + 1;
            end
        end else begin
            $display("    >> FAIL: SWAP_BUFFER failed to set swap_pending!");
            fail_count = fail_count + 1;
        end

        // =====================================================================
        // [TEST 8] LOAD_SPRITE Streaming (0x07, Len 7)
        // =====================================================================
        $display("");
        $display("--- [TEST 8] LOAD_SPRITE (0x07, Len 7: addr=0x040000, 4 bytes) ---");
        cs_active = 1'b1;
        send_byte(8'h07, 1'b1); // CMD: LOAD_SPRITE
        send_byte(8'h07, 1'b0); // LEN: 7 (3 addr + 4 data)
        send_byte(8'h04, 1'b0); // Addr HI: 0x04
        send_byte(8'h00, 1'b0); // Addr MID: 0x00
        send_byte(8'h00, 1'b0); // Addr LO: 0x00

        // Stream 4 data bytes: 0xAA, 0xBB, 0xCC, 0xDD
        send_byte(8'hAA, 1'b0);
        send_byte(8'hBB, 1'b0);
        send_byte(8'hCC, 1'b0);
        send_byte(8'hDD, 1'b0);
        cs_active = 1'b0;
        #(CLK_HALF * 6);

        if (sdram_load_start === 1'b0 && cmd_busy === 1'b0 && cmd_error === 1'b0) begin
            $display("    >> PASS: LOAD_SPRITE 4-byte stream completed successfully");
            pass_count = pass_count + 1;
        end else begin
            $display("    >> FAIL: LOAD_SPRITE stream failed! busy=%b, error=%b", cmd_busy, cmd_error);
            fail_count = fail_count + 1;
        end

        // =====================================================================
        // [TEST 9] Error Handling: Early CS Abort
        // =====================================================================
        $display("");
        $display("--- [TEST 9] Error Handling: Early CS Abort ---");
        cs_active = 1'b1;
        send_byte(8'h02, 1'b1); // CMD: DRAW_SPRITE
        send_byte(8'h07, 1'b0); // LEN: 7
        send_byte(8'h00, 1'b0); // Only send 1 byte of 7
        // Abort early!
        cs_active = 1'b0;
        #(CLK_HALF * 6);

        if (cmd_error === 1'b1 && cmd_busy === 1'b0) begin
            $display("    >> PASS: Early CS abort detected and flagged: cmd_error=%b", cmd_error);
            pass_count = pass_count + 1;
        end else begin
            $display("    >> FAIL: Early abort was not caught! cmd_error=%b", cmd_error);
            fail_count = fail_count + 1;
        end

        // Recovery: send clean NOP
        cs_active = 1'b1;
        send_byte(8'h00, 1'b1); // CMD: NOP
        send_byte(8'h00, 1'b0); // LEN: 0
        cs_active = 1'b0;
        #(CLK_HALF * 6);

        if (cmd_error === 1'b0) begin
            $display("    >> PASS: NOP cleared error flag and returned FSM to healthy idle");
            pass_count = pass_count + 1;
        end else begin
            $display("    >> FAIL: FSM failed to recover from error state");
            fail_count = fail_count + 1;
        end

        // =====================================================================
        // [TEST 10] Error Handling: Invalid Opcode (0xEE)
        // =====================================================================
        $display("");
        $display("--- [TEST 10] Error Handling: Invalid Opcode (0xEE) ---");
        cs_active = 1'b1;
        send_byte(8'hEE, 1'b1); // Invalid CMD: 0xEE
        send_byte(8'h02, 1'b0); // LEN: 2
        cs_active = 1'b0;
        #(CLK_HALF * 6);

        if (cmd_error === 1'b1) begin
            $display("    >> PASS: Invalid opcode 0xEE rejected with cmd_error=1");
            pass_count = pass_count + 1;
        end else begin
            $display("    >> FAIL: Invalid opcode not rejected!");
            fail_count = fail_count + 1;
        end

        // =====================================================================
        // Grand Summary
        // =====================================================================
        $display("");
        $display("========================================================");
        $display("            COMMAND DECODER SIMULATION SUMMARY          ");
        $display("========================================================");
        $display("  Total Tests Passed: %0d", pass_count);
        $display("  Total Tests Failed: %0d", fail_count);
        if (fail_count == 0) begin
            $display("  >> ALL COMMAND DECODER TESTS PASSED (100%% SUCCESS)");
        end else begin
            $display("  >> %0d TEST(S) FAILED", fail_count);
        end
        $display("========================================================");
        $display("[INFO] Simulation complete. Waveform saved to cmd_decoder_sim.vcd\n");

        $finish;
    end

endmodule
