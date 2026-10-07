// =============================================================================
// Module: TMDS Encoder (3-Channel, 8-bit to 10-bit)
// Project: Custom FPGA-Based GPU — Woxsen University
// Description:
//   Implements the DVI 1.0 TMDS (Transition-Minimized Differential Signaling)
//   encoding algorithm. Converts three 8-bit RGB pixel channels into three
//   10-bit TMDS-encoded outputs for HDMI/DVI transmission.
//
//   Contains two modules:
//     tmds_channel  — Single-channel 8b→10b encoder with DC balancing
//     tmds_encoder  — Top-level 3-channel wrapper with control token mapping
//
//   TMDS Encoding (per DVI 1.0 specification):
//     Stage 1: Transition minimization via XOR or XNOR based on popcount
//     Stage 2: DC balancing via selective inversion + running disparity
//     Blanking: Fixed control tokens replace data (4 tokens, DC-balanced)
//
//   Channel mapping (per DVI 1.0):
//     Channel 0 (Blue):  Control = {VSYNC, HSYNC}
//     Channel 1 (Green): Control = {CTL1, CTL0} = {0, 0}
//     Channel 2 (Red):   Control = {CTL3, CTL2} = {0, 0}
//
//   Resource estimate: ~600 LUT4 (3 channels × ~200 LUT each)
// =============================================================================

