`timescale 1ns/1ps
module tb_ov5640_known_config_timeout;
    reg clk=0,rst_n=0,start=0;
    wire busy,done,error_flag,reset1,pwdn1;
    tri1 scl1,sda1,scl2,sda2;
    always #5 clk=~clk;
    ov5640_stereo_known_config #(.PWDN_SETTLE_CYCLES(1),
        .RESET_RELEASE_WAIT_CYCLES(1), .SCCB_HALF_PERIOD_CYCLES(2),
        .SCCB_TIMEOUT_CYCLES(2)) dut (
        .sys_clk(clk),.rst_n(rst_n),.start(start),
        .ov1_reset_n(reset1),.ov1_pwdn(pwdn1),.ov2_reset_n(),.ov2_pwdn(),
        .ov1_scl(scl1),.ov1_sda(sda1),.ov2_scl(scl2),.ov2_sda(sda2),
        .busy(busy),.known_config_done(done),.known_config_error(error_flag));
    initial begin
        repeat(3) @(negedge clk); rst_n=1;
        @(negedge clk); start=1;
        @(negedge clk); start=0;
        wait(error_flag);
        repeat(3) @(negedge clk);
        if(done || busy || dut.u_sequence.table_index!=0 || dut.cfg_valid)
            $fatal(1,"transport timeout advanced/reported success");
        // Even if engines finish later, an error may not turn into success.
        repeat(200) @(negedge clk);
        if(!error_flag || done) $fatal(1,"late engine completion cleared error");
        rst_n=0; #1;
        if(error_flag || done || busy || reset1 || !pwdn1 || scl1!==1 || sda1!==1)
            $fatal(1,"timeout reset did not restore safe state");
        $display("TEST_PASS: real transport timeout, sticky failure despite late completion, reset safe state");
        $finish;
    end
    initial begin #10000; $fatal(1,"timeout test watchdog"); end
endmodule
