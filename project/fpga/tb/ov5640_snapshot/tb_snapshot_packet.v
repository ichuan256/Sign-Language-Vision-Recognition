`timescale 1ns/1ps
module tb_snapshot_packet;
    reg clk=0,rst=0,arm=0,fs=0,pv=0,sof=0,fd=0,full=0,fb=0;
    reg [15:0] data=0;
    wire we,busy,done,error,overflow;
    wire [33:0] din;
    integer words=0;
    reg [33:0] memory[0:31];
    always #6 clk=~clk;
    ov5640_snapshot_packet #(.PIXELS(8)) dut(
        .pclk(clk),.rst_n(rst),.arm_toggle(arm),.frame_start(fs),
        .pixel_valid(pv),.pixel_sof(sof),.pixel_data(data),
        .frame_done(fd),.fifo_full(full),.fifo_busy(fb),
        .fifo_wr_en(we),.fifo_din(din),.busy(busy),.done(done),
        .error(error),.overflow(overflow));
    always @(posedge clk) if(we) begin memory[words]=din; words=words+1; end
    task reset;
        begin
            @(negedge clk);rst=0;arm=0;fs=0;pv=0;sof=0;fd=0;full=0;fb=0;
            repeat(4) @(negedge clk);rst=1;repeat(4) @(negedge clk);words=0;
        end
    endtask
    task launch;
        begin @(negedge clk);arm=~arm;repeat(5) @(negedge clk);if(!busy)$fatal(1,"arm did not wait for SOF");end
    endtask
    task frame_start;
        begin @(negedge clk);fs=1;@(negedge clk);fs=0;end
    endtask
    task pixel;
        input integer n;input s;
        begin @(negedge clk);pv=1;sof=s;data=n;@(negedge clk);pv=0;sof=0;end
    endtask
    task finish_frame;
        begin @(negedge clk);fd=1;@(negedge clk);fd=0;end
    endtask
    integer i;
    initial begin
        reset; pixel(99,1);finish_frame();if(words||done)$fatal(1,"unarmed capture");
        launch;pixel(99,0);finish_frame();if(words||error||!busy)$fatal(1,"mid-frame arm should skip partial frame");
        frame_start;for(i=0;i<8;i=i+1)pixel(i,i==0);
        if(done)$fatal(1,"committed before frame closes");finish_frame();
        repeat(3) @(negedge clk);if(!done||error||busy||words!=4)$fatal(1,"normal frame status");
        for(i=0;i<4;i=i+1)begin
            if(memory[i][15:0]!=2*i||memory[i][31:16]!=2*i+1||memory[i][32]!=(i==3)||memory[i][33])
                $fatal(1,"packet word/order/TLAST/TKEEP index=%0d value=%h",i,memory[i]);
        end
        reset;launch;frame_start;
        for(i=0;i<5;i=i+1)pixel(i,i==0);
        finish_frame();
        repeat(3) @(negedge clk);if(!done||error||busy||words!=3)$fatal(1,"partial frame must terminate cleanly");
        if(memory[2][32:0]!=={1'b1,16'b0,16'd4}||memory[2][33]!==1'b1)
            $fatal(1,"one-pixel TKEEP/TLAST encoding %h",memory[2]);
        reset;launch;frame_start;
        for(i=0;i<6;i=i+1)pixel(i,i==0);
        finish_frame();
        repeat(3) @(negedge clk);if(!done||error||words!=3)$fatal(1,"packet layer must deliver short stream for PS thresholding");
        reset;launch;frame_start;fd=1;@(negedge clk);fd=0;
        if(!error||done||busy)$fatal(1,"empty armed frame must fail rather than hang DMA");
        repeat(4) @(negedge clk);arm=~arm;repeat(5) @(negedge clk);if(!error||busy)$fatal(1,"error not sticky");
        reset;launch;frame_start;pixel(0,1);pixel(1,0);full=1;pixel(2,0);pixel(3,0);
        if(!error||!overflow||done||words)$fatal(1,"overflow not rejected");
        reset;launch;frame_start;pixel(0,1);pixel(1,0);fb=1;pixel(2,0);pixel(3,0);
        if(!error||!overflow)$fatal(1,"FIFO reset busy ignored");
        reset;launch;frame_start;for(i=0;i<8;i=i+1)pixel(i,i==0);finish_frame();
        repeat(3) @(negedge clk);if(!done||error)$fatal(1,"full packet must complete without a geometry-error input");
        reset;launch;frame_start;pixel(0,1);pixel(1,1);if(!error||done)$fatal(1,"unexpected SOF ignored");
        reset;launch;frame_start;for(i=0;i<9;i=i+1)pixel(i,i==0);if(!error||done)$fatal(1,"overlength accepted");
        reset;launch;frame_start;pixel(0,1);reset;if(busy||done||error||we)$fatal(1,"mid-frame reset");
        $display("TEST_PASS: normal/short packet TLAST and TKEEP, mid-frame arm skip, empty frame timeout prevention, overflow, SOF/length guards and reset");$finish;
    end
    initial begin #1000000;$fatal(1,"watchdog");end
endmodule
