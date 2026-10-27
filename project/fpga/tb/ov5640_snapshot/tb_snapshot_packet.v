`timescale 1ns/1ps
module tb_snapshot_packet;
    reg clk=0,rst=0,arm=0,pv=0,sof=0,fd=0,fe=0,full=0,fb=0;
    reg [15:0] data=0; wire we,busy,done,error,overflow; wire [32:0] din;
    integer words=0; reg [32:0] memory[0:31];
    always #6 clk=~clk;
    ov5640_snapshot_packet #(.PIXELS(8)) dut(clk,rst,arm,pv,sof,data,fd,fe,full,fb,we,din,busy,done,error,overflow);
    always @(posedge clk) if(we) begin memory[words]=din; words=words+1; end
    task reset; begin @(negedge clk);rst=0;arm=0;pv=0;sof=0;fd=0;fe=0;full=0;fb=0;
        repeat(4) @(negedge clk);rst=1;repeat(4) @(negedge clk);words=0;end endtask
    task launch;begin @(negedge clk);arm=~arm;repeat(5) @(negedge clk);if(!busy)$fatal(1,"arm did not wait for SOF");end endtask
    task pixel;input integer n;input s;begin @(negedge clk);pv=1;sof=s;data=n;
        @(negedge clk);pv=0;sof=0;end endtask
    task finish_frame;input bad;begin @(negedge clk);fd=1;fe=bad;@(negedge clk);fd=0;fe=0;end endtask
    integer i;
    initial begin
        reset; pixel(99,1);finish_frame(0);if(words||done)$fatal(1,"unarmed capture");
        launch;pixel(99,0);finish_frame(1);if(words||error)$fatal(1,"partial previous frame accepted");
        for(i=0;i<8;i=i+1)pixel(i,i==0);
        if(done)$fatal(1,"committed before frame validation");finish_frame(0);
        if(!done||error||busy||words!=4)$fatal(1,"normal frame status");
        for(i=0;i<4;i=i+1)begin
            if(memory[i][15:0]!=2*i||memory[i][31:16]!=2*i+1||memory[i][32]!=(i==3))$fatal(1,"packet word/order/TLAST");end
        launch;for(i=0;i<8;i=i+1)pixel(i+100,i==0);finish_frame(0);
        if(!done||error||words!=8)$fatal(1,"second clean capture");
        reset;launch;for(i=0;i<6;i=i+1)pixel(i,i==0);finish_frame(1);
        if(!error||done||busy)$fatal(1,"short frame accepted");
        repeat(4) @(negedge clk);arm=~arm;repeat(5) @(negedge clk);if(!error||busy)$fatal(1,"error not sticky");
        reset;launch;pixel(0,1);full=1;pixel(1,0);
        if(!error||!overflow||done||words)$fatal(1,"overflow not rejected");
        reset;launch;fb=1;pixel(0,1);if(!error||!overflow)$fatal(1,"FIFO reset busy ignored");
        reset;launch;for(i=0;i<8;i=i+1)pixel(i,i==0);finish_frame(1);
        if(!error||done)$fatal(1,"late bad-frame flag ignored");
        reset;launch;pixel(0,1);pixel(1,1);if(!error||done)$fatal(1,"unexpected SOF ignored");
        reset;launch;for(i=0;i<9;i=i+1)pixel(i,i==0);if(!error||done)$fatal(1,"overlength accepted");
        reset;launch;pixel(0,1);reset;if(busy||done||error||we)$fatal(1,"mid-frame reset");
        $display("TEST_PASS: snapshot packet normal/rearm/SOF gating, RGB565 packing, exact TLAST, short/long/late error, overflow, FIFO busy, reset");$finish;
    end
    initial begin #1000000;$fatal(1,"watchdog");end
endmodule
