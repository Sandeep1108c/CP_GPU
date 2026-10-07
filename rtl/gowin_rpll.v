// =============================================================================
// Module: Gowin rPLL Hardware Primitive (27 MHz -> 25.2 MHz)
// Project: Custom FPGA-Based GPU — Woxsen University
// Device: Gowin GW2AR-18C (Sipeed Tang Nano 20K)
// Description:
//   Instantiates the Gowin rPLL hardware silicon primitive.
//   Converts the 27 MHz onboard crystal oscillator into a 25.2 MHz pixel clock.
//   Formula: FCLKOUT = (27 MHz * 14) / (3 * 5) = 25.2 MHz (0.09% error vs 25.175 MHz).
// =============================================================================

`timescale 1ns / 1ps

module gowin_rpll (
    input  wire clkin,          // 27 MHz onboard crystal (Pin 4)
    output wire clkout,         // 25.2 MHz pixel clock for VGA 640x480 (from CLKDIV)
    output wire lock,           // PLL locked indicator
    output wire clkout_serial   // 126.0 MHz 5x serial clock for OSER10
);

    wire gw_gnd;
    assign gw_gnd = 1'b0;
    wire w_serial_clk;

    // =========================================================================
    // Gowin rPLL: 27 MHz -> 126.0 MHz (5x TMDS bit clock)
    // Formula: VCO = (27 MHz / 3) * 70 = 630 MHz (within 400-1200 MHz spec)
    //          CLKOUT = 630 MHz / 5 = 126.0 MHz
    // =========================================================================
    rPLL rpll_inst (
        .CLKOUT(w_serial_clk),
        .LOCK(lock),
        .CLKOUTP(),
        .CLKOUTD(),
        .CLKOUTD3(),
        .RESET(gw_gnd),
        .RESET_P(gw_gnd),
        .CLKIN(clkin),
        .CLKFB(gw_gnd),
        .FBDSEL(6'b0),
        .IDSEL(6'b0),
        .ODSEL(6'b0),
        .PSDA(4'b0),
        .DUTYDA(4'b0),
        .FDLY(4'b0)
    );

    defparam rpll_inst.FCLKIN = "27";
    defparam rpll_inst.DYN_IDIV_SEL = "false";
    defparam rpll_inst.IDIV_SEL = 2;          // Divide by 3 -> 9 MHz PFD
    defparam rpll_inst.DYN_FBDIV_SEL = "false";
    defparam rpll_inst.FBDIV_SEL = 13;        // Multiply by 14
    defparam rpll_inst.DYN_ODIV_SEL = "false";
    defparam rpll_inst.ODIV_SEL = 8;          // Divide by 8 -> 1008 MHz VCO, 126.0 MHz CLKOUT
    defparam rpll_inst.PSDA_SEL = "0000";
    defparam rpll_inst.DYN_DA_EN = "true";
    defparam rpll_inst.DUTYDA_SEL = "1000";
    defparam rpll_inst.CLKOUT_FT_DIR = 1'b1;
    defparam rpll_inst.CLKOUTP_FT_DIR = 1'b1;
    defparam rpll_inst.CLKOUT_DLY_STEP = 0;
    defparam rpll_inst.CLKOUTP_DLY_STEP = 0;
    defparam rpll_inst.CLKFB_SEL = "internal";
    defparam rpll_inst.CLKOUT_BYPASS = "false";
    defparam rpll_inst.CLKOUTP_BYPASS = "false";
    defparam rpll_inst.CLKOUTD_BYPASS = "false";
    defparam rpll_inst.DYN_SDIV_SEL = 2;
    defparam rpll_inst.CLKOUTD_SRC = "CLKOUT";
    defparam rpll_inst.CLKOUTD3_SRC = "CLKOUT";
    defparam rpll_inst.DEVICE = "GW2AR-18C";

    assign clkout_serial = w_serial_clk;

    // =========================================================================
    // Gowin CLKDIV: 126.0 MHz / 5 -> 25.2 MHz (1x TMDS pixel clock)
    // Preserves phase relationship required by OSER10 serializers
    // =========================================================================
    CLKDIV u_clkdiv (
        .RESETN(lock),
        .HCLKIN(w_serial_clk),
        .CLKOUT(clkout),
        .CALIB(1'b0)
    );
    defparam u_clkdiv.DIV_MODE = "5";
    defparam u_clkdiv.GSREN = "false";

endmodule
