`timescale 1ns/1ps

// Startup/capture shell. Pixels and frame pulses stay in each camera PCLK
// domain. This adds no asynchronous pixel FIFO, DDR writer or frame pairing.
module ov5640_stereo_startup_capture #(
    parameter integer SYS_CLK_HZ=100000000,
    parameter integer FRAME_WIDTH=1280, FRAME_HEIGHT=720,
    parameter OV1_VSYNC_ACTIVE_LEVEL=1'b1, OV2_VSYNC_ACTIVE_LEVEL=1'b1,
    parameter integer PWDN_SETTLE_CYCLES=((SYS_CLK_HZ/1000)*20+((SYS_CLK_HZ%1000)*20+999)/1000 < 1) ? 1 : ((SYS_CLK_HZ/1000)*20+((SYS_CLK_HZ%1000)*20+999)/1000),
    parameter integer RESET_RELEASE_WAIT_CYCLES=((SYS_CLK_HZ/1000)*20+((SYS_CLK_HZ%1000)*20+999)/1000 < 1) ? 1 : ((SYS_CLK_HZ/1000)*20+((SYS_CLK_HZ%1000)*20+999)/1000),
    parameter integer SCCB_HALF_PERIOD_CYCLES=((SYS_CLK_HZ/200000)+((SYS_CLK_HZ%200000)!=0) < 1) ? 1 : ((SYS_CLK_HZ/200000)+((SYS_CLK_HZ%200000)!=0)),
    parameter integer SCCB_TIMEOUT_CYCLES=((SYS_CLK_HZ/1000)*10+((SYS_CLK_HZ%1000)*10+999)/1000 < 1) ? 1 : ((SYS_CLK_HZ/1000)*10+((SYS_CLK_HZ%1000)*10+999)/1000),
    parameter [7:0] DVP_POLARITY_VALUE=8'h22
) (
    input wire sys_clk, rst_n, start,
    output wire ov1_reset_n, ov1_pwdn, ov2_reset_n, ov2_pwdn,
    inout wire ov1_scl, ov1_sda, ov2_scl, ov2_sda,
    output wire busy, init_done, init_error,
    output wire [3:0] error_code,
    output wire [1:0] failed_cameras,
    input wire ov1_pclk, ov1_vsync, ov1_href,
    input wire [7:0] ov1_data,
    output wire ov1_pixel_valid, ov1_pixel_sof, ov1_pixel_eol,
    output wire [15:0] ov1_pixel_data,
    output wire ov1_frame_start, ov1_frame_done, ov1_frame_error,
    output wire [31:0] ov1_frame_id,
    input wire ov2_pclk, ov2_vsync, ov2_href,
    input wire [7:0] ov2_data,
    output wire ov2_pixel_valid, ov2_pixel_sof, ov2_pixel_eol,
    output wire [15:0] ov2_pixel_data,
    output wire ov2_frame_start, ov2_frame_done, ov2_frame_error,
    output wire [31:0] ov2_frame_id
);
    ov5640_stereo_startup #(.SYS_CLK_HZ(SYS_CLK_HZ),
        .PWDN_SETTLE_CYCLES(PWDN_SETTLE_CYCLES), .RESET_RELEASE_WAIT_CYCLES(RESET_RELEASE_WAIT_CYCLES),
        .SCCB_HALF_PERIOD_CYCLES(SCCB_HALF_PERIOD_CYCLES), .SCCB_TIMEOUT_CYCLES(SCCB_TIMEOUT_CYCLES),
        .DVP_POLARITY_VALUE(DVP_POLARITY_VALUE)) u_startup (
        .sys_clk(sys_clk), .rst_n(rst_n), .start(start),
        .ov1_reset_n(ov1_reset_n), .ov1_pwdn(ov1_pwdn), .ov2_reset_n(ov2_reset_n), .ov2_pwdn(ov2_pwdn),
        .ov1_scl(ov1_scl), .ov1_sda(ov1_sda), .ov2_scl(ov2_scl), .ov2_sda(ov2_sda),
        .busy(busy), .init_done(init_done), .init_error(init_error),
        .error_code(error_code), .failed_cameras(failed_cameras));
    (* ASYNC_REG = "TRUE" *) reg [1:0] init_sync1;
    always @(posedge ov1_pclk or negedge rst_n) begin
        if (!rst_n) init_sync1<=0;
        else init_sync1<={init_sync1[0],init_done};
    end
    ov5640_dvp_capture #(.FRAME_WIDTH(FRAME_WIDTH), .FRAME_HEIGHT(FRAME_HEIGHT),
        .VSYNC_ACTIVE_LEVEL(OV1_VSYNC_ACTIVE_LEVEL)) u_capture1 (
        .rst_n(rst_n && init_sync1[1] && !init_error),
        .cam_pclk(ov1_pclk), .cam_vsync(ov1_vsync), .cam_href(ov1_href), .cam_data(ov1_data),
        .pixel_valid(ov1_pixel_valid), .pixel_data(ov1_pixel_data),
        .pixel_sof(ov1_pixel_sof), .pixel_eol(ov1_pixel_eol),
        .frame_start(ov1_frame_start), .frame_done(ov1_frame_done),
        .frame_error(ov1_frame_error), .frame_id(ov1_frame_id));
    (* ASYNC_REG = "TRUE" *) reg [1:0] init_sync2;
    always @(posedge ov2_pclk or negedge rst_n) begin
        if (!rst_n) init_sync2<=0;
        else init_sync2<={init_sync2[0],init_done};
    end
    ov5640_dvp_capture #(.FRAME_WIDTH(FRAME_WIDTH), .FRAME_HEIGHT(FRAME_HEIGHT),
        .VSYNC_ACTIVE_LEVEL(OV2_VSYNC_ACTIVE_LEVEL)) u_capture2 (
        .rst_n(rst_n && init_sync2[1] && !init_error),
        .cam_pclk(ov2_pclk), .cam_vsync(ov2_vsync), .cam_href(ov2_href), .cam_data(ov2_data),
        .pixel_valid(ov2_pixel_valid), .pixel_data(ov2_pixel_data),
        .pixel_sof(ov2_pixel_sof), .pixel_eol(ov2_pixel_eol),
        .frame_start(ov2_frame_start), .frame_done(ov2_frame_done),
        .frame_error(ov2_frame_error), .frame_id(ov2_frame_id));
endmodule
