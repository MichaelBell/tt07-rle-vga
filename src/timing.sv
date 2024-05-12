// SPDX-FileCopyrightText: © 2022 Leo Moser <leo.moser@pm.me>, 2024 Michael Bell
// SPDX-License-Identifier: Apache-2.0

`default_nettype none

module timing #(
    parameter RESOLUTION=0,   // resolution of the active pixel
    parameter FRONT_PORCH=0,  // number of front porch pixel
    parameter SYNC_PULSE=0,   // number of sync pulse pixel
    parameter BACK_PORCH=0,   // number of back porch pixel
    parameter TOTAL=0,        // everything summed up
    parameter POLARITY=0
)(
    input  logic clk,       // clock
    input  logic enable,    // enable counting
    input  logic reset_n,   // reset counter
    output logic sync,      // 1'b1 if in sync region
    output logic blank,     // 1'b1 if in blank region
    output logic next,      // 1'b1 if max value is reached
    output logic signed [$clog2(TOTAL) : 0] counter // counter value
);

    // Signal to trigger next counter in the chain
    assign next = counter == RESOLUTION - 1 && enable;
    
    // Create the sync signal
    logic sync_tmp;
    assign sync_tmp = (counter >= -SYNC_PULSE - BACK_PORCH) && (counter < -BACK_PORCH);

    always_ff @(posedge clk)
        sync <= POLARITY ? sync_tmp : ~sync_tmp;

    // Blanking
    assign blank = counter < 0;

    // Counter logic
    always_ff @(posedge clk) begin
        if (!reset_n) begin
            counter <= -FRONT_PORCH - SYNC_PULSE - BACK_PORCH;
        end else begin
            if (enable) begin
                counter <= counter + 1;
                if (next) begin
                    counter <= -FRONT_PORCH - SYNC_PULSE - BACK_PORCH;
                end
            end
        end
    end

endmodule
