`timescale 1ns/1ps

// One OV5640 SCCB 3-phase write: device address, 16-bit register address,
// then 8-bit register data. SCCB's ninth write bit is don't-care; the master
// releases SDA for that bit and does not require an I2C-style ACK.
module ov5640_sccb_write #(
    parameter [6:0] DEVICE_ADDR = 7'h3c,
    parameter integer HALF_PERIOD_CYCLES = 500
) (
    input wire clk, rst_n, start,
    input wire [15:0] reg_addr,
    input wire [7:0] reg_data,
    output wire busy, done,
    inout wire sccb_scl, sccb_sda
);
    wire scl_low, sda_low;
    assign sccb_scl = scl_low ? 1'b0 : 1'bz;
    assign sccb_sda = sda_low ? 1'b0 : 1'bz;
    ov5640_sccb_write_core #(.DEVICE_ADDR(DEVICE_ADDR),
        .HALF_PERIOD_CYCLES(HALF_PERIOD_CYCLES)) u_core (
        .clk(clk), .rst_n(rst_n), .start(start), .reg_addr(reg_addr),
        .reg_data(reg_data), .busy(busy), .done(done),
        .scl_drive_low(scl_low), .sda_drive_low(sda_low));
endmodule

module ov5640_sccb_write_core #(
    parameter [6:0] DEVICE_ADDR = 7'h3c,
    parameter integer HALF_PERIOD_CYCLES = 500
) (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,
    input  wire [15:0] reg_addr,
    input  wire [7:0]  reg_data,
    output reg         busy,
    output reg         done,
    output wire        scl_drive_low,
    output wire        sda_drive_low
);

    localparam integer DIV_WIDTH =
        (HALF_PERIOD_CYCLES <= 1) ? 1 : $clog2(HALF_PERIOD_CYCLES);
    localparam [3:0] ST_IDLE       = 4'd0;
    localparam [3:0] ST_START      = 4'd1;
    localparam [3:0] ST_BIT_LOW    = 4'd2;
    localparam [3:0] ST_BIT_HIGH   = 4'd3;
    localparam [3:0] ST_ACK_LOW    = 4'd4;
    localparam [3:0] ST_ACK_HIGH   = 4'd5;
    localparam [3:0] ST_STOP_RAISE = 4'd6;
    localparam [3:0] ST_STOP_END   = 4'd7;
    localparam [3:0] ST_BUS_FREE   = 4'd8;
    localparam [3:0] ST_BUS_FREE2  = 4'd9;

    reg [3:0] state;
    reg [DIV_WIDTH-1:0] divider;
    reg scl_pull_low;
    reg sda_pull_low;
    reg [7:0] tx_shift;
    reg [15:0] reg_addr_latched;
    reg [7:0] reg_data_latched;
    reg [1:0] byte_index;
    reg [3:0] bit_index;

    assign scl_drive_low = scl_pull_low;
    assign sda_drive_low = sda_pull_low;

    wire half_tick = (divider == HALF_PERIOD_CYCLES - 1);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state            <= ST_IDLE;
            divider          <= {DIV_WIDTH{1'b0}};
            scl_pull_low     <= 1'b0;
            sda_pull_low     <= 1'b0;
            tx_shift         <= 8'h00;
            reg_addr_latched <= 16'h0000;
            reg_data_latched <= 8'h00;
            byte_index       <= 2'd0;
            bit_index        <= 4'd0;
            busy             <= 1'b0;
            done             <= 1'b0;
        end else begin
            done <= 1'b0;

            if (!busy) begin
                divider <= {DIV_WIDTH{1'b0}};
                state   <= ST_IDLE;
                if (start) begin
                    reg_addr_latched <= reg_addr;
                    reg_data_latched <= reg_data;
                    tx_shift         <= {DEVICE_ADDR, 1'b0};
                    byte_index       <= 2'd0;
                    bit_index        <= 4'd7;
                    busy             <= 1'b1;
                    // A START is SDA falling while SCL is released high.
                    scl_pull_low     <= 1'b0;
                    sda_pull_low     <= 1'b1;
                    state            <= ST_START;
                end
            end else if (half_tick) begin
                divider <= {DIV_WIDTH{1'b0}};
                case (state)
                    ST_START: begin
                        // Hold START, then begin the first low clock phase.
                        scl_pull_low <= 1'b1;
                        sda_pull_low <= ~tx_shift[7];
                        state <= ST_BIT_LOW;
                    end

                    ST_BIT_LOW: begin
                        // Data is stable for a half-period before SCL rises.
                        scl_pull_low <= 1'b0;
                        state <= ST_BIT_HIGH;
                    end

                    ST_BIT_HIGH: begin
                        scl_pull_low <= 1'b1;
                        if (bit_index == 0) begin
                            // SCCB write ninth bit is don't-care; release SDA.
                            sda_pull_low <= 1'b0;
                            state <= ST_ACK_LOW;
                        end else begin
                            tx_shift <= {tx_shift[6:0], 1'b0};
                            bit_index <= bit_index - 1'b1;
                            sda_pull_low <= ~tx_shift[6];
                            state <= ST_BIT_LOW;
                        end
                    end

                    ST_ACK_LOW: begin
                        scl_pull_low <= 1'b0;
                        state <= ST_ACK_HIGH;
                    end

                    ST_ACK_HIGH: begin
                        scl_pull_low <= 1'b1;
                        if (byte_index == 2'd3) begin
                            // Prepare STOP while SCL is low.
                            sda_pull_low <= 1'b1;
                            state <= ST_STOP_RAISE;
                        end else begin
                            byte_index <= byte_index + 1'b1;
                            bit_index <= 4'd7;
                            case (byte_index)
                                2'd0: tx_shift <= reg_addr_latched[15:8];
                                2'd1: tx_shift <= reg_addr_latched[7:0];
                                2'd2: tx_shift <= reg_data_latched;
                                default: tx_shift <= 8'h00;
                            endcase
                            case (byte_index)
                                2'd0: sda_pull_low <= ~reg_addr_latched[15];
                                2'd1: sda_pull_low <= ~reg_addr_latched[7];
                                2'd2: sda_pull_low <= ~reg_data_latched[7];
                                default: sda_pull_low <= 1'b0;
                            endcase
                            state <= ST_BIT_LOW;
                        end
                    end

                    ST_STOP_RAISE: begin
                        // SDA is held low while SCL rises.
                        scl_pull_low <= 1'b0;
                        state <= ST_STOP_END;
                    end

                    ST_STOP_END: begin
                        // SDA rising while SCL is high completes STOP.
                        sda_pull_low <= 1'b0;
                        state <= ST_BUS_FREE;
                    end
                    // Keep ownership until one full SCL period after STOP.
                    // At the supported <=400kHz this exceeds tBUF >=1.3us.
                    ST_BUS_FREE: state <= ST_BUS_FREE2;
                    ST_BUS_FREE2: begin
                        busy <= 1'b0;
                        done <= 1'b1;
                        state <= ST_IDLE;
                    end

                    default: begin
                        scl_pull_low <= 1'b0;
                        sda_pull_low <= 1'b0;
                        busy <= 1'b0;
                        state <= ST_IDLE;
                    end
                endcase
            end else begin
                divider <= divider + 1'b1;
            end
        end
    end

endmodule
