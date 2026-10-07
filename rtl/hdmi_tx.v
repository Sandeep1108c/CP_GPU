// =============================================================================
// Module: HDMI Physical Transmitter Core (hdmi_tx.v)
// Project: Custom FPGA-Based GPU — Woxsen University
// Device: Gowin GW2AR-18C (Sipeed Tang Nano 20K)
// Description:
//   Bridges the internal GPU video pipeline to physical HDMI differential pins.
//   1. Takes 8-bit RGB + HSYNC + VSYNC + VIDEO_ACTIVE on the 25.2 MHz pixel clock.
//   2. Encodes video and control tokens into 10-bit TMDS symbols via tmds_encoder.v.
//   3. Serializes each 10-bit word into a 1-bit high-speed bitstream using Gowin
//      OSER10 hardware DDR serializer primitives running on FCLK = 126.0 MHz (5x)
//      and PCLK = 25.2 MHz (1x).
//   4. Converts single-ended serial bitstreams to differential TMDS pairs using
//      Gowin ELVDS_OBUF output buffers to drive the onboard HDMI port (Pins 33-40).
// =============================================================================

`timescale 1ns / 1ps

module hdmi_tx (
    input  wire        clk_pixel,      // 25.2 MHz pixel clock (PCLK)
    input  wire        clk_serial,     // 126.0 MHz serial clock (FCLK = 5x pixel clock)
    input  wire        reset,          // Active-high synchronous reset
    input  wire [7:0]  red,            // 8-bit red pixel data
    input  wire [7:0]  green,          // 8-bit green pixel data
    input  wire [7:0]  blue,           // 8-bit blue pixel data
    input  wire        hsync,          // Horizontal sync
    input  wire        vsync,          // Vertical sync
    input  wire        video_active,   // Data enable (high during visible screen)

    // Physical HDMI TMDS differential pairs
    output wire        tmds_clk_p,     // Clock + (Pin 33)
    output wire        tmds_clk_n,     // Clock - (Pin 34)
    output wire [2:0]  tmds_d_p,       // [0]=Blue+ (35), [1]=Green+ (37), [2]=Red+ (39)
    output wire [2:0]  tmds_d_n        // [0]=Blue- (36), [1]=Green- (38), [2]=Red- (40)
);

    // =========================================================================
    // 1. TMDS 8b/10b Encoding
    // =========================================================================
    wire [9:0] tmds_red;
    wire [9:0] tmds_green;
    wire [9:0] tmds_blue;
    // TMDS Clock channel sends constant 10'b1111100000 (square wave at clk_pixel)
    wire [9:0] tmds_clk_word = 10'b1111100000;

    tmds_encoder u_tmds_enc (
        .clk          (clk_pixel),
        .reset        (reset),
        .red          (red),
        .green        (green),
        .blue         (blue),
        .hsync        (hsync),
        .vsync        (vsync),
        .video_active (video_active),
        .tmds_red     (tmds_red),
        .tmds_green   (tmds_green),
        .tmds_blue    (tmds_blue)
    );

    // =========================================================================
    // 2. 10:1 DDR Serialization (OSER10)
    // Serializes 10-bit parallel words (PCLK) into 1-bit serial bitstreams (FCLK)
    // OSER10 transmits LSB first (D0, then D1, ..., up to D9)
    // =========================================================================
    wire ser_blue;
    wire ser_green;
    wire ser_red;
    wire ser_clk;

    // Channel 0: Blue / HSYNC / VSYNC
    OSER10 u_oser_blue (
        .Q     (ser_blue),
        .D0    (tmds_blue[0]),
        .D1    (tmds_blue[1]),
        .D2    (tmds_blue[2]),
        .D3    (tmds_blue[3]),
        .D4    (tmds_blue[4]),
        .D5    (tmds_blue[5]),
        .D6    (tmds_blue[6]),
        .D7    (tmds_blue[7]),
        .D8    (tmds_blue[8]),
        .D9    (tmds_blue[9]),
        .PCLK  (clk_pixel),
        .FCLK  (clk_serial),
        .RESET (reset)
    );
    defparam u_oser_blue.GSREN = "false";
    defparam u_oser_blue.LSREN = "true";

    // Channel 1: Green
    OSER10 u_oser_green (
        .Q     (ser_green),
        .D0    (tmds_green[0]),
        .D1    (tmds_green[1]),
        .D2    (tmds_green[2]),
        .D3    (tmds_green[3]),
        .D4    (tmds_green[4]),
        .D5    (tmds_green[5]),
        .D6    (tmds_green[6]),
        .D7    (tmds_green[7]),
        .D8    (tmds_green[8]),
        .D9    (tmds_green[9]),
        .PCLK  (clk_pixel),
        .FCLK  (clk_serial),
        .RESET (reset)
    );
    defparam u_oser_green.GSREN = "false";
    defparam u_oser_green.LSREN = "true";

    // Channel 2: Red
    OSER10 u_oser_red (
        .Q     (ser_red),
        .D0    (tmds_red[0]),
        .D1    (tmds_red[1]),
        .D2    (tmds_red[2]),
        .D3    (tmds_red[3]),
        .D4    (tmds_red[4]),
        .D5    (tmds_red[5]),
        .D6    (tmds_red[6]),
        .D7    (tmds_red[7]),
        .D8    (tmds_red[8]),
        .D9    (tmds_red[9]),
        .PCLK  (clk_pixel),
        .FCLK  (clk_serial),
        .RESET (reset)
    );
    defparam u_oser_red.GSREN = "false";
    defparam u_oser_red.LSREN = "true";

    // Clock Channel
    OSER10 u_oser_clk (
        .Q     (ser_clk),
        .D0    (tmds_clk_word[0]),
        .D1    (tmds_clk_word[1]),
        .D2    (tmds_clk_word[2]),
        .D3    (tmds_clk_word[3]),
        .D4    (tmds_clk_word[4]),
        .D5    (tmds_clk_word[5]),
        .D6    (tmds_clk_word[6]),
        .D7    (tmds_clk_word[7]),
        .D8    (tmds_clk_word[8]),
        .D9    (tmds_clk_word[9]),
        .PCLK  (clk_pixel),
        .FCLK  (clk_serial),
        .RESET (reset)
    );
    defparam u_oser_clk.GSREN = "false";
    defparam u_oser_clk.LSREN = "true";

    // =========================================================================
    // 3. Differential Output Buffers (ELVDS_OBUF)
    // Emulated LVDS output buffers drive the physical TMDS differential pairs
    // =========================================================================
    ELVDS_OBUF u_obuf_blue (
        .I  (ser_blue),
        .O  (tmds_d_p[0]),
        .OB (tmds_d_n[0])
    );

    ELVDS_OBUF u_obuf_green (
        .I  (ser_green),
        .O  (tmds_d_p[1]),
        .OB (tmds_d_n[1])
    );

    ELVDS_OBUF u_obuf_red (
        .I  (ser_red),
        .O  (tmds_d_p[2]),
        .OB (tmds_d_n[2])
    );

    ELVDS_OBUF u_obuf_clk (
        .I  (ser_clk),
        .O  (tmds_clk_p),
        .OB (tmds_clk_n)
    );

endmodule
