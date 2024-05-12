/*
 * Copyright (c) 2024 Michael Bell
 * SPDX-License-Identifier: Apache-2.0
 */

`define default_netname none

module rle_vga_top (
        input clk,
        input rst_n,

        inout flash_cs,
        inout [3:0] sd,
        inout sck,
        inout ram_a_cs,
        inout ram_b_cs,

        input [7:0] ui_in,
        output [7:0] uo_out

);
    localparam CLOCK_FREQ = 25_000_000;

    // Register the reset on the negative edge of clock for safety.
    // This also allows the option of async reset in the design, which might be preferable in some cases
    reg rst_reg_n;
    always @(negedge clk) rst_reg_n <= rst_n;

    // Bidirs are used for SPI interface
    wire [3:0] qspi_data_in;
    wire [3:0] qspi_data_out;
    wire [3:0] qspi_data_oe;
    wire       qspi_clk_out;
    wire       qspi_flash_select;
    wire       qspi_ram_a_select = 1;
    wire       qspi_ram_b_select = 1;

    SB_IO #(
//		.PIN_TYPE(6'b 1101_00),  // Registered in, out and oe
		.PIN_TYPE(6'b 1010_01),
		.PULLUP(1'b 0)
    ) qspi_data [3:0] (
		.PACKAGE_PIN(sd),
        .OUTPUT_CLK(clk),
        .INPUT_CLK(clk),
		.OUTPUT_ENABLE(qspi_data_oe),
		.D_OUT_0(qspi_data_out),
		.D_IN_0(qspi_data_in)
	);
    SB_IO #(
//		.PIN_TYPE(6'b 1001_01),  // Registered out only
		.PIN_TYPE(6'b 1010_01),
		.PULLUP(1'b 0)
    ) qspi_pins [3:0] (
		.PACKAGE_PIN({flash_cs, sck, ram_a_cs, ram_b_cs}),
        .OUTPUT_CLK(clk),
		.OUTPUT_ENABLE({4{rst_n}}),
		.D_OUT_0({qspi_flash_select, qspi_clk_out, qspi_ram_a_select, qspi_ram_b_select})
	);

  wire vga_blank;
  wire next_frame;

  vga i_vga (
    .clk        (clk),
    .reset_n    (rst_n),
    .hsync      (uo_out[7]),
    .vsync      (uo_out[3]),
    .blank      (vga_blank),
    .vsync_pulse(next_frame)
  );

  wire [15:0] spi_data;
  wire spi_busy;
  reg spi_start_read;
  wire spi_stop_read;
  reg spi_continue_read;
  reg [23:1] addr;

  spi_flash_controller #(
    .DATA_WIDTH_BYTES(2),
    .ADDR_BITS(24)
  ) i_spi (
    .clk        (clk),
    .rstn       (rst_n),
    .spi_data_in(qspi_data_in),
    .spi_data_out(qspi_data_out),
    .spi_data_oe(qspi_data_oe),
    .spi_select (qspi_flash_select),
    .spi_clk_out(qspi_clk_out),
    .latency    (3'b000),
    .addr_in    ({addr, 1'b0}),
    .start_read (spi_start_read),
    .stop_read  (spi_stop_read),
    .continue_read(spi_continue_read),
    .data_out   (spi_data),
    .busy       (spi_busy)
  );

  reg spi_started;
  wire spi_data_ready = spi_started && !spi_busy && !spi_start_read && !spi_continue_read;
  wire read_next;
  wire [5:0] video_colour;

  reg [23:1] addr_saved;
  wire save_addr;
  wire load_addr;
  wire clear_addr;

  rle_video i_video (
    .clk        (clk),
    .rstn       (rst_n),
    .read_next  (read_next),
    .stop_data  (spi_stop_read),
    .data_ready (spi_data_ready),
    .data       (spi_data),
    .next_frame (next_frame),
    .next_pixel (!vga_blank),
    .colour     (video_colour),
    .save_addr  (save_addr),
    .load_addr  (load_addr),
    .clear_addr (clear_addr)
  );

  always @(posedge clk) begin
    if (!rst_n) begin
      spi_started <= 0;
    end else begin

      if (spi_stop_read) 
        spi_started <= 0;
      else if (read_next) begin
        spi_started <= 1;
      end
    end
  end

  always @(posedge clk) begin
    if (!rst_n || clear_addr) begin
      addr <= 0;
      addr_saved <= 0;
    end else begin
      if (save_addr) addr_saved <= addr - 1;
      else if (load_addr) addr <= addr_saved;
      else if (spi_started && read_next) addr <= addr + 1;
    end
  end

  assign spi_continue_read = read_next && spi_started;
  assign spi_start_read = read_next && !spi_started;

  assign uo_out[0] = vga_blank ? 1'b0 : video_colour[5];
  assign uo_out[1] = vga_blank ? 1'b0 : video_colour[3];
  assign uo_out[2] = vga_blank ? 1'b0 : video_colour[1];
  assign uo_out[4] = vga_blank ? 1'b0 : video_colour[4];
  assign uo_out[5] = vga_blank ? 1'b0 : video_colour[2];
  assign uo_out[6] = vga_blank ? 1'b0 : video_colour[0];

endmodule
