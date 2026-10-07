// =============================================================================
// Module: Palette LUT (Color Lookup Table — 256 × 24-bit RGB)
// Project: Custom FPGA-Based GPU — Woxsen University
// Description:
//   Color Lookup Table (CLUT) implemented in Block RAM (BRAM).
//   Maps 8-bit indexed color pixel values (0–255) from the framebuffer/SDRAM
//   into full 24-bit TrueColor RGB (8-bit Red, 8-bit Green, 8-bit Blue).
//
//   Features:
//     - 256 entries × 24-bit RGB = 768 bytes (infers 1 Gowin BSRAM block)
//     - Read Port: Single-cycle synchronous registered read (1 pixel-clock latency)
//     - Write Port: Allows dynamic palette modification via SET_PALETTE (0x05)
//     - Pre-initialized with full standard 256-color palette:
//         • Indices 0–15:   Classic 16 ANSI/VGA standard colors
//         • Indices 16–231: 6×6×6 TrueColor RGB cube (216 colors)
//         • Indices 232–255: 24 grayscale shades (dark to bright)
//
// Hardware Resource: ~100 LUT4 + 1 Gowin BSRAM block
// =============================================================================

`timescale 1ns / 1ps

module palette_lut (
    input  wire        clk,        // Pixel/system clock
    input  wire        reset,      // Active-high synchronous reset

    // -------------------------------------------------------------------------
    // Read Port (Video Rendering Pipeline, 1-cycle latency)
    // -------------------------------------------------------------------------
    input  wire [7:0]  color_idx,  // 8-bit palette index from framebuffer
    output reg  [7:0]  red,        // 8-bit red component
    output reg  [7:0]  green,      // 8-bit green component
    output reg  [7:0]  blue,       // 8-bit blue component
    output wire [23:0] rgb,        // Combined 24-bit RGB {red, green, blue}

    // -------------------------------------------------------------------------
    // Write Port (Host / Command Decoder: SET_PALETTE opcode 0x05)
    // -------------------------------------------------------------------------
    input  wire        wr_en,      // Write enable
    input  wire [7:0]  wr_addr,    // Palette index to update (0–255)
    input  wire [7:0]  wr_r,       // Red value to write
    input  wire [7:0]  wr_g,       // Green value to write
    input  wire [7:0]  wr_b        // Blue value to write
);

    // =========================================================================
    // Palette Memory: 256 entries of 24-bit RGB
    // =========================================================================
    reg [23:0] lut_mem [0:255];

    // =========================================================================
    // Palette Initialization (Standard 256-Color Palette)
    // =========================================================================
    integer i, r_idx, g_idx, b_idx, gray_val;

    // Helper function to map 0..5 levels of 6x6x6 color cube to 0..255
    function [7:0] cube_level;
        input [2:0] lvl;
        begin
            case (lvl)
                3'd0: cube_level = 8'd0;
                3'd1: cube_level = 8'd51;
                3'd2: cube_level = 8'd102;
                3'd3: cube_level = 8'd153;
                3'd4: cube_level = 8'd204;
                default: cube_level = 8'd255;
            endcase
        end
    endfunction

    initial begin
        // --- Indices 0–15: Standard 16 VGA / ANSI colors ---
        lut_mem[0]  = 24'h000000; // Black
        lut_mem[1]  = 24'h0000AA; // Blue
        lut_mem[2]  = 24'h00AA00; // Green
        lut_mem[3]  = 24'h00AAAA; // Cyan
        lut_mem[4]  = 24'hAA0000; // Red
        lut_mem[5]  = 24'hAA00AA; // Magenta
        lut_mem[6]  = 24'hAA5500; // Brown / Dark Yellow
        lut_mem[7]  = 24'hAAAAAA; // Light Gray
        lut_mem[8]  = 24'h555555; // Dark Gray
        lut_mem[9]  = 24'h5555FF; // Bright Blue
        lut_mem[10] = 24'h55FF55; // Bright Green
        lut_mem[11] = 24'h55FFFF; // Bright Cyan
        lut_mem[12] = 24'hFF5555; // Bright Red
        lut_mem[13] = 24'hFF55FF; // Bright Magenta
        lut_mem[14] = 24'hFFFF55; // Bright Yellow
        lut_mem[15] = 24'hFFFFFF; // Bright White

        // --- Indices 16–231: 6x6x6 Color Cube (216 Colors) ---
        for (r_idx = 0; r_idx < 6; r_idx = r_idx + 1) begin
            for (g_idx = 0; g_idx < 6; g_idx = g_idx + 1) begin
                for (b_idx = 0; b_idx < 6; b_idx = b_idx + 1) begin
                    i = 16 + (r_idx * 36) + (g_idx * 6) + b_idx;
                    lut_mem[i] = {cube_level(r_idx[2:0]),
                                  cube_level(g_idx[2:0]),
                                  cube_level(b_idx[2:0])};
                end
            end
        end

        // --- Indices 232–255: 24 Grayscale Levels ---
        for (i = 0; i < 24; i = i + 1) begin
            gray_val = 8 + (i * 10);
            lut_mem[232 + i] = {gray_val[7:0], gray_val[7:0], gray_val[7:0]};
        end
    end

    // =========================================================================
    // Synchronous Read & Write (1-Cycle Latency BRAM)
    // =========================================================================
    always @(posedge clk) begin
        if (wr_en) begin
            lut_mem[wr_addr] <= {wr_r, wr_g, wr_b};
        end

        if (reset) begin
            red   <= 8'd0;
            green <= 8'd0;
            blue  <= 8'd0;
        end else begin
            red   <= lut_mem[color_idx][23:16];
            green <= lut_mem[color_idx][15:8];
            blue  <= lut_mem[color_idx][7:0];
        end
    end

    assign rgb = {red, green, blue};

endmodule
