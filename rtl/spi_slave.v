// =============================================================================
// Module: SPI Slave Interface (ESP32-S3 Master -> FPGA GPU Slave)
// Project: Custom FPGA-Based GPU — Woxsen University
// Device: Gowin GW2AR-18C (Sipeed Tang Nano 20K)
// Description:
//   Robust, fully synchronous SPI slave receiver and transmitter.
//   Synchronizes external asynchronous SPI signals (SCLK, CS_n, MOSI) to
//   the internal FPGA system clock (clk) using multi-stage synchronizers
//   to eliminate metastability and bus glitching.
//
//   Features:
//     - Standard SPI Mode 0 (CPOL=0, CPHA=0: sample on rising edge, shift on falling)
//     - 8-bit byte-stream reception with 1-cycle rx_valid strobe
//     - rx_first strobe to identify the command opcode (first byte of transaction)
//     - Incomplete byte rejection: aborts cleanly if CS_n rises before 8 bits
//     - Bidirectional: Full-duplex MISO transmission (GPU status/telemetry to ESP32)
//     - Tri-state MISO when unselected (allows shared SPI bus)
//
// Protocol (ESP32-S3 -> FPGA):
//   Packet: [OPCODE (8b)] [LEN (8b)] [PAYLOAD (N bytes)] under active CS_n
// =============================================================================

