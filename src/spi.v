/* Copyright 2023-2024 (c) Michael Bell
   SPDX-License-Identifier: Apache-2.0

   A simple SPI flash controller
   
   To perform a read:
   - Set addr_in and set start_read high for 1 cycle
   - Wait for busy to go low
   - The read data is now available on data_out

   If stop_read is high when the read finishes or at any point thereafter,
   the CS is released and a new read can be performed as above.
   If stop_read is held low, then continue_read can be pulsed high to
   read the next word.

   If the controller is configured to transfer multiple bytes, then
   note that the word transferred in data_out is in big
   endian order, i.e. the byte with the lowest address is aligned to 
   the MSB of the word. 
   */

`default_nettype none

module spi_flash_controller #(parameter DATA_WIDTH_BYTES=4, parameter ADDR_BITS=16) (
    input clk,
    input rstn,

    // External SPI interface
    input  spi_miso,
    output spi_select,
    output spi_clk_out,
    output spi_mosi,

    // Configuration
    input [2:0] latency,

    // Internal interface for reading data
    input [ADDR_BITS-1:0]           addr_in,
    input                           start_read,
    input                           stop_read,
    input                           continue_read,
    output [DATA_WIDTH_BYTES*8-1:0] data_out,
    output                          busy
);

`define max(a, b) (a > b) ? a : b

    localparam DATA_WIDTH_BITS = DATA_WIDTH_BYTES * 8;
    localparam BITS_REM_BITS = $clog2(`max(DATA_WIDTH_BITS,ADDR_BITS));

    localparam FSM_IDLE = 3;
    localparam FSM_CMD  = 4;
    localparam FSM_ADDR = 5;
    localparam FSM_DUMMY = 6;
    localparam FSM_DATA = 7;
    localparam FSM_LAT1 = 0;
    localparam FSM_LAT2 = 1;
    localparam FSM_HOLD = 2;

    reg [2:0] fsm_state;
    reg [3:0] spi_miso_buf_n;
    reg [3:0] spi_miso_buf_p;
    reg [ADDR_BITS-1:0]       addr;
    reg [DATA_WIDTH_BITS-1:0] data;
    reg [BITS_REM_BITS-1:0] bits_remaining;

    assign data_out = data;
    assign busy = !fsm_state[1] || fsm_state[2];

    always @(posedge clk) begin
        if (!rstn) begin
            fsm_state <= FSM_IDLE;
            bits_remaining <= 0;
        end else begin
            if (fsm_state == FSM_IDLE) begin
                if (start_read) begin
                    fsm_state <= FSM_CMD;
                    bits_remaining <= 8-1;
                end
            end else if (fsm_state == FSM_HOLD) begin
                if (stop_read) fsm_state <= FSM_IDLE;
                if (continue_read) begin
                    fsm_state <= FSM_DUMMY;
                    bits_remaining <= 3-1;
                end
            end else begin
                if (bits_remaining == 0) begin
                    fsm_state <= fsm_state + 1;
                    if (fsm_state == FSM_CMD)        bits_remaining <= ADDR_BITS-1;
                    else if (fsm_state == FSM_ADDR)  bits_remaining <= 3-1;
                    else if (fsm_state == FSM_DUMMY) bits_remaining <= DATA_WIDTH_BITS-4;
                    else if (fsm_state == FSM_LAT1)  bits_remaining <= 0;
                    else if (fsm_state == FSM_LAT2)  bits_remaining <= 0;
                end else begin
                    bits_remaining <= bits_remaining - 1;
                end
            end
        end
    end

    always @(posedge clk) begin
        if (fsm_state == FSM_IDLE && start_read) begin
            addr <= addr_in;
        end else if (fsm_state == FSM_ADDR) begin
            addr <= {addr[ADDR_BITS-2:0], 1'b0};
        end
    end

    always @(negedge clk) begin
        spi_miso_buf_n <= {spi_miso_buf_n[2:0], spi_miso};
    end

    always @(posedge clk) begin
        spi_miso_buf_p <= {spi_miso_buf_p[2:0], spi_miso};
    end

    wire spi_miso_in = latency[0] ? spi_miso_buf_p[2'b01 - latency[2:1]] : spi_miso_buf_n[2'b10 - latency[2:1]];

    always @(posedge clk) begin
        if (busy) begin
            data <= {data[DATA_WIDTH_BITS-2:0], spi_miso_in};
        end
    end

    assign spi_select = fsm_state == FSM_IDLE;
    assign spi_clk_out = !clk && fsm_state[2];

    assign spi_mosi = fsm_state == FSM_CMD  ? (bits_remaining[2:1] == 2'b00) :
                      fsm_state == FSM_ADDR ? addr[ADDR_BITS-1] :
                                              1'b0;

endmodule