`timescale 1ns / 1ps

// =============================================================================
// Module: tmds_channel
// Description:
//   Single-channel TMDS encoder. Converts one 8-bit data input to a 10-bit
//   TMDS-encoded output. During blanking (de=0), outputs one of four
//   predefined control tokens based on {c1, c0}.
//
//   The encoding has two stages:
//   1. Transition Minimization — choose XOR or XNOR to minimize bit toggles
//   2. DC Balancing — selectively invert the word and track running disparity
// =============================================================================
module tmds_channel (
    input  wire        clk,        // Pixel clock (25.175 MHz for 640x480)
    input  wire        reset,      // Active-high synchronous reset
    input  wire [7:0]  data_in,    // 8-bit pixel data
    input  wire        c0,         // Control bit 0 (HSYNC on channel 0)
    input  wire        c1,         // Control bit 1 (VSYNC on channel 0)
    input  wire        de,         // Data enable (high = active video)
    output reg  [9:0]  tmds_out    // 10-bit TMDS encoded output
);

    // =========================================================================
    // Stage 1: Transition Minimization
    // =========================================================================
    // Count number of 1-bits in the input data
    wire [3:0] n1_data;
    assign n1_data = data_in[0] + data_in[1] + data_in[2] + data_in[3]
                   + data_in[4] + data_in[5] + data_in[6] + data_in[7];

    // Choose XNOR when input has more 1s than 0s (reduces transitions)
    // Also use XNOR when exactly 4 ones and LSB is 0 (tie-breaker rule)
    wire use_xnor = (n1_data > 4'd4) || (n1_data == 4'd4 && data_in[0] == 1'b0);

    // Build the 9-bit intermediate word q_m
    // q_m[0]   = data_in[0] (always passed through)
    // q_m[n]   = q_m[n-1] XOR/XNOR data_in[n], for n = 1..7
    // q_m[8]   = 1 if XOR was used, 0 if XNOR was used
    wire [8:0] q_m;
    assign q_m[0] = data_in[0];
    assign q_m[1] = use_xnor ? (q_m[0] ~^ data_in[1]) : (q_m[0] ^ data_in[1]);
    assign q_m[2] = use_xnor ? (q_m[1] ~^ data_in[2]) : (q_m[1] ^ data_in[2]);
    assign q_m[3] = use_xnor ? (q_m[2] ~^ data_in[3]) : (q_m[2] ^ data_in[3]);
    assign q_m[4] = use_xnor ? (q_m[3] ~^ data_in[4]) : (q_m[3] ^ data_in[4]);
    assign q_m[5] = use_xnor ? (q_m[4] ~^ data_in[5]) : (q_m[4] ^ data_in[5]);
    assign q_m[6] = use_xnor ? (q_m[5] ~^ data_in[6]) : (q_m[5] ^ data_in[6]);
    assign q_m[7] = use_xnor ? (q_m[6] ~^ data_in[7]) : (q_m[6] ^ data_in[7]);
    assign q_m[8] = ~use_xnor;  // 1 = XOR was used, 0 = XNOR was used

    // =========================================================================
    // Stage 2: DC Balancing
    // =========================================================================
    // Count 1-bits and 0-bits in q_m[7:0]
    wire [3:0] n1_qm;
    assign n1_qm = q_m[0] + q_m[1] + q_m[2] + q_m[3]
                 + q_m[4] + q_m[5] + q_m[6] + q_m[7];
    wire [3:0] n0_qm = 4'd8 - n1_qm;

    // Running disparity counter (5-bit, MSB used as sign in 2's complement)
    // Tracks cumulative DC imbalance across encoded symbols.
    // Positive = too many 1s transmitted, negative = too many 0s.
    reg [4:0] cnt;

    always @(posedge clk) begin
        if (reset) begin
            tmds_out <= 10'b1101010100;  // Default: control token {0,0}
            cnt      <= 5'd0;
        end else if (!de) begin
            // =================================================================
            // Control / Blanking Period
            // Output DC-balanced control tokens (5 ones, 5 zeros each)
            // Reset disparity counter since tokens are inherently balanced
            // =================================================================
            cnt <= 5'd0;
            case ({c1, c0})
                2'b00:   tmds_out <= 10'b1101010100;  // 0x354
                2'b01:   tmds_out <= 10'b0010101011;  // 0x0AB
                2'b10:   tmds_out <= 10'b0101010100;  // 0x154
                default: tmds_out <= 10'b1010101011;  // 0x2AB
            endcase
        end else begin
            // =================================================================
            // Data Period — TMDS encode with DC balancing
            // =================================================================
            if (cnt == 5'd0 || n1_qm == 4'd4) begin
                // Disparity is zero OR intermediate word is perfectly balanced
                // → choose inversion based solely on q_m[8]
                tmds_out[9]   <= ~q_m[8];
                tmds_out[8]   <= q_m[8];
                tmds_out[7:0] <= q_m[8] ? q_m[7:0] : ~q_m[7:0];
                if (~q_m[8])
                    cnt <= cnt + n0_qm - n1_qm;  // XNOR: inverted data
                else
                    cnt <= cnt + n1_qm - n0_qm;  // XOR: non-inverted data
            end else if ((!cnt[4] && n1_qm > n0_qm) ||
                         ( cnt[4] && n0_qm > n1_qm)) begin
                // Disparity and word imbalance are in the same direction
                // → invert the data bits to push disparity back toward zero
                tmds_out[9]   <= 1'b1;
                tmds_out[8]   <= q_m[8];
                tmds_out[7:0] <= ~q_m[7:0];
                cnt <= cnt + {q_m[8], 1'b0} + n0_qm - n1_qm;
            end else begin
                // Disparity and word imbalance are in opposite directions
                // → keep data bits as-is (they naturally correct the balance)
                tmds_out[9]   <= 1'b0;
                tmds_out[8]   <= q_m[8];
                tmds_out[7:0] <= q_m[7:0];
                cnt <= cnt - {~q_m[8], 1'b0} + n1_qm - n0_qm;
            end
        end
    end

endmodule

// =============================================================================
// Module: tmds_encoder
// Description:
//   Top-level 3-channel TMDS encoder. Instantiates three tmds_channel modules
//   for Red, Green, and Blue, mapping sync signals to the correct channel.
//
//   Outputs are parallel 10-bit TMDS words (one per pixel clock). A separate
//   serializer module (using Gowin OSER10 or equivalent) is needed to convert
//   these to the 10:1 serial bitstream for the physical HDMI/DVI interface.
// =============================================================================
module tmds_encoder (
    input  wire        clk,          // Pixel clock (25.175 MHz for 640x480)
    input  wire        reset,        // Active-high synchronous reset
    input  wire [7:0]  red,          // 8-bit red pixel data
    input  wire [7:0]  green,        // 8-bit green pixel data
    input  wire [7:0]  blue,         // 8-bit blue pixel data
    input  wire        hsync,        // Horizontal sync
    input  wire        vsync,        // Vertical sync
    input  wire        video_active, // Data enable (high during visible area)
    output wire [9:0]  tmds_red,     // 10-bit TMDS encoded red   (channel 2)
    output wire [9:0]  tmds_green,   // 10-bit TMDS encoded green (channel 1)
    output wire [9:0]  tmds_blue     // 10-bit TMDS encoded blue  (channel 0)
);

    // =========================================================================
    // Channel 0 — Blue
    // Carries HSYNC and VSYNC as control signals during blanking
    // =========================================================================
    tmds_channel u_ch0_blue (
        .clk      (clk),
        .reset    (reset),
        .data_in  (blue),
        .c0       (hsync),
        .c1       (vsync),
        .de       (video_active),
        .tmds_out (tmds_blue)
    );

    // =========================================================================
    // Channel 1 — Green
    // Control = {CTL1, CTL0} = {0, 0} (no sync on this channel)
    // =========================================================================
    tmds_channel u_ch1_green (
        .clk      (clk),
        .reset    (reset),
        .data_in  (green),
        .c0       (1'b0),
        .c1       (1'b0),
        .de       (video_active),
        .tmds_out (tmds_green)
    );

    // =========================================================================
    // Channel 2 — Red
    // Control = {CTL3, CTL2} = {0, 0} (no sync on this channel)
    // =========================================================================
    tmds_channel u_ch2_red (
        .clk      (clk),
        .reset    (reset),
        .data_in  (red),
        .c0       (1'b0),
        .c1       (1'b0),
        .de       (video_active),
        .tmds_out (tmds_red)
    );

endmodule
