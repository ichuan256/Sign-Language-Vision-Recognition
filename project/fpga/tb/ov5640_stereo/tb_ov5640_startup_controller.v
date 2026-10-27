`timescale 1ns/1ps

// Directed transport-boundary faults use public done inputs; no forced DUT
// hierarchy. Physical SCCB decoding is covered in tb_ov5640_stereo_startup.
module startup_controller_case #(parameter integer FAULT=0)(output reg completed=0);
    reg clk=0,rst_n=0,start=0;
    wire busy,done,error_flag,transport_rst_n;
    wire reset1,reset2,pwdn1,pwdn2;
    wire [3:0] error_code;
    wire [1:0] cameras;
    wire [9:0] index;
    wire tx_start,tx_read;
    wire [15:0] addr;
    wire [7:0] value,mask;
    reg [1:0] tx_done=0;
    reg [7:0] rd1=0,rd2=0;
    integer elapsed=0,cycles=0,requests=0,writes=0,verify_reads=0,table_done_at=0;
    reg pending=0;
    wire table_valid=FAULT!=3;
    wire last=FAULT!=4;
    always #5 clk=~clk;
    always @(posedge clk) cycles=cycles+1;
    ov5640_stereo_startup_controller #(.SYS_CLK_HZ(1001),
        .PWDN_SETTLE_CYCLES(3),.RESET_RELEASE_WAIT_CYCLES(4),
        .SCCB_TIMEOUT_CYCLES(20)) dut (
        .clk(clk),.rst_n(rst_n),.start(start),.ov1_reset_n(reset1),.ov1_pwdn(pwdn1),.ov2_reset_n(reset2),.ov2_pwdn(pwdn2),
        .busy(busy),.init_done(done),.init_error(error_flag),.error_code(error_code),.failed_cameras(cameras),
        .table_index(index),.table_valid(table_valid),.table_last(last),
        .table_addr(16'h3503),.table_value(8'h00),.table_mask(8'h03),
        .table_delay_ms(FAULT==4 ? 16'd0 : 16'd300),
        .tx_start(tx_start),.tx_read_only(tx_read),.tx_addr(addr),.tx_value(value),.tx_mask(mask),
        .tx_busy(2'b00),.tx_done(tx_done),.read_data_ov1(rd1),.read_data_ov2(rd2),
        .transport_rst_n(transport_rst_n));
    function [7:0] response;
        input [15:0] a;
        begin
            case(a)
                16'h300a: response=8'h56; 16'h300b: response=8'h40;
                16'h3034: response=8'h18; 16'h3035: response=8'h20;
                16'h3036: response=8'h54; 16'h3037: response=8'h13;
                16'h3108: response=8'h01;
                16'h3808: response=8'h05; 16'h3809: response=8'h00;
                16'h380a: response=8'h02; 16'h380b: response=8'hd0;
                16'h380c: response=8'h07; 16'h380d: response=8'h64;
                16'h380e: response=8'h02; 16'h380f: response=8'he4;
                16'h4300: response=8'h6f; 16'h501f: response=8'h01;
                16'h4740: response=8'ha2; 16'h3008: response=8'h12;
                default: response=8'h00;
            endcase
        end
    endfunction
    always @(negedge clk) begin
        tx_done=0;
        if(!rst_n) begin pending=0; elapsed=0; end
        else if(tx_start) begin
            if(pending) $fatal(1,"controller overlapped requests");
            pending=1; elapsed=0; requests=requests+1;
            rd1=response(addr); rd2=response(addr);
            if(tx_read && addr!=16'h300a && addr!=16'h300b && addr!=16'h3008) verify_reads=verify_reads+1;
            if(!tx_read) begin
                writes=writes+1;
                if(addr==16'h3008 && (verify_reads!=16 || cycles-table_done_at<301))
                    $fatal(1,"stream-on before all verification/delay");
            end
        end else if(pending) begin
            elapsed=elapsed+1;
            if(elapsed==3 && FAULT!=1) tx_done[0]=1;
            if(elapsed==7 && FAULT!=2) begin
                tx_done[1]=1;
                if(addr==16'h3503) table_done_at=cycles;
            end
            if(elapsed==8) pending=0;
        end
    end
    initial begin
        repeat(3) @(negedge clk); rst_n=1;
        @(negedge clk);start=1;@(negedge clk);start=0;
        wait(done || error_flag); #1;
        if(FAULT==0) begin
            if(error_flag || !done || writes!=2 || verify_reads!=16) $fatal(1,"normal controller failed");
            if(dut.ms_cycles(16'd300)!==64'd301) $fatal(1,"round-up delay");
        end else if(FAULT==1 || FAULT==2) begin
            if(!error_flag || error_code!=3 || cameras!==(FAULT==1 ? 2'b01 : 2'b10) || writes)
                $fatal(1,"one-camera timeout mismatch error=%d cam=%b",error_code,cameras);
        end else if(!error_flag || error_code!=4 || cameras!=3 || (FAULT==3 && writes) || (FAULT==4 && index!=1023))
            $fatal(1,"invalid ROM/overflow not rejected");
        if(FAULT!=0 && transport_rst_n) $fatal(1,"failure did not reset transport");
        if(FAULT!=0 && (reset1 || reset2 || !pwdn1 || !pwdn2)) $fatal(1,"failure sensor controls unsafe");
        // Late completion and extra starts never turn failure into success.
        repeat(4) @(negedge clk);
        start=1; tx_done=3; @(negedge clk); start=0;
        repeat(25) @(negedge clk);
        if(FAULT==0 ? !done : (!error_flag || done)) $fatal(1,"terminal result not sticky");
        rst_n=0; #1;
        if(done || error_flag || busy) $fatal(1,"reset failed");
        $display("CONTROL_CASE_PASS fault=%0d requests=%0d writes=%0d",FAULT,requests,writes);
        completed=1;
    end
endmodule

module tb_ov5640_startup_controller;
    wire [4:0] completed;
    startup_controller_case #(.FAULT(0)) c0(completed[0]);
    startup_controller_case #(.FAULT(1)) c1(completed[1]);
    startup_controller_case #(.FAULT(2)) c2(completed[2]);
    startup_controller_case #(.FAULT(3)) c3(completed[3]);
    startup_controller_case #(.FAULT(4)) c4(completed[4]);
    initial begin wait(&completed); $display("TEST_PASS: independent completion, one-camera timeouts, illegal/missing ROM terminator, sticky error and delay rounding"); $finish; end
    initial begin #1000000; $fatal(1,"controller watchdog"); end
endmodule
