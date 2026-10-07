// =============================================================================
// Module: SDRAM Controller (Adapted from nand2mario's open-source controller)
// Project: Custom FPGA-Based GPU — Woxsen University
// Device: Gowin GW2AR-18C (Sipeed Tang Nano 20K)
// Description:
//   Byte-addressable, low-latency SDR SDRAM controller for the embedded 64Mbit
//   SIP SDRAM on the Tang Nano 20K FPGA (2048 rows × 256 words × 4 banks × 32 bits = 8MB).
//
//   Features & Performance:
//     - 23-bit byte addressing (addr[22:0] covers all 8MB)
//     - Read latency: 4 clock cycles (CAS latency = 2)
//     - Write cycle: 5 clock cycles
//     - Automatic precharge on every read/write command (eliminates row tracking)
//     - DQM byte masking: supports single-byte writes to 32-bit memory words
//     - Dual outputs: 8-bit byte output (dout) and full 32-bit word output (dout32)
//     - Fully registered read data: latches DQ bus on the exact CAS cycle
//     - Parameterized timing and simulation speedup mode
// =============================================================================

`timescale 1ns / 1ps

module sdram_ctrl #(
    parameter FREQ           = 27_000_000, // Controller clock frequency in Hz
    parameter DATA_WIDTH     = 32,
    parameter ROW_WIDTH      = 11,         // 2K rows
    parameter COL_WIDTH      = 8,          // 256 words per row (1024 bytes/row)
    parameter BANK_WIDTH     = 2,          // 4 banks
    parameter SIM_INIT_WAIT  = 0,          // 1: Fast init for simulation; 0: Full 200us hardware wait

    // Timing parameters in clock cycles (at <= 66.7 MHz, clock period >= 15ns)
    parameter [3:0] CAS      = 4'd2,       // CAS Latency (2 cycles)
    parameter [3:0] T_WR     = 4'd2,       // Write recovery time
    parameter [3:0] T_MRD    = 4'd2,       // Mode register set delay
    parameter [3:0] T_RP     = 4'd1,       // Precharge to active
    parameter [3:0] T_RCD    = 4'd1,       // Active to read/write
    parameter [3:0] T_RC     = 4'd4        // Refresh/active to refresh/active
)(
    // -------------------------------------------------------------------------
    // Logic / Host Interface
    // -------------------------------------------------------------------------
    input  wire                   clk,        // Controller logic clock
    input  wire                   clk_sdram,  // 180-degree phase-shifted clock for SDRAM pad
    input  wire                   resetn,     // Active-low synchronous reset
    input  wire                   rd,         // Read strobe (pulse 1 cycle)
    input  wire                   wr,         // Write strobe (pulse 1 cycle)
    input  wire                   wr32,       // 32-bit word write strobe (pulse 1 cycle)
    input  wire                   refresh,    // Auto-refresh strobe (pulse 1 cycle every ~15us)
    input  wire [22:0]            addr,       // 23-bit byte address (0 to 8,388,607)
    input  wire [7:0]             din,        // 8-bit data input to write
    output wire [7:0]             dout,       // 8-bit data output (latched until next read)
    output wire [DATA_WIDTH-1:0]  dout32,     // Full 32-bit data output (latched)
    output reg                    data_ready, // High for 1 cycle when read data is valid
    output reg                    busy,       // High when busy executing a command

    // -------------------------------------------------------------------------
    // Physical SDRAM Chip Interface (Gowin GW2AR-18 Embedded SIP SDRAM)
    // -------------------------------------------------------------------------
    inout  wire [DATA_WIDTH-1:0]  SDRAM_DQ,   // 32-bit bidirectional data bus
    output reg  [ROW_WIDTH-1:0]   SDRAM_A,    // 11-bit multiplexed address bus
    output reg  [BANK_WIDTH-1:0]  SDRAM_BA,   // 2-bit bank address (4 banks)
    output wire                   SDRAM_nCS,  // Chip select (always active 0)
    output reg                    SDRAM_nRAS, // Row address strobe
    output reg                    SDRAM_nCAS, // Column address strobe
    output reg                    SDRAM_nWE,  // Write enable
    output wire                   SDRAM_CLK,  // SDRAM clock (phase-shifted)
    output wire                   SDRAM_CKE,  // Clock enable (always active 1)
    output reg  [3:0]             SDRAM_DQM   // Byte data mask (active-high mask)
);

    // =========================================================================
    // Tri-State DQ Bus Control
    // =========================================================================
    reg                  dq_oen; // 0 = drive output, 1 = high-Z input
    reg [DATA_WIDTH-1:0] dq_out;
    assign SDRAM_DQ  = dq_oen ? 32'bzzzz_zzzz_zzzz_zzzz_zzzz_zzzz_zzzz_zzzz : dq_out;
    wire [DATA_WIDTH-1:0] dq_in = SDRAM_DQ;

    // =========================================================================
    // Read Data Latching into Flip-Flops
    // =========================================================================
    reg [1:0]            byte_off;      // Byte offset within 32-bit word (addr[1:0])
    reg [DATA_WIDTH-1:0] read_word0;    // Holds Word 0 of the burst (stable for single byte/word read)
    reg [DATA_WIDTH-1:0] read_data_reg; // Holds current burst word for 32-bit streaming

    wire [7:0] byte_out = (byte_off == 2'd0) ? read_word0[7:0]   :
                          (byte_off == 2'd1) ? read_word0[15:8]  :
                          (byte_off == 2'd2) ? read_word0[23:16] : read_word0[31:24];

    assign dout   = byte_out;
    assign dout32 = data_ready ? read_data_reg : read_word0;

    // Static SDRAM control lines
    assign SDRAM_CLK = clk_sdram;
    assign SDRAM_CKE = 1'b1;
    assign SDRAM_nCS = 1'b0; // Embedded SDRAM only has one chip

    // =========================================================================
    // SDRAM Commands: {nRAS, nCAS, nWE}
    // =========================================================================
    localparam CMD_SetModeReg  = 3'b000;
    localparam CMD_AutoRefresh = 3'b001;
    localparam CMD_PreCharge   = 3'b010;
    localparam CMD_BankActivate= 3'b011;
    localparam CMD_Write       = 3'b100;
    localparam CMD_Read        = 3'b101;
    localparam CMD_NOP         = 3'b111;

    // Mode Register: Burst length = 4, Sequential, CAS Latency = CAS[2:0], M9=1 (Single Location Write)
    localparam [2:0]  BURST_LEN  = 3'b010; // Burst length = 4
    localparam        BURST_TYPE = 1'b0;   // Sequential
    localparam [10:0] MODE_REG   = {1'b0, 1'b1, 2'b00, CAS[2:0], BURST_TYPE, BURST_LEN};

    // =========================================================================
    // Controller States
    // =========================================================================
    localparam STATE_INIT    = 3'd0;
    localparam STATE_CONFIG  = 3'd1;
    localparam STATE_IDLE    = 3'd2;
    localparam STATE_READ    = 3'd3;
    localparam STATE_WRITE   = 3'd4;
    localparam STATE_REFRESH = 3'd5;

    reg [2:0]  state;
    reg [3:0]  cycle;
    reg [7:0]  din_buf;
    reg        wr32_buf;
    reg [22:0] addr_buf;
    reg        cfg_now;

    // =========================================================================
    // Main SDRAM State Machine
    // =========================================================================
    always @(posedge clk) begin
        cycle <= (cycle == 4'd15) ? 4'd15 : cycle + 4'd1;

        // Default: NOP command on every cycle
        {SDRAM_nRAS, SDRAM_nCAS, SDRAM_nWE} <= CMD_NOP;

        case (state)
            // -----------------------------------------------------------------
            // STATE_INIT: Wait for power-on delay (200us) before config
            // -----------------------------------------------------------------
            STATE_INIT: begin
                if (cfg_now) begin
                    state <= STATE_CONFIG;
                    cycle <= 4'd0;
                end
            end

            // -----------------------------------------------------------------
            // STATE_CONFIG: Standard SDRAM initialization sequence:
            //   Precharge All -> AutoRefresh 1 -> AutoRefresh 2 -> SetModeReg
            // -----------------------------------------------------------------
            STATE_CONFIG: begin
                if (cycle == 4'd0) begin
                    // Precharge all banks
                    {SDRAM_nRAS, SDRAM_nCAS, SDRAM_nWE} <= CMD_PreCharge;
                    SDRAM_A[10] <= 1'b1; // A10 = 1 means all banks
                end else if (cycle == T_RP) begin
                    // 1st Auto-Refresh
                    {SDRAM_nRAS, SDRAM_nCAS, SDRAM_nWE} <= CMD_AutoRefresh;
                end else if (cycle == T_RP + T_RC) begin
                    // 2nd Auto-Refresh
                    {SDRAM_nRAS, SDRAM_nCAS, SDRAM_nWE} <= CMD_AutoRefresh;
                end else if (cycle == T_RP + T_RC + T_RC) begin
                    // Program Mode Register
                    {SDRAM_nRAS, SDRAM_nCAS, SDRAM_nWE} <= CMD_SetModeReg;
                    SDRAM_A <= MODE_REG;
                end else if (cycle == T_RP + T_RC + T_RC + T_MRD) begin
                    // Initialization complete!
                    state <= STATE_IDLE;
                    busy  <= 1'b0;
                end
            end

            // -----------------------------------------------------------------
            // STATE_IDLE: Await Read, Write, or Refresh commands
            // -----------------------------------------------------------------
            STATE_IDLE: begin
                if (rd || wr || wr32) begin
                    // Bank Activate: activate row in selected bank
                    {SDRAM_nRAS, SDRAM_nCAS, SDRAM_nWE} <= CMD_BankActivate;
                    // Address mapping:
                    // addr[22:21] = Bank (4 banks)
                    // addr[20:10] = Row  (2048 rows)
                    // addr[9:2]   = Col  (256 32-bit words)
                    // addr[1:0]   = Byte offset within 32-bit word
                    SDRAM_BA <= addr[ROW_WIDTH + COL_WIDTH + BANK_WIDTH - 1 + 2 : ROW_WIDTH + COL_WIDTH + 2];
                    SDRAM_A  <= addr[ROW_WIDTH + COL_WIDTH - 1 + 2 : COL_WIDTH + 2];
                    state    <= rd ? STATE_READ : STATE_WRITE;
                    addr_buf <= addr;
                    if (wr || wr32) begin
                        din_buf  <= din;
                        wr32_buf <= wr32;
                    end
                    cycle    <= 4'd1;
                    busy     <= 1'b1;
                end else if (refresh) begin
                    // Auto-Refresh
                    {SDRAM_nRAS, SDRAM_nCAS, SDRAM_nWE} <= CMD_AutoRefresh;
                    state <= STATE_REFRESH;
                    cycle <= 4'd1;
                    busy  <= 1'b1;
                end
            end

            // -----------------------------------------------------------------
            // STATE_READ: Read sequence with Auto-Precharge (BL=4 Burst Read)
            // -----------------------------------------------------------------
            STATE_READ: begin
                if (cycle == T_RCD) begin
                    {SDRAM_nRAS, SDRAM_nCAS, SDRAM_nWE} <= CMD_Read;
                    SDRAM_A[10]  <= 1'b1; // Auto-precharge enabled
                    SDRAM_A[9:0] <= {2'b00, addr_buf[COL_WIDTH - 1 + 2 : 2]}; // Column address
                    SDRAM_DQM    <= 4'b0000;
                    byte_off     <= addr_buf[1:0];
                end else if (cycle == T_RCD + CAS) begin
                    // Latch Word 0: holds data for single byte/word read
                    read_word0    <= dq_in;
                    read_data_reg <= dq_in;
                    data_ready    <= 1'b1;
                end else if (cycle > T_RCD + CAS && cycle <= T_RCD + CAS + 4'd3) begin
                    // Stream burst words (Words 1..3)
                    read_data_reg <= dq_in;
                    data_ready    <= 1'b1;
                end else if (cycle == T_RCD + CAS + 4'd4) begin
                    data_ready    <= 1'b0;
                    busy          <= 1'b0;
                    state         <= STATE_IDLE;
                end
            end

            // -----------------------------------------------------------------
            // STATE_WRITE: Single-byte write sequence with DQM masking
            // -----------------------------------------------------------------
            STATE_WRITE: begin
                if (cycle == T_RCD) begin
                    {SDRAM_nRAS, SDRAM_nCAS, SDRAM_nWE} <= CMD_Write;
                    SDRAM_A[10]  <= 1'b1; // Auto-precharge enabled
                    SDRAM_A[9:0] <= {2'b00, addr_buf[COL_WIDTH - 1 + 2 : 2]}; // Column address
                    // DQM mask: 0 enables byte write, 1 masks (preserves) byte
                    if (wr32_buf) begin
                        SDRAM_DQM <= 4'b0000; // All 4 bytes enabled!
                    end else begin
                        SDRAM_DQM <= (addr_buf[1:0] == 2'd0) ? 4'b1110 :
                                     (addr_buf[1:0] == 2'd1) ? 4'b1101 :
                                     (addr_buf[1:0] == 2'd2) ? 4'b1011 : 4'b0111;
                    end
                    byte_off     <= addr_buf[1:0];
                    dq_out       <= {din_buf, din_buf, din_buf, din_buf};
                    dq_oen       <= 1'b0; // Enable DQ drive
                end else if (cycle == T_RCD + 4'd1) begin
                    dq_oen <= 1'b1; // Turn off DQ drive
                end else if (cycle == T_RCD + T_WR + T_RP) begin
                    busy  <= 1'b0;
                    state <= STATE_IDLE;
                end
            end

            // -----------------------------------------------------------------
            // STATE_REFRESH: Auto-refresh sequence
            // -----------------------------------------------------------------
            STATE_REFRESH: begin
                if (cycle == T_RC) begin
                    busy  <= 1'b0;
                    state <= STATE_IDLE;
                end
            end

            default: state <= STATE_INIT;
        endcase

        // Synchronous Reset
        if (!resetn) begin
            busy          <= 1'b1;
            dq_oen        <= 1'b1; // High-Z
            SDRAM_DQM     <= 4'b0000;
            data_ready    <= 1'b0;
            read_word0    <= 32'd0;
            read_data_reg <= 32'd0;
            wr32_buf      <= 1'b0;
            state         <= STATE_INIT;
            cycle         <= 4'd0;
        end
    end

    // =========================================================================
    // Power-On Delay Counter (200us in hardware, or instant in simulation)
    // =========================================================================
    localparam INIT_COUNT_MAX = (SIM_INIT_WAIT == 1) ? 15'd20 : (FREQ / 1000 * 200 / 1000);

    reg [14:0] rst_cnt;
    reg        rst_done, rst_done_p1;

    always @(posedge clk) begin
        rst_done_p1 <= rst_done;
        cfg_now     <= rst_done && ~rst_done_p1; // Rising edge detector

        if (rst_cnt < INIT_COUNT_MAX) begin
            rst_cnt  <= rst_cnt + 15'd1;
            rst_done <= 1'b0;
        end else begin
            rst_done <= 1'b1;
        end

        if (!resetn) begin
            rst_cnt  <= 15'd0;
            rst_done <= 1'b0;
        end
    end

endmodule
