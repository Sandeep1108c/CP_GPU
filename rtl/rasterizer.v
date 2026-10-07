// =============================================================================
// Module: 2D Hardware Primitive Rasterizer Engine (rasterizer.v)
// Project: Custom FPGA-Based GPU — Woxsen University
// Device: Gowin GW2AR-18C (Sipeed Tang Nano 20K)
// Description:
//   Hardware 2D primitive rasterization engine.
//   - Accelerated Bresenham line drawing (OP_DRAW_LINE: 0x03)
//   - Fast solid rectangle fill (OP_DRAW_RECT: 0x04)
//   - Full-screen fast framebuffer clear (OP_CLEAR: 0x01)
//   - Supports all 8 octants with integer Bresenham arithmetic (zero division)
//   - Multiplierless destination address math: (y * 640) = (y<<9) + (y<<7)
//   - Signed 18-bit viewport clipping against 640x480 active display area
//   - Direct SDRAM write interface targeting active back buffer
// =============================================================================

`timescale 1ns / 1ps

module rasterizer #(
    parameter [18:0] CLEAR_PIXELS = 19'd307200 // 640 * 480
) (
    input  wire                   clk,
    input  wire                   reset,

    // Command Interface (from cmd_decoder.v)
    // -------------------------------------------------------------------------
    // 1. Line Drawing
    input  wire                   line_start,
    input  wire signed [15:0]     line_x0,
    input  wire signed [15:0]     line_y0,
    input  wire signed [15:0]     line_x1,
    input  wire signed [15:0]     line_y1,
    input  wire        [7:0]      line_color,
    output reg                    line_done,
    output wire                   line_busy,

    // 2. Rectangle Fill
    input  wire                   rect_start,
    input  wire signed [15:0]     rect_x,
    input  wire signed [15:0]     rect_y,
    input  wire        [15:0]     rect_w,
    input  wire        [15:0]     rect_h,
    input  wire        [7:0]      rect_color,
    output reg                    rect_done,
    output wire                   rect_busy,

    // 3. Screen Clear
    input  wire                   clear_start,
    input  wire        [7:0]      clear_color,
    output reg                    clear_done,
    output wire                   clear_busy,

    // Framebuffer target selection (from cmd_decoder.v)
    input  wire                   buf_back_idx, // 0 -> 23'h000000, 1 -> 23'h050000

    // SDRAM Memory Controller Interface
    output reg                    mem_wr,       // valid; held until mem_ready accepts it
    output reg                    mem_wr32,     // 32-bit valid; held until mem_ready accepts it
    output reg         [22:0]     mem_addr,     // 23-bit byte address
    output reg         [7:0]      mem_wdata,    // 8-bit palette index
    input  wire                   mem_ready     // this port's request accepted by arbiter
);

    // =========================================================================
    // Frame Buffer Base Addresses
    // =========================================================================
    localparam [22:0] FB0_BASE = 23'h000000;
    localparam [22:0] FB1_BASE = 23'h050000;
    wire [22:0] dst_base = buf_back_idx ? FB1_BASE : FB0_BASE;

    // =========================================================================
    // FSM State Encoding
    // =========================================================================
    localparam [2:0] ST_IDLE            = 3'd0;
    localparam [2:0] ST_LINE_EVAL       = 3'd1;
    localparam [2:0] ST_LINE_WRITE_WAIT = 3'd2;
    localparam [2:0] ST_RECT_REQ        = 3'd3;
    localparam [2:0] ST_RECT_WAIT       = 3'd4;
    localparam [2:0] ST_CLEAR_REQ       = 3'd5;
    localparam [2:0] ST_CLEAR_WAIT      = 3'd6;

    reg [2:0] state;

    assign line_busy  = (state == ST_LINE_EVAL) || (state == ST_LINE_WRITE_WAIT);
    assign rect_busy  = (state == ST_RECT_REQ)  || (state == ST_RECT_WAIT);
    assign clear_busy = (state == ST_CLEAR_REQ) || (state == ST_CLEAR_WAIT);

    // Active color latch
    reg [7:0] active_color;

    // =========================================================================
    // Line Drawing Registers & Arithmetic (Bresenham)
    // =========================================================================
    // Explicitly sign-extended input coordinates to avoid unsigned concatenation traps
    wire signed [17:0] s_lx0 = {{2{line_x0[15]}}, line_x0};
    wire signed [17:0] s_ly0 = {{2{line_y0[15]}}, line_y0};
    wire signed [17:0] s_lx1 = {{2{line_x1[15]}}, line_x1};
    wire signed [17:0] s_ly1 = {{2{line_y1[15]}}, line_y1};

    wire signed [17:0] init_dx = (s_lx0 <= s_lx1) ? (s_lx1 - s_lx0) : (s_lx0 - s_lx1);
    wire signed [17:0] init_dy = (s_ly0 <= s_ly1) ? (s_ly1 - s_ly0) : (s_ly0 - s_ly1);
    wire               init_sx = (s_lx0 <= s_lx1);
    wire               init_sy = (s_ly0 <= s_ly1);

    reg signed [17:0] curr_x;
    reg signed [17:0] curr_y;
    reg signed [17:0] end_x;
    reg signed [17:0] end_y;

    reg signed [17:0] dx;
    reg signed [17:0] dy;
    reg               sx_dir; // 1: +1, 0: -1
    reg               sy_dir; // 1: +1, 0: -1
    reg signed [18:0] err;

    // Arithmetic shift and negation preserving signed representation
    wire signed [19:0] e2     = err <<< 1;
    wire signed [19:0] neg_dy = -dy;
    wire signed [19:0] pos_dx = dx;

    // Viewport visibility check for current line pixel
    wire is_line_pix_visible = (curr_x >= 18'sd0) && (curr_x < 18'sd640) &&
                               (curr_y >= 18'sd0) && (curr_y < 18'sd480);

    // Multiplierless screen coordinate mapping for line pixel:
    // (y * 640) + x = (y << 9) + (y << 7) + x
    wire [22:0] line_dst_addr = dst_base +
                                {4'd0, curr_y[9:0], 9'd0} +
                                {6'd0, curr_y[9:0], 7'd0} +
                                {13'd0, curr_x[9:0]};

    // Combinational calculation of next Bresenham state
    reg signed [17:0] next_x;
    reg signed [17:0] next_y;
    reg signed [18:0] next_err;
    reg signed [18:0] temp_err;

    always @(*) begin
        next_x   = curr_x;
        next_y   = curr_y;
        temp_err = err;

        if (e2 > neg_dy) begin
            temp_err = temp_err - dy;
            next_x   = curr_x + (sx_dir ? 18'sd1 : -18'sd1);
        end

        if (e2 < pos_dx) begin
            temp_err = temp_err + dx;
            next_y   = curr_y + (sy_dir ? 18'sd1 : -18'sd1);
        end

        next_err = temp_err;
    end

    // Line Trivial Rejection Check (both endpoints on same off-screen side)
    wire line_trivial_reject =
        (line_x0 < 16'sd0 && line_x1 < 16'sd0) ||
        (line_x0 >= 16'sd640 && line_x1 >= 16'sd640) ||
        (line_y0 < 16'sd0 && line_y1 < 16'sd0) ||
        (line_y0 >= 16'sd480 && line_y1 >= 16'sd480);

    // =========================================================================
    // Rectangle Fill Registers & Arithmetic
    // =========================================================================
    reg [9:0] rect_rx;
    reg [8:0] rect_ry;
    reg [9:0] clip_x0;
    reg [9:0] clip_x1;
    reg [8:0] clip_y0;
    reg [8:0] clip_y1;

    // Multiplierless screen coordinate mapping for rect pixel
    wire [22:0] rect_dst_addr = dst_base +
                                {4'd0, rect_ry, 9'd0} +
                                {6'd0, rect_ry, 7'd0} +
                                {13'd0, rect_rx};

    // Rectangle boundary clipping calculations at trigger time
    wire signed [17:0] s_rx  = {{2{rect_x[15]}}, rect_x};
    wire signed [17:0] s_ry  = {{2{rect_y[15]}}, rect_y};
    wire signed [17:0] s_rw  = {2'b00, rect_w};
    wire signed [17:0] s_rh  = {2'b00, rect_h};
    wire signed [17:0] s_rx2 = s_rx + s_rw;
    wire signed [17:0] s_ry2 = s_ry + s_rh;

    // Rectangle trivial reject check
    wire rect_trivial_reject =
        (rect_w == 16'd0) || (rect_h == 16'd0) ||
        (s_rx2 <= 18'sd0) || (s_rx >= 18'sd640) ||
        (s_ry2 <= 18'sd0) || (s_ry >= 18'sd480);

    // =========================================================================
    // Screen Clear Counter
    // =========================================================================
    reg [18:0] clear_addr;
    wire [22:0] clear_dst_addr = dst_base + {4'd0, clear_addr};

    // =========================================================================
    // Main Rasterizer FSM
    // =========================================================================
    always @(posedge clk) begin
        if (reset) begin
            state        <= ST_IDLE;
            line_done    <= 1'b0;
            rect_done    <= 1'b0;
            clear_done   <= 1'b0;
            mem_wr       <= 1'b0;
            mem_wr32     <= 1'b0;
            mem_addr     <= 23'd0;
            mem_wdata    <= 8'd0;
            active_color <= 8'd0;
            curr_x       <= 18'sd0;
            curr_y       <= 18'sd0;
            end_x        <= 18'sd0;
            end_y        <= 18'sd0;
            dx           <= 18'sd0;
            dy           <= 18'sd0;
            sx_dir       <= 1'b0;
            sy_dir       <= 1'b0;
            err          <= 19'sd0;
            rect_rx      <= 10'd0;
            rect_ry      <= 9'd0;
            clip_x0      <= 10'd0;
            clip_x1      <= 10'd0;
            clip_y0      <= 9'd0;
            clip_y1      <= 9'd0;
            clear_addr   <= 19'd0;
        end else begin
            // Default 1-cycle strobe deassertions
            line_done  <= 1'b0;
            rect_done  <= 1'b0;
            clear_done <= 1'b0;

            case (state)
                // -------------------------------------------------------------
                // ST_IDLE: Await Draw Trigger
                // -------------------------------------------------------------
                ST_IDLE: begin
                    mem_wr <= 1'b0;

                    if (line_start) begin
                        active_color <= line_color;

                        if (line_trivial_reject) begin
                            // 1-cycle early exit for off-screen lines
                            line_done <= 1'b1;
                            state     <= ST_IDLE;
                        end else begin
                            curr_x <= s_lx0;
                            curr_y <= s_ly0;
                            end_x  <= s_lx1;
                            end_y  <= s_ly1;
                            dx     <= init_dx;
                            dy     <= init_dy;
                            sx_dir <= init_sx;
                            sy_dir <= init_sy;
                            err    <= init_dx - init_dy;
                            state  <= ST_LINE_EVAL;
                        end
                    end else if (rect_start) begin
                        active_color <= rect_color;

                        if (rect_trivial_reject) begin
                            // 1-cycle early exit for empty or off-screen rects
                            rect_done <= 1'b1;
                            state     <= ST_IDLE;
                        end else begin
                            // Compute clipped boundaries
                            clip_x0 <= (s_rx < 18'sd0) ? 10'd0 : s_rx[9:0];
                            clip_x1 <= (s_rx2 > 18'sd640) ? 10'd640 : s_rx2[9:0];
                            clip_y0 <= (s_ry < 18'sd0) ? 9'd0 : s_ry[8:0];
                            clip_y1 <= (s_ry2 > 18'sd480) ? 9'd480 : s_ry2[8:0];

                            rect_rx <= (s_rx < 18'sd0) ? 10'd0 : s_rx[9:0];
                            rect_ry <= (s_ry < 18'sd0) ? 9'd0 : s_ry[8:0];

                            state   <= ST_RECT_REQ;
                        end
                    end else if (clear_start) begin
                        active_color <= clear_color;
                        clear_addr   <= 19'd0;
                        state        <= ST_CLEAR_REQ;
                    end
                end

                // -------------------------------------------------------------
                // ST_LINE_EVAL: Evaluate Visibility of Current Line Pixel
                // -------------------------------------------------------------
                ST_LINE_EVAL: begin
                    if (is_line_pix_visible) begin
                        // Visible on-screen pixel: issue SDRAM write
                        mem_wr    <= 1'b1;
                        mem_addr  <= line_dst_addr;
                        mem_wdata <= active_color;
                        state     <= ST_LINE_WRITE_WAIT;
                    end else begin
                        // Off-screen clipped pixel: skip SDRAM cycle and advance
                        mem_wr <= 1'b0;
                        if (curr_x == end_x && curr_y == end_y) begin
                            // Line complete
                            line_done <= 1'b1;
                            state     <= ST_IDLE;
                        end else begin
                            // Step Bresenham
                            curr_x <= next_x;
                            curr_y <= next_y;
                            err    <= next_err;
                            state  <= ST_LINE_EVAL;
                        end
                    end
                end

                // -------------------------------------------------------------
                // ST_LINE_WRITE_WAIT: Await Memory Acceptance
                // -------------------------------------------------------------
                ST_LINE_WRITE_WAIT: begin
                    // Keep valid and payload stable until this port wins
                    // arbitration.  A one-cycle pulse can otherwise be lost
                    // behind video scanout.
                    mem_wr <= 1'b1;

                    if (mem_ready) begin
                        mem_wr <= 1'b0;
                        if (curr_x == end_x && curr_y == end_y) begin
                            // Final pixel written
                            line_done <= 1'b1;
                            state     <= ST_IDLE;
                        end else begin
                            // Step Bresenham to next pixel
                            curr_x <= next_x;
                            curr_y <= next_y;
                            err    <= next_err;
                            state  <= ST_LINE_EVAL;
                        end
                    end
                end

                // -------------------------------------------------------------
                // ST_RECT_REQ: Issue Memory Write for Current Rect Pixel
                // -------------------------------------------------------------
                ST_RECT_REQ: begin
                    mem_wr    <= 1'b1;
                    mem_addr  <= rect_dst_addr;
                    mem_wdata <= active_color;
                    state     <= ST_RECT_WAIT;
                end

                // -------------------------------------------------------------
                // ST_RECT_WAIT: Await Memory Acceptance and Advance Rect Pixel
                // -------------------------------------------------------------
                ST_RECT_WAIT: begin
                    mem_wr <= 1'b1;

                    if (mem_ready) begin
                        mem_wr <= 1'b0;
                        if (rect_rx + 10'd1 < clip_x1) begin
                            rect_rx <= rect_rx + 10'd1;
                            state   <= ST_RECT_REQ;
                        end else begin
                            rect_rx <= clip_x0;
                            if (rect_ry + 9'd1 < clip_y1) begin
                                rect_ry <= rect_ry + 9'd1;
                                state   <= ST_RECT_REQ;
                            end else begin
                                // All rectangle pixels rendered
                                rect_done <= 1'b1;
                                state     <= ST_IDLE;
                            end
                        end
                    end
                end

                // -------------------------------------------------------------
                // ST_CLEAR_REQ: Issue Memory Write for Full Framebuffer Clear
                // -------------------------------------------------------------
                ST_CLEAR_REQ: begin
                    mem_wr    <= 1'b1;
                    mem_wr32  <= 1'b1;
                    mem_addr  <= clear_dst_addr;
                    mem_wdata <= active_color;
                    state     <= ST_CLEAR_WAIT;
                end

                // -------------------------------------------------------------
                // ST_CLEAR_WAIT: Await Memory Acceptance and Advance Clear Address
                // -------------------------------------------------------------
                ST_CLEAR_WAIT: begin
                    mem_wr   <= 1'b1;
                    mem_wr32 <= 1'b1;

                    if (mem_ready) begin
                        mem_wr   <= 1'b0;
                        mem_wr32 <= 1'b0;
                        if (clear_addr >= CLEAR_PIXELS - 19'd4) begin
                            // Clear finished
                            clear_done <= 1'b1;
                            state      <= ST_IDLE;
                        end else begin
                            clear_addr <= clear_addr + 19'd4;
                            state      <= ST_CLEAR_REQ;
                        end
                    end
                end

                default: state <= ST_IDLE;
            endcase
        end
    end

endmodule
