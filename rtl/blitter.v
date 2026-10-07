// =============================================================================
// Module: 2D Hardware Sprite Blitter Engine (blitter.v)
// Project: Custom FPGA-Based GPU — Woxsen University
// Device: Gowin GW2AR-18C (Sipeed Tang Nano 20K)
// Description:
//   Hardware 2D sprite block transfer engine.
//   - Receives DRAW_SPRITE execution trigger from cmd_decoder.v.
//   - Reads indexed-color sprite pixels from Sprite Storage in SDRAM.
//   - Supports sprite size modes: 16x16 (tiles), 16x32 (characters/NPCs),
//     32x32 (bosses/monsters), 64x64 (portraits), 8x8 (font glyphs).
//   - Supports horizontal flip (flip_x) and vertical flip (flip_y).
//   - Performs color-key transparency skipping: pixels with value 0x00
//     are skipped without destination writes, saving memory bus cycles.
//   - Performs signed viewport clipping against 640x480 screen boundaries.
//   - Writes visible, opaque pixels directly into the active Back Buffer
//     in SDRAM using shift-and-add address math: (y * 640) = (y<<9) + (y<<7).
// =============================================================================

`timescale 1ns / 1ps

module blitter (
    input  wire                   clk,
    input  wire                   reset,

    // Command Interface (from cmd_decoder.v)
    input  wire                   start,            // 1-cycle trigger strobe
    input  wire signed [15:0]     sprite_x,         // Screen X coordinate (-32768 to 32767)
    input  wire signed [15:0]     sprite_y,         // Screen Y coordinate (-32768 to 32767)
    input  wire        [15:0]     sprite_id,        // Sprite index in asset bank
    input  wire        [7:0]      sprite_flags,     // [0]=flip_x, [1]=flip_y, [2]=trans_en, [5:3]=size
    input  wire                   buf_back_idx,     // 0 -> base 0x000000, 1 -> base 0x050000
    input  wire        [22:0]     sprite_base_addr, // SDRAM asset storage offset (e.g. 23'h100000)

    output wire                   busy,             // High while blit in progress
    output reg                    done,             // 1-cycle completion strobe

    // SDRAM Memory Controller Interface
    output reg                    mem_rd,           // Read strobe (1 cycle pulse)
    output reg                    mem_wr,           // Write strobe (1 cycle pulse)
    output reg         [22:0]     mem_addr,         // 23-bit byte address
    output reg         [7:0]      mem_wdata,        // 8-bit pixel byte to write
    input  wire        [7:0]      mem_rdata,        // 8-bit pixel byte read
    input  wire                   mem_rvalid,       // High when mem_rdata is valid
    input  wire                   mem_ready         // High when SDRAM can accept command (~busy)
);

    // =========================================================================
    // Size Modes Definition (sprite_flags[5:3])
    // =========================================================================
    localparam [2:0] SIZE_16x16 = 3'b000;  // 16x16  (256 bytes)
    localparam [2:0] SIZE_16x32 = 3'b001;  // 16x32  (512 bytes - standard character/NPC)
    localparam [2:0] SIZE_32x32 = 3'b010;  // 32x32  (1024 bytes)
    localparam [2:0] SIZE_64x64 = 3'b011;  // 64x64  (4096 bytes)
    localparam [2:0] SIZE_8x8   = 3'b100;  // 8x8    (64 bytes - font glyph)

    // =========================================================================
    // Frame Buffer Base Addresses
    // =========================================================================
    localparam [22:0] FB0_BASE = 23'h000000;
    localparam [22:0] FB1_BASE = 23'h050000;

    // =========================================================================
    // FSM State Encoding
    // =========================================================================
    localparam [2:0] ST_IDLE        = 3'd0;
    localparam [2:0] ST_READ_REQ    = 3'd1;
    localparam [2:0] ST_READ_ACCEPT = 3'd2;
    localparam [2:0] ST_READ_WAIT   = 3'd3;
    localparam [2:0] ST_CHECK_PIXEL = 3'd4;
    localparam [2:0] ST_WRITE_REQ   = 3'd5;
    localparam [2:0] ST_WRITE_WAIT  = 3'd6;

    reg [2:0] state;

    assign busy = (state != ST_IDLE);

    // Latched command parameters
    reg signed [15:0] reg_x;
    reg signed [15:0] reg_y;
    reg        [15:0] reg_id;
    reg        [7:0]  reg_flags;
    reg               reg_back_idx;

    // Decoded sprite dimensions
    reg [6:0]  sprite_w;       // 8, 16, 32, 64
    reg [6:0]  sprite_h;       // 8, 16, 32, 64
    reg [2:0]  shift_w;        // 3 (8), 4 (16), 5 (32), 6 (64)
    reg [22:0] src_base;       // Starting byte address of sprite in SDRAM
    reg [22:0] dst_base;       // Starting byte address of active back buffer

    // Pixel counters within sprite
    reg [6:0] u;               // Current X pixel inside sprite (0..W-1)
    reg [6:0] v;               // Current Y pixel inside sprite (0..H-1)

    // Pixel buffer and coordinates
    reg [7:0] read_pixel;
    wire      is_visible;
    wire      is_transparent;

    // Effective coordinates taking horizontal and vertical flip into account
    wire [6:0] eff_u = reg_flags[0] ? (sprite_w - 7'd1 - u) : u; // flip_x
    wire [6:0] eff_v = reg_flags[1] ? (sprite_h - 7'd1 - v) : v; // flip_y

    // Destination coordinates on screen with explicit signed addition
    wire signed [17:0] s_reg_x   = {{2{reg_x[15]}}, reg_x};
    wire signed [17:0] s_eff_u   = {11'd0, eff_u};
    wire signed [17:0] cur_dst_x = s_reg_x + s_eff_u;

    wire signed [17:0] s_reg_y   = {{2{reg_y[15]}}, reg_y};
    wire signed [17:0] s_eff_v   = {11'd0, eff_v};
    wire signed [17:0] cur_dst_y = s_reg_y + s_eff_v;

    // Screen clipping: visible only if within 640x480 resolution
    assign is_visible = (cur_dst_x >= 18'sd0) && (cur_dst_x < 18'sd640) &&
                        (cur_dst_y >= 18'sd0) && (cur_dst_y < 18'sd480);

    // Color key transparency: 0x00 is transparent when trans_en (flag bit 2) is active
    assign is_transparent = reg_flags[2] && (read_pixel == 8'h00);

    // =========================================================================
    // Blitter FSM Execution Engine
    // =========================================================================
    always @(posedge clk) begin
        if (reset) begin
            state        <= ST_IDLE;
            done         <= 1'b0;
            mem_rd       <= 1'b0;
            mem_wr       <= 1'b0;
            mem_addr     <= 23'd0;
            mem_wdata    <= 8'd0;
            read_pixel   <= 8'd0;
            u            <= 7'd0;
            v            <= 7'd0;
            sprite_w     <= 7'd16;
            sprite_h     <= 7'd16;
            shift_w      <= 3'd4;
            src_base     <= 23'd0;
            dst_base     <= 23'd0;
            reg_x        <= 16'sd0;
            reg_y        <= 16'sd0;
            reg_id       <= 16'd0;
            reg_flags    <= 8'd0;
            reg_back_idx <= 1'b0;
        end else begin
            // Default strobe resets
            done   <= 1'b0;
            mem_rd <= 1'b0;
            mem_wr <= 1'b0;

            case (state)
                // -------------------------------------------------------------
                // ST_IDLE: Wait for start command strobe
                // -------------------------------------------------------------
                ST_IDLE: begin
                    if (start) begin
                        reg_x        <= sprite_x;
                        reg_y        <= sprite_y;
                        reg_id       <= sprite_id;
                        reg_flags    <= sprite_flags;
                        reg_back_idx <= buf_back_idx;

                        // Target active back buffer
                        dst_base <= buf_back_idx ? FB1_BASE : FB0_BASE;

                        // Decode sprite size parameters
                        case (sprite_flags[5:3])
                            SIZE_8x8: begin
                                sprite_w <= 7'd8;
                                sprite_h <= 7'd8;
                                shift_w  <= 3'd3;
                                src_base <= sprite_base_addr + ({7'd0, sprite_id} << 6); // id * 64
                            end
                            SIZE_16x32: begin
                                sprite_w <= 7'd16;
                                sprite_h <= 7'd32;
                                shift_w  <= 3'd4;
                                src_base <= sprite_base_addr + ({7'd0, sprite_id} << 9); // id * 512
                            end
                            SIZE_32x32: begin
                                sprite_w <= 7'd32;
                                sprite_h <= 7'd32;
                                shift_w  <= 3'd5;
                                src_base <= sprite_base_addr + ({7'd0, sprite_id} << 10); // id * 1024
                            end
                            SIZE_64x64: begin
                                sprite_w <= 7'd64;
                                sprite_h <= 7'd64;
                                shift_w  <= 3'd6;
                                src_base <= sprite_base_addr + ({7'd0, sprite_id} << 12); // id * 4096
                            end
                            default: begin // SIZE_16x16
                                sprite_w <= 7'd16;
                                sprite_h <= 7'd16;
                                shift_w  <= 3'd4;
                                src_base <= sprite_base_addr + ({7'd0, sprite_id} << 8); // id * 256
                            end
                        endcase

                        u     <= 7'd0;
                        v     <= 7'd0;
                        state <= ST_READ_REQ;
                    end
                end

                // -------------------------------------------------------------
                // ST_READ_REQ / ST_READ_ACCEPT: hold valid until the arbiter
                // accepts this particular port.  mem_ready is an acceptance
                // response; it is not a global "SDRAM is probably idle" flag.
                // -------------------------------------------------------------
                ST_READ_REQ: begin
                    mem_addr <= src_base + {16'd0, v << shift_w} + {16'd0, u};
                    mem_rd   <= 1'b1;
                    state    <= ST_READ_ACCEPT;
                end

                ST_READ_ACCEPT: begin
                    mem_rd <= 1'b1;
                    if (mem_ready) begin
                        mem_rd <= 1'b0;
                        state  <= ST_READ_WAIT;
                    end
                end

                // -------------------------------------------------------------
                // ST_READ_WAIT: Wait for SDRAM to return source pixel
                // -------------------------------------------------------------
                ST_READ_WAIT: begin
                    if (mem_rvalid) begin
                        read_pixel <= mem_rdata;
                        state      <= ST_CHECK_PIXEL;
                    end
                end

                // -------------------------------------------------------------
                // ST_CHECK_PIXEL: Check clipping and color-key transparency
                // -------------------------------------------------------------
                ST_CHECK_PIXEL: begin
                    if (!is_visible || is_transparent) begin
                        // Skip write cycle! Advance immediately to next pixel
                        if (u == sprite_w - 7'd1) begin
                            u <= 7'd0;
                            if (v == sprite_h - 7'd1) begin
                                done  <= 1'b1;
                                state <= ST_IDLE;
                            end else begin
                                v     <= v + 7'd1;
                                state <= ST_READ_REQ;
                            end
                        end else begin
                            u     <= u + 7'd1;
                            state <= ST_READ_REQ;
                        end
                    end else begin
                        // Pixel is visible and opaque: proceed to write
                        state <= ST_WRITE_REQ;
                    end
                end

                // -------------------------------------------------------------
                // ST_WRITE_REQ / ST_WRITE_WAIT: as above, keep the request
                // asserted until it is accepted.  The arbiter serializes the
                // following request until this write has completed.
                // Address: dst_base + (y * 640) + x = dst_base + (y<<9) + (y<<7) + x
                // -------------------------------------------------------------
                ST_WRITE_REQ: begin
                    mem_addr  <= dst_base + 
                                 {2'd0, cur_dst_y[11:0], 9'd0} + 
                                 {4'd0, cur_dst_y[11:0], 7'd0} + 
                                 {7'd0, cur_dst_x[15:0]};
                    mem_wdata <= read_pixel;
                    mem_wr    <= 1'b1;
                    state     <= ST_WRITE_WAIT;
                end

                // -------------------------------------------------------------
                // ST_WRITE_WAIT: Wait for SDRAM write command acceptance
                // -------------------------------------------------------------
                ST_WRITE_WAIT: begin
                    mem_wr <= 1'b1;
                    // Advance only after this port's write was accepted.
                    if (mem_ready) begin
                        mem_wr <= 1'b0;
                        if (u == sprite_w - 7'd1) begin
                            u <= 7'd0;
                            if (v == sprite_h - 7'd1) begin
                                done  <= 1'b1;
                                state <= ST_IDLE;
                            end else begin
                                v     <= v + 7'd1;
                                state <= ST_READ_REQ;
                            end
                        end else begin
                            u     <= u + 7'd1;
                            state <= ST_READ_REQ;
                        end
                    end
                end

                default: state <= ST_IDLE;
            endcase
        end
    end

endmodule
