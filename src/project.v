/*
 * Copyright (c) 2024 Michael Bell
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_example (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  assign uio_oe  = 8'b11001011;
  assign uio_out[2] = 0;
  assign uio_out[7:4] = 4'b1100;

  wire vga_blank;
  wire next_frame;

  vga i_vga (
    .clk        (clk),
    .reset_n    (rst_n),
    .hsync      (uo_out[7]),
    .vsync      (uo_out[3]),
    .blank      (vga_blank),
    .next_frame (next_frame)
  );

  wire [15:0] spi_data;
  wire spi_busy;
  reg spi_start_read;
  wire spi_stop_read;
  reg spi_continue_read;

  spi_flash_controller #(
    .DATA_WIDTH_BYTES(2),
    .ADDR_BITS(24)
  ) i_spi (
    .clk        (clk),
    .rstn       (rst_n),
    .spi_select (uio_out[0]),
    .spi_mosi   (uio_out[1]),
    .spi_miso   (uio_in[2]),
    .spi_clk_out(uio_out[3]),
    .latency    (ui_in[2:0]),
    .addr_in    (24'h0),
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

  rle_video i_video (
    .clk        (clk),
    .rstn       (rst_n),
    .read_next  (read_next),
    .stop_data  (spi_stop_read),
    .data_ready (spi_data_ready),
    .data       (spi_data),
    .next_frame (next_frame),
    .next_pixel (!vga_blank),
    .colour     (video_colour)
  );

  always @(posedge clk) begin
    if (!rst_n) begin
      spi_started <= 0;
      spi_start_read <= 0;
      spi_continue_read <= 0;
    end else begin
      spi_start_read <= 0;
      spi_continue_read <= 0;

      if (spi_stop_read) 
        spi_started <= 0;
      else if (read_next) begin
        if (spi_started) spi_continue_read <= 1;
        else spi_start_read <= 1;

        spi_started <= 1;
      end
    end
  end

  assign uo_out[0] = vga_blank ? 1'b0 : video_colour[5];
  assign uo_out[1] = vga_blank ? 1'b0 : video_colour[3];
  assign uo_out[2] = vga_blank ? 1'b0 : video_colour[1];
  assign uo_out[4] = vga_blank ? 1'b0 : video_colour[4];
  assign uo_out[5] = vga_blank ? 1'b0 : video_colour[2];
  assign uo_out[6] = vga_blank ? 1'b0 : video_colour[0];

endmodule
