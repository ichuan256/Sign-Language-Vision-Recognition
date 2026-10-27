`timescale 1ns/1ps
module delay_conversion_case #(parameter integer HZ=125000000)(output reg completed=0);
    reg clk=0, rst_n=0, start=0;
    reg [15:0] milliseconds=0;
    reg [1:0] tx_done=0;
    reg [7:0] response=0;
    wire tx_start, tx_read;
    wire [15:0] addr;
    wire error_flag;
    integer i, ticks;
    reg [63:0] expected;
    always #4 clk=~clk;
    ov5640_stereo_startup_controller #(.SYS_CLK_HZ(HZ),
        .PWDN_SETTLE_CYCLES(2),.RESET_RELEASE_WAIT_CYCLES(2),.SCCB_TIMEOUT_CYCLES(20)) dut (
        .clk(clk),.rst_n(rst_n),.start(start),.init_error(error_flag),
        .table_valid(1'b1),.table_last(1'b1),.table_addr(16'h3503),
        .table_value(8'h00),.table_mask(8'hff),.table_delay_ms(milliseconds),
        .tx_start(tx_start),.tx_read_only(tx_read),.tx_addr(addr),
        .tx_busy(2'b00),.tx_done(tx_done),.read_data_ov1(response),.read_data_ov2(response));
    always @(negedge clk) begin
        tx_done=0;
        if (rst_n && tx_start) begin
            response=(addr==16'h300a) ? 8'h56 : 8'h40;
            tx_done=3;
        end
    end
    task restart;
        begin
            @(posedge clk); #1; rst_n=0; start=0;
            repeat(3) @(posedge clk); #1; rst_n=1; start=1;
            @(posedge clk); #1; start=0;
        end
    endtask
    initial begin
        for(i=0;i<14;i=i+1) begin
            case(i)
                0:milliseconds=0; 1:milliseconds=1; 2:milliseconds=2;
                3:milliseconds=20; 4:milliseconds=300; 5:milliseconds=999;
                6:milliseconds=1000; 7:milliseconds=1001; 8:milliseconds=32767;
                9:milliseconds=32768; 10:milliseconds=65534; 11:milliseconds=65535;
                12:milliseconds=16'h5555; 13:milliseconds=16'haaaa;
            endcase
            expected=(64'd1*HZ*milliseconds+999)/1000;
            restart();
            wait(tx_start && !tx_read); #1;
            if(error_flag || dut.delay_cycles!==expected)
                $fatal(1,"conversion HZ=%0d ms=%0d expected=%0d actual=%0d",HZ,milliseconds,expected,dut.delay_cycles);
            wait(dut.state==6); #1;
            if(dut.wait_count!=0) $fatal(1,"post-delay did not start at zero");
            // Real elapsed clocks, independent of the arithmetic implementation.
            if(HZ<=1001 || milliseconds==0) begin
                ticks=0;
                while(dut.state==6) begin @(posedge clk); #1; ticks=ticks+1; end
                if(ticks!=expected+1) $fatal(1,"post-delay HZ=%0d ms=%0d ticks=%0d",HZ,milliseconds,ticks);
            end
            @(posedge clk); #1; rst_n=0;
        end
        milliseconds=65535; restart();
        wait(dut.state==9); repeat(5) @(posedge clk); #1; rst_n=0;
        #1; if(dut.delay_cycles!=0 || tx_start) $fatal(1,"reset during conversion");
        milliseconds=1; restart(); wait(tx_start && !tx_read); #1;
        if(dut.delay_cycles!=(64'd1*HZ+999)/1000) $fatal(1,"conversion restart");
        $display("DELAY_CASE_PASS HZ=%0d vectors=14 reset_restart=1",HZ);
        completed=1;
    end
endmodule
module tb_ov5640_delay_conversion;
    wire [5:0] completed;
    delay_conversion_case #(.HZ(1)) c0(completed[0]);
    delay_conversion_case #(.HZ(999)) c1(completed[1]);
    delay_conversion_case #(.HZ(1001)) c2(completed[2]);
    delay_conversion_case #(.HZ(125000000)) c3(completed[3]);
    delay_conversion_case #(.HZ(125000003)) c4(completed[4]);
    delay_conversion_case #(.HZ(2000000000)) c5(completed[5]);
    initial begin wait(&completed); $display("TEST_PASS: runtime conversion, full 16-bit delays, rounding, elapsed wait and reset restart"); $finish; end
    initial begin #10000000; $fatal(1,"delay conversion watchdog"); end
endmodule
