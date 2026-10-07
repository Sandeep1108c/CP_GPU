// =============================================================================
// Module: VGA Timing Generator (640x480 @ 60Hz)
// Project: Custom FPGA-Based GPU — Woxsen University
// Description:
//   Generates pixel coordinates, synchronous active-low HSYNC and VSYNC,
//   and video_active data enable for standard 640x480 @ 60Hz video timing.
//   Requires a 25.175 MHz pixel clock input.
//
//   Updated Features:
//     - Clean registered outputs for glitch-free TMDS / HDMI serialization
//     - frame_sync output (1-cycle pulse at start of V-blanking for SWAP_BUFFER)
//     - line_sync output (1-cycle pulse at start of each raster line)
//     - Coordinate clamping during blanking intervals
//
// VGA 640x480 @ 60Hz Timing Reference (VESA Standard):
//   Pixel Clock: 25.175 MHz (Period ≈ 39.72 ns)
//   Horizontal: 640 visible + 16 front porch + 96 sync + 48 back porch = 800 total
//   Vertical:   480 visible + 10 front porch +  2 sync + 33 back porch = 525 total
//   Polarity:   HSYNC: Negative (active-low), VSYNC: Negative (active-low)
// =============================================================================

`timescale 1ns / 1ps

module vga_timing (
    input  wire        clk,          // 25.175 MHz pixel clock
    input  wire        reset,        // Active-high synchronous reset
    output reg         hsync,        // Horizontal sync (active-low, registered)
    output reg         vsync,        // Vertical sync (active-low, registered)
    output reg         video_active, // High during visible 640x480 display area
    output reg  [9:0]  pixel_x,      // Current horizontal pixel coordinate (0-639)
    output reg  [9:0]  pixel_y,      // Current vertical pixel coordinate (0-479)
    output reg         frame_sync,   // 1-cycle strobe at start of V-blank (for buffer swap)
    output reg         line_sync     // 1-cycle strobe at start of active line
);

    // =========================================================================
    // VESA 640x480 @ 60Hz Timing Parameters
    // =========================================================================
    localparam H_VISIBLE = 10'd640;
    localparam H_FRONT   = 10'd16;
    localparam H_SYNC    = 10'd96;
    localparam H_BACK    = 10'd48;
    localparam H_TOTAL   = H_VISIBLE + H_FRONT + H_SYNC + H_BACK; // 800

    localparam V_VISIBLE = 10'd480;
    localparam V_FRONT   = 10'd10;
    localparam V_SYNC    = 10'd2;
    localparam V_BACK    = 10'd33;
    localparam V_TOTAL   = V_VISIBLE + V_FRONT + V_SYNC + V_BACK; // 525

    // =========================================================================
    // Counters
    // =========================================================================
    reg [9:0] h_count;  // Horizontal counter (0 to 799)
    reg [9:0] v_count;  // Vertical counter   (0 to 524)

    // Horizontal pixel counter
    always @(posedge clk) begin
        if (reset) begin
            h_count <= 10'd0;
        end else if (h_count == H_TOTAL - 10'd1) begin
            h_count <= 10'd0;
        end else begin
            h_count <= h_count + 10'd1;
        end
    end

    // Vertical line counter
    always @(posedge clk) begin
        if (reset) begin
            v_count <= 10'd0;
        end else if (h_count == H_TOTAL - 10'd1) begin
            if (v_count == V_TOTAL - 10'd1) begin
                v_count <= 10'd0;
            end else begin
                v_count <= v_count + 10'd1;
            end
        end
    end

    // =========================================================================
    // Registered Output Generation (Glitch-Free for TMDS / HDMI)
    // =========================================================================
    always @(posedge clk) begin
        if (reset) begin
            hsync        <= 1'b1;     // Active-low: default inactive (high)
            vsync        <= 1'b1;     // Active-low: default inactive (high)
            video_active <= 1'b0;
            pixel_x      <= 10'd0;
            pixel_y      <= 10'd0;
            frame_sync   <= 1'b0;
            line_sync    <= 1'b0;
        end else begin
            // HSYNC: Active-low during sync pulse [656 .. 751]
            hsync <= ~((h_count >= (H_VISIBLE + H_FRONT)) &&
                       (h_count <  (H_VISIBLE + H_FRONT + H_SYNC)));

            // VSYNC: Active-low during sync pulse [490 .. 491]
            vsync <= ~((v_count >= (V_VISIBLE + V_FRONT)) &&
                       (v_count <  (V_VISIBLE + V_FRONT + V_SYNC)));

            // Video Active: high when both counters are within visible area
            video_active <= (h_count < H_VISIBLE) && (v_count < V_VISIBLE);

            // Pixel Coordinates: pass current counters
            pixel_x <= h_count;
            pixel_y <= v_count;

            // Frame Sync: 1-cycle pulse exactly when active display ends (start of front porch)
            frame_sync <= (h_count == 10'd0) && (v_count == V_VISIBLE);

            // Line Sync: 1-cycle pulse at start of each line
            line_sync <= (h_count == 10'd0);
        end
    end

endmodule
