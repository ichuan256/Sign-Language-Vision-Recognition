`timescale 1ns/1ps

module tb_ov5640_known_config_sequence;
    reg [5:0] rom_index=0;
    wire rom_valid, rom_last;
    wire [15:0] rom_address, rom_delay;
    wire [7:0] rom_value, rom_mask;
    reg [31:0] expected [0:26];
    integer i;
    ov5640_known_config_table rom (.index(rom_index), .valid(rom_valid),
        .reg_addr(rom_address), .reg_value(rom_value), .write_mask(rom_mask),
        .post_delay_ms(rom_delay), .last(rom_last));

    reg clk=0, rst_n=0, start=0, ready=0, tx_done=0, tx_error=0;
    wire [5:0] index;
    wire valid, busy, done, error_flag;
    wire [15:0] delay_ms = (index==0) ? 16'd2 : (index==2) ? 16'd3 : 16'd0;
    integer cycles=0, at_completion;
    reg rom_checked=0;
    always #5 clk=~clk;
    always @(posedge clk) cycles=cycles+1;
    ov5640_known_config_sequencer #(.SYS_CLK_HZ(1001)) dut (
        .clk(clk), .rst_n(rst_n), .start(start), .table_index(index),
        .table_valid(index<3), .table_last(index==2), .table_delay_ms(delay_ms),
        .cfg_valid(valid), .cfg_ready(ready), .transport_done(tx_done),
        .transport_error(tx_error), .busy(busy), .done(done), .error_flag(error_flag));
    // Check the production 100MHz x 300ms conversion independently of the
    // shortened dynamic wait; a 32-bit intermediate would overflow here.
    ov5640_known_config_sequencer #(.SYS_CLK_HZ(100000000)) full_scale_delay (
        .clk(clk), .rst_n(rst_n), .start(1'b0), .table_index(),
        .table_valid(1'b1), .table_last(1'b1), .table_delay_ms(16'd300),
        .cfg_valid(), .cfg_ready(1'b0), .transport_done(1'b0),
        .transport_error(1'b0), .busy(), .done(), .error_flag());

    initial begin
        #1;
        if(full_scale_delay.delay_cycles !== 64'd30000000)
            $fatal(1,"100MHz 300ms delay arithmetic overflow");
        expected[0]=32'h303418ff; expected[1]=32'h303520ff;
        expected[2]=32'h303654ff; expected[3]=32'h303713ff;
        expected[4]=32'h310801ff; expected[5]=32'h380805ff;
        expected[6]=32'h380900ff; expected[7]=32'h380a02ff;
        expected[8]=32'h380bd0ff; expected[9]=32'h380c07ff;
        expected[10]=32'h380d64ff; expected[11]=32'h380e02ff;
        expected[12]=32'h380fe4ff; expected[13]=32'h43006fff;
        expected[14]=32'h501f01ff; expected[15]=32'h47402020;
        expected[16]=32'h3a0800ff; expected[17]=32'h3a09ddff;
        expected[18]=32'h3a0a00ff; expected[19]=32'h3a0bb8ff;
        expected[20]=32'h3a0d04ff; expected[21]=32'h3a0e03ff;
        expected[22]=32'h3c018080; expected[23]=32'h3a002024;
        expected[24]=32'h35030003; expected[25]=32'h34060001;
        expected[26]=32'h3c000404;
        for(i=0;i<64;i=i+1) begin
            rom_index=i; #1;
            if(i<27) begin
                if(!rom_valid || {rom_address,rom_value,rom_mask}!==expected[i] ||
                    rom_last!==(i==26) || rom_delay!==((i==26)?16'd300:16'd0))
                    $fatal(1,"table entry %0d mismatch",i);
            end else if(rom_valid || rom_last || rom_mask!==0)
                $fatal(1,"invalid table address %0d accepted",i);
        end
        rom_checked=1;
    end
    task launch;
        begin
            @(negedge clk); start=1;
            @(negedge clk); start=0;
            wait(valid);
        end
    endtask
    task accept_and_complete;
        input integer item;
        begin
            wait(valid); #1;
            if(index!=item) $fatal(1,"wrong table order");
            // Producer must not move the selected row under backpressure.
            repeat(5) begin
                @(negedge clk);
                if(!valid || index!=item || done) $fatal(1,"unstable backpressure");
            end
            ready=1;
            @(negedge clk); ready=0;
            repeat(4) @(negedge clk);
            if(valid || index!=item || done) $fatal(1,"advanced before transport completion");
            if(item==2) tx_done=1;
            else ready=1;
            @(posedge clk); #1; at_completion=cycles;
        end
    endtask
    initial begin
        repeat(3) @(negedge clk); rst_n=1;
        launch();
        accept_and_complete(0);
        wait(valid); #1;
        // ceil(1001 Hz * 2ms)=3. The state transition may add overhead,
        // but must never offer the next item before those three clocks.
        if(cycles-at_completion<3 || index!=1) $fatal(1,"non-last post-delay too short");
        @(negedge clk); ready=0;
        accept_and_complete(1);
        wait(valid); #1;
        if(index!=2) $fatal(1,"zero-delay item order");
        @(negedge clk); ready=0;
        accept_and_complete(2);
        wait(done); #1;
        if(cycles-at_completion<4 || ready || busy || error_flag || index!=2)
            $fatal(1,"last-item delay or terminal-done handshake");
        repeat(3) @(negedge clk);
        if(!done || valid) $fatal(1,"completion not sticky");
        rst_n=0; #1;
        if(done || busy || error_flag) $fatal(1,"reset after done");
        @(negedge clk); rst_n=1; tx_done=0;
        launch();
        @(negedge clk); tx_error=1;
        @(negedge clk);
        if(!error_flag || busy || valid || done) $fatal(1,"transport-error propagation");
        tx_error=0;
        repeat(3) @(negedge clk);
        if(!error_flag) $fatal(1,"error not sticky");
        rst_n=0; #1;
        if(error_flag || done || valid) $fatal(1,"reset during error");
        wait(rom_checked);
        $display("TEST_PASS: exact 27-row table, invalid indices, backpressure, rounded intermediate/final delays and errors");
        $finish;
    end
    initial begin #100000; $fatal(1,"sequence watchdog"); end
endmodule
