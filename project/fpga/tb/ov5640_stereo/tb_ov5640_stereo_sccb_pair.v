`timescale 1ns/1ps

module tb_ov5640_stereo_sccb_pair;
    reg clk = 1'b0;
    reg rst_n = 1'b0;
    reg start_ov1 = 1'b0;
    reg start_ov2 = 1'b0;
    reg [15:0] reg_addr = 16'h0000;
    reg [7:0] reg_data = 8'h00;
    wire busy_ov1, done_ov1, busy_ov2, done_ov2;
    tri1 ov1_scl, ov1_sda, ov2_scl, ov2_sda;

    reg collect_ov1 = 1'b0;
    reg collect_ov2 = 1'b0;
    integer bits_ov1 = 0;
    integer bits_ov2 = 0;
    reg [35:0] capture_ov1 = 36'd0;
    reg [35:0] capture_ov2 = 36'd0;

    always #5 clk = ~clk;

    ov5640_stereo_sccb_pair #(
        .DEVICE_ADDR(7'h3c),
        .HALF_PERIOD_CYCLES(2)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .start_ov1(start_ov1),
        .start_ov2(start_ov2),
        .reg_addr(reg_addr),
        .reg_data(reg_data),
        .busy_ov1(busy_ov1),
        .done_ov1(done_ov1),
        .ov1_scl(ov1_scl),
        .ov1_sda(ov1_sda),
        .busy_ov2(busy_ov2),
        .done_ov2(done_ov2),
        .ov2_scl(ov2_scl),
        .ov2_sda(ov2_sda)
    );

    always @(negedge ov1_sda) begin
        if (ov1_scl === 1'b1) begin
            collect_ov1 = 1'b1;
            bits_ov1 = 0;
            capture_ov1 = 36'd0;
        end
    end
    always @(negedge ov2_sda) begin
        if (ov2_scl === 1'b1) begin
            collect_ov2 = 1'b1;
            bits_ov2 = 0;
            capture_ov2 = 36'd0;
        end
    end

    always @(posedge ov1_scl) begin
        if (collect_ov1 && bits_ov1 < 36) begin
            capture_ov1[35-bits_ov1] = ov1_sda;
            bits_ov1 = bits_ov1 + 1;
        end
    end
    always @(posedge ov2_scl) begin
        if (collect_ov2 && bits_ov2 < 36) begin
            capture_ov2[35-bits_ov2] = ov2_sda;
            bits_ov2 = bits_ov2 + 1;
        end
    end

    always @(posedge ov1_sda)
        if (collect_ov1 && ov1_scl === 1'b1) collect_ov1 = 1'b0;
    always @(posedge ov2_sda)
        if (collect_ov2 && ov2_scl === 1'b1) collect_ov2 = 1'b0;

    function [8:0] pack_byte;
        input [7:0] value;
        begin pack_byte = {value, 1'b1}; end
    endfunction

    task pulse_starts;
        input start1;
        input start2;
        begin
            @(negedge clk);
            start_ov1 = start1;
            start_ov2 = start2;
            @(negedge clk);
            start_ov1 = 1'b0;
            start_ov2 = 1'b0;
        end
    endtask

    initial begin
        repeat (4) @(posedge clk);
        @(negedge clk); rst_n = 1'b1;
        repeat (2) @(posedge clk);

        reg_addr = 16'h3008;
        reg_data = 8'h82;
        pulse_starts(1'b1, 1'b1);
        wait(done_ov1 && done_ov2);
        #1;
        if (bits_ov1 != 36 || bits_ov2 != 36)
            $fatal(1, "simultaneous transactions not complete: %0d/%0d", bits_ov1, bits_ov2);
        if (capture_ov1 !== {pack_byte(8'h78), pack_byte(8'h30),
                             pack_byte(8'h08), pack_byte(8'h82)} ||
            capture_ov2 !== {pack_byte(8'h78), pack_byte(8'h30),
                             pack_byte(8'h08), pack_byte(8'h82)})
            $fatal(1, "simultaneous bus payloads differ: %h / %h", capture_ov1, capture_ov2);

        reg_addr = 16'h4300;
        reg_data = 8'h61;
        pulse_starts(1'b1, 1'b0);
        wait(done_ov1);
        #1;
        if (bits_ov1 != 36 || capture_ov1 !== {pack_byte(8'h78), pack_byte(8'h43),
                                               pack_byte(8'h00), pack_byte(8'h61)})
            $fatal(1, "OV1-only second transaction mismatch: %h", capture_ov1);
        if (bits_ov2 != 36 || capture_ov2 !== {pack_byte(8'h78), pack_byte(8'h30),
                                               pack_byte(8'h08), pack_byte(8'h82)})
            $fatal(1, "OV2 was disturbed by OV1-only transaction: %h", capture_ov2);
        if (busy_ov1 || busy_ov2)
            $fatal(1, "SCCB engine busy after completed transactions");

        $display("TEST_PASS: simultaneous and independent OV1/OV2 SCCB writes");
        $finish;
    end

    initial begin
        #200000;
        $fatal(1, "watchdog timeout");
    end
endmodule
