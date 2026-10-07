// =============================================================================
// Module: GPU Command Decoder FSM (cmd_decoder.v)
// Project: Custom FPGA-Based GPU — Woxsen University
// Device: Gowin GW2AR-18C (Sipeed Tang Nano 20K)
// Description:
//   Central command processing unit for the 2D Gaming GPU.
//   Receives serialized byte streams from the SPI slave (ESP32-S3 master),
//   parses variable-length GPU command frames, and routes execution strobes
//   and parameters to graphics rendering engines (Blitter, Rasterizer,
//   Palette LUT, Framebuffer Swap, and SDRAM Asset Loader).
//
// Command Frame Protocol (ESP32-S3 -> FPGA):
//   ┌──────────┬──────────┬─────────────────────────────────┐
//   │ CMD (8b) │ LEN (8b) │ PAYLOAD (N bytes, Big-Endian)   │
//   └──────────┴──────────┴─────────────────────────────────┘
//
// Supported Opcode Matrix:
//   0x00: NOP          (Len 0)  - No-op, clears error flags
//   0x01: CLEAR        (Len 1)  - Fill framebuffer with palette color (color: 8b)
//   0x02: DRAW_SPRITE  (Len 7)  - Blit sprite (x: 16b, y: 16b, sprite_id: 16b, flags: 8b)
//   0x03: DRAW_LINE    (Len 9)  - Bresenham line (x0: 16b, y0: 16b, x1: 16b, y1: 16b, color: 8b)
//   0x04: DRAW_RECT    (Len 9)  - Filled rect (x: 16b, y: 16b, w: 16b, h: 16b, color: 8b)
//   0x05: SET_PALETTE  (Len 4)  - Update CLUT (index: 8b, R: 8b, G: 8b, B: 8b)
//   0x06: SWAP_BUFFER  (Len 0)  - Double-buffer swap synchronized to VSYNC
//   0x07: LOAD_SPRITE  (Len 3+N)- Stream sprite pixels to SDRAM (addr: 24b, data: N bytes)
// =============================================================================

