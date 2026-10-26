`timescale 1ns/1ps

// Applies the indexed subset through the existing cfg handshake. A table item
// stays stable through transport AND its post-delay. The last item completes
// on transport_done, since the original init never raises ready after last.
module ov5640_known_config_sequencer #(
    parameter integer SYS_CLK_HZ = 100000000
) (
    input wire clk, rst_n, start,
    output reg [5:0] table_index,
    input wire table_valid, table_last,
    input wire [15:0] table_delay_ms,
    output wire cfg_valid,
    input wire cfg_ready, transport_done, transport_error,
    output reg busy, done, error_flag
);
    localparam [2:0] IDLE=0, OFFER=1, WAIT_LOW=2, WAIT_COMPLETE=3,
                     DELAY=4, FINISHED=5, FAILED=6;
    localparam [63:0] CLOCK_HZ = SYS_CLK_HZ;
    reg [2:0] state;
    reg [63:0] delay_count;
    reg last_latched;
    // 64-bit intermediates avoid overflow at the 300 ms entry even at 100MHz.
    wire [63:0] delay_cycles =
        (CLOCK_HZ * table_delay_ms + 64'd999) / 64'd1000;
    assign cfg_valid = (state == OFFER) && table_valid && !transport_error;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            table_index <= 0;
            delay_count <= 0;
            last_latched <= 0;
            busy <= 0;
            done <= 0;
            error_flag <= 0;
        end else if (transport_error && busy) begin
            state <= FAILED;
            busy <= 0;
            error_flag <= 1;
        end else begin
            case (state)
                IDLE: if (start) begin
                    table_index <= 0;
                    busy <= 1;
                    done <= 0;
                    error_flag <= 0;
                    state <= OFFER;
                end
                OFFER: if (!table_valid) begin
                    busy <= 0;
                    error_flag <= 1;
                    state <= FAILED;
                end else if (cfg_ready) begin
                    last_latched <= table_last;
                    state <= WAIT_LOW;
                end
                WAIT_LOW: if (!cfg_ready) state <= WAIT_COMPLETE;
                WAIT_COMPLETE: if ((last_latched && transport_done) ||
                                   (!last_latched && cfg_ready)) begin
                    delay_count <= delay_cycles;
                    state <= DELAY;
                end
                DELAY: if (delay_count > 1) begin
                    delay_count <= delay_count - 1'b1;
                end else if (last_latched) begin
                    busy <= 0;
                    done <= 1;
                    state <= FINISHED;
                end else begin
                    table_index <= table_index + 1'b1;
                    state <= OFFER;
                end
                FINISHED: done <= 1;
                FAILED: error_flag <= 1;
                default: begin busy <= 0; error_flag <= 1; state <= FAILED; end
            endcase
        end
    end
endmodule
