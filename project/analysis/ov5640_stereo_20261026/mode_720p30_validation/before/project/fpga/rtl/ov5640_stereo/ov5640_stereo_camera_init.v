`timescale 1ns/1ps

// Power/reset sequencing and transport of an externally verified register
// stream to two independent OV5640 SCCB buses. SCCB done is an open-loop
// transmitter completion indication; it does not confirm sensor ACK or writes.
module ov5640_stereo_camera_init #(
    // Ceil divisions preserve minimum delays without multiplying SYS_CLK_HZ.
    // start requires stable supplies (>=5 ms) and a running sensor XCLK.
    parameter integer PWDN_SETTLE_CYCLES = (SYS_CLK_HZ <= 50) ? 1 :
        (SYS_CLK_HZ / 50) + ((SYS_CLK_HZ % 50) != 0), // 20 ms
    parameter integer RESET_RELEASE_WAIT_CYCLES = (SYS_CLK_HZ <= 50) ? 1 :
        (SYS_CLK_HZ / 50) + ((SYS_CLK_HZ % 50) != 0), // 20 ms
    parameter integer SCCB_TIMEOUT_CYCLES = (SYS_CLK_HZ <= 100) ? 1 :
        (SYS_CLK_HZ / 100) + ((SYS_CLK_HZ % 100) != 0), // 10 ms
    parameter integer SYS_CLK_HZ = 100000000
) (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,
    output reg         ov1_reset_n,
    output reg         ov1_pwdn,
    output reg         ov2_reset_n,
    output reg         ov2_pwdn,
    input  wire        cfg_valid,
    output wire        cfg_ready,
    input  wire [15:0] cfg_reg_addr,
    input  wire [7:0]  cfg_reg_data,
    input  wire        cfg_last,
    output reg         config_done,
    output reg         config_error,
    output reg         sccb_start_ov1,
    output reg         sccb_start_ov2,
    output reg  [15:0] sccb_reg_addr,
    output reg  [7:0]  sccb_reg_data,
    input  wire        sccb_busy_ov1,
    input  wire        sccb_done_ov1,
    input  wire        sccb_busy_ov2,
    input  wire        sccb_done_ov2
);
    localparam [2:0] ST_IDLE       = 3'd0;
    localparam [2:0] ST_PWDN_WAIT  = 3'd1;
    localparam [2:0] ST_RESET_WAIT = 3'd2;
    localparam [2:0] ST_CFG_WAIT   = 3'd3;
    localparam [2:0] ST_SCCB_WAIT  = 3'd4;
    localparam [2:0] ST_DONE       = 3'd5;
    localparam [2:0] ST_ERROR      = 3'd6;
    localparam integer WAIT_MAX = (PWDN_SETTLE_CYCLES > RESET_RELEASE_WAIT_CYCLES) ?
                                  PWDN_SETTLE_CYCLES : RESET_RELEASE_WAIT_CYCLES;
    localparam integer WAIT_WIDTH = (WAIT_MAX <= 1) ? 1 : $clog2(WAIT_MAX + 1);
    localparam integer TIMEOUT_WIDTH = (SCCB_TIMEOUT_CYCLES <= 1) ?
                                       1 : $clog2(SCCB_TIMEOUT_CYCLES + 1);

    reg [2:0] state;
    reg [WAIT_WIDTH-1:0] wait_count;
    reg [TIMEOUT_WIDTH-1:0] timeout_count;
    reg done_ov1_seen, done_ov2_seen;
    reg current_cfg_last;

    assign cfg_ready = (state == ST_CFG_WAIT) && !config_error &&
                       !sccb_busy_ov1 && !sccb_busy_ov2;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= ST_IDLE;
            wait_count <= {WAIT_WIDTH{1'b0}};
            timeout_count <= {TIMEOUT_WIDTH{1'b0}};
            done_ov1_seen <= 1'b0;
            done_ov2_seen <= 1'b0;
            current_cfg_last <= 1'b0;
            ov1_reset_n <= 1'b0;
            ov1_pwdn <= 1'b1;
            ov2_reset_n <= 1'b0;
            ov2_pwdn <= 1'b1;
            config_done <= 1'b0;
            config_error <= 1'b0;
            sccb_start_ov1 <= 1'b0;
            sccb_start_ov2 <= 1'b0;
            sccb_reg_addr <= 16'h0000;
            sccb_reg_data <= 8'h00;
        end else begin
            sccb_start_ov1 <= 1'b0;
            sccb_start_ov2 <= 1'b0;
            case (state)
                ST_IDLE: begin
                    ov1_reset_n <= 1'b0;
                    ov1_pwdn <= 1'b1;
                    ov2_reset_n <= 1'b0;
                    ov2_pwdn <= 1'b1;
                    config_done <= 1'b0;
                    config_error <= 1'b0;
                    wait_count <= {WAIT_WIDTH{1'b0}};
                    if (start) begin
                        ov1_pwdn <= 1'b0;
                        ov2_pwdn <= 1'b0;
                        wait_count <= {WAIT_WIDTH{1'b0}};
                        state <= ST_PWDN_WAIT;
                    end
                end
                ST_PWDN_WAIT: begin
                    if (wait_count >= PWDN_SETTLE_CYCLES - 1) begin
                        ov1_reset_n <= 1'b1;
                        ov2_reset_n <= 1'b1;
                        wait_count <= {WAIT_WIDTH{1'b0}};
                        state <= ST_RESET_WAIT;
                    end else begin
                        wait_count <= wait_count + 1'b1;
                    end
                end
                ST_RESET_WAIT: begin
                    if (wait_count >= RESET_RELEASE_WAIT_CYCLES - 1) begin
                        wait_count <= {WAIT_WIDTH{1'b0}};
                        state <= ST_CFG_WAIT;
                    end else begin
                        wait_count <= wait_count + 1'b1;
                    end
                end
                ST_CFG_WAIT: begin
                    if (cfg_valid && cfg_ready) begin
                        sccb_reg_addr <= cfg_reg_addr;
                        sccb_reg_data <= cfg_reg_data;
                        current_cfg_last <= cfg_last;
                        done_ov1_seen <= 1'b0;
                        done_ov2_seen <= 1'b0;
                        timeout_count <= {TIMEOUT_WIDTH{1'b0}};
                        sccb_start_ov1 <= 1'b1;
                        sccb_start_ov2 <= 1'b1;
                        state <= ST_SCCB_WAIT;
                    end
                end
                ST_SCCB_WAIT: begin
                    done_ov1_seen <= done_ov1_seen | sccb_done_ov1;
                    done_ov2_seen <= done_ov2_seen | sccb_done_ov2;
                    if ((done_ov1_seen || sccb_done_ov1) &&
                        (done_ov2_seen || sccb_done_ov2)) begin
                        if (current_cfg_last) begin
                            config_done <= 1'b1;
                            state <= ST_DONE;
                        end else begin
                            state <= ST_CFG_WAIT;
                        end
                    end else if (timeout_count >= SCCB_TIMEOUT_CYCLES - 1) begin
                        config_error <= 1'b1;
                        state <= ST_ERROR;
                    end else begin
                        timeout_count <= timeout_count + 1'b1;
                    end
                end
                ST_DONE: begin
                    config_done <= 1'b1;
                end
                ST_ERROR: begin
                    config_error <= 1'b1;
                end
                default: state <= ST_ERROR;
            endcase
        end
    end

endmodule
