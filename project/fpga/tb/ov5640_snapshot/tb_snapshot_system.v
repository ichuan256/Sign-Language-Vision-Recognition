`timescale 1ns/1ps
module tb_snapshot_system;
    reg clk=0,pclk=0,rst=0; reg [31:0] control=0;
    reg vs=0,href=0;reg [7:0] data=0; reg ready=1;
    tri1 scl,sda,scl2,sda2;wire reset1,pwdn1,reset2,pwdn2;
    wire [31:0] status,axis_data;wire [3:0] keep;wire av,al;
    wire [31:0] writes,reads,streams;wire [15:0] address;wire [7:0] value;
    reg [2:0] fault=0;integer words=0;reg [31:0] saved[0:63];reg [3:0] saved_keep[0:63];
    reg stalled=0;reg [31:0] stalled_data;reg stalled_last;
    reg pclk_run=1;
    reg physical_vs_invert=0, physical_href_invert=0;
    always #5 clk=~clk;always #6 if(pclk_run) pclk=~pclk;
    ov5640_snapshot #(.SYS_CLK_HZ(1000),.FRAME_WIDTH(4),.FRAME_HEIGHT(2),
        .PWDN_CYCLES(3),.RESET_CYCLES(4),.SCCB_HALF_CYCLES(2),.TIMEOUT_CYCLES(2000)) dut(
        .sys_clk(clk),.sys_reset_n(rst),.control(control),.status(status),
        .ov1_pclk(pclk),.ov1_vsync(vs ^ physical_vs_invert),.ov1_href(href ^ physical_href_invert),.ov1_data(data),
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
                if(keep!==4'hf && !(al && keep===4'h3))$fatal(1,"TKEEP");
                if(al!==(words%4==3))$fatal(1,"TLAST must end frame not line words=%0d",words);
                saved[words]=axis_data;saved_keep[words]=keep;words=words+1;
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
    task manual_transaction;
        input rd; input [15:0] address_in; input [7:0] value_in;
        begin
            @(negedge clk);control={address_in,value_in,rd,~control[6],3'd7,3'b011};
            repeat(8)@(negedge clk);
            wait(status[9]);#1;
            if(status[31:16]!==16'hd167 || status[8] || av || dut.capture_reset_n)
                $fatal(1,"manual ownership/status/capture isolation");
        end
    endtask
    integer i, maintenance_streams;
    // Observe the physical FIFO boundary, not merely the software status.
    always @(posedge pclk) begin
        if (dut.fifo_write && (dut.fifo_reset || dut.wr_busy || dut.fifo_full))
            $fatal(1,"FIFO write during reset/busy/full");
    end
    always @(posedge clk) begin
        if (dut.u_fifo.rd_en && dut.rd_busy) $fatal(1,"FIFO read during reset busy");
    end
    initial begin
        repeat(3)@(negedge clk);start;
        if(!status[1]||status[2]||writes!=309||reads!=30||streams!=1)$fatal(1,"single camera startup");
        if(reset2||!pwdn2||scl2!==1||sda2!==1)$fatal(1,"unselected camera not safe");
        frame(99,0);repeat(10)@(negedge clk);if(words)$fatal(1,"unarmed output");
        arm;ready=0;frame(0,0);repeat(20)@(negedge clk);if(!av||words)$fatal(1,"FIFO buffered output");
        ready=1;wait(words==4);repeat(15)@(negedge clk);
        if(!status[4]||status[5])$fatal(1,"good capture status %h",status);
        for(i=0;i<4;i=i+1)if(saved[i]!==((2*i+1)*65536+2*i))$fatal(1,"frame pixel ordering");
        // A software-control glitch wholly between sys_clk edges must not
        // asynchronously reset the camera or clear the completed status.
        @(negedge clk);#1;control[0]=0;#1;control[0]=1;
        repeat(3)@(negedge clk);
        if(!status[1]||!status[4])$fatal(1,"subcycle GPIO glitch caused reset");
        arm;frame(100,0);wait(words==8);repeat(15)@(negedge clk);
        if(!status[4]||status[5])$fatal(1,"rearm status stale");
        arm;frame(200,1);wait(words==12);repeat(20)@(negedge clk);
        if(!status[4]||status[5])$fatal(1,"short DVP frame must be delivered for PS length validation %h",status);
        if(saved_keep[11]!==4'h3 || saved[11]!==32'd206)
            $fatal(1,"short frame final pixel/TKEEP mismatch data=%h keep=%h",saved[11],saved_keep[11]);
        control[5:3]=1;#1;if(status!==0)$fatal(1,"removed DVP diagnostic page remains visible %h",status);
        // Stop the sensor clock while stale words are buffered, reset from
        // sys_clk, then resume. No stale AXIS word may escape during restart.
        @(negedge pclk);pclk_run=0;ready=0;
        control=0;repeat(20)@(negedge clk);if(status[6:0]||av)$fatal(1,"reset retained status/data");
        // Reinitialize while PCLK is still stopped: stale FIFO must stay gated
        // until the resumed write clock has actually performed reset.
        words=0;fault=0;start;
        repeat(40)@(negedge clk);
        if(av)$fatal(1,"FIFO opened before stopped PCLK delivered reset");
        pclk_run=1;repeat(60)@(negedge clk);
        if(!dut.empty||av)$fatal(1,"FIFO not flushed after stopped-clock reset");
        repeat(40)@(negedge pclk);
        if(av)$fatal(1,"stale data after restart");
        ready=1;arm;frame(0,0);wait(words==4);repeat(15)@(negedge clk);
        for(i=0;i<4;i=i+1)if(saved[i]!==((2*i+1)*65536+2*i))$fatal(1,"restart pixel ordering");
        fault=1;start;if(!status[2]||status[1]||status[13:12]!=1)$fatal(1,"single camera ID fault mapping");
        fault=3;start;if(status[11:8]!=2)$fatal(1,"expected verify failure");
        fault=4;start;if(status[11:8]!=2)$fatal(1,"expected stream verify failure");
        fault=0;control=0;repeat(8)@(negedge clk);
        control=32'h39;repeat(8)@(negedge clk);
        control=32'h3b;repeat(8)@(negedge clk);
        manual_transaction(1,16'h300a,0);if(status[7:0]!==8'h56)$fatal(1,"manual ID");
        manual_transaction(0,16'h3034,8'h18);
        manual_transaction(1,16'h3034,0);if(status[7:0]!==8'h18)$fatal(1,"manual write/read");
        repeat(300)@(negedge clk);if(status[7:0]!==8'h18)$fatal(1,"manual result not retained");
        control=0;repeat(8)@(negedge clk);
        if(reset1 || !pwdn1 || scl!==1 || sda!==1)$fatal(1,"manual reset cleanup");
        start;if(!status[1] || status[2])$fatal(1,"automatic startup after manual");
        // Sensor test-pattern/format edits must survive returning from SCCB
        // maintenance, without resetting the sensor or bypassing startup.
        maintenance_streams=streams;
        control=32'h3b;repeat(12)@(negedge clk);
        if(!dut.init_done || dut.capture_reset_n || !reset1 || pwdn1)
            $fatal(1,"post-init maintenance did not retain safe sensor state");
        manual_transaction(0,16'h503d,8'h80);
        manual_transaction(1,16'h503d,0);
        if(status[7:0]!==8'h80)$fatal(1,"test pattern readback");
        control=1;repeat(80)@(negedge pclk);
        if(!status[1] || status[2] || !reset1 || pwdn1 || streams!=maintenance_streams)
            $fatal(1,"maintenance exit reset or reinitialized sensor");
        words=0;arm;frame(0,0);wait(words==4);repeat(15)@(negedge clk);
        if(!status[4] || status[5])$fatal(1,"capture after maintenance");
        $display("TEST_PASS: initialized maintenance retains sensor/config, blocks capture, resumes strict frame without reinitialization");
        physical_vs_invert=1;physical_href_invert=1;control[9:8]=2'b11;
        words=0;repeat(20)@(negedge pclk);
        frame(50,0);arm;frame(0,0);wait(words==4);repeat(15)@(negedge clk);
        if(!status[4] || status[5])$fatal(1,"configurable input polarity capture");
        for(i=0;i<4;i=i+1)if(saved[i]!==((2*i+1)*65536+2*i))$fatal(1,"polarity pixel ordering");
        $display("TEST_PASS: inverted physical VSYNC/HREF normalized with stable control before arm");
        $display("TEST_PASS: manual SCCB ID/write/read, retained result, capture isolation, reset and automatic restart");
        $display("TEST_PASS: single-camera SCCB startup, unused right camera safe, DVP-to-XPM-to-AXIS order/TLAST/TKEEP/backpressure, short frame delivered for PS length validation, rearm, GPIO glitch filtering, stopped-PCLK reset/flush/restart, FIFO reset/busy/full guards, ID fault mapping");$finish;
    end
    initial begin #20000000;$fatal(1,"snapshot system watchdog status=%h words=%0d",status,words);end
endmodule
