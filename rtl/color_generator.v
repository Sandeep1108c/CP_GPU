// =============================================================================
// Module: Color Pattern Generator
// Project: Custom FPGA-Based GPU — Woxsen University
// Description:
//   Generates RGB pixel data based on the current pixel coordinates.
//   Produces a visually striking color bar test pattern to verify the
//   rendering pipeline is working correctly in simulation.
//
//   Pattern: 8 vertical color bars (like a TV test card)
//   Bar 0: White    | Bar 1: Yellow   | Bar 2: Cyan     | Bar 3: Green
//   Bar 4: Magenta  | Bar 5: Red      | Bar 6: Blue     | Bar 7: Black
// =============================================================================

`timescale 1ns / 1ps

module color_generator (
    input  wire        clk,
    input  wire        video_active,
    input  wire [9:0]  pixel_x,
    input  wire [9:0]  pixel_y,
    output reg  [7:0]  red,
    output reg  [7:0]  green,
    output reg  [7:0]  blue
);

    // Divide 640 pixels into 8 bars of 80 pixels each
    wire [2:0] bar_index = pixel_x[9:7]; // Top 3 bits of x (0-7)

    always @(posedge clk) begin
        if (!video_active) begin
            // During blanking intervals, output black
            red   <= 8'h00;
            green <= 8'h00;
            blue  <= 8'h00;
        end else begin
            case (bar_index)
                3'd0: begin red <= 8'hFF; green <= 8'hFF; blue <= 8'hFF; end // White
                3'd1: begin red <= 8'hFF; green <= 8'hFF; blue <= 8'h00; end // Yellow
                3'd2: begin red <= 8'h00; green <= 8'hFF; blue <= 8'hFF; end // Cyan
                3'd3: begin red <= 8'h00; green <= 8'hFF; blue <= 8'h00; end // Green
                3'd4: begin red <= 8'hFF; green <= 8'h00; blue <= 8'hFF; end // Magenta
                3'd5: begin red <= 8'hFF; green <= 8'h00; blue <= 8'h00; end // Red
                3'd6: begin red <= 8'h00; green <= 8'h00; blue <= 8'hFF; end // Blue
                3'd7: begin red <= 8'h00; green <= 8'h00; blue <= 8'h00; end // Black
            endcase
        end
    end

endmodule
