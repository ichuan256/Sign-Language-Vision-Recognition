`timescale 1ns/1ps

module tb_ov5640_stereo_camera_init;
    reg clk = 1'b0;
    reg rst_n = 1'b0;
    reg start = 1'b0;
    reg cfg_valid = 1'b0;
    reg [15:0] cfg_reg_addr = 16'h0000;
    reg [7:0] cfg_reg_data = 8'h00;
    reg cfg_last = 1'b0;
    wire ov1_reset_n, ov1_pwdn, ov2_reset_n, ov2_pwdn;
    wire cfg_ready, config_done, config_error;
    wire sccb_start_ov1, sccb_start_ov2;
    wire [15:0] sccb_reg_addr;
    wire [7:0] sccb_reg_data;
    reg sccb_busy_ov1 = 1'b0, sccb_busy_ov2 = 1'b0;
    reg sccb_done_ov1 = 1'b0, sccb_done_ov2 = 1'b0;
    reg suppress_done = 1'b0;
    integer delay_ov1 = 0, delay_ov2 = 0;
    integer writes = 0;
    reg [15:0] seen_addr [0:1];
    reg [7:0] seen_data [0:1];

    always #5 clk = ~clk;

    ov5640_stereo_camera_init #(
        .PWDN_SETTLE_CYCLES(3),
        .RESET_RELEASE_WAIT_CYCLES(4),
        .SCCB_TIMEOUT_CYCLES(20)
    ) dut (
        .clk(clk), .rst_n(rst_n), .start(start),
        .ov1_reset_n(ov1_reset_n), .ov1_pwdn(ov1_pwdn),
        .ov2_reset_n(ov2_reset_n), .ov2_pwdn(ov2_pwdn),
        .cfg_valid(cfg_valid), .cfg_ready(cfg_ready),
        .cfg_reg_addr(cfg_reg_addr), .cfg_reg_data(cfg_reg_data),
        .cfg_last(cfg_last), .config_done(config_done),
        .config_error(config_error),
        .sccb_start_ov1(sccb_start_ov1), .sccb_start_ov2(sccb_start_ov2),
        .sccb_reg_addr(sccb_reg_addr), .sccb_reg_data(sccb_reg_data),
        .sccb_busy_ov1(sccb_busy_ov1), .sccb_done_ov1(sccb_done_ov1),
        .sccb_busy_ov2(sccb_busy_ov2), .sccb_done_ov2(sccb_done_ov2)
    );

    always @(posedge clk) begin
        sccb_done_ov1 <= 1'b0;
        sccb_done_ov2 <= 1'b0;
        if (!rst_n) begin
            sccb_busy_ov1 <= 1'b0;
            sccb_busy_ov2 <= 1'b0;
            delay_ov1 <= 0;
            delay_ov2 <= 0;
            writes <= 0;
        end else begin
            if (sccb_start_ov1 !== sccb_start_ov2)
                $fatal(1, "stereo start pulses were not simultaneous");
            if (sccb_start_ov1) begin
                if (sccb_busy_ov1 || sccb_busy_ov2)
                    $fatal(1, "a new register started while an engine was busy");
                if (writes >= 2)
                    $fatal(1, "unexpected extra register write");
                seen_addr[writes] = sccb_reg_addr;
                seen_data[writes] = sccb_reg_data;
                writes = writes + 1;
                if (!suppress_done) begin
                    sccb_busy_ov1 <= 1'b1;
                    sccb_busy_ov2 <= 1'b1;
                    delay_ov1 <= 3;
                    delay_ov2 <= 6;
                end
            end
            if (delay_ov1 > 0) begin
                delay_ov1 <= delay_ov1 - 1;
                if (delay_ov1 == 1) begin
                    sccb_busy_ov1 <= 1'b0;
                    sccb_done_ov1 <= 1'b1;
                end
            end
            if (delay_ov2 > 0) begin
                delay_ov2 <= delay_ov2 - 1;
                if (delay_ov2 == 1) begin
                    sccb_busy_ov2 <= 1'b0;
                    sccb_done_ov2 <= 1'b1;
                end
            end
        end
    end

    task pulse_start;
        begin
            @(negedge clk); start = 1'b1;
            @(negedge clk); start = 1'b0;
        end
    endtask

    task send_cfg;
        input [15:0] address;
        input [7:0] value;
        input last_item;
        begin
            wait(cfg_ready);
            @(negedge clk);
            cfg_reg_addr = address;
            cfg_reg_data = value;
            cfg_last = last_item;
            cfg_valid = 1'b1;
            @(negedge clk); cfg_valid = 1'b0;
        end
    endtask

    initial begin
        repeat (3) @(posedge clk);
        #1;
        if (ov1_reset_n || ov2_reset_n || !ov1_pwdn || !ov2_pwdn)
            $fatal(1, "reset state must assert RESET and PWDN on both sensors");
        @(negedge clk); rst_n = 1'b1;
        pulse_start();
        wait(ov1_reset_n);
        #1;
        if (ov1_pwdn || ov2_pwdn || !ov2_reset_n)
            $fatal(1, "RESET released before both sensors left PWDN");
        wait(cfg_ready);
        #1;
        if (!ov1_reset_n || !ov2_reset_n || ov1_pwdn || ov2_pwdn)
            $fatal(1, "configuration became ready before RESET/PWDN sequence completed");

        send_cfg(16'h3008, 8'h82, 1'b0);
        wait(sccb_done_ov1);
        @(posedge clk); #1;
        if (cfg_ready)
            $fatal(1, "configuration advanced after only one SCCB completed");
        send_cfg(16'h4300, 8'h61, 1'b1);
        wait(config_done);
        #1;
        if (config_error || writes != 2 ||
            seen_addr[0] !== 16'h3008 || seen_data[0] !== 8'h82 ||
            seen_addr[1] !== 16'h4300 || seen_data[1] !== 8'h61)
            $fatal(1, "register stream order/payload or terminal status mismatch");

        @(negedge clk); rst_n = 1'b0; suppress_done = 1'b1;
        repeat (2) @(posedge clk);
        @(negedge clk); rst_n = 1'b1;
        pulse_start();
        wait(cfg_ready);
        send_cfg(16'h3808, 8'h07, 1'b1);
        wait(config_error);
        if (config_done)
            $fatal(1, "SCCB timeout incorrectly reported configuration success");

        $display("TEST_PASS: power sequencing, ordered dual writes, completion and timeout");
        $finish;
    end

    initial begin
        #100000;
        $fatal(1, "watchdog timeout");
    end
endmodule