`timescale 1ns / 1ps

module spi_slave #(
    parameter SPI_MODE = 0 // Mode 0 (CPOL=0, CPHA=0)
)(
    // -------------------------------------------------------------------------
    // FPGA System Clock & Reset Domain
    // -------------------------------------------------------------------------
    input  wire        clk,        // FPGA system/logic clock (25 MHz - 50 MHz)
    input  wire        reset,      // Active-high synchronous reset

    // -------------------------------------------------------------------------
    // Physical SPI Bus (From ESP32-S3 Master)
    // -------------------------------------------------------------------------
    input  wire        spi_sclk,   // SPI Clock (from ESP32-S3)
    input  wire        spi_cs_n,   // Active-low Chip Select (from ESP32-S3)
    input  wire        spi_mosi,   // Master-Out-Slave-In data
    output wire        spi_miso,   // Master-In-Slave-Out data (tri-state)

    // -------------------------------------------------------------------------
    // Receive Interface (To Command Decoder: cmd_decoder.v)
    // -------------------------------------------------------------------------
    output reg  [7:0]  rx_data,    // Received byte
    output reg         rx_valid,   // 1-cycle strobe when rx_data is valid
    output reg         rx_first,   // High for the first byte of a transaction (OPCODE)
    output wire        cs_active,  // High while CS_n is low (packet in progress)

    // -------------------------------------------------------------------------
    // Transmit Interface (From GPU Status / Command Decoder)
    // -------------------------------------------------------------------------
    input  wire [7:0]  tx_data,    // Byte to send back to ESP32 on MISO
    input  wire        tx_load,    // Strobe to load new tx_data byte
    output reg         tx_ready    // High when ready to accept next tx byte
);

    // =========================================================================
    // 3-Stage Metastability Synchronizers & Edge Detectors
    // =========================================================================
    reg [2:0] sclk_sync;
    reg [2:0] cs_n_sync;
    reg [2:0] mosi_sync;

    always @(posedge clk) begin
        if (reset) begin
            sclk_sync <= 3'b000;
            cs_n_sync <= 3'b111; // Default CS_n high (inactive)
            mosi_sync <= 3'b000;
        end else begin
            sclk_sync <= {sclk_sync[1:0], spi_sclk};
            cs_n_sync <= {cs_n_sync[1:0], spi_cs_n};
            mosi_sync <= {mosi_sync[1:0], spi_mosi};
        end
    end

    // Detect edges in FPGA clock domain
    wire sclk_rising  = (sclk_sync[2:1] == 2'b01);
    wire sclk_falling = (sclk_sync[2:1] == 2'b10);
    wire cs_falling   = (cs_n_sync[2:1] == 2'b10); // Transaction start
    wire cs_rising    = (cs_n_sync[2:1] == 2'b01); // Transaction end

    assign cs_active  = ~cs_n_sync[1]; // Filtered active-low CS_n

    // =========================================================================
    // Receive Logic (MOSI Deserializer)
    // =========================================================================
    reg [2:0] rx_bit_cnt;
    reg [6:0] rx_shift;
    reg       is_first_byte;

    always @(posedge clk) begin
        if (reset || cs_rising || !cs_active) begin
            rx_bit_cnt    <= 3'd0;
            rx_shift      <= 7'd0;
            rx_data       <= 8'd0;
            rx_valid      <= 1'b0;
            rx_first      <= 1'b0;
            is_first_byte <= 1'b1;
        end else begin
            // Default 1-cycle strobes low
            rx_valid <= 1'b0;
            rx_first <= 1'b0;

            // Sample MOSI on rising edge of SCLK
            if (sclk_rising) begin
                if (rx_bit_cnt == 3'd7) begin
                    // Byte complete: MSB shifted in first, current bit is LSB [0]
                    rx_data       <= {rx_shift[6:0], mosi_sync[1]};
                    rx_valid      <= 1'b1;
                    rx_first      <= is_first_byte;
                    is_first_byte <= 1'b0; // Subsequent bytes are payload
                    rx_bit_cnt    <= 3'd0;
                end else begin
                    rx_shift   <= {rx_shift[5:0], mosi_sync[1]};
                    rx_bit_cnt <= rx_bit_cnt + 3'd1;
                end
            end
        end
    end

    // =========================================================================
    // Transmit Logic (MISO Serializer)
    // =========================================================================
    reg [7:0] tx_buf;
    reg [7:0] tx_shift;
    reg [2:0] tx_bit_cnt;
    reg       miso_out;
    reg       miso_oe;

    // Drive MISO tri-state: only drive when CS_n is active
    assign spi_miso = (cs_active && miso_oe) ? miso_out : 1'bz;

    wire [7:0] next_tx_byte = tx_load ? tx_data : tx_buf;

    always @(posedge clk) begin
        if (reset) begin
            tx_buf     <= 8'h40;
            tx_shift   <= 8'h00;
            tx_bit_cnt <= 3'd0;
            miso_out   <= 1'b0;
            miso_oe    <= 1'b0;
            tx_ready   <= 1'b1;
        end else begin
            // Buffer loading (can occur anytime)
            if (tx_load) begin
                tx_buf   <= tx_data;
                tx_ready <= 1'b0;
            end

            if (cs_falling) begin
                // Transaction starting: present bit 7 immediately
                miso_oe    <= 1'b1;
                miso_out   <= next_tx_byte[7];
                tx_shift   <= {next_tx_byte[6:0], 1'b0};
                tx_bit_cnt <= 3'd0;
                tx_buf     <= 8'h40;
                tx_ready   <= 1'b1;
            end else if (cs_rising || !cs_active) begin
                // Transaction ended or bus idle: tri-state MISO
                miso_oe    <= 1'b0;
                miso_out   <= 1'b0;
                tx_bit_cnt <= 3'd0;
                // Note: tx_buf is preserved across idle so master can preload data
            end else if (sclk_falling) begin
                // Shift next bit on falling edge of SCLK
                if (tx_bit_cnt == 3'd7) begin
                    // Byte boundary: load next byte from tx_buf if available
                    miso_out   <= next_tx_byte[7];
                    tx_shift   <= {next_tx_byte[6:0], 1'b0};
                    tx_bit_cnt <= 3'd0;
                    tx_buf     <= 8'h40;
                    tx_ready   <= 1'b1;
                end else begin
                    miso_out   <= tx_shift[7];
                    tx_shift   <= {tx_shift[6:0], 1'b0};
                    tx_bit_cnt <= tx_bit_cnt + 3'd1;
                end
            end
        end
    end

endmodule
