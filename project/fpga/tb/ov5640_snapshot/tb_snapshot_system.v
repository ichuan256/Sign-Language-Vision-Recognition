`timescale 1ns/1ps
module tb_snapshot_system;
    reg clk=0,pclk=0,rst=0; reg [2:0] control=0;
    reg vs=0,href=0;reg [7:0] data=0; reg ready=1;
    tri1 scl,sda,scl2,sda2;wire reset1,pwdn1,reset2,pwdn2;
    wire [31:0] status,axis_data;wire [3:0] keep;wire av,al;
    wire [31:0] writes,reads,streams;wire [15:0] address;wire [7:0] value;
    reg [2:0] fault=0;integer words=0;reg [31:0] saved[0:63];
    reg stalled=0;reg [31:0] stalled_data;reg stalled_last;
    always #5 clk=~clk;always #6 pclk=~pclk;
    ov5640_snapshot #(.SYS_CLK_HZ(1000),.FRAME_WIDTH(4),.FRAME_HEIGHT(2),
        .PWDN_CYCLES(3),.RESET_CYCLES(4),.SCCB_HALF_CYCLES(2),.TIMEOUT_CYCLES(2000)) dut(
        .sys_clk(clk),.sys_reset_n(rst),.control(control),.status(status),
        .ov1_pclk(pclk),.ov1_vsync(vs),.ov1_href(href),.ov1_data(data),
        .ov2_pclk(1'b0),.ov2_vsync(1'b0),.ov2_href(1'b0),.ov2_data(8'b0),
        .ov1_scl(scl),.ov1_sda(sda),.ov2_scl(scl2),.ov2_sda(sda2),
        .ov1_reset_n(reset1),.ov1_pwdn(pwdn1),.ov2_reset_n(reset2),.ov2_pwdn(pwdn2),
        .m_axis_tdata(axis_data),.m_axis_tkeep(keep),.m_axis_tvalid(av),.m_axis_tready(ready),.m_axis_tlast(al));
    ov5640_startup_sensor_model #(.CAMERA(1)) sensor(.scl(scl),.sda(sda),.reset_n(reset1),
        .fault(fault),.writes(writes),.reads(reads),.stream_writes(streams),.last_address(address),.last_value(value));
    always @(posedge clk) begin
        if(!rst||!control[0])stalled<=0;
        else begin
            if(stalled && (!av || axis_data!==stalled_data || al!==stalled_last))$fatal(1,"AXIS not stable under backpressure");
            stalled<=av&&!ready;stalled_data<=axis_data;stalled_last<=al;
            if(av&&ready)begin
                if(keep!==4'hf)$fatal(1,"TKEEP");
                if(al!==(words%4==3))$fatal(1,"TLAST must end frame not line words=%0d",words);
                saved[words]=axis_data;words=words+1;
            end
        end
    end
    task byte_out;input [7:0] b;begin @(negedge pclk);data=b;end endtask
    task frame;input integer n;input short_line;integer y,x;reg [15:0] pixel;begin
        @(negedge pclk);vs=1;repeat(3)@(negedge pclk);vs=0;repeat(4)@(negedge pclk);
        for(y=0;y<2;y=y+1)begin
            @(negedge pclk);href=1;
            for(x=0;x<(short_line&&y==1?3:4);x=x+1)begin
                pixel=n+y*4+x;data=pixel[7:0];byte_out(pixel[15:8]);@(negedge pclk);
            end
            href=0;repeat(4)@(negedge pclk);
        end
        vs=1;repeat(5)@(negedge pclk);
    end endtask
    task start;begin
        @(negedge clk);control=0;repeat(8)@(negedge clk);rst=1;control=1;
        repeat(8)@(negedge clk);control=3;@(negedge clk);control=1;
        wait(status[1]||status[2]);#1;
    end endtask
    task arm;begin @(negedge clk);control[2]=~control[2];repeat(15)@(negedge pclk);end endtask
    integer i;
    initial begin
        repeat(3)@(negedge clk);start;
        if(!status[1]||status[2]||writes!=309||reads!=30||streams!=1)$fatal(1,"single camera startup");
        if(reset2||!pwdn2||scl2!==1||sda2!==1)$fatal(1,"unselected camera not safe");
        frame(99,0);repeat(10)@(negedge clk);if(words)$fatal(1,"unarmed output");
        arm;ready=0;frame(0,0);repeat(20)@(negedge clk);if(!av||words)$fatal(1,"FIFO buffered output");
        ready=1;wait(words==4);repeat(15)@(negedge clk);
        if(!status[4]||status[5])$fatal(1,"good capture status %h",status);
        for(i=0;i<4;i=i+1)if(saved[i]!==((2*i+1)*65536+2*i))$fatal(1,"frame pixel ordering");
        arm;frame(100,0);wait(words==8);repeat(15)@(negedge clk);
        if(!status[4]||status[5])$fatal(1,"rearm status stale");
        arm;frame(200,1);repeat(20)@(negedge clk);
        if(!status[5]||status[4])$fatal(1,"short frame accepted %h",status);
        control=0;repeat(20)@(negedge clk);if(status[6:0]||av)$fatal(1,"reset retained status/data");
        fault=1;start;if(!status[2]||status[1]||status[13:12]!=1)$fatal(1,"single camera ID fault mapping");
        $display("TEST_PASS: single-camera SCCB startup, unused right camera safe, DVP-to-XPM-to-AXIS order/TLAST/backpressure, rearm, bad frame, reset, ID fault mapping");$finish;
    end
    initial begin #20000000;$fatal(1,"snapshot system watchdog status=%h words=%0d",status,words);end
endmodule
