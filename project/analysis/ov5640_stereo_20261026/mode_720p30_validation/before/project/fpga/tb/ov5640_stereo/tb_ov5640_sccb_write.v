`timescale 1ns/1ps

module tb_ov5640_sccb_write;
    reg clk = 1'b0;
    reg rst_n = 1'b0;
    reg start = 1'b0;
    reg [15:0] reg_addr = 16'h0000;
    reg [7:0] reg_data = 8'h00;
    wire busy;
    wire done;
    tri1 sccb_scl;
    tri1 sccb_sda;

    reg collecting = 1'b0;
    integer bit_samples = 0;
    reg [35:0] sampled_bits;

    always #5 clk = ~clk;

    ov5640_sccb_write #(
        .DEVICE_ADDR(7'h3c),
        .HALF_PERIOD_CYCLES(2)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),
        .reg_addr(reg_addr),
        .reg_data(reg_data),
        .busy(busy),
        .done(done),
        .sccb_scl(sccb_scl),
        .sccb_sda(sccb_sda)
    );

    always @(negedge sccb_sda) begin
        if (sccb_scl === 1'b1) begin
            collecting = 1'b1;
            bit_samples = 0;
        end
    end

    always @(posedge sccb_scl) begin
        if (collecting && bit_samples < 36) begin
            sampled_bits[35-bit_samples] = sccb_sda;
            bit_samples = bit_samples + 1;
        end
    end

    always @(posedge sccb_sda) begin
        if (collecting && sccb_scl === 1'b1)
            collecting = 1'b0;
    end

    function [8:0] pack_byte;
        input [7:0] value;
        begin
            pack_byte = {value, 1'b1}; // ninth bit is SCCB write don't-care
        end
    endfunction

    initial begin
        sampled_bits = 27'd0;
        repeat (4) @(posedge clk);
        @(negedge clk); rst_n = 1'b1;
        repeat (2) @(posedge clk);
        @(negedge clk);
        reg_addr = 16'h1234;
        reg_data = 8'hA5;
        start = 1'b1;
        @(negedge clk); start = 1'b0;

        wait(done);
        #1;
        if (busy)
            $fatal(1, "busy remained high after done");
        if (collecting)
            $fatal(1, "STOP condition was not observed");
        if (bit_samples != 36)
            $fatal(1, "expected 36 SCCB bits, sampled %0d", bit_samples);
        if (sampled_bits !== {pack_byte(8'h78), pack_byte(8'h12),
                              pack_byte(8'h34), pack_byte(8'hA5)})
            $fatal(1, "SCCB device/register/data sequence mismatch: %h", sampled_bits);
        $display("TEST_PASS: SCCB open-drain start/stop and device/register bytes");
        $finish;
    end

    initial begin
        #200000;
        $fatal(1, "watchdog timeout");
    end
endmodule
