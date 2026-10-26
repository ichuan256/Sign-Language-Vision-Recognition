`timescale 1ns/1ps

// Independent SCCB write engines for OV1 and OV2. The shared payload makes
// applying the same register write to both sensors straightforward; either
// bus can also be started independently.
module ov5640_stereo_sccb_pair #(
    parameter [6:0] DEVICE_ADDR = 7'h3c,
    parameter integer HALF_PERIOD_CYCLES = 500
) (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start_ov1,
    input  wire        start_ov2,
    input  wire [15:0] reg_addr,
    input  wire [7:0]  reg_data,
    output wire        busy_ov1,
    output wire        done_ov1,
    inout  wire        ov1_scl,
    inout  wire        ov1_sda,
    output wire        busy_ov2,
    output wire        done_ov2,
    inout  wire        ov2_scl,
    inout  wire        ov2_sda
);

    ov5640_sccb_write #(
        .DEVICE_ADDR(DEVICE_ADDR),
        .HALF_PERIOD_CYCLES(HALF_PERIOD_CYCLES)
    ) u_ov1_sccb_write (
        .clk(clk),
        .rst_n(rst_n),
        .start(start_ov1),
        .reg_addr(reg_addr),
        .reg_data(reg_data),
        .busy(busy_ov1),
        .done(done_ov1),
        .sccb_scl(ov1_scl),
        .sccb_sda(ov1_sda)
    );

    ov5640_sccb_write #(
        .DEVICE_ADDR(DEVICE_ADDR),
        .HALF_PERIOD_CYCLES(HALF_PERIOD_CYCLES)
    ) u_ov2_sccb_write (
        .clk(clk),
        .rst_n(rst_n),
        .start(start_ov2),
        .reg_addr(reg_addr),
        .reg_data(reg_data),
        .busy(busy_ov2),
        .done(done_ov2),
        .sccb_scl(ov2_scl),
        .sccb_sda(ov2_sda)
    );

endmodule
