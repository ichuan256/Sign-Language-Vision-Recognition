`timescale 1ns/1ps

module tb_ov5640_pll_config;
    reg clk = 1'b0;
    reg rst_n = 1'b0;
    reg start = 1'b0;
    reg cfg_ready = 1'b1;
    wire cfg_valid;
    wire [15:0] cfg_reg_addr;
    wire [7:0] cfg_reg_data;
    wire cfg_last;
    wire busy;
    wire done;
    integer accepted = 0;
    integer wait_cycles = 0;
    reg transaction_active = 1'b0;

    always #5 clk = ~clk;

    ov5640_pll_config #(.LAST_CONFIG(1)) dut (
        .clk(clk), .rst_n(rst_n), .start(start),
        .cfg_valid(cfg_valid), .cfg_ready(cfg_ready),
        .cfg_reg_addr(cfg_reg_addr), .cfg_reg_data(cfg_reg_data),
        .cfg_last(cfg_last), .busy(busy), .done(done)
    );

    always @(posedge clk) begin
        if (!rst_n) begin
            cfg_ready <= 1'b1;
            wait_cycles <= 0;
            transaction_active <= 1'b0;
        end else if (cfg_valid && cfg_ready) begin
            case (accepted)
                0: if (cfg_reg_addr !== 16'h3034 || cfg_reg_data !== 8'h18 || cfg_last !== 1'b0) $fatal(1, "bad PLL entry 0");
                1: if (cfg_reg_addr !== 16'h3035 || cfg_reg_data !== 8'h20 || cfg_last !== 1'b0) $fatal(1, "bad PLL entry 1");
                2: if (cfg_reg_addr !== 16'h3036 || cfg_reg_data !== 8'h54 || cfg_last !== 1'b0) $fatal(1, "bad PLL entry 2");
                3: if (cfg_reg_addr !== 16'h3037 || cfg_reg_data !== 8'h13 || cfg_last !== 1'b0) $fatal(1, "bad PLL entry 3");
                4: if (cfg_reg_addr !== 16'h3108 || cfg_reg_data !== 8'h01 || cfg_last !== 1'b1) $fatal(1, "bad PLL entry 4");
                default: $fatal(1, "unexpected extra PLL entry");
            endcase
            accepted <= accepted + 1;
            cfg_ready <= 1'b0;
            wait_cycles <= 0;
            transaction_active <= 1'b1;
        end else if (transaction_active) begin
            wait_cycles <= wait_cycles + 1;
            if (wait_cycles == 2) begin
                cfg_ready <= 1'b1;
                transaction_active <= 1'b0;
            end
        end
    end

    initial begin
        repeat (3) @(posedge clk);
        rst_n = 1'b1;
        @(posedge clk);
        start = 1'b1;
        @(posedge clk);
        start = 1'b0;
        wait (done);
        if (accepted != 5)
            $fatal(1, "expected five accepted PLL writes, got %0d", accepted);
        if (busy !== 1'b0)
            $fatal(1, "busy remained high after done");
        $display("PASS: 5 PLL writes accepted in order");
        $finish;
    end

    initial begin
        #10000;
        $fatal(1, "timeout waiting for PLL register stream");
    end
endmodule
