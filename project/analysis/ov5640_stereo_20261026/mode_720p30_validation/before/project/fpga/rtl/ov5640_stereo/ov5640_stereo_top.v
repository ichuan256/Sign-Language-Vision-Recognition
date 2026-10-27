`timescale 1ns/1ps

// First integration shell for two independent OV5640 DVP and SCCB interfaces.
// Pixel outputs remain in their own camera PCLK domains. SCCB commands use
// sys_clk and are supplied by an external initialization/control sequencer.
module ov5640_stereo_top #(
    parameter integer FRAME_WIDTH = 640,
    parameter integer FRAME_HEIGHT = 480,
    parameter         OV1_VSYNC_ACTIVE_LEVEL = 1'b1,
    parameter         OV2_VSYNC_ACTIVE_LEVEL = 1'b1,
    parameter [6:0]   SCCB_DEVICE_ADDR = 7'h3c,
    parameter integer SCCB_HALF_PERIOD_CYCLES = 500
) (
    input  wire        sys_clk,
    input  wire        rst_n,

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

    input  wire        sccb_start_ov1,
    input  wire        sccb_start_ov2,
    input  wire [15:0] sccb_reg_addr,
    input  wire [7:0]  sccb_reg_data,
    output wire        sccb_busy_ov1,
    output wire        sccb_done_ov1,
    inout  wire        ov1_scl,
    inout  wire        ov1_sda,
    output wire        sccb_busy_ov2,
    output wire        sccb_done_ov2,
    inout  wire        ov2_scl,
    inout  wire        ov2_sda
);

    ov5640_stereo_capture_pair #(
        .FRAME_WIDTH(FRAME_WIDTH),
        .FRAME_HEIGHT(FRAME_HEIGHT),
        .OV1_VSYNC_ACTIVE_LEVEL(OV1_VSYNC_ACTIVE_LEVEL),
        .OV2_VSYNC_ACTIVE_LEVEL(OV2_VSYNC_ACTIVE_LEVEL)
    ) u_capture_pair (
        .rst_n(rst_n),
        .ov1_pclk(ov1_pclk),
        .ov1_vsync(ov1_vsync),
        .ov1_href(ov1_href),
        .ov1_data(ov1_data),
        .ov1_pixel_valid(ov1_pixel_valid),
        .ov1_pixel_data(ov1_pixel_data),
        .ov1_pixel_sof(ov1_pixel_sof),
        .ov1_pixel_eol(ov1_pixel_eol),
        .ov1_frame_start(ov1_frame_start),
        .ov1_frame_done(ov1_frame_done),
        .ov1_frame_error(ov1_frame_error),
        .ov1_frame_id(ov1_frame_id),
        .ov2_pclk(ov2_pclk),
        .ov2_vsync(ov2_vsync),
        .ov2_href(ov2_href),
        .ov2_data(ov2_data),
        .ov2_pixel_valid(ov2_pixel_valid),
        .ov2_pixel_data(ov2_pixel_data),
        .ov2_pixel_sof(ov2_pixel_sof),
        .ov2_pixel_eol(ov2_pixel_eol),
        .ov2_frame_start(ov2_frame_start),
        .ov2_frame_done(ov2_frame_done),
        .ov2_frame_error(ov2_frame_error),
        .ov2_frame_id(ov2_frame_id)
    );

    ov5640_stereo_sccb_pair #(
        .DEVICE_ADDR(SCCB_DEVICE_ADDR),
        .HALF_PERIOD_CYCLES(SCCB_HALF_PERIOD_CYCLES)
    ) u_sccb_pair (
        .clk(sys_clk),
        .rst_n(rst_n),
        .start_ov1(sccb_start_ov1),
        .start_ov2(sccb_start_ov2),
        .reg_addr(sccb_reg_addr),
        .reg_data(sccb_reg_data),
        .busy_ov1(sccb_busy_ov1),
        .done_ov1(sccb_done_ov1),
        .ov1_scl(ov1_scl),
        .ov1_sda(ov1_sda),
        .busy_ov2(sccb_busy_ov2),
        .done_ov2(sccb_done_ov2),
        .ov2_scl(ov2_scl),
        .ov2_sda(ov2_sda)
    );

endmodule
