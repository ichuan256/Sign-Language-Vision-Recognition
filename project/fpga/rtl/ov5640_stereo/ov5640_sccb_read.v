`timescale 1ns/1ps

// One OV5640 SCCB register read.  The transaction is:
// START, device/write, register high, register low, repeated START,
// device/read, eight data bits, don't-care ninth bit, STOP.
//
// SCCB has no required I2C ACK phase.  The ninth bit after each transmitted
// byte and after the received byte is therefore released by the master.
module ov5640_sccb_read #(
    parameter [6:0] DEVICE_ADDR = 7'h3c,
    parameter integer HALF_PERIOD_CYCLES = 500
) (
    input wire clk, rst_n, start,
    input wire [15:0] reg_addr,
    output wire busy, done,
    output wire [7:0] read_data,
    inout wire sccb_scl, sccb_sda
);
    wire scl_low, sda_low;
    assign sccb_scl = scl_low ? 1'b0 : 1'bz;
    assign sccb_sda = sda_low ? 1'b0 : 1'bz;
    ov5640_sccb_read_core #(.DEVICE_ADDR(DEVICE_ADDR),
        .HALF_PERIOD_CYCLES(HALF_PERIOD_CYCLES)) u_core (
        .clk(clk), .rst_n(rst_n), .start(start), .reg_addr(reg_addr),
        .busy(busy), .done(done), .read_data(read_data),
        .sccb_sda_in(sccb_sda), .scl_drive_low(scl_low), .sda_drive_low(sda_low));
endmodule

// Pad-independent core lets bus owners combine low enables before one buffer.
module ov5640_sccb_read_core #(
    parameter [6:0] DEVICE_ADDR = 7'h3c,
    parameter integer HALF_PERIOD_CYCLES = 500
) (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,
    input  wire [15:0] reg_addr,
    output reg         busy,
    output reg         done,
    output reg [7:0]   read_data,
    input  wire        sccb_sda_in,
    output wire        scl_drive_low,
    output wire        sda_drive_low
);

    localparam integer DIV_WIDTH =
        (HALF_PERIOD_CYCLES <= 1) ? 1 : $clog2(HALF_PERIOD_CYCLES);
    localparam [4:0] ST_IDLE       = 5'd0;
    localparam [4:0] ST_START      = 5'd1;
    localparam [4:0] ST_TX_LOW     = 5'd2;
    localparam [4:0] ST_TX_HIGH    = 5'd3;
    localparam [4:0] ST_TX_DNC_LOW = 5'd4;
    localparam [4:0] ST_TX_DNC_HIGH= 5'd5;
    localparam [4:0] ST_REP_HIGH   = 5'd6;
    localparam [4:0] ST_REP_LOW    = 5'd7;
    localparam [4:0] ST_RX_LOW     = 5'd8;
    localparam [4:0] ST_RX_HIGH    = 5'd9;
    localparam [4:0] ST_RX_DNC_LOW = 5'd10;
    localparam [4:0] ST_RX_DNC_HIGH= 5'd11;
    localparam [4:0] ST_STOP_PREP  = 5'd12;
    localparam [4:0] ST_STOP_RAISE = 5'd13;
    localparam [4:0] ST_STOP_END   = 5'd14;
    localparam [4:0] ST_REP_ASSERT = 5'd15;
    localparam [4:0] ST_REP_SETUP  = 5'd16;

    reg [4:0] state;
    reg [DIV_WIDTH-1:0] divider;
    reg scl_pull_low;
    reg sda_pull_low;
    reg [7:0] tx_shift;
    reg [7:0] rx_shift;
    reg [15:0] reg_addr_latched;
    reg [1:0] tx_index;
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
            rx_shift         <= 8'h00;
            reg_addr_latched <= 16'h0000;
            tx_index         <= 2'd0;
            bit_index        <= 4'd0;
            busy             <= 1'b0;
            done             <= 1'b0;
            read_data        <= 8'h00;
        end else begin
            done <= 1'b0;

            if (!busy) begin
                divider <= {DIV_WIDTH{1'b0}};
                state   <= ST_IDLE;
                if (start) begin
                    reg_addr_latched <= reg_addr;
                    tx_shift         <= {DEVICE_ADDR, 1'b0};
                    tx_index         <= 2'd0;
                    bit_index         <= 4'd7;
                    rx_shift         <= 8'h00;
                    busy              <= 1'b1;
                    scl_pull_low     <= 1'b0;
                    sda_pull_low     <= 1'b1;
                    state             <= ST_START;
                end
            end else if (half_tick) begin
                divider <= {DIV_WIDTH{1'b0}};
                case (state)
                    ST_START: begin
                        scl_pull_low <= 1'b1;
                        sda_pull_low <= ~tx_shift[7];
                        state <= ST_TX_LOW;
                    end

                    ST_TX_LOW: begin
                        scl_pull_low <= 1'b0;
                        state <= ST_TX_HIGH;
                    end

                    ST_TX_HIGH: begin
                        scl_pull_low <= 1'b1;
                        if (bit_index == 0) begin
                            sda_pull_low <= 1'b0;
                            state <= ST_TX_DNC_LOW;
                        end else begin
                            tx_shift <= {tx_shift[6:0], 1'b0};
                            bit_index <= bit_index - 1'b1;
                            sda_pull_low <= ~tx_shift[6];
                            state <= ST_TX_LOW;
                        end
                    end

                    ST_TX_DNC_LOW: begin
                        scl_pull_low <= 1'b0;
                        state <= ST_TX_DNC_HIGH;
                    end

                    ST_TX_DNC_HIGH: begin
                        scl_pull_low <= 1'b1;
                        case (tx_index)
                            2'd0: begin
                                tx_index <= 2'd1;
                                tx_shift <= reg_addr_latched[15:8];
                                bit_index <= 4'd7;
                                sda_pull_low <= ~reg_addr_latched[15];
                                state <= ST_TX_LOW;
                            end
                            2'd1: begin
                                tx_index <= 2'd2;
                                tx_shift <= reg_addr_latched[7:0];
                                bit_index <= 4'd7;
                                sda_pull_low <= ~reg_addr_latched[7];
                                state <= ST_TX_LOW;
                            end
                            2'd2: begin
                                // Repeated START, then the read address.
                                sda_pull_low <= 1'b1;
                                state <= ST_REP_HIGH;
                            end
                            default: begin
                                // The read-address ninth bit is don't-care too.
                                sda_pull_low <= 1'b0;
                                bit_index <= 4'd7;
                                rx_shift <= 8'h00;
                                state <= ST_RX_LOW;
                            end
                        endcase
                    end

                    ST_REP_HIGH: begin
                        scl_pull_low <= 1'b1;
                        sda_pull_low <= 1'b0;
                        state <= ST_REP_LOW;
                    end

                    ST_REP_LOW: begin
                        scl_pull_low <= 1'b0;
                        state <= ST_REP_ASSERT;
                    end

                    ST_REP_ASSERT: begin
                        scl_pull_low <= 1'b0;
                        sda_pull_low <= 1'b1;
                        tx_shift <= {DEVICE_ADDR, 1'b1};
                        bit_index <= 4'd7;
                        tx_index <= 2'd3;
                        state <= ST_REP_SETUP;
                    end

                    ST_REP_SETUP: begin
                        // Hold repeated START, then provide the first read-
                        // address bit while SCL is low before its rising edge.
                        scl_pull_low <= 1'b1;
                        sda_pull_low <= ~tx_shift[7];
                        state <= ST_TX_LOW;
                    end

                    ST_RX_LOW: begin
                        scl_pull_low <= 1'b0;
                        sda_pull_low <= 1'b0;
                        state <= ST_RX_HIGH;
                    end

                    ST_RX_HIGH: begin
                        scl_pull_low <= 1'b1;
                        rx_shift <= {rx_shift[6:0], sccb_sda_in};
                        if (bit_index == 0) begin
                            state <= ST_RX_DNC_LOW;
                        end else begin
                            bit_index <= bit_index - 1'b1;
                            state <= ST_RX_LOW;
                        end
                    end

                    ST_RX_DNC_LOW: begin
                        scl_pull_low <= 1'b0;
                        state <= ST_RX_DNC_HIGH;
                    end

                    ST_RX_DNC_HIGH: begin
                        scl_pull_low <= 1'b1;
                        read_data <= rx_shift;
                        state <= ST_STOP_PREP;
                    end

                    ST_STOP_PREP: begin
                        sda_pull_low <= 1'b1;
                        // Prepare SDA while SCL is still low. Raising SCL
                        // here as SDA falls can look like an extra START.
                        scl_pull_low <= 1'b1;
                        state <= ST_STOP_RAISE;
                    end

                    ST_STOP_RAISE: begin
                        scl_pull_low <= 1'b0;
                        state <= ST_STOP_END;
                    end

                    ST_STOP_END: begin
                        sda_pull_low <= 1'b0;
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
