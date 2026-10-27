`timescale 1ns/1ps
module startup_defaults_case #(
    parameter integer HZ=100000000, WAIT_EXPECTED=2000000,
    parameter integer HALF_EXPECTED=500, TIMEOUT_EXPECTED=1000000
) (output reg completed=0);
    reg rst_n=0;
    tri1 scl1,sda1,scl2,sda2;
    ov5640_stereo_startup #(.SYS_CLK_HZ(HZ)) dut (
        .sys_clk(1'b0),.rst_n(rst_n),.start(1'b0),
        .ov1_reset_n(),.ov1_pwdn(),.ov2_reset_n(),.ov2_pwdn(),
        .ov1_scl(scl1),.ov1_sda(sda1),.ov2_scl(scl2),.ov2_sda(sda2),
        .busy(),.init_done(),.init_error(),.error_code(),.failed_cameras());
    initial begin
        #2;
        if(dut.PWDN_SETTLE_CYCLES!=WAIT_EXPECTED || dut.RESET_RELEASE_WAIT_CYCLES!=WAIT_EXPECTED ||
            dut.SCCB_HALF_PERIOD_CYCLES!=HALF_EXPECTED || dut.SCCB_TIMEOUT_CYCLES!=TIMEOUT_EXPECTED ||
            dut.u_control.PWDN_SETTLE_CYCLES!=WAIT_EXPECTED || dut.u_control.SCCB_TIMEOUT_CYCLES!=TIMEOUT_EXPECTED)
            $fatal(1,"frequency-derived startup parameters HZ=%0d",HZ);
        if(HZ==100000000 && dut.u_control.ms_cycles(16'd300)!==64'd30000000)
            $fatal(1,"64-bit delay 100MHz * 300ms");
        if(HZ==2000000000 && dut.u_control.ms_cycles(16'd65535)!==64'd131070000000)
            $fatal(1,"64-bit maximum supported frequency/delay");
        $display("DEFAULT_CASE_PASS HZ=%0d wait=%0d half=%0d timeout=%0d",HZ,WAIT_EXPECTED,HALF_EXPECTED,TIMEOUT_EXPECTED);
        completed=1;
    end
endmodule
module tb_ov5640_startup_defaults;
    wire [4:0] completed;
    ov5640_stereo_startup #(.PWDN_SETTLE_CYCLES(7)) override_dut (
        .sys_clk(1'b0),.rst_n(1'b0),.start(1'b0),
        .ov1_reset_n(),.ov1_pwdn(),.ov2_reset_n(),.ov2_pwdn(),
        .ov1_scl(),.ov1_sda(),.ov2_scl(),.ov2_sda(),
        .busy(),.init_done(),.init_error(),.error_code(),.failed_cameras());
    startup_defaults_case c0(completed[0]);
    startup_defaults_case #(.HZ(50000000),.WAIT_EXPECTED(1000000),.HALF_EXPECTED(250),.TIMEOUT_EXPECTED(500000)) c1(completed[1]);
    startup_defaults_case #(.HZ(125000003),.WAIT_EXPECTED(2500001),.HALF_EXPECTED(626),.TIMEOUT_EXPECTED(1250001)) c2(completed[2]);
    startup_defaults_case #(.HZ(1),.WAIT_EXPECTED(1),.HALF_EXPECTED(1),.TIMEOUT_EXPECTED(1)) c3(completed[3]);
    startup_defaults_case #(.HZ(2000000000),.WAIT_EXPECTED(40000000),.HALF_EXPECTED(10000),.TIMEOUT_EXPECTED(20000000)) c4(completed[4]);
    initial begin
        wait(&completed);
        if(override_dut.PWDN_SETTLE_CYCLES!=7 || override_dut.RESET_RELEASE_WAIT_CYCLES!=2000000)
            $fatal(1,"PWDN override changed independent RESET default");
        $display("TEST_PASS: startup parameter rounding, low-frequency clamp and 64-bit delay arithmetic");$finish;
    end
    initial begin #100; $fatal(1,"defaults watchdog");end
endmodule
