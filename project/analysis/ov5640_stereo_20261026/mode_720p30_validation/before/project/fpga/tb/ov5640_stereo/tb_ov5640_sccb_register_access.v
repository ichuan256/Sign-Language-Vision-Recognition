`timescale 1ns/1ps
module tb_ov5640_sccb_register_access;
    reg clk=0,rst_n=0,start=0,read_only=0;
    reg [15:0] addr=16'h4740;
    reg [7:0] value=8'h22,mask=8'h23;
    wire busy,done;
    wire [7:0] rd;
    tri1 scl,sda;
    wire [31:0] writes,reads;
    always #5 clk=~clk;
    ov5640_sccb_register_access #(.HALF_PERIOD_CYCLES(2)) dut (
        .clk(clk),.rst_n(rst_n),.start(start),.read_only(read_only),
        .reg_addr(addr),.reg_value(value),.write_mask(mask),
        .busy(busy),.done(done),.read_data(rd),.sccb_scl(scl),.sccb_sda(sda));
    ov5640_sccb_sensor_model sensor(.scl(scl),.sda(sda),.writes(writes),.reads(reads),
        .starts(),.stops(),.last_address(),.last_value());
    always @(negedge clk) if(rst_n) begin
        if(dut.read_busy && dut.write_busy) $fatal(1,"overlapping engines");
        if(scl===1'bx || sda===1'bx) $fatal(1,"pad contention");
    end
    task pulse;
        begin @(negedge clk);start=1;@(negedge clk);start=0;end
    endtask
    task reset_active;
        begin
            @(negedge clk);rst_n=0;#1;
            if(busy || done || scl!==1 || sda!==1) $fatal(1,"active reset pad release");
            repeat(2) @(negedge clk);rst_n=1;
        end
    endtask
    initial begin
        repeat(3) @(negedge clk);rst_n=1;
        pulse();
        // Busy inputs cannot replace the transaction latched at start.
        addr=16'h1234;value=8'hff;mask=8'hff;read_only=1;pulse();
        wait(done);#1;
        if(writes!=1 || reads!=1 || sensor.memory[16'h4740]!==8'ha2 || sensor.memory[16'h1234]!==0)
            $fatal(1,"RMW preserve/latch failed");
        addr=16'h4740;read_only=1;pulse();wait(done);#1;
        if(rd!==8'ha2 || writes!=1 || reads!=2) $fatal(1,"read-only wrote a register");
        read_only=0;mask=0;value=0;pulse();wait(done);#1;
        if(sensor.memory[16'h4740]!==8'ha2 || writes!=2 || reads!=3) $fatal(1,"zero-mask preserve");
        mask=8'hff;value=8'h12;pulse();wait(done);#1;
        if(sensor.memory[16'h4740]!==8'h12 || writes!=3 || reads!=3) $fatal(1,"full-mask direct write");
        read_only=1;pulse();wait(dut.read_busy);reset_active();
        read_only=0;pulse();wait(dut.write_busy);reset_active();
        read_only=0;addr=16'h4321;mask=8'hff;value=8'hab;
        pulse();wait(done);#1;
        if(sensor.memory[16'h4321]!==8'hab) $fatal(1,"reset recovery");
        $display("TEST_PASS: read-only, independent masked/direct/zero-mask accesses, busy latching and mid-engine reset recovery");$finish;
    end
    initial begin #200000; $fatal(1,"access watchdog");end
endmodule
