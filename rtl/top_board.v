// =============================================================================
// Module: Board Top-Level Wrapper (Tang Nano 20K)
// Project: Custom FPGA-Based GPU — Woxsen University
// Device: Gowin GW2AR-18C (Sipeed Tang Nano 20K)
// Description:
//   Board-level wrapper for the Sipeed Tang Nano 20K FPGA (GW2AR-18C).
//   Wraps the complete GPU top-level, routes physical SPI to header pins,
//   wires Gowin SIP SDRAM ports, drives HDMI transmitter, and exposes
//   hardware status LEDs for immediate board diagnostics.
// =============================================================================

`timescale 1ns / 1ps

module top_board (
    input  wire        sys_clk,    // 27 MHz onboard crystal (Pin 4)
    input  wire        key_reset,  // Onboard Button S1 (Pin 88, active-low)
    
    // Physical SPI Bus from ESP32 / ESP32-S3 Master
    input  wire        spi_sclk,   // Pin 49
    input  wire        spi_cs_n,   // Pin 86
    input  wire        spi_mosi,   // Pin 48
    output wire        spi_miso,   // Pin 51

    // Embedded 64Mbit SIP SDRAM (Gowin Magic Port Names)
    output wire        O_sdram_clk,
    output wire        O_sdram_cke,
    output wire        O_sdram_cs_n,
    output wire        O_sdram_cas_n,
    output wire        O_sdram_ras_n,
    output wire        O_sdram_wen_n,
    inout  wire [31:0] IO_sdram_dq,
    output wire [10:0] O_sdram_addr,
    output wire [1:0]  O_sdram_ba,
    output wire [3:0]  O_sdram_dqm,

    // Onboard LEDs (Pins 15-20, active-low on Tang Nano 20K)
    output wire [5:0]  led,
    
    // Header Pins (VGA outputs for monitor or oscilloscope)
    output wire        vga_hsync,  // Pin 73
    output wire        vga_vsync,  // Pin 74
    output wire [2:0]  vga_rgb,    // Red=Pin 75, Green=Pin 76, Blue=Pin 77

    // Physical HDMI Output (Onboard connector: Pins 33-40)
    output wire        tmds_clk_p, // Pin 33
    output wire        tmds_clk_n, // Pin 34
    output wire [2:0]  tmds_d_p,   // [0]=35, [1]=37, [2]=39
    output wire [2:0]  tmds_d_n    // [0]=36, [1]=38, [2]=40
);

    // =========================================================================
    // Power-On Reset (POR) Generator
    // Releases automatically after ~2.4 ms (65,536 cycles of 27 MHz clock)
    // =========================================================================
    reg [16:0] por_cnt = 17'd0;
    wire por_reset = ~por_cnt[16];

    always @(posedge sys_clk) begin
        if (!por_cnt[16])
            por_cnt <= por_cnt + 17'd1;
    end

    wire reset_internal = por_reset;

    // Internal wires from GPU top
    wire        w_hsync;
    wire        w_vsync;
    wire        w_video_active;
    wire [9:0]  w_pixel_x;
    wire [9:0]  w_pixel_y;
    wire [7:0]  w_red;
    wire [7:0]  w_green;
    wire [7:0]  w_blue;
    wire        w_pll_lock;
    wire        w_clk_pixel;
    wire        w_clk_serial;
    wire        w_gpu_busy;
    wire        w_cmd_busy;
    wire        w_cmd_error;
    wire        w_buf_front_idx;

    // =========================================================================
    // Instantiate Complete GPU Pipeline Core
    // =========================================================================
    gpu_top u_gpu (
        .clk_27m       (sys_clk),
        .reset         (reset_internal),

        // SPI Interface (ESP32-S3)
        .spi_sclk      (spi_sclk),
        .spi_cs_n      (spi_cs_n),
        .spi_mosi      (spi_mosi),
        .spi_miso      (spi_miso),

        // SDRAM Interface
        .SDRAM_DQ      (IO_sdram_dq),
        .SDRAM_A       (O_sdram_addr),
        .SDRAM_BA      (O_sdram_ba),
        .SDRAM_nCS     (O_sdram_cs_n),
        .SDRAM_nRAS    (O_sdram_ras_n),
        .SDRAM_nCAS    (O_sdram_cas_n),
        .SDRAM_nWE     (O_sdram_wen_n),
        .SDRAM_CLK     (O_sdram_clk),
        .SDRAM_CKE     (O_sdram_cke),
        .SDRAM_DQM     (O_sdram_dqm),

        // Video Output
        .hsync         (w_hsync),
        .vsync         (w_vsync),
        .video_active  (w_video_active),
        .pixel_x       (w_pixel_x),
        .pixel_y       (w_pixel_y),
        .red           (w_red),
        .green         (w_green),
        .blue          (w_blue),

        // Clocks & Diagnostics
        .clk_pixel     (w_clk_pixel),
        .clk_serial    (w_clk_serial),
        .pll_lock      (w_pll_lock),
        .gpu_busy      (w_gpu_busy),
        .cmd_busy      (w_cmd_busy),
        .cmd_error     (w_cmd_error),
        .buf_front_idx (w_buf_front_idx)
    );

    // =========================================================================
    // Instantiate HDMI Physical Transmitter (OSER10 + ELVDS_OBUF)
    // =========================================================================
    hdmi_tx u_hdmi (
        .clk_pixel    (w_clk_pixel),
        .clk_serial   (w_clk_serial),
        .reset        (reset_internal | ~w_pll_lock),
        .red          (w_red),
        .green        (w_green),
        .blue         (w_blue),
        .hsync        (w_hsync),
        .vsync        (w_vsync),
        .video_active (w_video_active),
        .tmds_clk_p   (tmds_clk_p),
        .tmds_clk_n   (tmds_clk_n),
        .tmds_d_p     (tmds_d_p),
        .tmds_d_n     (tmds_d_n)
    );

    // =========================================================================
    // Visual Verification: Heartbeat Generator
    // =========================================================================
    reg [23:0] sec_counter = 24'd0;
    reg        heartbeat = 1'b0;

    always @(posedge sys_clk) begin
        if (reset_internal) begin
            sec_counter <= 24'd0;
            heartbeat   <= 1'b0;
        end else begin
            if (sec_counter == 24'd13_500_000 - 1) begin
                sec_counter <= 24'd0;
                heartbeat   <= ~heartbeat; // Toggles every 0.5s = 1 Hz blink
            end else begin
                sec_counter <= sec_counter + 24'd1;
            end
        end
    end

    // Onboard LEDs (Active-Low on Tang Nano 20K: 0 = ON, 1 = OFF)
    assign led[0] = ~heartbeat;         // LED 0 (Pin 15): 1 Hz crystal heartbeat
    assign led[1] = ~w_pll_lock;        // LED 1 (Pin 16): Solid ON (PLL Locked)
    assign led[2] = ~w_gpu_busy;        // LED 2 (Pin 17): Lights up during drawing activity
    assign led[3] = ~w_video_active;    // LED 3 (Pin 18): Solid ON (Video Raster Active)
    assign led[4] = ~w_buf_front_idx;   // LED 4 (Pin 19): Active front buffer (0 vs 1)
    assign led[5] = ~w_cmd_error;       // LED 5 (Pin 20): Command error indicator

    // Header outputs (MSBs of color channels + sync pulses)
    assign vga_hsync  = w_hsync;
    assign vga_vsync  = w_vsync;
    assign vga_rgb[2] = w_red[7];       // Red MSB
    assign vga_rgb[1] = w_green[7];     // Green MSB
    assign vga_rgb[0] = w_blue[7];      // Blue MSB

endmodule
