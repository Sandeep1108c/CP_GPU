// =============================================================================
// Module: SDRAM Behavioral Simulation Model (64Mbit 32-bit SDR SDRAM)
// Project: Custom FPGA-Based GPU — Woxsen University
// Description:
//   Accurate behavioral simulation model of the Gowin GW2AR-18 embedded
//   SIP SDRAM (2048 rows × 256 words × 4 banks × 32 bits = 8 MB).
//   Used for verifying the sdram_ctrl module in Icarus Verilog without
//   requiring proprietary encrypted Gowin vendor libraries.
//
//   Supported Features:
//     - Bank Activate (Row latching per bank)
//     - Read command with CAS latency 2
//     - Write command with DQM byte-lane masking
//     - Precharge and Auto-Precharge
//     - Mode Register Set
//     - Auto-Refresh command decode
//     - Bidirectional 32-bit DQ bus
// =============================================================================

`timescale 1ns / 1ps

module sdram_model #(
    parameter DATA_WIDTH = 32,
    parameter ROW_WIDTH  = 11,
    parameter COL_WIDTH  = 8,
    parameter BANK_WIDTH = 2
)(
    input  wire                   clk,
    input  wire                   cke,
    input  wire                   cs_n,
    input  wire                   ras_n,
    input  wire                   cas_n,
    input  wire                   we_n,
    input  wire [3:0]             dqm,
    input  wire [ROW_WIDTH-1:0]   addr,
    input  wire [BANK_WIDTH-1:0]  ba,
    inout  wire [DATA_WIDTH-1:0]  dq
);

    // SDRAM Commands
    localparam CMD_MRS  = 3'b000;
    localparam CMD_REF  = 3'b001;
    localparam CMD_PRE  = 3'b010;
    localparam CMD_ACT  = 3'b011;
    localparam CMD_WR   = 3'b100;
    localparam CMD_RD   = 3'b101;
    localparam CMD_NOP  = 3'b111;

    wire [2:0] cmd = {ras_n, cas_n, we_n};

    // Full 64Mbit (8MB) internal memory: 2M × 32-bit words (4 banks × 2048 rows × 256 cols)
    reg [31:0] mem [0:2097151];

    // Bank active row tracking
    reg [ROW_WIDTH-1:0] active_row [0:3];
    reg                 bank_active [0:3];

    // Mode Register
    reg [10:0] mode_reg;

    // Read pipeline registers (CAS latency = 2)
    reg [31:0] read_pipe_0;
    reg [31:0] read_pipe_1;
    reg        read_valid_0;
    reg        read_valid_1;
    reg [2:0]  burst_remain;
    reg [1:0]  burst_ba;
    reg [10:0] burst_row;
    reg [7:0]  burst_col;

    // Tri-state DQ bus drive
    assign dq = read_valid_1 ? read_pipe_1 : 32'bzzzz_zzzz_zzzz_zzzz_zzzz_zzzz_zzzz_zzzz;

    // Direct 21-bit address into full 2M-word memory (zero hash collisions)
    function [20:0] get_mem_addr;
        input [1:0]  b;
        input [10:0] r;
        input [7:0]  c;
        begin
            get_mem_addr = {b[1:0], r[10:0], c[7:0]};
        end
    endfunction

    integer b_idx;
    initial begin
        for (b_idx = 0; b_idx < 4; b_idx = b_idx + 1) begin
            active_row[b_idx]  = 0;
            bank_active[b_idx] = 0;
        end
        read_valid_0 = 0;
        read_valid_1 = 0;
        read_pipe_0  = 0;
        read_pipe_1  = 0;
        burst_remain = 0;
    end

    // Clocked command and data handling
    always @(posedge clk) begin
        if (cke && !cs_n) begin
            case (cmd)
                CMD_MRS: begin
                    mode_reg <= addr;
                end

                CMD_ACT: begin
                    active_row[ba]  <= addr;
                    bank_active[ba] <= 1'b1;
                end

                CMD_PRE: begin
                    if (addr[10]) begin // Precharge all
                        bank_active[0] <= 1'b0;
                        bank_active[1] <= 1'b0;
                        bank_active[2] <= 1'b0;
                        bank_active[3] <= 1'b0;
                    end else begin
                        bank_active[ba] <= 1'b0;
                    end
                end

                CMD_WR: begin
                    if (bank_active[ba]) begin
                        if (!dqm[0]) mem[get_mem_addr(ba, active_row[ba], addr[7:0])][7:0]   <= dq[7:0];
                        if (!dqm[1]) mem[get_mem_addr(ba, active_row[ba], addr[7:0])][15:8]  <= dq[15:8];
                        if (!dqm[2]) mem[get_mem_addr(ba, active_row[ba], addr[7:0])][23:16] <= dq[23:16];
                        if (!dqm[3]) mem[get_mem_addr(ba, active_row[ba], addr[7:0])][31:24] <= dq[31:24];
                    end
                    if (addr[10]) bank_active[ba] <= 1'b0; // Auto-precharge
                end

                CMD_RD: begin
                    if (bank_active[ba]) begin
                        read_pipe_0  <= mem[get_mem_addr(ba, active_row[ba], addr[7:0])];
                        read_valid_0 <= 1'b1;
                        burst_remain <= (mode_reg[2:0] == 3'b010) ? 3'd3 : 3'd0;
                        burst_ba     <= ba;
                        burst_row    <= active_row[ba];
                        burst_col    <= addr[7:0] + 8'd1;
                    end else begin
                        read_pipe_0  <= 32'hDEADBEEF;
                        read_valid_0 <= 1'b1;
                        burst_remain <= 3'd0;
                    end
                    if (addr[10]) bank_active[ba] <= 1'b0; // Auto-precharge
                end

                default: begin
                    if (burst_remain > 3'd0) begin
                        read_pipe_0  <= mem[get_mem_addr(burst_ba, burst_row, burst_col)];
                        read_valid_0 <= 1'b1;
                        burst_remain <= burst_remain - 3'd1;
                        burst_col    <= burst_col + 8'd1;
                    end else begin
                        read_valid_0 <= 1'b0;
                    end
                end
            endcase
        end else begin
            if (burst_remain > 3'd0) begin
                read_pipe_0  <= mem[get_mem_addr(burst_ba, burst_row, burst_col)];
                read_valid_0 <= 1'b1;
                burst_remain <= burst_remain - 3'd1;
                burst_col    <= burst_col + 8'd1;
            end else begin
                read_valid_0 <= 1'b0;
            end
        end

        // CAS latency pipeline: stage 0 -> stage 1 -> DQ
        read_pipe_1  <= read_pipe_0;
        read_valid_1 <= read_valid_0;
    end

endmodule
