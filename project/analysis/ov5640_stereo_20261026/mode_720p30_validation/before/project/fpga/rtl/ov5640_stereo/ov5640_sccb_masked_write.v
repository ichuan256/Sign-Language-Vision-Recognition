`timescale 1ns/1ps

// One camera owns its own read/modify/write context. Pad-independent cores
// start exclusively; low enables merge before ONE tristate driver per pad.
// done confirms transmitter completion only: no ACK/existence/stuck-bus check.
module ov5640_sccb_masked_write #(
    parameter [6:0] DEVICE_ADDR = 7'h3c,
    parameter integer HALF_PERIOD_CYCLES = 500
) (
    input wire clk, rst_n, start,
    input wire [15:0] reg_addr,
    input wire [7:0] reg_value, write_mask,
    output reg busy, done,
    inout wire sccb_scl, sccb_sda
);
    localparam [1:0] IDLE=0, READ_WAIT=1, WRITE_WAIT=2;
    reg [1:0] state;
    reg read_start, write_start;
    reg [15:0] address_latched;
    reg [7:0] value_latched, mask_latched, write_data;
    wire read_busy, read_done, write_busy, write_done;
    wire [7:0] read_data;
    wire read_scl_low, read_sda_low, write_scl_low, write_sda_low;
    assign sccb_scl = (read_scl_low | write_scl_low) ? 1'b0 : 1'bz;
    assign sccb_sda = (read_sda_low | write_sda_low) ? 1'b0 : 1'bz;

    ov5640_sccb_read_core #(.DEVICE_ADDR(DEVICE_ADDR),
        .HALF_PERIOD_CYCLES(HALF_PERIOD_CYCLES)) u_read (
        .clk(clk), .rst_n(rst_n), .start(read_start),
        .reg_addr(address_latched), .busy(read_busy), .done(read_done),
        .read_data(read_data), .sccb_sda_in(sccb_sda),
        .scl_drive_low(read_scl_low), .sda_drive_low(read_sda_low)
    );
    ov5640_sccb_write_core #(.DEVICE_ADDR(DEVICE_ADDR),
        .HALF_PERIOD_CYCLES(HALF_PERIOD_CYCLES)) u_write (
        .clk(clk), .rst_n(rst_n), .start(write_start),
        .reg_addr(address_latched), .reg_data(write_data),
        .busy(write_busy), .done(write_done),
        .scl_drive_low(write_scl_low), .sda_drive_low(write_sda_low)
    );

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            read_start <= 0;
            write_start <= 0;
            address_latched <= 0;
            value_latched <= 0;
            mask_latched <= 0;
            write_data <= 0;
            busy <= 0;
            done <= 0;
        end else begin
            read_start <= 0;
            write_start <= 0;
            done <= 0;
            case (state)
                IDLE: if (start) begin
                    address_latched <= reg_addr;
                    value_latched <= reg_value;
                    mask_latched <= write_mask;
                    busy <= 1;
                    if (write_mask == 8'hff) begin
                        write_data <= reg_value;
                        write_start <= 1;
                        state <= WRITE_WAIT;
                    end else begin
                        read_start <= 1;
                        state <= READ_WAIT;
                    end
                end
                READ_WAIT: if (read_done) begin
                    write_data <= (read_data & ~mask_latched) |
                                  (value_latched & mask_latched);
                    write_start <= 1;
                    state <= WRITE_WAIT;
                end
                WRITE_WAIT: if (write_done) begin
                    busy <= 0;
                    done <= 1;
                    state <= IDLE;
                end
                default: begin busy <= 0; state <= IDLE; end
            endcase
        end
    end
endmodule
