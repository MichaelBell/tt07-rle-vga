/*
 * Copyright (c) 2024 Michael Bell
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_MichaelBell_rle_vga (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  // Bidirs are used for SPI interface
  wire [3:0] qspi_data_in = {uio_in[5:4], uio_in[2:1]};
  wire [3:0] qspi_data_out;
  wire [3:0] qspi_data_oe;
  wire       qspi_clk_out;
  wire       qspi_flash_select;
  wire       qspi_ram_a_select = 1'b1;
  wire       qspi_ram_b_select = 1'b1;
  assign uio_out = {qspi_ram_b_select, qspi_ram_a_select, qspi_data_out[3:2], 
                    qspi_clk_out, qspi_data_out[1:0], qspi_flash_select};
  assign uio_oe = rst_n ? {2'b11, qspi_data_oe[3:2], 1'b1, qspi_data_oe[1:0], 1'b1} : 8'h00;  

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
  wire spi_start_read;
  wire spi_stop_read;
  wire spi_continue_read;
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
    .latency    (ui_in[2:0]),
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
