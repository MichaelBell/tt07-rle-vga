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
    input  logic       next_row,
    input  logic       next_pixel,
    output logic [5:0] colour,

    input  logic       half_frame_rate,

    output logic [1:0] save_addr,
    output logic [1:0] load_addr,
    output logic       clear_addr
);

    logic [9:0] run_length;
    logic start;
    logic read_next_r;
    logic frame_counter;
    logic [8:0] repeat_count;

    assign stop_data = (run_length == 10'h3ff) || (|load_addr);
    assign read_next = read_next_r && !stop_data;

    assign save_addr[0] = next_frame && frame_counter;
    assign load_addr[0] = next_frame && !frame_counter;

    assign save_addr[1] = next_row;
    assign load_addr[1] = (run_length[9:4] == 6'h3e) && repeat_count != 1;

    always_ff @(posedge clk) begin
        if (!rstn) begin
            read_next_r <= 0;
            run_length <= 10'h3ff;
            start <= 0;
            colour <= 0;
            frame_counter <= 1;
            clear_addr <= 0;
            repeat_count <= 0;
        end else begin
            read_next_r <= 0;

            if (run_length == 10'h3ff) begin
                run_length <= 1;
                start <= 1;
                colour <= 0;
                frame_counter <= 1;
                clear_addr <= 1;
            end
            else if (start) begin
                if (run_length[0]) begin
                    read_next_r <= 1;
                    clear_addr <= 1;
                    run_length[0] <= 0;
                end else if (next_frame && data_ready) begin
                    run_length <= data[15:6];
                    colour <= data[5:0];
                    clear_addr <= 0;
                    read_next_r <= 1;
                    start <= 0;
                    frame_counter <= !half_frame_rate;
                end
            end
            else begin
                if (next_frame && half_frame_rate) begin
                    frame_counter <= ~frame_counter;
                    if (!frame_counter) begin
                        run_length <= 0;
                        read_next_r <= 1;
                    end
                end else if (run_length == 0) begin
                    if (data_ready) begin
                        run_length <= data[15:6];
                        colour <= data[5:0];
                        read_next_r <= 1;
                    end
                end else if (run_length[9:4] == 6'h3e) begin
                    read_next_r <= repeat_count != 1;
                    run_length <= 0;
                    if (repeat_count >= 1) repeat_count <= repeat_count - 1;
                    else repeat_count <= {run_length[2:0], colour[5:0]};
                end else if (next_pixel) begin
                    if (run_length == 1 && data_ready) begin
                        run_length <= data[15:6];
                        colour <= data[5:0];
                        read_next_r <= 1;
                    end
                    else begin
                        run_length <= run_length - 1;
                    end
                end
            end
        end
    end

endmodule
