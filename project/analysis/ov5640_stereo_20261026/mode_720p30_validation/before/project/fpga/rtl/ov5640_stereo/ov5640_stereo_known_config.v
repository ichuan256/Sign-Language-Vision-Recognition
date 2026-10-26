`timescale 1ns/1ps

// Executable confirmed-subset entry point. This is NOT a complete sensor boot
// sequence or image-ready indication. start requires stable power/XCLK as
// documented for camera_init; external global/ISP setup remains required.
module ov5640_stereo_known_config #(
    parameter integer SYS_CLK_HZ = 100000000,
    parameter [6:0] DEVICE_ADDR = 7'h3c,
    parameter integer SCCB_HALF_PERIOD_CYCLES = (SYS_CLK_HZ <= 200000) ? 1 :
        (SYS_CLK_HZ / 200000) + ((SYS_CLK_HZ % 200000) != 0),
    parameter integer PWDN_SETTLE_CYCLES = (SYS_CLK_HZ <= 50) ? 1 :
        (SYS_CLK_HZ / 50) + ((SYS_CLK_HZ % 50) != 0),
    parameter integer RESET_RELEASE_WAIT_CYCLES = (SYS_CLK_HZ <= 50) ? 1 :
        (SYS_CLK_HZ / 50) + ((SYS_CLK_HZ % 50) != 0),
    parameter integer SCCB_TIMEOUT_CYCLES = (SYS_CLK_HZ <= 100) ? 1 :
        (SYS_CLK_HZ / 100) + ((SYS_CLK_HZ % 100) != 0)
) (
    input wire sys_clk, rst_n, start,
    output wire ov1_reset_n, ov1_pwdn, ov2_reset_n, ov2_pwdn,
    inout wire ov1_scl, ov1_sda, ov2_scl, ov2_sda,
    output wire busy, known_config_done, known_config_error
);
    wire [5:0] index;
    wire table_valid, last;
    wire [15:0] address, delay_ms;
    wire [7:0] value, mask;
    wire cfg_valid, cfg_ready, transport_done, transport_error, sequence_error;
    wire start1, start2, busy1, busy2, done1, done2;
    wire [15:0] tx_address;
    wire [7:0] tx_value;
    assign known_config_error = transport_error | sequence_error;

    ov5640_known_config_table u_table (.index(index), .valid(table_valid),
        .reg_addr(address), .reg_value(value), .write_mask(mask),
        .post_delay_ms(delay_ms), .last(last));
    ov5640_known_config_sequencer #(.SYS_CLK_HZ(SYS_CLK_HZ)) u_sequence (
        .clk(sys_clk), .rst_n(rst_n), .start(start), .table_index(index),
        .table_valid(table_valid), .table_last(last), .table_delay_ms(delay_ms),
        .cfg_valid(cfg_valid), .cfg_ready(cfg_ready),
        .transport_done(transport_done), .transport_error(transport_error),
        .busy(busy), .done(known_config_done), .error_flag(sequence_error));
    ov5640_stereo_camera_init #(.SYS_CLK_HZ(SYS_CLK_HZ),
        .PWDN_SETTLE_CYCLES(PWDN_SETTLE_CYCLES),
        .RESET_RELEASE_WAIT_CYCLES(RESET_RELEASE_WAIT_CYCLES),
        .SCCB_TIMEOUT_CYCLES(SCCB_TIMEOUT_CYCLES)) u_init (
        .clk(sys_clk), .rst_n(rst_n), .start(start),
        .ov1_reset_n(ov1_reset_n), .ov1_pwdn(ov1_pwdn),
        .ov2_reset_n(ov2_reset_n), .ov2_pwdn(ov2_pwdn),
        .cfg_valid(cfg_valid), .cfg_ready(cfg_ready), .cfg_reg_addr(address),
        .cfg_reg_data(value), .cfg_last(last), .config_done(transport_done),
        .config_error(transport_error), .sccb_start_ov1(start1),
        .sccb_start_ov2(start2), .sccb_reg_addr(tx_address),
        .sccb_reg_data(tx_value), .sccb_busy_ov1(busy1), .sccb_done_ov1(done1),
        .sccb_busy_ov2(busy2), .sccb_done_ov2(done2));
    ov5640_sccb_masked_write #(.DEVICE_ADDR(DEVICE_ADDR),
        .HALF_PERIOD_CYCLES(SCCB_HALF_PERIOD_CYCLES)) u_ov1 (
        .clk(sys_clk), .rst_n(rst_n), .start(start1),
        .reg_addr(tx_address), .reg_value(tx_value), .write_mask(mask),
        .busy(busy1), .done(done1), .sccb_scl(ov1_scl), .sccb_sda(ov1_sda));
    ov5640_sccb_masked_write #(.DEVICE_ADDR(DEVICE_ADDR),
        .HALF_PERIOD_CYCLES(SCCB_HALF_PERIOD_CYCLES)) u_ov2 (
        .clk(sys_clk), .rst_n(rst_n), .start(start2),
        .reg_addr(tx_address), .reg_value(tx_value), .write_mask(mask),
        .busy(busy2), .done(done2), .sccb_scl(ov2_scl), .sccb_sda(ov2_sda));
endmodule
