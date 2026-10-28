`timescale 1ns/1ps
module tb_snapshot_720p;
    reg clk=0,pclk=0,rst=0; reg [31:0] control=0;
    reg vs=0,href=0;reg [7:0] data=0; reg ready=1;
    tri1 scl,sda,scl2,sda2;wire reset1,pwdn1,reset2,pwdn2;
    wire [31:0] status,axis_data;wire [3:0] keep;wire av,al;
    wire [31:0] writes,reads,streams;wire [15:0] address;wire [7:0] value;
    reg [2:0] fault=0;integer words=0,cycles=0;reg [31:0] expected;reg score=1;
    reg stalled=0;reg [31:0] stalled_data;reg stalled_last;
    always #5 clk=~clk;always #6 pclk=~pclk;
    ov5640_snapshot #(.SYS_CLK_HZ(1000),.FRAME_WIDTH(1280),.FRAME_HEIGHT(720),
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
                if(al!==(words%460800==460799))$fatal(1,"TLAST must end frame not line words=%0d",words);
                expected=(((2*(words%460800)+1+(words/460800)*100)&65535)*65536)+((2*(words%460800)+(words/460800)*100)&65535); if(score && axis_data!==expected)$fatal(1,"pixel mismatch %0d got=%h expected=%h",words,axis_data,expected);words=words+1;
            end
        end
    end
    task byte_out;input [7:0] b;begin @(negedge pclk);data=b;end endtask
    task frame;input integer n;input short_line;integer y,x;reg [15:0] pixel;begin
        @(negedge pclk);vs=1;repeat(3)@(negedge pclk);vs=0;repeat(4)@(negedge pclk);
        for(y=0;y<720;y=y+1)begin
            @(negedge pclk);href=1;
            for(x=0;x<(short_line&&y==719?1279:1280);x=x+1)begin
                pixel=n+y*1280+x;data=pixel[7:0];byte_out(pixel[15:8]);@(negedge pclk);
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
    always @(negedge clk) begin
        cycles=cycles+1;
        if(score)ready=(cycles%128>=16);
    end
    integer j;
    initial begin
        repeat(3)@(negedge clk);start;
        if(!status[1]||status[2])$fatal(1,"720p startup");
        arm;frame(0,0);wait(words==460800);repeat(20)@(negedge clk);
        if(!status[4]||status[5])$fatal(1,"first 720p status %h",status);
        arm;frame(100,0);wait(words==921600);repeat(20)@(negedge clk);
        if(!status[4]||status[5])$fatal(1,"720p rearm %h",status);
        score=0;ready=0;arm;
        @(negedge pclk);vs=0;repeat(4)@(negedge pclk);
        for(j=0;j<10;j=j+1)begin
            @(negedge pclk);href=1;
            repeat(1280)begin data=8'h55;byte_out(8'haa);@(negedge pclk);end
            href=0;repeat(4)@(negedge pclk);
        end
        repeat(20)@(negedge clk);
        if(!status[5]||!status[6]||status[4])$fatal(1,"FIFO overflow not rejected %h",status);
        control=0;repeat(20)@(negedge clk);
        if(status[6:0]||av)$fatal(1,"720p reset retained data/status");
        $display("TEST_PASS: two 1280x720 frames, 921600 ordered AXIS words, final-only TLAST, periodic backpressure, rearm, FIFO overflow, reset");$finish;
    end
    initial begin #120000000;$fatal(1,"720p watchdog status=%h words=%0d",status,words);end
endmodule
