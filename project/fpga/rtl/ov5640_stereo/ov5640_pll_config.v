`timescale 1ns/1ps

// Emits the OV5640 clock-tree register writes for the frozen camera target:
// 24 MHz XCLK, 1280x720@30 nominal, RGB565 over 8-bit DVP.
//
// This is a register-stream source, not an FPGA fabric PLL and not a complete
// sensor mode table. Connect cfg_* to the camera initialization stream (or
// merge it with the remaining sensor setup sequence).
module ov5640_pll_config #(
    parameter integer LAST_CONFIG = 0
) (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,
    output wire        cfg_valid,
    input  wire        cfg_ready,
    output reg  [15:0] cfg_reg_addr,
    output reg  [7:0]  cfg_reg_data,
    output wire        cfg_last,
    output reg         busy,
    output reg         done
);
    localparam [1:0] ST_IDLE      = 2'd0;
    localparam [1:0] ST_OFFER     = 2'd1;
    localparam [1:0] ST_WAIT_LOW  = 2'd2;
    localparam [1:0] ST_WAIT_HIGH = 2'd3;

    reg [1:0] state;
    reg [2:0] index;

    assign cfg_valid = (state == ST_OFFER);
    assign cfg_last = LAST_CONFIG && (index == 3'd4);

    always @* begin
        case (index)
            3'd0: begin cfg_reg_addr = 16'h3034; cfg_reg_data = 8'h18; end
            3'd1: begin cfg_reg_addr = 16'h3035; cfg_reg_data = 8'h20; end
            3'd2: begin cfg_reg_addr = 16'h3036; cfg_reg_data = 8'h54; end
            3'd3: begin cfg_reg_addr = 16'h3037; cfg_reg_data = 8'h13; end
            3'd4: begin cfg_reg_addr = 16'h3108; cfg_reg_data = 8'h01; end
            default: begin cfg_reg_addr = 16'h0000; cfg_reg_data = 8'h00; end
        endcase
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= ST_IDLE;
            index <= 3'd0;
            busy <= 1'b0;
            done <= 1'b0;
        end else begin
            done <= 1'b0;
            case (state)
                ST_IDLE: begin
                    busy <= 1'b0;
                    index <= 3'd0;
                    if (start) begin
                        busy <= 1'b1;
                        state <= ST_OFFER;
                    end
                end

                ST_OFFER: begin
                    if (cfg_ready)
                        state <= ST_WAIT_LOW;
                end

                ST_WAIT_LOW: begin
                    // camera_init deasserts ready while the two SCCB writes
                    // are in flight; wait for that event before accepting a
                    // subsequent high level as transaction completion.
                    if (!cfg_ready)
                        state <= ST_WAIT_HIGH;
                end

                ST_WAIT_HIGH: begin
                    if (cfg_ready) begin
                        if (index == 3'd4) begin
                            busy <= 1'b0;
                            done <= 1'b1;
                            state <= ST_IDLE;
                        end else begin
                            index <= index + 1'b1;
                            state <= ST_OFFER;
                        end
                    end
                end

                default: begin
                    busy <= 1'b0;
                    state <= ST_IDLE;
                end
            endcase
        end
    end
endmodule
