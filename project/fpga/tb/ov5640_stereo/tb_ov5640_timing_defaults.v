`timescale 1ns/1ps

// Literal cycle expectations come from the 20 ms / 20 ms / 10 ms contract.
module init_timing_check #(
    parameter integer HZ = 100000000,
    parameter integer WAIT_CYCLES = 2000000,
    parameter integer TIMEOUT_CYCLES = 1000000
) (output reg passed = 0);
    reg clk = 0, rst_n = 0, start = 0, cfg_valid = 0;
    wire reset1, reset2, pwdn1, pwdn2, ready, done, error_flag;
    wire start1, start2;
    integer cycles = 0, edge_at;
    always #5 clk = ~clk;
    always @(posedge clk) cycles = cycles + 1;

    ov5640_stereo_camera_init #(.SYS_CLK_HZ(HZ)) dut (
        .clk(clk), .rst_n(rst_n), .start(start),
        .ov1_reset_n(reset1), .ov2_reset_n(reset2),
        .ov1_pwdn(pwdn1), .ov2_pwdn(pwdn2),
        .cfg_valid(cfg_valid), .cfg_ready(ready),
        .cfg_reg_addr(16'h300a), .cfg_reg_data(8'h00), .cfg_last(1'b1),
        .config_done(done), .config_error(error_flag),
        .sccb_start_ov1(start1), .sccb_start_ov2(start2),
        .sccb_reg_addr(), .sccb_reg_data(),
        .sccb_busy_ov1(1'b0), .sccb_done_ov1(1'b0),
        .sccb_busy_ov2(1'b0), .sccb_done_ov2(1'b0)
    );

    initial begin
        repeat (3) @(negedge clk);
        rst_n = 1;
        @(negedge clk); start = 1;
        @(posedge clk); #1;
        edge_at = cycles;
        if (pwdn1 || pwdn2 || reset1 || reset2 || ready)
            $fatal(1, "HZ=%0d bad PWDN release state", HZ);
        @(negedge clk); start = 0;
        wait (reset1); #1;
        if (cycles - edge_at != WAIT_CYCLES || !reset2 || ready)
            $fatal(1, "HZ=%0d PWDN to RESET cycles=%0d expected=%0d",
                   HZ, cycles-edge_at, WAIT_CYCLES);
        edge_at = cycles;
        wait (ready); #1;
        if (cycles - edge_at != WAIT_CYCLES || pwdn1 || pwdn2)
            $fatal(1, "HZ=%0d RESET to ready cycles=%0d expected=%0d",
                   HZ, cycles-edge_at, WAIT_CYCLES);
        @(negedge clk); cfg_valid = 1;
        @(posedge clk); #1;
        edge_at = cycles;
        if (!start1 || !start2 || ready || done || error_flag)
            $fatal(1, "HZ=%0d transaction handshake mismatch", HZ);
        @(negedge clk); cfg_valid = 0;
        wait (error_flag); #1;
        if (cycles-edge_at != TIMEOUT_CYCLES || done || ready)
            $fatal(1, "HZ=%0d timeout cycles=%0d expected=%0d",
                   HZ, cycles-edge_at, TIMEOUT_CYCLES);
        $display("TIMING_PASS HZ=%0d waits=%0d timeout=%0d", HZ,
                 WAIT_CYCLES, TIMEOUT_CYCLES);
        passed = 1;
    end
endmodule

module top_sccb_timing_check #(
    parameter integer HZ = 100000000,
    parameter integer HALF_CYCLES = 500
) (output reg passed = 0);
    reg clk = 0, rst_n = 0, start = 0, valid = 0;
    wire ready, done, error_flag;
    tri1 scl1, sda1, scl2, sda2;
    integer cycles = 0, edge_at, bit_number;
    always #5 clk = ~clk;
    always @(posedge clk) cycles = cycles + 1;
    ov5640_stereo_camera_top #(
        .FRAME_WIDTH(1), .FRAME_HEIGHT(1), .SYS_CLK_HZ(HZ),
        .PWDN_SETTLE_CYCLES(1), .RESET_RELEASE_WAIT_CYCLES(1)
    ) dut (
        .sys_clk(clk), .rst_n(rst_n), .start_init(start),
        .cfg_valid(valid), .cfg_ready(ready), .cfg_last(1'b1),
        .cfg_reg_addr(16'h3008), .cfg_reg_data(8'h42),
        .config_done(done), .config_error(error_flag),
        .ov1_pclk(1'b0), .ov1_vsync(1'b0), .ov1_href(1'b0), .ov1_data(8'b0),
        .ov2_pclk(1'b0), .ov2_vsync(1'b0), .ov2_href(1'b0), .ov2_data(8'b0),
        .ov1_scl(scl1), .ov1_sda(sda1), .ov2_scl(scl2), .ov2_sda(sda2)
    );
    initial begin
        repeat (3) @(negedge clk);
        rst_n = 1;
        @(negedge clk); start = 1;
        @(negedge clk); start = 0;
        wait (ready);
        @(negedge clk); valid = 1;
        @(negedge clk); valid = 0;
        // Measure actual SCL edges instead of only inspecting the divider.
        @(negedge scl1); #1; edge_at = cycles;
        for (bit_number=0; bit_number<8; bit_number=bit_number+1) begin
            @(posedge scl1); #1;
            if (cycles-edge_at != HALF_CYCLES || scl2 !== 1'b1)
                $fatal(1, "HZ=%0d SCL low half-period mismatch", HZ);
            edge_at = cycles;
            @(negedge scl1); #1;
            if (cycles-edge_at != HALF_CYCLES || scl2 !== 1'b0)
                $fatal(1, "HZ=%0d SCL high half-period mismatch", HZ);
            edge_at = cycles;
        end
        wait (done); #1;
        if (error_flag || scl1 !== 1'b1 || scl2 !== 1'b1)
            $fatal(1, "HZ=%0d default SCCB transfer did not finish", HZ);
        $display("SCCB_TIMING_PASS HZ=%0d half_cycles=%0d", HZ, HALF_CYCLES);
        passed = 1;
    end
endmodule

module tb_ov5640_timing_defaults;
    wire a, b, c, d, e, f;
    init_timing_check init100(a);
    init_timing_check #(.HZ(50000000), .WAIT_CYCLES(1000000),
        .TIMEOUT_CYCLES(500000)) init50(b);
    init_timing_check #(.HZ(125000003), .WAIT_CYCLES(2500001),
        .TIMEOUT_CYCLES(1250001)) init_rounded(c);
    top_sccb_timing_check top100(d);
    top_sccb_timing_check #(.HZ(50000000), .HALF_CYCLES(250)) top50(e);
    top_sccb_timing_check #(.HZ(125000003), .HALF_CYCLES(626)) top_rounded(f);

    // Elaboration edge cases: default omitted, original positional overrides,
    // very low clocks, and a large frequency without arithmetic overflow.
    ov5640_stereo_camera_init default_init();
    ov5640_stereo_camera_init #(3,4,20) positional_init();
    ov5640_stereo_camera_top #(.SYS_CLK_HZ(1)) low_clock();
    ov5640_stereo_camera_top #(.SYS_CLK_HZ(2000000001)) high_clock();
    initial begin
        #1;
        if (default_init.SYS_CLK_HZ != 100000000 ||
            default_init.PWDN_SETTLE_CYCLES != 2000000 ||
            default_init.RESET_RELEASE_WAIT_CYCLES != 2000000 ||
            default_init.SCCB_TIMEOUT_CYCLES != 1000000)
            $fatal(1, "100 MHz omitted-parameter defaults mismatch");
        if (positional_init.PWDN_SETTLE_CYCLES != 3 ||
            positional_init.RESET_RELEASE_WAIT_CYCLES != 4 ||
            positional_init.SCCB_TIMEOUT_CYCLES != 20)
            $fatal(1, "legacy positional overrides changed");
        if (low_clock.PWDN_SETTLE_CYCLES != 1 ||
            low_clock.SCCB_TIMEOUT_CYCLES != 1 ||
            low_clock.SCCB_HALF_PERIOD_CYCLES != 1 ||
            high_clock.PWDN_SETTLE_CYCLES != 40000001 ||
            high_clock.SCCB_TIMEOUT_CYCLES != 20000001 ||
            high_clock.SCCB_HALF_PERIOD_CYCLES != 10001)
            $fatal(1, "rounding/clamping/overflow boundary mismatch");
        wait (a && b && c && d && e && f);
        $display("TEST_PASS: frequency-derived waits/timeouts, SCCB edges, override compatibility");
        $finish;
    end
    initial begin
        #70000000;
        $fatal(1, "timing defaults watchdog timeout");
    end
endmodule
