// =============================================================================
// Module: SDRAM Memory Arbiter & Bus Multiplexer (sdram_arbiter.v)
// Project: Custom FPGA-Based GPU — Woxsen University
// Device: Gowin GW2AR-18C (Sipeed Tang Nano 20K)
// Description:
//   Prioritized memory bus arbiter connecting multiple GPU masters to the
//   shared SDRAM controller:
//     1. Port 0: VGA Scanout Reader (Highest priority - timing critical)
//     2. Port 1: SPI Asset Streaming Loader (cmd_decoder.v OP_LOAD_SPRITE)
//     3. Port 2: 2D Sprite Blitter Engine (blitter.v)
//     4. Port 3: 2D Primitive Rasterizer Engine (rasterizer.v)
//
//   Guarantees atomic memory transactions with zero bus collisions and
//   correct multi-cycle SDRAM busy handshaking.
// =============================================================================

`timescale 1ns / 1ps

module sdram_arbiter (
    input  wire        clk,
    input  wire        reset,

    // Port 0: VGA Scanout Framebuffer Reader (Priority 1)
    input  wire        vga_rd,
    input  wire [22:0] vga_addr,
    output wire [7:0]  vga_rdata,
    output wire [31:0] vga_rdata32,
    output wire        vga_rvalid,
    output wire        vga_ready,

    // Port 1: SPI Asset Streamer (Priority 2)
    input  wire        load_wr,
    input  wire [22:0] load_addr,
    input  wire [7:0]  load_wdata,
    output wire        load_ready,

    // Port 2: Sprite Blitter Engine (Priority 3)
    input  wire        blit_rd,
    input  wire        blit_wr,
    input  wire [22:0] blit_addr,
    input  wire [7:0]  blit_wdata,
    output wire [7:0]  blit_rdata,
    output wire        blit_rvalid,
    output wire        blit_ready,

    // Port 3: Primitive Rasterizer Engine (Priority 4)
    input  wire        rast_wr,
    input  wire        rast_wr32,
    input  wire [22:0] rast_addr,
    input  wire [7:0]  rast_wdata,
    output wire        rast_ready,

    // Shared Interface to sdram_ctrl.v
    output reg         sdram_rd,
    output reg         sdram_wr,
    output reg         sdram_wr32,
    output reg  [22:0] sdram_addr,
    output reg  [7:0]  sdram_din,
    input  wire [7:0]  sdram_dout,
    input  wire [31:0] sdram_dout32,
    input  wire        sdram_data_ready,
    input  wire        sdram_busy
);

    // Grant encoding
    localparam [2:0] GRANT_IDLE = 3'd0;
    localparam [2:0] GRANT_VGA  = 3'd1;
    localparam [2:0] GRANT_LOAD = 3'd2;
    localparam [2:0] GRANT_BLIT = 3'd3;
    localparam [2:0] GRANT_RAST = 3'd4;

    localparam [1:0] S_IDLE = 2'd0;
    localparam [1:0] S_BUSY = 2'd1;

    reg [1:0] arb_state;
    reg [2:0] active_grant;
    reg       busy_seen;

    // A ready signal is an *acceptance*, not a hint that the SDRAM might be
    // idle.  The old implementation raised ready on every port at once.  A
    // lower-priority requester could therefore see ready, emit a one-cycle
    // request, lose arbitration to VGA, and wait forever for a response.
    //
    // Requesters hold their valid signal and address stable until their own
    // ready is asserted.  Exactly one ready can be high in a cycle.
    wire can_accept = (arb_state == S_IDLE) && !sdram_busy;
    wire sel_vga  = vga_rd;
    wire sel_load = !sel_vga && load_wr;
    wire sel_blit = !sel_vga && !sel_load && (blit_rd || blit_wr);
    wire sel_rast = !sel_vga && !sel_load && !sel_blit && rast_wr;

    assign vga_ready  = can_accept && sel_vga;
    assign load_ready = can_accept && sel_load;
    assign blit_ready = can_accept && sel_blit;
    assign rast_ready = can_accept && sel_rast;

    // Route read data and valid strobes based on active grant
    assign vga_rdata   = sdram_dout;
    assign vga_rdata32 = sdram_dout32;
    assign vga_rvalid  = (active_grant == GRANT_VGA)  ? sdram_data_ready : 1'b0;

    assign blit_rdata  = sdram_dout;
    assign blit_rvalid = (active_grant == GRANT_BLIT) ? sdram_data_ready : 1'b0;

    always @(posedge clk) begin
        if (reset) begin
            arb_state    <= S_IDLE;
            active_grant <= GRANT_IDLE;
            busy_seen    <= 1'b0;
            sdram_rd     <= 1'b0;
            sdram_wr     <= 1'b0;
            sdram_wr32   <= 1'b0;
            sdram_addr   <= 23'd0;
            sdram_din    <= 8'd0;
        end else begin
            // Strobes are strictly 1-cycle pulses
            sdram_rd   <= 1'b0;
            sdram_wr   <= 1'b0;
            sdram_wr32 <= 1'b0;

            case (arb_state)
                S_IDLE: begin
                    busy_seen <= 1'b0;
                    if (!sdram_busy) begin
                        if (sel_vga) begin
                            active_grant <= GRANT_VGA;
                            sdram_rd     <= 1'b1;
                            sdram_addr   <= vga_addr;
                            arb_state    <= S_BUSY;
                        end else if (sel_load) begin
                            active_grant <= GRANT_LOAD;
                            sdram_wr     <= 1'b1;
                            sdram_addr   <= load_addr;
                            sdram_din    <= load_wdata;
                            arb_state    <= S_BUSY;
                        end else if (sel_blit) begin
                            active_grant <= GRANT_BLIT;
                            sdram_rd     <= blit_rd;
                            sdram_wr     <= blit_wr;
                            sdram_addr   <= blit_addr;
                            sdram_din    <= blit_wdata;
                            arb_state    <= S_BUSY;
                        end else if (sel_rast) begin
                            active_grant <= GRANT_RAST;
                            sdram_wr     <= !rast_wr32;
                            sdram_wr32   <= rast_wr32;
                            sdram_addr   <= rast_addr;
                            sdram_din    <= rast_wdata;
                            arb_state    <= S_BUSY;
                        end else begin
                            active_grant <= GRANT_IDLE;
                        end
                    end else begin
                        active_grant <= GRANT_IDLE;
                    end
                end

                S_BUSY: begin
                    if (sdram_busy) begin
                        busy_seen <= 1'b1;
                    end

                    // Complete transaction once SDRAM controller finishes
                    if (busy_seen && !sdram_busy) begin
                        arb_state    <= S_IDLE;
                        active_grant <= GRANT_IDLE;
                    end
                end

                default: arb_state <= S_IDLE;
            endcase
        end
    end

endmodule