`timescale 1ns / 1ps

module cmd_decoder (
    // -------------------------------------------------------------------------
    // Clock and Reset
    // -------------------------------------------------------------------------
    input  wire        clk,              // System clock (27 MHz)
    input  wire        reset,            // Active-high synchronous reset

    // -------------------------------------------------------------------------
    // SPI Slave Byte Stream Interface (from spi_slave.v)
    // -------------------------------------------------------------------------
    input  wire [7:0]  rx_data,          // Received byte from SPI
    input  wire        rx_valid,         // 1-cycle strobe when rx_data is valid
    input  wire        rx_first,         // 1-cycle strobe indicating opcode byte
    input  wire        cs_active,        // Active while SPI CS_n is asserted (low)

    // -------------------------------------------------------------------------
    // SPI Slave Telemetry / Transmit Interface (MISO return to ESP32)
    // -------------------------------------------------------------------------
    output reg  [7:0]  tx_data,          // Telemetry byte
    output reg         tx_load,          // 1-cycle strobe to load tx_data
    input  wire        tx_ready,         // High when SPI slave can accept next tx byte

    // -------------------------------------------------------------------------
    // Video Timing & Double-Buffering Interface (vga_timing.v)
    // -------------------------------------------------------------------------
    input  wire        vsync,            // VSYNC pulse from video timing core
    input  wire        in_vblank,        // High during vertical blanking
    output reg         buf_front_idx,    // Active front buffer (read by scanout: 0 or 1)
    output wire        buf_back_idx,     // Active back buffer (written by draw engines: ~buf_front_idx)
    output reg         swap_pending,     // High while waiting for next VSYNC to flip buffers

    // -------------------------------------------------------------------------
    // Palette LUT Interface (to palette_lut.v - SET_PALETTE 0x05)
    // -------------------------------------------------------------------------
    output reg         palette_wr_en,    // Palette write strobe (1 cycle)
    output reg  [7:0]  palette_addr,     // Palette index (0..255)
    output reg  [7:0]  palette_r,        // Red (0..255)
    output reg  [7:0]  palette_g,        // Green (0..255)
    output reg  [7:0]  palette_b,        // Blue (0..255)

    // -------------------------------------------------------------------------
    // Screen Clear Engine Interface (CLEAR 0x01)
    // -------------------------------------------------------------------------
    output reg         clear_start,      // 1-cycle trigger strobe
    output reg  [7:0]  clear_color,      // 8-bit palette index
    input  wire        clear_done,       // High when clear completed
    input  wire        clear_busy,       // High while clear engine is running

    // -------------------------------------------------------------------------
    // Blitter / Sprite Engine Interface (DRAW_SPRITE 0x02)
    // -------------------------------------------------------------------------
    output reg         sprite_start,     // 1-cycle trigger strobe
    output reg  [15:0] sprite_x,         // X coordinate (0..639)
    output reg  [15:0] sprite_y,         // Y coordinate (0..479)
    output reg  [15:0] sprite_id,        // Sprite ID index in SDRAM memory
    output reg  [7:0]  sprite_flags,     // Flags (bit 0: flip_x, 1: flip_y, 2: trans_en)
    input  wire        sprite_done,      // High when blit completed
    input  wire        sprite_busy,      // High while blitter is running

    // -------------------------------------------------------------------------
    // Rasterizer Engine Interface (DRAW_LINE 0x03, DRAW_RECT 0x04)
    // -------------------------------------------------------------------------
    output reg         line_start,       // 1-cycle trigger strobe
    output reg  [15:0] line_x0,
    output reg  [15:0] line_y0,
    output reg  [15:0] line_x1,
    output reg  [15:0] line_y1,
    output reg  [7:0]  line_color,
    input  wire        line_done,
    input  wire        line_busy,

    output reg         rect_start,       // 1-cycle trigger strobe
    output reg  [15:0] rect_x,
    output reg  [15:0] rect_y,
    output reg  [15:0] rect_w,
    output reg  [15:0] rect_h,
    output reg  [7:0]  rect_color,
    input  wire        rect_done,
    input  wire        rect_busy,

    // -------------------------------------------------------------------------
    // SDRAM Asset Streaming / Direct Writer (LOAD_SPRITE 0x07)
    // -------------------------------------------------------------------------
    output reg         sdram_load_start, // Asserted during upload burst
    output reg  [23:0] sdram_load_addr,  // 24-bit SDRAM destination byte address
    output reg  [7:0]  sdram_load_data,  // Pixel byte to write
    output reg         sdram_load_valid, // 1-cycle strobe per written byte
    input  wire        sdram_load_ready, // High when SDRAM controller can accept byte

    // -------------------------------------------------------------------------
    // Status & Diagnostics
    // -------------------------------------------------------------------------
    output wire        gpu_busy,         // Any draw engine active or cmd executing
    output reg         cmd_busy,         // Command decoder active
    output reg         cmd_error         // Unknown opcode, length mismatch, or early abort
);

    // =========================================================================
    // Opcodes Definition
    // =========================================================================
    localparam [7:0] OP_NOP         = 8'h00;
    localparam [7:0] OP_CLEAR       = 8'h01;
    localparam [7:0] OP_DRAW_SPRITE = 8'h02;
    localparam [7:0] OP_DRAW_LINE   = 8'h03;
    localparam [7:0] OP_DRAW_RECT   = 8'h04;
    localparam [7:0] OP_SET_PALETTE = 8'h05;
    localparam [7:0] OP_SWAP_BUFFER = 8'h06;
    localparam [7:0] OP_LOAD_SPRITE = 8'h07;

    // Expected payload lengths
    localparam [7:0] LEN_NOP         = 8'd0;
    localparam [7:0] LEN_CLEAR       = 8'd1;
    localparam [7:0] LEN_DRAW_SPRITE = 8'd7;
    localparam [7:0] LEN_DRAW_LINE   = 8'd9;
    localparam [7:0] LEN_DRAW_RECT   = 8'd9;
    localparam [7:0] LEN_SET_PALETTE = 8'd4;
    localparam [7:0] LEN_SWAP_BUFFER = 8'd0;

    // =========================================================================
    // Double-Buffer Back Buffer Pointer
    // =========================================================================
    assign buf_back_idx = ~buf_front_idx;

    // Detect vsync rising edge for tear-free page flip
    reg vsync_d;
    always @(posedge clk) begin
        if (reset)
            vsync_d <= 1'b0;
        else
            vsync_d <= vsync;
    end
    wire vsync_rising = (vsync && !vsync_d);

    // Overall GPU busy status (hardware rendering engines only)
    assign gpu_busy = clear_busy | sprite_busy | line_busy | rect_busy;

    // =========================================================================
    // Telemetry Generator (MISO Status Byte)
    // =========================================================================
    // Bit 0: gpu_busy
    // Telemetry Mapping:
    // Bits [7:5]: Signature 3'b010
    // Bit 4: buf_front_idx
    // Bit 3: rect_busy
    // Bit 2: line_busy
    // Bit 1: sprite_busy
    // Bit 0: clear_busy
    wire [7:0] current_telemetry = {
        3'b010,           // Signature [7:5]
        buf_front_idx,    // [4]
        rect_busy,        // [3]
        line_busy,        // [2]
        sprite_busy,      // [1]
        clear_busy        // [0]
    };

    always @(posedge clk) begin
        if (reset) begin
            tx_data <= 8'h40;
            tx_load <= 1'b0;
        end else begin
            tx_load <= 1'b0;
            if (tx_ready) begin
                tx_data <= current_telemetry;
                tx_load <= 1'b1;
            end
        end
    end

    // =========================================================================
    // Main Command Decoder FSM
    // =========================================================================
    localparam [2:0] ST_IDLE    = 3'd0;
    localparam [2:0] ST_LEN     = 3'd1;
    localparam [2:0] ST_PAYLOAD = 3'd2;
    localparam [2:0] ST_EXEC    = 3'd3;
    localparam [2:0] ST_WAIT    = 3'd4;
    localparam [2:0] ST_ERROR   = 3'd5;

    reg [2:0] state;
    reg [7:0] active_cmd;
    reg [7:0] active_len;
    reg [7:0] payload_cnt;

    always @(posedge clk) begin
        if (reset) begin
            state            <= ST_IDLE;
            active_cmd       <= 8'h00;
            active_len       <= 8'h00;
            payload_cnt      <= 8'h00;
            cmd_busy         <= 1'b0;
            cmd_error        <= 1'b0;

            palette_wr_en    <= 1'b0;
            palette_addr     <= 8'h00;
            palette_r        <= 8'h00;
            palette_g        <= 8'h00;
            palette_b        <= 8'h00;

            clear_start      <= 1'b0;
            clear_color      <= 8'h00;

            sprite_start     <= 1'b0;
            sprite_x         <= 16'd0;
            sprite_y         <= 16'd0;
            sprite_id        <= 16'd0;
            sprite_flags     <= 8'd0;

            line_start       <= 1'b0;
            line_x0          <= 16'd0;
            line_y0          <= 16'd0;
            line_x1          <= 16'd0;
            line_y1          <= 16'd0;
            line_color       <= 8'd0;

            rect_start       <= 1'b0;
            rect_x           <= 16'd0;
            rect_y           <= 16'd0;
            rect_w           <= 16'd0;
            rect_h           <= 16'd0;
            rect_color       <= 8'd0;

            sdram_load_start <= 1'b0;
            sdram_load_addr  <= 24'd0;
            sdram_load_data  <= 8'd0;
            sdram_load_valid <= 1'b0;

            buf_front_idx    <= 1'b0;
            swap_pending     <= 1'b0;
        end else begin
            // Double-buffer swap execution on VSYNC edge
            if (swap_pending && vsync_rising) begin
                buf_front_idx <= ~buf_front_idx;
                swap_pending  <= 1'b0;
            end

            // Default 1-cycle strobes low
            palette_wr_en    <= 1'b0;
            clear_start      <= 1'b0;
            sprite_start     <= 1'b0;
            line_start       <= 1'b0;
            rect_start       <= 1'b0;
            sdram_load_valid <= 1'b0;

            // CS Abort Protection
            if (!cs_active && (
                (state == ST_LEN && !rx_valid) ||
                (state == ST_PAYLOAD && !(rx_valid && (payload_cnt == active_len - 8'd1)))
            )) begin
                state            <= ST_IDLE;
                cmd_busy         <= 1'b0;
                cmd_error        <= 1'b1;
                sdram_load_start <= 1'b0;
            end else begin
                case (state)
                    // ---------------------------------------------------------
                    // ST_IDLE: Wait for new transaction with rx_first opcode
                    // ---------------------------------------------------------
                    ST_IDLE: begin
                        cmd_busy <= 1'b0;
                        if (rx_valid && rx_first) begin
                            active_cmd  <= rx_data;
                            cmd_busy    <= 1'b1;
                            cmd_error   <= 1'b0;
                            state       <= ST_LEN;
                        end
                    end

                    // ---------------------------------------------------------
                    // ST_LEN: Receive payload length byte
                    // ---------------------------------------------------------
                    ST_LEN: begin
                        if (rx_valid) begin
                            active_len  <= rx_data;
                            payload_cnt <= 8'd0;

                            if (rx_data == 8'd0) begin
                                state <= ST_EXEC;
                            end else begin
                                if (active_cmd == OP_CLEAR ||
                                    active_cmd == OP_DRAW_SPRITE ||
                                    active_cmd == OP_DRAW_LINE ||
                                    active_cmd == OP_DRAW_RECT ||
                                    active_cmd == OP_SET_PALETTE ||
                                    active_cmd == OP_LOAD_SPRITE) begin
                                    state <= ST_PAYLOAD;
                                    if (active_cmd == OP_LOAD_SPRITE) begin
                                        sdram_load_start <= 1'b1;
                                    end
                                end else begin
                                    cmd_error <= 1'b1;
                                    state     <= ST_ERROR;
                                end
                            end
                        end
                    end

                    // ---------------------------------------------------------
                    // ST_PAYLOAD: Deserialize multi-byte parameters
                    // ---------------------------------------------------------
                    ST_PAYLOAD: begin
                        if (rx_valid) begin
                            payload_cnt <= payload_cnt + 8'd1;

                            case (active_cmd)
                                // --- CLEAR: 1 byte [color] ---
                                OP_CLEAR: begin
                                    clear_color <= rx_data;
                                end

                                // --- DRAW_SPRITE: 7 bytes ---
                                OP_DRAW_SPRITE: begin
                                    case (payload_cnt)
                                        8'd0: sprite_x[15:8]   <= rx_data;
                                        8'd1: sprite_x[7:0]    <= rx_data;
                                        8'd2: sprite_y[15:8]   <= rx_data;
                                        8'd3: sprite_y[7:0]    <= rx_data;
                                        8'd4: sprite_id[15:8]  <= rx_data;
                                        8'd5: sprite_id[7:0]   <= rx_data;
                                        8'd6: sprite_flags     <= rx_data;
                                    endcase
                                end

                                // --- DRAW_LINE: 9 bytes ---
                                OP_DRAW_LINE: begin
                                    case (payload_cnt)
                                        8'd0: line_x0[15:8] <= rx_data;
                                        8'd1: line_x0[7:0]  <= rx_data;
                                        8'd2: line_y0[15:8] <= rx_data;
                                        8'd3: line_y0[7:0]  <= rx_data;
                                        8'd4: line_x1[15:8] <= rx_data;
                                        8'd5: line_x1[7:0]  <= rx_data;
                                        8'd6: line_y1[15:8] <= rx_data;
                                        8'd7: line_y1[7:0]  <= rx_data;
                                        8'd8: line_color    <= rx_data;
                                    endcase
                                end

                                // --- DRAW_RECT: 9 bytes ---
                                OP_DRAW_RECT: begin
                                    case (payload_cnt)
                                        8'd0: rect_x[15:8] <= rx_data;
                                        8'd1: rect_x[7:0]  <= rx_data;
                                        8'd2: rect_y[15:8] <= rx_data;
                                        8'd3: rect_y[7:0]  <= rx_data;
                                        8'd4: rect_w[15:8] <= rx_data;
                                        8'd5: rect_w[7:0]  <= rx_data;
                                        8'd6: rect_h[15:8] <= rx_data;
                                        8'd7: rect_h[7:0]  <= rx_data;
                                        8'd8: rect_color   <= rx_data;
                                    endcase
                                end

                                // --- SET_PALETTE: 4 bytes ---
                                OP_SET_PALETTE: begin
                                    case (payload_cnt)
                                        8'd0: palette_addr <= rx_data;
                                        8'd1: palette_r    <= rx_data;
                                        8'd2: palette_g    <= rx_data;
                                        8'd3: palette_b    <= rx_data;
                                    endcase
                                end

                                // --- LOAD_SPRITE: 3 bytes addr + N data bytes ---
                                OP_LOAD_SPRITE: begin
                                    case (payload_cnt)
                                        8'd0: sdram_load_addr[23:16] <= rx_data;
                                        8'd1: sdram_load_addr[15:8]  <= rx_data;
                                        8'd2: sdram_load_addr[7:0]   <= rx_data;
                                        default: begin
                                            sdram_load_data  <= rx_data;
                                            sdram_load_valid <= 1'b1;
                                            if (payload_cnt > 8'd3)
                                                sdram_load_addr <= sdram_load_addr + 24'd1;
                                        end
                                    endcase
                                end
                            endcase

                            if (payload_cnt == active_len - 8'd1) begin
                                state <= ST_EXEC;
                            end
                        end
                    end

                    // ---------------------------------------------------------
                    // ST_EXEC: Dispatch triggers to execution engines
                    // ---------------------------------------------------------
                    ST_EXEC: begin
                        case (active_cmd)
                            OP_NOP: begin
                                state <= ST_IDLE;
                            end

                            OP_SWAP_BUFFER: begin
                                swap_pending <= 1'b1;
                                state        <= ST_IDLE;
                            end

                            OP_SET_PALETTE: begin
                                palette_wr_en <= 1'b1;
                                state         <= ST_IDLE;
                            end

                            OP_CLEAR: begin
                                if (!gpu_busy) begin
                                    clear_start <= 1'b1;
                                    state       <= ST_IDLE;
                                end
                            end

                            OP_DRAW_SPRITE: begin
                                if (!gpu_busy) begin
                                    sprite_start <= 1'b1;
                                    state        <= ST_IDLE;
                                end
                            end

                            OP_DRAW_LINE: begin
                                if (!gpu_busy) begin
                                    line_start <= 1'b1;
                                    state      <= ST_IDLE;
                                end
                            end

                            OP_DRAW_RECT: begin
                                if (!gpu_busy) begin
                                    rect_start <= 1'b1;
                                    state      <= ST_IDLE;
                                end
                            end

                            OP_LOAD_SPRITE: begin
                                sdram_load_start <= 1'b0;
                                state            <= ST_IDLE;
                            end

                            default: begin
                                cmd_error <= 1'b1;
                                state     <= ST_IDLE;
                            end
                        endcase
                    end

                    // ---------------------------------------------------------
                    // ST_ERROR: Drain erroneous packet until CS deasserts
                    // ---------------------------------------------------------
                    ST_ERROR: begin
                        cmd_error <= 1'b1;
                        if (!cs_active) begin
                            state    <= ST_IDLE;
                            cmd_busy <= 1'b0;
                        end
                    end

                    default: state <= ST_IDLE;
                endcase
            end
        end
    end

endmodule
