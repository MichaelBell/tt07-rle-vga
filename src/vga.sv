// SPDX-FileCopyrightText: © 2022 Leo Moser <leo.moser@pm.me>, 2024 Michael Bell
// SPDX-License-Identifier: Apache-2.0

`default_nettype none

    /*
        Default parameters are VGA 640x480 @ 60 Hz
        clock = 25.175 MHz
    */

module vga #(
    parameter WIDTH=640,    // display width
    parameter HEIGHT=480,   // display height
    parameter HFRONT=16,    // horizontal front porch
    parameter HSYNC=96,     // horizontal sync
    parameter HBACK=48,     // horizontal back porch
    parameter VFRONT=10,    // vertical front porch
    parameter VSYNC=2,      // vertical sync
    parameter VBACK=33      // vertical back porch
)(
    input  logic clk,       // clock
    input  logic reset_n,   // reset
    output logic hsync,     // 1'b1 if in hsync region
    output logic vsync,     // 1'b1 if in vsync region
    output logic blank,     // 1'b1 if in blank region
    output logic hsync_pulse, // 1'b1 for one clock in hsync
    output logic vsync_pulse  // 1'b1 for one clock in vsync
);

    localparam HTOTAL = WIDTH + HFRONT + HSYNC + HBACK;
    localparam VTOTAL = HEIGHT + VFRONT + VSYNC + VBACK;

    logic signed [$clog2(HTOTAL) : 0] x_pos;
    logic signed [$clog2(VTOTAL) : 0] y_pos;

    /* Horizontal and Vertical Timing */
    
    logic hblank;
    logic vblank;
    logic vblank_w;
    logic next_row;
    logic next_frame;
     
    // Horizontal timing
    timing #(
        .RESOLUTION     (WIDTH),
        .FRONT_PORCH    (HFRONT-1),
        .SYNC_PULSE     (HSYNC),
        .BACK_PORCH     (HBACK+1),
        .TOTAL          (HTOTAL),
        .POLARITY       (1'b0)
    ) timing_hor (
        .clk        (clk),
        .enable     (1'b1),
        .reset_n    (reset_n),
        .sync       (hsync),
        .blank      (hblank),
        .next       (next_row),
        .counter    (x_pos)
    );

    // Vertical timing
    timing #(
        .RESOLUTION     (HEIGHT),
        .FRONT_PORCH    (VFRONT),
        .SYNC_PULSE     (VSYNC),
        .BACK_PORCH     (VBACK),
        .TOTAL          (VTOTAL),
        .POLARITY       (1'b0)
    ) timing_ver (
        .clk        (clk),
        .enable     (x_pos == WIDTH - 2),
        .reset_n    (reset_n),
        .sync       (vsync),
        .blank      (vblank_w),
        .next       (next_frame),
        .counter    (y_pos)
    );

    assign blank = hblank || vblank;
    assign vsync_pulse = next_row && (y_pos == -VBACK - VSYNC);
    assign hsync_pulse = x_pos == -HBACK;

    always_ff @(posedge clk) vblank <= vblank_w;

endmodule
