`timescale 1ns/1ps

module tb_ov5640_masked_write;
    reg clk=0, rst_n=0, start=0;
    reg [15:0] address=16'h4740;
    reg [7:0] value=8'h20, mask=8'h20;
    wire busy, done;
    tri1 scl, sda;
    wire [31:0] writes, reads;
    wire [31:0] starts, stops;
    wire [15:0] last_address;
    wire [7:0] last_value;
    always #5 clk=~clk;
    ov5640_sccb_masked_write #(.HALF_PERIOD_CYCLES(2)) dut (
        .clk(clk), .rst_n(rst_n), .start(start), .reg_addr(address),
        .reg_value(value), .write_mask(mask), .busy(busy), .done(done),
        .sccb_scl(scl), .sccb_sda(sda));
    ov5640_sccb_sensor_model sensor (.scl(scl), .sda(sda),
        .starts(starts), .stops(stops),
        .writes(writes), .reads(reads), .last_address(last_address), .last_value(last_value));
    always @(negedge clk) if(rst_n) begin
        if(dut.read_busy && dut.write_busy) $fatal(1,"bus engines overlap");
        if(scl===1'bx || sda===1'bx) $fatal(1,"open-drain contention");
    end
    task pulse;
        begin @(negedge clk); start=1; @(negedge clk); start=0; end
    endtask
    task reset_active;
        begin
            @(negedge clk); rst_n=0; #1;
            if(busy || done || scl!==1 || sda!==1) $fatal(1,"active reset failed to release bus");
            repeat(2) @(negedge clk);
            rst_n=1;
        end
    endtask
    initial begin
        repeat(3) @(negedge clk); rst_n=1;
        pulse();
        // Inputs, including a spurious start, cannot replace a busy request.
        address=16'hffff; value=8'hff; mask=8'hff;
        pulse();
        wait(done); #1;
        if(last_address!==16'h4740 || last_value!==8'ha3 || writes!=1 || reads!=1)
            $fatal(1,"masked request did not latch/preserve bits");
        @(negedge clk); address=16'h4300; value=8'h6f; mask=8'hff;
        pulse(); wait(done); #1;
        if(last_address!==16'h4300 || last_value!==8'h6f || reads!=1 || writes!=2)
            $fatal(1,"full-mask path must write directly without reading");
        if(starts!=4 || stops!=3) $fatal(1,"extra START/STOP around read-modify-write");
        @(negedge clk); address=16'h4740; value=0; mask=8'h20;
        pulse(); wait(dut.read_busy);
        repeat(3) @(negedge clk);
        reset_active();
        @(negedge clk); address=16'h4300; value=8'h12; mask=8'hff;
        pulse(); wait(dut.write_busy);
        repeat(3) @(negedge clk);
        reset_active();
        // A fresh direct write must work after interrupting both engine types.
        address=16'h4300; value=8'h34; mask=8'hff;
        pulse(); wait(done); #1;
        if(last_address!==16'h4300 || last_value!==8'h34)
            $fatal(1,"adapter did not recover after mid-transaction reset");
        $display("TEST_PASS: real SCCB RMW/direct write, latched busy request, mutually exclusive engines, reset recovery");
        $finish;
    end
    initial begin #100000; $fatal(1,"masked-write watchdog"); end
endmodule
