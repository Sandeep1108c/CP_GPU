// =============================================================================
// Module: GPU Top-Level Core Pipeline (gpu_top.v)
// Project: Custom FPGA-Based GPU — Woxsen University
// Device: Gowin GW2AR-18C (Sipeed Tang Nano 20K)
// Description:
//   Integrated graphics processing pipeline combining:
//     1. Gowin rPLL + CLKDIV (27 MHz -> 25.2 MHz pixel, 126.0 MHz serial)
//     2. VGA 640x480 @ 60 Hz Timing Generator (vga_timing.v)
//     3. High-Speed SPI Slave Interface (spi_slave.v, Mode 0)
//     4. Command Decoder FSM (cmd_decoder.v)
//     5. 2D Sprite Blitter Engine (blitter.v)
//     6. 2D Primitive Rasterizer Engine (rasterizer.v)
//     7. Prioritized SDRAM Memory Arbiter (sdram_arbiter.v)
//     8. Low-Latency SDR SDRAM Controller (sdram_ctrl.v)
//     9. 256-Entry Color Lookup Table (palette_lut.v)
//    10. Test Pattern Color Bar Generator (color_generator.v)
// =============================================================================

`timescale 1ns / 1ps

module gpu_top (
    // Clock and Reset
    input  wire                   clk_27m,          // 27 MHz crystal oscillator (Pin 4)
    input  wire                   reset,            // Active-high synchronous reset

    // Physical SPI Interface (from ESP32-S3 Master)
    input  wire                   spi_sclk,
    input  wire                   spi_cs_n,
    input  wire                   spi_mosi,
    output wire                   spi_miso,

    // Physical SDRAM Chip Interface (Gowin GW2AR-18 Embedded SIP SDRAM)
    inout  wire [31:0]            SDRAM_DQ,
    output wire [10:0]            SDRAM_A,
    output wire [1:0]             SDRAM_BA,
    output wire                   SDRAM_nCS,
    output wire                   SDRAM_nRAS,
    output wire                   SDRAM_nCAS,
    output wire                   SDRAM_nWE,
    output wire                   SDRAM_CLK,
    output wire                   SDRAM_CKE,
    output wire [3:0]             SDRAM_DQM,

    // Video Output Interface (to HDMI transmitter / VGA DAC)
    output wire                   hsync,
    output wire                   vsync,
    output wire                   video_active,
    output wire [9:0]             pixel_x,
    output wire [9:0]             pixel_y,
    output wire [7:0]             red,
    output wire [7:0]             green,
    output wire [7:0]             blue,

    // Clocks and Diagnostics for Top-Level Wrapper
    output wire                   clk_pixel,        // 25.2 MHz pixel clock
    output wire                   clk_serial,       // 126.0 MHz 5x serial clock
    output wire                   pll_lock,         // PLL lock indicator
    output wire                   gpu_busy,         // Any drawing engine active
    output wire                   cmd_busy,         // Command parser active
    output wire                   cmd_error,        // Protocol error flag
    output wire                   buf_front_idx     // Active display buffer (0 or 1)
);

    // =========================================================================
    // 1. Clock Generation: 27 MHz -> 25.2 MHz (Pixel) + 126.0 MHz (Serial)
    // =========================================================================
    wire w_clk_pixel;
    wire w_clk_serial;
    wire w_pll_lock;

    gowin_rpll u_pll (
        .clkin          (clk_27m),
        .clkout         (w_clk_pixel),
        .clkout_serial  (w_clk_serial),
        .lock           (w_pll_lock)
    );

    assign clk_pixel  = w_clk_pixel;
    assign clk_serial = w_clk_serial;
    assign pll_lock   = w_pll_lock;

    wire core_reset = reset | ~w_pll_lock;

    // =========================================================================
    // 2. Video Timing Generator (640x480 @ 60 Hz)
    // =========================================================================
    wire       w_hsync;
    wire       w_vsync;
    wire       w_video_active;
    wire [9:0] w_pixel_x;
    wire [9:0] w_pixel_y;

    wire       w_frame_sync;
    wire       w_line_sync;

    vga_timing u_vga_timing (
        .clk          (w_clk_pixel),
        .reset        (core_reset),
        .hsync        (w_hsync),
        .vsync        (w_vsync),
        .video_active (w_video_active),
        .pixel_x      (w_pixel_x),
        .pixel_y      (w_pixel_y),
        .frame_sync   (w_frame_sync),
        .line_sync    (w_line_sync)
    );

    reg       render_mode;
    reg [1:0] hsync_pipe, vsync_pipe, vid_act_pipe;
    always @(posedge w_clk_pixel) begin
        if (core_reset) begin
            hsync_pipe   <= 2'b11;
            vsync_pipe   <= 2'b11;
            vid_act_pipe <= 2'b00;
        end else begin
            hsync_pipe   <= {hsync_pipe[0],   w_hsync};
            vsync_pipe   <= {vsync_pipe[0],   w_vsync};
            vid_act_pipe <= {vid_act_pipe[0], w_video_active};
        end
    end

    assign hsync        = render_mode ? hsync_pipe[1]   : w_hsync;
    assign vsync        = render_mode ? vsync_pipe[1]   : w_vsync;
    assign video_active = render_mode ? vid_act_pipe[1] : w_video_active;
    assign pixel_x      = w_pixel_x;
    assign pixel_y      = w_pixel_y;

    // =========================================================================
    // 3. SPI Slave Interface (Mode 0, ESP32-S3 Master)
    // =========================================================================
    wire [7:0] spi_rx_data;
    wire       spi_rx_valid;
    wire       spi_rx_first;
    wire       spi_cs_active;
    wire [7:0] spi_tx_data;
    wire       spi_tx_load;
    wire       spi_tx_ready;

    spi_slave #(
        .SPI_MODE (0)
    ) u_spi_slave (
        .clk       (w_clk_pixel),
        .reset     (core_reset),
        .spi_sclk  (spi_sclk),
        .spi_cs_n  (spi_cs_n),
        .spi_mosi  (spi_mosi),
        .spi_miso  (spi_miso),
        .rx_data   (spi_rx_data),
        .rx_valid  (spi_rx_valid),
        .rx_first  (spi_rx_first),
        .cs_active (spi_cs_active),
        .tx_data   (spi_tx_data),
        .tx_load   (spi_tx_load),
        .tx_ready  (spi_tx_ready)
    );

    // =========================================================================
    // 4. Command Decoder FSM
    // =========================================================================
    wire        w_buf_front_idx;
    wire        w_buf_back_idx;
    wire        w_swap_pending;

    wire        w_palette_wr_en;
    wire [7:0]  w_palette_addr;
    wire [7:0]  w_palette_r;
    wire [7:0]  w_palette_g;
    wire [7:0]  w_palette_b;

    wire        w_clear_start;
    wire [7:0]  w_clear_color;
    wire        w_clear_done;
    wire        w_clear_busy;

    wire        w_sprite_start;
    wire [15:0] w_sprite_x;
    wire [15:0] w_sprite_y;
    wire [15:0] w_sprite_id;
    wire [7:0]  w_sprite_flags;
    wire        w_sprite_done;
    wire        w_sprite_busy;

    wire        w_line_start;
    wire [15:0] w_line_x0;
    wire [15:0] w_line_y0;
    wire [15:0] w_line_x1;
    wire [15:0] w_line_y1;
    wire [7:0]  w_line_color;
    wire        w_line_done;
    wire        w_line_busy;

    wire        w_rect_start;
    wire [15:0] w_rect_x;
    wire [15:0] w_rect_y;
    wire [15:0] w_rect_w;
    wire [15:0] w_rect_h;
    wire [7:0]  w_rect_color;
    wire        w_rect_done;
    wire        w_rect_busy;

    wire        w_load_start;
    wire [23:0] w_load_addr;
    wire [7:0]  w_load_data;
    wire        w_load_valid;
    wire        w_load_ready;

    wire        w_gpu_busy;
    wire        w_cmd_busy;
    wire        w_cmd_error;

    cmd_decoder u_cmd_dec (
        .clk              (w_clk_pixel),
        .reset            (core_reset),
        .rx_data          (spi_rx_data),
        .rx_valid         (spi_rx_valid),
        .rx_first         (spi_rx_first),
        .cs_active        (spi_cs_active),
        .tx_data          (spi_tx_data),
        .tx_load          (spi_tx_load),
        .tx_ready         (spi_tx_ready),
        .vsync            (w_frame_sync),
        .in_vblank        (w_pixel_y >= 10'd480),
        .buf_front_idx    (w_buf_front_idx),
        .buf_back_idx     (w_buf_back_idx),
        .swap_pending     (w_swap_pending),
        .palette_wr_en    (w_palette_wr_en),
        .palette_addr     (w_palette_addr),
        .palette_r        (w_palette_r),
        .palette_g        (w_palette_g),
        .palette_b        (w_palette_b),
        .clear_start      (w_clear_start),
        .clear_color      (w_clear_color),
        .clear_done       (w_clear_done),
        .clear_busy       (w_clear_busy),
        .sprite_start     (w_sprite_start),
        .sprite_x         (w_sprite_x),
        .sprite_y         (w_sprite_y),
        .sprite_id        (w_sprite_id),
        .sprite_flags     (w_sprite_flags),
        .sprite_done      (w_sprite_done),
        .sprite_busy      (w_sprite_busy),
        .line_start       (w_line_start),
        .line_x0          (w_line_x0),
        .line_y0          (w_line_y0),
        .line_x1          (w_line_x1),
        .line_y1          (w_line_y1),
        .line_color       (w_line_color),
        .line_done        (w_line_done),
        .line_busy        (w_line_busy),
        .rect_start       (w_rect_start),
        .rect_x           (w_rect_x),
        .rect_y           (w_rect_y),
        .rect_w           (w_rect_w),
        .rect_h           (w_rect_h),
        .rect_color       (w_rect_color),
        .rect_done        (w_rect_done),
        .rect_busy        (w_rect_busy),
        .sdram_load_start (w_load_start),
        .sdram_load_addr  (w_load_addr),
        .sdram_load_data  (w_load_data),
        .sdram_load_valid (w_load_valid),
        .sdram_load_ready (w_load_ready),
        .gpu_busy         (w_gpu_busy),
        .cmd_busy         (w_cmd_busy),
        .cmd_error        (w_cmd_error)
    );

    assign gpu_busy      = w_gpu_busy;
    assign cmd_busy      = w_cmd_busy;
    assign cmd_error     = w_cmd_error;
    assign buf_front_idx = w_buf_front_idx;

    // =========================================================================
    // 5. 2D Hardware Sprite Blitter Engine
    // =========================================================================
    wire        blit_mem_rd;
    wire        blit_mem_wr;
    wire [22:0] blit_mem_addr;
    wire [7:0]  blit_mem_wdata;
    wire [7:0]  blit_mem_rdata;
    wire        blit_mem_rvalid;
    wire        blit_mem_ready;

    blitter u_blitter (
        .clk              (w_clk_pixel),
        .reset            (core_reset),
        .start            (w_sprite_start),
        .sprite_x         (w_sprite_x),
        .sprite_y         (w_sprite_y),
        .sprite_id        (w_sprite_id),
        .sprite_flags     (w_sprite_flags),
        .buf_back_idx     (w_buf_back_idx),
        .sprite_base_addr (23'h100000), // SDRAM Asset Bank (offset 1MB)
        .busy             (w_sprite_busy),
        .done             (w_sprite_done),
        .mem_rd           (blit_mem_rd),
        .mem_wr           (blit_mem_wr),
        .mem_addr         (blit_mem_addr),
        .mem_wdata        (blit_mem_wdata),
        .mem_rdata        (blit_mem_rdata),
        .mem_rvalid       (blit_mem_rvalid),
        .mem_ready        (blit_mem_ready)
    );

    // =========================================================================
    // 6. 2D Hardware Primitive Rasterizer Engine
    // =========================================================================
    wire        rast_mem_wr;
    wire        rast_mem_wr32;
    wire [22:0] rast_mem_addr;
    wire [7:0]  rast_mem_wdata;
    wire        rast_mem_ready;

    rasterizer u_rasterizer (
        .clk          (w_clk_pixel),
        .reset        (core_reset),
        .line_start   (w_line_start),
        .line_x0      (w_line_x0),
        .line_y0      (w_line_y0),
        .line_x1      (w_line_x1),
        .line_y1      (w_line_y1),
        .line_color   (w_line_color),
        .line_done    (w_line_done),
        .line_busy    (w_line_busy),
        .rect_start   (w_rect_start),
        .rect_x       (w_rect_x),
        .rect_y       (w_rect_y),
        .rect_w       (w_rect_w),
        .rect_h       (w_rect_h),
        .rect_color   (w_rect_color),
        .rect_done    (w_rect_done),
        .rect_busy    (w_rect_busy),
        .clear_start  (w_clear_start),
        .clear_color  (w_clear_color),
        .clear_done   (w_clear_done),
        .clear_busy   (w_clear_busy),
        .buf_back_idx (w_buf_back_idx),
        .mem_wr       (rast_mem_wr),
        .mem_wr32     (rast_mem_wr32),
        .mem_addr     (rast_mem_addr),
        .mem_wdata    (rast_mem_wdata),
        .mem_ready    (rast_mem_ready)
    );

    // =========================================================================
    // 7. Prioritized SDRAM Memory Arbiter
    // =========================================================================
    wire        sdram_rd;
    wire        sdram_wr;
    wire        sdram_wr32;
    wire [22:0] sdram_addr;
    wire [7:0]  sdram_din;
    wire [7:0]  sdram_dout;
    wire [31:0] sdram_dout32;
    wire        sdram_data_ready;
    wire        sdram_busy;

    wire        vga_rd;
    wire [22:0] vga_addr;
    wire [31:0] vga_rdata32;
    wire        vga_rvalid;
    wire        vga_ready;

    sdram_arbiter u_arbiter (
        .clk              (w_clk_pixel),
        .reset            (core_reset),
        .vga_rd           (vga_rd),
        .vga_addr         (vga_addr),
        .vga_rdata        (),
        .vga_rdata32      (vga_rdata32),
        .vga_rvalid       (vga_rvalid),
        .vga_ready        (vga_ready),
        .load_wr          (w_load_valid),
        .load_addr        (w_load_addr[22:0]),
        .load_wdata       (w_load_data),
        .load_ready       (w_load_ready),
        .blit_rd          (blit_mem_rd),
        .blit_wr          (blit_mem_wr),
        .blit_addr        (blit_mem_addr),
        .blit_wdata       (blit_mem_wdata),
        .blit_rdata       (blit_mem_rdata),
        .blit_rvalid      (blit_mem_rvalid),
        .blit_ready       (blit_mem_ready),
        .rast_wr          (rast_mem_wr),
        .rast_wr32        (rast_mem_wr32),
        .rast_addr        (rast_mem_addr),
        .rast_wdata       (rast_mem_wdata),
        .rast_ready       (rast_mem_ready),
        .sdram_rd         (sdram_rd),
        .sdram_wr         (sdram_wr),
        .sdram_wr32       (sdram_wr32),
        .sdram_addr       (sdram_addr),
        .sdram_din        (sdram_din),
        .sdram_dout       (sdram_dout),
        .sdram_dout32     (sdram_dout32),
        .sdram_data_ready (sdram_data_ready),
        .sdram_busy       (sdram_busy)
    );

    // =========================================================================
    // 8. Low-Latency SDR SDRAM Controller (GW2AR-18 Embedded 64Mbit SIP)
    // =========================================================================
    sdram_ctrl #(
        .FREQ (25_200_000)
    ) u_sdram (
        .clk        (w_clk_pixel),
        .clk_sdram  (~w_clk_pixel),
        .resetn     (~core_reset),
        .rd         (sdram_rd),
        .wr         (sdram_wr),
        .wr32       (sdram_wr32),
        .refresh    (1'b0),
        .addr       (sdram_addr),
        .din        (sdram_din),
        .dout       (sdram_dout),
        .dout32     (sdram_dout32),
        .data_ready (sdram_data_ready),
        .busy       (sdram_busy),
        .SDRAM_DQ   (SDRAM_DQ),
        .SDRAM_A    (SDRAM_A),
        .SDRAM_BA   (SDRAM_BA),
        .SDRAM_nCS  (SDRAM_nCS),
        .SDRAM_nRAS (SDRAM_nRAS),
        .SDRAM_nCAS (SDRAM_nCAS),
        .SDRAM_nWE  (SDRAM_nWE),
        .SDRAM_CLK  (SDRAM_CLK),
        .SDRAM_CKE  (SDRAM_CKE),
        .SDRAM_DQM  (SDRAM_DQM)
    );

    // =========================================================================
    // 9. Dual-Line-Buffer Video Scanout Engine
    // =========================================================================
    wire [7:0] scanout_pixel_idx;

    video_scanout u_scanout (
        .clk           (w_clk_pixel),
        .reset         (core_reset),
        .pixel_x       (w_pixel_x),
        .pixel_y       (w_pixel_y),
        .video_active  (w_video_active),
        .line_sync     (w_line_sync),
        .frame_sync    (w_frame_sync),
        .buf_front_idx (w_buf_front_idx),
        .vga_rd        (vga_rd),
        .vga_addr      (vga_addr),
        .vga_rdata32   (vga_rdata32),
        .vga_rvalid    (vga_rvalid),
        .vga_ready     (vga_ready),
        .pixel_idx     (scanout_pixel_idx)
    );

    // =========================================================================
    // 10. Palette LUT (256 entries x 24-bit TrueColor RGB)
    // =========================================================================
    wire [7:0] pal_red;
    wire [7:0] pal_green;
    wire [7:0] pal_blue;

    palette_lut u_palette (
        .clk       (w_clk_pixel),
        .reset     (core_reset),
        .color_idx (scanout_pixel_idx),
        .red       (pal_red),
        .green     (pal_green),
        .blue      (pal_blue),
        .rgb       (),
        .wr_en     (w_palette_wr_en),
        .wr_addr   (w_palette_addr),
        .wr_r      (w_palette_r),
        .wr_g      (w_palette_g),
        .wr_b      (w_palette_b)
    );

    // =========================================================================
    // 11. Video Display Multiplexer (Test Bars vs Game Framebuffer)
    // =========================================================================
    wire [7:0] gen_red;
    wire [7:0] gen_green;
    wire [7:0] gen_blue;

    color_generator u_color_gen (
        .clk          (w_clk_pixel),
        .video_active (w_video_active),
        .pixel_x      (w_pixel_x),
        .pixel_y      (w_pixel_y),
        .red          (gen_red),
        .green        (gen_green),
        .blue         (gen_blue)
    );

    // Automatically transition to game rendering once commands begin arriving
    always @(posedge w_clk_pixel) begin
        if (core_reset)
            render_mode <= 1'b0; // Default on boot: crisp test pattern
        else if (w_cmd_busy || w_swap_pending)
            render_mode <= 1'b1; // Switch to live game framebuffer
    end

    // Mux: test pattern until ESP32 issues draw commands
    assign red   = render_mode ? pal_red   : gen_red;
    assign green = render_mode ? pal_green : gen_green;
    assign blue  = render_mode ? pal_blue  : gen_blue;

endmodule
