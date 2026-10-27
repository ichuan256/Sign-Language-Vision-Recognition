`timescale 1ns/1ps

// Two independent OV5640 DVP receivers. Each output group remains in its
// own camera PCLK domain; use one asynchronous FIFO per eye before combining
// either stream with a system-clocked AXI/V DMA path.
module ov5640_stereo_capture_pair #(
    parameter integer FRAME_WIDTH = 640,
    parameter integer FRAME_HEIGHT = 480,
    parameter         OV1_VSYNC_ACTIVE_LEVEL = 1'b1,
    parameter         OV2_VSYNC_ACTIVE_LEVEL = 1'b1
) (
    input wire        rst_n,

    input wire        ov1_pclk,
    input wire        ov1_vsync,
    input wire        ov1_href,
    input wire [7:0]  ov1_data,
    output wire       ov1_pixel_valid,
    output wire [15:0] ov1_pixel_data,
    output wire       ov1_pixel_sof,
    output wire       ov1_pixel_eol,
    output wire       ov1_frame_start,
    output wire       ov1_frame_done,
    output wire       ov1_frame_error,
    output wire [31:0] ov1_frame_id,

    input wire        ov2_pclk,
    input wire        ov2_vsync,
    input wire        ov2_href,
    input wire [7:0]  ov2_data,
    output wire       ov2_pixel_valid,
    output wire [15:0] ov2_pixel_data,
    output wire       ov2_pixel_sof,
    output wire       ov2_pixel_eol,
    output wire       ov2_frame_start,
    output wire       ov2_frame_done,
    output wire       ov2_frame_error,
    output wire [31:0] ov2_frame_id
);

    ov5640_dvp_capture #(
        .FRAME_WIDTH(FRAME_WIDTH),
        .FRAME_HEIGHT(FRAME_HEIGHT),
        .VSYNC_ACTIVE_LEVEL(OV1_VSYNC_ACTIVE_LEVEL)
    ) u_ov1_capture (
        .rst_n(rst_n),
        .cam_pclk(ov1_pclk),
        .cam_vsync(ov1_vsync),
        .cam_href(ov1_href),
        .cam_data(ov1_data),
        .pixel_valid(ov1_pixel_valid),
        .pixel_data(ov1_pixel_data),
        .pixel_sof(ov1_pixel_sof),
        .pixel_eol(ov1_pixel_eol),
        .frame_start(ov1_frame_start),
        .frame_done(ov1_frame_done),
        .frame_error(ov1_frame_error),
        .frame_id(ov1_frame_id)
    );

    ov5640_dvp_capture #(
        .FRAME_WIDTH(FRAME_WIDTH),
        .FRAME_HEIGHT(FRAME_HEIGHT),
        .VSYNC_ACTIVE_LEVEL(OV2_VSYNC_ACTIVE_LEVEL)
    ) u_ov2_capture (
        .rst_n(rst_n),
        .cam_pclk(ov2_pclk),
        .cam_vsync(ov2_vsync),
        .cam_href(ov2_href),
        .cam_data(ov2_data),
        .pixel_valid(ov2_pixel_valid),
        .pixel_data(ov2_pixel_data),
        .pixel_sof(ov2_pixel_sof),
        .pixel_eol(ov2_pixel_eol),
        .frame_start(ov2_frame_start),
        .frame_done(ov2_frame_done),
        .frame_error(ov2_frame_error),
        .frame_id(ov2_frame_id)
    );

endmodule
