// SPDX-FileCopyrightText: © 2024 Michael Bell
// SPDX-License-Identifier: Apache-2.0

`default_nettype none

module rle_video (
    input logic clk,
    input logic rstn,

    output logic        read_next,
    output logic        stop_data,
    input  logic        data_ready,
    input  logic [15:0] data,

    input  logic       next_frame,
    input  logic       next_pixel,
    output logic [5:0] colour
);

    logic [9:0] run_length;
    logic start;

    assign stop_data = (run_length == 10'h3ff);

    always_ff @(posedge clk) begin
        if (!rstn) begin
            read_next <= 0;
            run_length <= 10'h3ff;
            start <= 0;
            colour <= 0;
        end else begin
            read_next <= 0;

            if (run_length == 10'h3ff) begin
                run_length <= 1;
                start <= 1;
                colour <= 0;
            end
            else if (start) begin
                if (run_length[0]) begin
                    read_next <= 1;
                    run_length[0] <= 0;
                end else if (next_frame && data_ready) begin
                    run_length <= data[15:6];
                    colour <= data[5:0];
                    read_next <= 1;
                    start <= 0;
                end
            end
            else if (run_length == 0) begin
                if (data_ready) begin
                    run_length <= data[15:6];
                    colour <= data[5:0];
                    read_next <= 1;
                end
            end else if (next_pixel) begin
                if (run_length == 1 && data_ready) begin
                    run_length <= data[15:6];
                    colour <= data[5:0];
                    read_next <= 1;
                end
                else begin
                    run_length <= run_length - 1;
                end
            end
        end
    end

endmodule
