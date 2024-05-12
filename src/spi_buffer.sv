// SPDX-FileCopyrightText: © 2024 Michael Bell
// SPDX-License-Identifier: Apache-2.0

`default_nettype none

module spi_buffer #(parameter DATA_WIDTH_BYTES=4) (
    input logic clk,
    input logic rstn,

    input  logic                          start_read,
    input  logic                          continue_read,
    input  logic [DATA_WIDTH_BYTES*8-1:0] data_in,
    input  logic                          spi_busy,
    input  logic                          prev_empty,
    output logic [DATA_WIDTH_BYTES*8-1:0] data_out,
    output logic                          empty
);

    logic [DATA_WIDTH_BYTES*8-1:0] fifo;

    assign data_out = empty ? data_in : fifo;

    always_ff @(posedge clk) begin
        if (!rstn) begin
            empty <= 0;
        end else begin
            if (start_read) begin
                empty <= 1;
            end else if (continue_read && !empty) begin
                if (!spi_busy || !prev_empty) fifo <= data_in;
                else empty <= 1;
            end else if (!continue_read && !spi_busy && empty) begin
                empty <= 0;
                fifo <= data_in;
            end
        end
    end

endmodule
