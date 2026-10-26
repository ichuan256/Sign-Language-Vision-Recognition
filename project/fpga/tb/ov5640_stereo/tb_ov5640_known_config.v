`timescale 1ns/1ps

module tb_ov5640_known_config;
    reg clk=0, rst_n=0, start=0;
    wire reset1, reset2, pwdn1, pwdn2, busy, done, error_flag;
    tri1 scl1, sda1, scl2, sda2;
    wire [31:0] writes1, writes2, reads1, reads2;
    wire [31:0] starts1, starts2, stops1, stops2;
    wire [15:0] address1, address2;
    wire [7:0] value1, value2;
    integer cycles=0, completed_at=0, started_at=0;
    integer seen1=0, seen2=0;
    reg saw_transport=0;
    always #5 clk=~clk;
    always @(posedge clk) cycles=cycles+1;
    ov5640_stereo_known_config #(
        // Scaled clock declaration makes the 300ms wait 300 cycles in this
        // protocol test; full-scale default timing is independently covered.
        .SYS_CLK_HZ(1000), .SCCB_HALF_PERIOD_CYCLES(2),
        .PWDN_SETTLE_CYCLES(3), .RESET_RELEASE_WAIT_CYCLES(4),
        .SCCB_TIMEOUT_CYCLES(10000)
    ) dut (.sys_clk(clk), .rst_n(rst_n), .start(start),
        .ov1_reset_n(reset1), .ov2_reset_n(reset2),
        .ov1_pwdn(pwdn1), .ov2_pwdn(pwdn2),
        .ov1_scl(scl1), .ov1_sda(sda1), .ov2_scl(scl2), .ov2_sda(sda2),
        .busy(busy), .known_config_done(done), .known_config_error(error_flag));
    ov5640_sccb_sensor_model #(.CAMERA(1)) sensor1 (
        .scl(scl1), .sda(sda1), .writes(writes1), .reads(reads1),
        .starts(starts1), .stops(stops1),
        .last_address(address1), .last_value(value1));
    ov5640_sccb_sensor_model #(.CAMERA(2)) sensor2 (
        .scl(scl2), .sda(sda2), .writes(writes2), .reads(reads2),
        .starts(starts2), .stops(stops2),
        .last_address(address2), .last_value(value2));

    function [7:0] expected;
        input [15:0] address;
        input integer camera;
        begin
            case (address)
                16'h4740: expected=(camera==1) ? 8'ha3 : 8'h76;
                16'h3503: expected=(camera==1) ? 8'hd4 : 8'h88;
                16'h3406: expected=(camera==1) ? 8'haa : 8'h7c;
                16'h3c01: expected=(camera==1) ? 8'h92 : 8'ha2;
                16'h3a00: expected=(camera==1) ? 8'h29 : 8'hfa;
                16'h3c00: expected=(camera==1) ? 8'h35 : 8'h8e;
                default: expected=dut.value;
            endcase
        end
    endfunction
    always @(negedge clk) if (rst_n) begin
        if ((dut.u_ov1.read_busy && dut.u_ov1.write_busy) ||
            (dut.u_ov2.read_busy && dut.u_ov2.write_busy))
            $fatal(1, "read and write engines occupied a camera bus together");
        if (scl1 === 1'bx || sda1 === 1'bx || scl2 === 1'bx || sda2 === 1'bx)
            $fatal(1, "SCCB bus contention/unknown");
        if (writes1 != seen1) begin
            if (address1 !== dut.address || value1 !== expected(address1,1))
                $fatal(1, "OV1 address=%04x value=%02x expected=%02x",
                    address1,value1,expected(address1,1));
            seen1=writes1;
        end
        if (writes2 != seen2) begin
            if (address2 !== dut.address || value2 !== expected(address2,2))
                $fatal(1, "OV2 address=%04x value=%02x expected=%02x",
                    address2,value2,expected(address2,2));
            seen2=writes2;
        end
        if (dut.transport_done && !saw_transport) begin
            completed_at=cycles;
            saw_transport=1;
            if (done || !busy) $fatal(1, "final post-delay was bypassed");
        end
    end
    initial begin
        repeat(3) @(negedge clk);
        if (reset1 || reset2 || !pwdn1 || !pwdn2) $fatal(1,"reset outputs");
        rst_n=1;
        @(negedge clk); start=1;
        @(posedge clk); #1; started_at=cycles;
        @(negedge clk); start=0;
        wait(reset1); #1;
        if(cycles-started_at != 3 || !reset2 || pwdn1 || pwdn2)
            $fatal(1,"PWDN/RESET sequence");
        started_at=cycles;
        wait(dut.cfg_ready); #1;
        if(cycles-started_at != 4 || writes1 || writes2)
            $fatal(1,"table applied before reset release wait");
        wait(done); #1;
        if (error_flag || busy || writes1!=27 || writes2!=27 || reads1!=6 || reads2!=6)
            $fatal(1,"wrong completion/counts writes=%0d/%0d reads=%0d/%0d",
                writes1,writes2,reads1,reads2);
        if (!saw_transport || cycles-completed_at < 300 || dut.cfg_ready)
            $fatal(1,"last-item delay/deadlock contract");
        if(starts1!=39 || starts2!=39 || stops1!=33 || stops2!=33)
            $fatal(1,"unexpected START/STOP edges: starts=%0d/%0d stops=%0d/%0d",
                starts1,starts2,stops1,stops2);
        if(sensor1.memory[16'h4740]!==8'ha3 || sensor2.memory[16'h4740]!==8'h76)
            $fatal(1,"independent VSYNC/HREF preservation");
        @(negedge clk); rst_n=0;
        #1;
        if(done || error_flag || busy || reset1 || !pwdn1 || scl1!==1 || sda1!==1)
            $fatal(1,"reset after completion did not return safe state");
        $display("TEST_PASS: 27 dual bus writes, six independent RMW reads per sensor, startup and final delay");
        $finish;
    end
    initial begin #1000000; $fatal(1,"known config watchdog"); end
endmodule
