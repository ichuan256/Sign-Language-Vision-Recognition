`timescale 1ns/1ps

module tb_ov5640_sccb_read;
    reg clk = 1'b0;
    reg rst_n = 1'b0;
    reg start = 1'b0;
    reg [15:0] reg_addr = 16'h300a;
    wire busy;
    wire done;
    wire [7:0] read_data;
    tri1 sccb_scl;
    tri1 sccb_sda;
    reg slave_pull_low = 1'b0;
    integer start_count = 0;
    integer stop_count = 0;
    integer i;
    reg [7:0] expected = 8'h56;

    assign sccb_sda = slave_pull_low ? 1'b0 : 1'bz;

    always #5 clk = ~clk;

    always @(negedge sccb_sda) begin
        if (sccb_scl === 1'b1)
            start_count = start_count + 1;
    end

    always @(posedge sccb_sda) begin
        if (sccb_scl === 1'b1 && start_count > 0)
            stop_count = stop_count + 1;
    end

    ov5640_sccb_read #(
        .DEVICE_ADDR(7'h3c),
        .HALF_PERIOD_CYCLES(2)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),
        .reg_addr(reg_addr),
        .busy(busy),
        .done(done),
        .read_data(read_data),
        .sccb_scl(sccb_scl),
        .sccb_sda(sccb_sda)
    );

    initial begin
        repeat (3) @(posedge clk);
        rst_n = 1'b1;
        @(posedge clk);
        start = 1'b1;
        @(posedge clk);
        start = 1'b0;

        wait (start_count == 2);
        // All eight read-address bits AND its ninth don't-care clock precede
        // receive data. The previous eight-edge model advanced one bit early.
        repeat (9) @(posedge sccb_scl);
        @(negedge sccb_scl);
        slave_pull_low = ~expected[7];
        @(posedge sccb_scl);
        for (i = 6; i >= 0; i = i - 1) begin
            @(negedge sccb_scl);
            slave_pull_low = ~expected[i];
            @(posedge sccb_scl);
        end
        @(negedge sccb_scl);
        slave_pull_low = 1'b0;

        wait (done);
        #1;
        if (read_data !== expected)
            $fatal(1, "read_data mismatch: got %02x expected %02x", read_data, expected);
        if (busy !== 1'b0)
            $fatal(1, "busy did not clear after STOP");
        if (start_count != 2 || stop_count != 1)
            $fatal(1, "unexpected START/STOP edges: %0d/%0d", start_count, stop_count);
        $display("PASS: SCCB read returned %02x after repeated START", read_data);
        $finish;
    end

    initial begin
        #100000;
        $fatal(1, "timeout waiting for SCCB read completion");
    end
endmodule
