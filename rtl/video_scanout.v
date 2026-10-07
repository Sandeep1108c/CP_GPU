// =============================================================================
// Module: Video Scanout Engine with Ping-Pong Dual Line Buffer (video_scanout.v)
// Project: Custom FPGA-Based GPU — Woxsen University
// Device: Gowin GW2AR-18C (Sipeed Tang Nano 20K)
// Description:
//   Fetches 640x480 @ 60Hz indexed 8-bit framebuffer scanlines from SDRAM
//   into an on-chip dual-port BRAM line buffer.
//
//   Architecture:
//     - True Dual-Port Block RAM line buffer: 320 words x 32 bits (1280 bytes)
//       holding two alternating 640-pixel scanlines (Buffer 0 and Buffer 1).
//     - Display Port: Reads 1 pixel per clock cycle (25.2 MHz) from active buffer.
//     - Prefetch Port: Prefetches next scanline from front-buffer SDRAM in
//       160 word-bursts (32-bit words = 4 pixels each = 640 pixels).
//     - Interleaves cleanly with SDRAM arbiter, leaving SDRAM available during
//       horizontal blanking and full vertical blanking for blitter/rasterizer.
// =============================================================================

`timescale 1ns / 1ps

module video_scanout (
    input  wire        clk,            // 25.2 MHz pixel clock
    input  wire        reset,          // Active-high synchronous reset

    // VGA Timing Generator (from vga_timing.v)
    input  wire [9:0]  pixel_x,        // Current beam X (0..639 active)
    input  wire [9:0]  pixel_y,        // Current beam Y (0..479 active)
    input  wire        video_active,   // Visible display enable
    input  wire        line_sync,      // 1-cycle strobe at start of each line
    input  wire        frame_sync,     // 1-cycle strobe at start of VBLANK

    // Double-Buffer Selection (from cmd_decoder.v)
    input  wire        buf_front_idx,  // 0 -> FB0 (0x000000), 1 -> FB1 (0x050000)

    // SDRAM Arbiter Port 0 Interface (Priority 1)
    output reg         vga_rd,
    output reg  [22:0] vga_addr,
    input  wire [31:0] vga_rdata32,
    input  wire        vga_rvalid,
    input  wire        vga_ready,

    // Pixel Output to Palette LUT
    output wire [7:0]  pixel_idx
);

    // Front-buffer base address in SDRAM
    localparam [22:0] FB0_BASE = 23'h000000;
    localparam [22:0] FB1_BASE = 23'h050000;
    wire [22:0] front_base = buf_front_idx ? FB1_BASE : FB0_BASE;

    // Line RAM: 512 entries x 32-bit words (Total 2048 bytes in 1 Gowin BSRAM)
    // Entries 0..159   : Buffer 0 (Line Y[0] == 0)
    // Entries 256..415 : Buffer 1 (Line Y[0] == 1)
    reg [31:0] line_ram [0:511];

    // =========================================================================
    // 1. SDRAM Prefetch State Machine
    // =========================================================================
    localparam [2:0] S_IDLE   = 3'd0;
    localparam [2:0] S_REQ    = 3'd1;
    localparam [2:0] S_ACCEPT = 3'd2;
    localparam [2:0] S_WAIT   = 3'd3;
    localparam [2:0] S_DONE   = 3'd4;

    reg [2:0]  pf_state;
    reg [7:0]  word_cnt;     // 0..159 (160 words = 640 pixels)
    reg [9:0]  fetch_line;   // Which line we are prefetching (0..479)
    reg        target_buf;   // Which line buffer to write (0 or 1)

    // Multiplierless address calculation: fetch_line * 640 = (fetch_line << 9) + (fetch_line << 7)
    wire [22:0] line_offset = {4'd0, fetch_line, 9'd0} + {6'd0, fetch_line, 7'd0};
    wire [22:0] fetch_base  = front_base + line_offset;

    always @(posedge clk) begin
        if (reset) begin
            pf_state   <= S_IDLE;
            vga_rd     <= 1'b0;
            vga_addr   <= 23'd0;
            word_cnt   <= 8'd0;
            fetch_line <= 10'd0;
            target_buf <= 1'b0;
        end else begin
            // Default: clear 1-cycle read strobe
            vga_rd <= 1'b0;

            // Do not destroy an in-flight request on the next line boundary.
            // A missed completion previously restarted the fetch and stranded
            // the associated arbiter transaction.
            if (line_sync && (pf_state == S_IDLE || pf_state == S_DONE)) begin
                vga_rd <= 1'b0;
                if (pixel_y == 10'd524) begin
                    fetch_line <= 10'd0;
                    target_buf <= 1'b0;
                    word_cnt   <= 8'd0;
                    pf_state   <= S_REQ;
                end else if (pixel_y < 10'd479) begin
                    fetch_line <= pixel_y + 10'd1;
                    target_buf <= ~pixel_y[0];
                    word_cnt   <= 8'd0;
                    pf_state   <= S_REQ;
                end else begin
                    pf_state   <= S_IDLE;
                end
            end else begin
                case (pf_state)
                    S_REQ: begin
                        vga_rd   <= 1'b1;
                        vga_addr <= fetch_base + {13'd0, word_cnt, 2'b00};
                        pf_state <= S_ACCEPT;
                    end

                    S_ACCEPT: begin
                        vga_rd <= 1'b1;
                        if (vga_ready) begin
                            vga_rd   <= 1'b0;
                            pf_state <= S_WAIT;
                        end
                    end

                    S_WAIT: begin
                        if (vga_rvalid) begin
                            line_ram[{target_buf, word_cnt}] <= vga_rdata32;
                            if (word_cnt == 8'd159) begin
                                pf_state <= S_DONE;
                            end else if (word_cnt[1:0] == 2'b11) begin
                                word_cnt <= word_cnt + 8'd1;
                                pf_state <= S_REQ;
                            end else begin
                                word_cnt <= word_cnt + 8'd1;
                            end
                        end
                    end

                    S_DONE: begin
                        vga_rd <= 1'b0;
                    end

                    default: pf_state <= S_IDLE;
                endcase
            end
        end
    end

    // =========================================================================
    // 2. Video Scanout Display Port (Synchronous BRAM Read)
    // =========================================================================
    reg [31:0] read_word32;
    reg [1:0]  pix_byte_sel;
    reg        vid_act_d;

    always @(posedge clk) begin
        if (reset) begin
            read_word32  <= 32'd0;
            pix_byte_sel <= 2'd0;
            vid_act_d    <= 1'b0;
        end else begin
            read_word32  <= line_ram[{pixel_y[0], pixel_x[9:2]}];
            pix_byte_sel <= pixel_x[1:0];
            vid_act_d    <= video_active;
        end
    end

    // Byte mux based on registered pixel_x[1:0]
    wire [7:0] raw_pixel = (pix_byte_sel == 2'd0) ? read_word32[7:0]   :
                           (pix_byte_sel == 2'd1) ? read_word32[15:8]  :
                           (pix_byte_sel == 2'd2) ? read_word32[23:16] :
                                                    read_word32[31:24];

    // Blank out outside visible display area
    assign pixel_idx = vid_act_d ? raw_pixel : 8'h00;

endmodule
