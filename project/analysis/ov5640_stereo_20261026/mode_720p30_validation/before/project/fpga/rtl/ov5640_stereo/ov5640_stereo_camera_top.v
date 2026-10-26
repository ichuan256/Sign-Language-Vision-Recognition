`timescale 1ns/1ps

// Higher-level dual-camera shell. The frame dimensions describe the intended
// capture contract; a verified register stream must still be supplied through
// cfg_* before config_done can assert. No 1080p30 mode table is built in.
module ov5640_stereo_camera_top #(
    parameter integer FRAME_WIDTH = 1920,
    parameter integer FRAME_HEIGHT = 1080,
    parameter         OV1_VSYNC_ACTIVE_LEVEL = 1'b1,
    parameter         OV2_VSYNC_ACTIVE_LEVEL = 1'b1,
    parameter [6:0]   SCCB_DEVICE_ADDR = 7'h3c,
    // Ceil division keeps SCL at or below the 100 kHz bring-up target.
    parameter integer SCCB_HALF_PERIOD_CYCLES = (SYS_CLK_HZ <= 200000) ? 1 :
        (SYS_CLK_HZ / 200000) + ((SYS_CLK_HZ % 200000) != 0),
    parameter integer PWDN_SETTLE_CYCLES = (SYS_CLK_HZ <= 50) ? 1 :
        (SYS_CLK_HZ / 50) + ((SYS_CLK_HZ % 50) != 0), // 20 ms
    parameter integer RESET_RELEASE_WAIT_CYCLES = (SYS_CLK_HZ <= 50) ? 1 :
        (SYS_CLK_HZ / 50) + ((SYS_CLK_HZ % 50) != 0), // 20 ms
    parameter integer SCCB_TIMEOUT_CYCLES = (SYS_CLK_HZ <= 100) ? 1 :
        (SYS_CLK_HZ / 100) + ((SYS_CLK_HZ % 100) != 0), // 10 ms
    parameter integer SYS_CLK_HZ = 100000000
) (
    input  wire        sys_clk,
    input  wire        rst_n,
    input  wire        start_init,
    output wire        ov1_reset_n,
    output wire        ov1_pwdn,
    output wire        ov2_reset_n,
    output wire        ov2_pwdn,
    input  wire        cfg_valid,
    output wire        cfg_ready,
    input  wire [15:0] cfg_reg_addr,
    input  wire [7:0]  cfg_reg_data,
    input  wire        cfg_last,
    output wire        config_done,
    output wire        config_error,

    input  wire        ov1_pclk,
    input  wire        ov1_vsync,
    input  wire        ov1_href,
    input  wire [7:0]  ov1_data,
    output wire        ov1_pixel_valid,
    output wire [15:0] ov1_pixel_data,
    output wire        ov1_pixel_sof,
    output wire        ov1_pixel_eol,
    output wire        ov1_frame_start,
    output wire        ov1_frame_done,
    output wire        ov1_frame_error,
    output wire [31:0] ov1_frame_id,

    input  wire        ov2_pclk,
    input  wire        ov2_vsync,
    input  wire        ov2_href,
    input  wire [7:0]  ov2_data,
    output wire        ov2_pixel_valid,
    output wire [15:0] ov2_pixel_data,
    output wire        ov2_pixel_sof,
    output wire        ov2_pixel_eol,
    output wire        ov2_frame_start,
    output wire        ov2_frame_done,
    output wire        ov2_frame_error,
    output wire [31:0] ov2_frame_id,

    output wire        sccb_busy_ov1,
    output wire        sccb_done_ov1,
    inout  wire        ov1_scl,
    inout  wire        ov1_sda,
    output wire        sccb_busy_ov2,
    output wire        sccb_done_ov2,
    inout  wire        ov2_scl,
    inout  wire        ov2_sda
);
    wire sccb_start_ov1, sccb_start_ov2;
    wire [15:0] sccb_reg_addr;
    wire [7:0] sccb_reg_data;

    ov5640_stereo_capture_pair #(
        .FRAME_WIDTH(FRAME_WIDTH),
        .FRAME_HEIGHT(FRAME_HEIGHT),
        .OV1_VSYNC_ACTIVE_LEVEL(OV1_VSYNC_ACTIVE_LEVEL),
        .OV2_VSYNC_ACTIVE_LEVEL(OV2_VSYNC_ACTIVE_LEVEL)
    ) u_capture_pair (
        .rst_n(rst_n),
        .ov1_pclk(ov1_pclk), .ov1_vsync(ov1_vsync),
        .ov1_href(ov1_href), .ov1_data(ov1_data),
        .ov1_pixel_valid(ov1_pixel_valid), .ov1_pixel_data(ov1_pixel_data),
        .ov1_pixel_sof(ov1_pixel_sof), .ov1_pixel_eol(ov1_pixel_eol),
        .ov1_frame_start(ov1_frame_start), .ov1_frame_done(ov1_frame_done),
        .ov1_frame_error(ov1_frame_error), .ov1_frame_id(ov1_frame_id),
        .ov2_pclk(ov2_pclk), .ov2_vsync(ov2_vsync),
        .ov2_href(ov2_href), .ov2_data(ov2_data),
        .ov2_pixel_valid(ov2_pixel_valid), .ov2_pixel_data(ov2_pixel_data),
        .ov2_pixel_sof(ov2_pixel_sof), .ov2_pixel_eol(ov2_pixel_eol),
        .ov2_frame_start(ov2_frame_start), .ov2_frame_done(ov2_frame_done),
        .ov2_frame_error(ov2_frame_error), .ov2_frame_id(ov2_frame_id)
    );

    ov5640_stereo_sccb_pair #(
        .DEVICE_ADDR(SCCB_DEVICE_ADDR),
        .HALF_PERIOD_CYCLES(SCCB_HALF_PERIOD_CYCLES)
    ) u_sccb_pair (
        .clk(sys_clk), .rst_n(rst_n),
        .start_ov1(sccb_start_ov1), .start_ov2(sccb_start_ov2),
        .reg_addr(sccb_reg_addr), .reg_data(sccb_reg_data),
        .busy_ov1(sccb_busy_ov1), .done_ov1(sccb_done_ov1),
        .ov1_scl(ov1_scl), .ov1_sda(ov1_sda),
        .busy_ov2(sccb_busy_ov2), .done_ov2(sccb_done_ov2),
        .ov2_scl(ov2_scl), .ov2_sda(ov2_sda)
    );

    ov5640_stereo_camera_init #(
        .PWDN_SETTLE_CYCLES(PWDN_SETTLE_CYCLES),
        .RESET_RELEASE_WAIT_CYCLES(RESET_RELEASE_WAIT_CYCLES),
        .SCCB_TIMEOUT_CYCLES(SCCB_TIMEOUT_CYCLES),
        .SYS_CLK_HZ(SYS_CLK_HZ)
    ) u_camera_init (
        .clk(sys_clk), .rst_n(rst_n), .start(start_init),
        .ov1_reset_n(ov1_reset_n), .ov1_pwdn(ov1_pwdn),
        .ov2_reset_n(ov2_reset_n), .ov2_pwdn(ov2_pwdn),
        .cfg_valid(cfg_valid), .cfg_ready(cfg_ready),
        .cfg_reg_addr(cfg_reg_addr), .cfg_reg_data(cfg_reg_data),
        .cfg_last(cfg_last), .config_done(config_done),
        .config_error(config_error),
        .sccb_start_ov1(sccb_start_ov1), .sccb_start_ov2(sccb_start_ov2),
        .sccb_reg_addr(sccb_reg_addr), .sccb_reg_data(sccb_reg_data),
        .sccb_busy_ov1(sccb_busy_ov1), .sccb_done_ov1(sccb_done_ov1),
        .sccb_busy_ov2(sccb_busy_ov2), .sccb_done_ov2(sccb_done_ov2)
    );
endmodule
