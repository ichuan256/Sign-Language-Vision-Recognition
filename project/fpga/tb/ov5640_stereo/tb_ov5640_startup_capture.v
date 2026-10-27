`timescale 1ns/1ps
module tb_ov5640_startup_capture;
    reg clk=0,rst_n=0,start=0;
    wire done,error_flag,busy;
    wire reset1,reset2;
    tri1 scl1,sda1,scl2,sda2;
    always #5 clk=~clk;
    reg pclk1=0,enable1=1,vsync1=0,href1=0;
    reg [7:0] data1=0;
    wire valid1,sof1,eol1,frame_done1,frame_error1;
    wire [15:0] pixel1;
    wire [31:0] frame_id1;
    integer pixels1=0,frames1=0;
    always #7 if(enable1) pclk1=~pclk1;
    always @(posedge pclk1) begin
        #1;
        if(!done && (valid1 || frame_done1)) $fatal(1,"capture before startup 1");
        if(valid1) begin
            pixels1=pixels1+1;
            if(pixel1!==16'hf800 || !sof1 || !eol1) $fatal(1,"capture 1 pixel/markers");
        end
        if(frame_done1) begin
            frames1=frames1+1;
            if(frame_error1) $fatal(1,"capture 1 frame error");
        end
    end
    reg pclk2=0,enable2=0,vsync2=0,href2=0;
    reg [7:0] data2=0;
    wire valid2,sof2,eol2,frame_done2,frame_error2;
    wire [15:0] pixel2;
    wire [31:0] frame_id2;
    integer pixels2=0,frames2=0;
    always #11 if(enable2) pclk2=~pclk2;
    always @(posedge pclk2) begin
        #1;
        if(!done && (valid2 || frame_done2)) $fatal(1,"capture before startup 2");
        if(valid2) begin
            pixels2=pixels2+1;
            if(pixel2!==16'h07e0 || !sof2 || !eol2) $fatal(1,"capture 2 pixel/markers");
        end
        if(frame_done2) begin
            frames2=frames2+1;
            if(frame_error2) $fatal(1,"capture 2 frame error");
        end
    end
    ov5640_stereo_startup_capture #(.SYS_CLK_HZ(1000),.FRAME_WIDTH(1),.FRAME_HEIGHT(1),
        .PWDN_SETTLE_CYCLES(2),.RESET_RELEASE_WAIT_CYCLES(2),
        .SCCB_HALF_PERIOD_CYCLES(2),.SCCB_TIMEOUT_CYCLES(2000)) dut (
        .sys_clk(clk),.rst_n(rst_n),.start(start),.init_done(done),.init_error(error_flag),.busy(busy),
        .error_code(),.failed_cameras(),.ov1_reset_n(reset1),.ov2_reset_n(reset2),.ov1_pwdn(),.ov2_pwdn(),
        .ov1_scl(scl1),.ov1_sda(sda1),.ov2_scl(scl2),.ov2_sda(sda2),
        .ov1_pclk(pclk1),.ov1_vsync(vsync1),.ov1_href(href1),.ov1_data(data1),
        .ov1_pixel_valid(valid1),.ov1_pixel_sof(sof1),.ov1_pixel_eol(eol1),.ov1_pixel_data(pixel1),
        .ov1_frame_start(),.ov1_frame_done(frame_done1),.ov1_frame_error(frame_error1),.ov1_frame_id(frame_id1),
        .ov2_pclk(pclk2),.ov2_vsync(vsync2),.ov2_href(href2),.ov2_data(data2),
        .ov2_pixel_valid(valid2),.ov2_pixel_sof(sof2),.ov2_pixel_eol(eol2),.ov2_pixel_data(pixel2),
        .ov2_frame_start(),.ov2_frame_done(frame_done2),.ov2_frame_error(frame_error2),.ov2_frame_id(frame_id2));
    ov5640_startup_sensor_model #(.CAMERA(1)) sensor1 (
        .scl(scl1),.sda(sda1),.reset_n(reset1),.fault(3'd0),
        .writes(),.reads(),.stream_writes(),.last_address(),.last_value());
    task send_frame1;
        begin
            @(negedge pclk1);vsync1=1;
            repeat(2) @(negedge pclk1);vsync1=0;
            repeat(3) @(negedge pclk1);href1=1;data1=8'h00;
            @(negedge pclk1);data1=8'hf8;
            @(negedge pclk1);href1=0;
            repeat(3) @(negedge pclk1);vsync1=1;
            repeat(3) @(negedge pclk1);
        end
    endtask
    ov5640_startup_sensor_model #(.CAMERA(2)) sensor2 (
        .scl(scl2),.sda(sda2),.reset_n(reset2),.fault(3'd0),
        .writes(),.reads(),.stream_writes(),.last_address(),.last_value());
    task send_frame2;
        begin
            @(negedge pclk2);vsync2=1;
            repeat(2) @(negedge pclk2);vsync2=0;
            repeat(3) @(negedge pclk2);href2=1;data2=8'he0;
            @(negedge pclk2);data2=8'h07;
            @(negedge pclk2);href2=0;
            repeat(3) @(negedge pclk2);vsync2=1;
            repeat(3) @(negedge pclk2);
        end
    endtask
    initial begin
        repeat(3) @(negedge clk);rst_n=1;
        @(negedge clk);start=1;@(negedge clk);start=0;
        send_frame1();
        if(pixels1 || frames1) $fatal(1,"pre-init DVP was accepted");
        wait(done || error_flag);#1;
        if(error_flag || !done || pixels1 || frames1 || frame_id2!==0 || dut.u_capture2.reset_sync!==0)
            $fatal(1,"startup failed or stopped PCLK reset released");
        repeat(3) @(negedge clk);
        if(!dut.capture_reset_n || dut.u_capture2.pclk_rst_n!==0)
            $fatal(1,"stopped PCLK released capture reset");
        enable2=1;
        @(posedge pclk2); #1;
        if(dut.u_capture2.pclk_rst_n!==0) $fatal(1,"reset released on first PCLK");
        @(posedge pclk2); #1;
        if(dut.u_capture2.pclk_rst_n!==1) $fatal(1,"reset not released on second PCLK");
        repeat(8) @(negedge pclk1);
        repeat(8) @(negedge pclk2);
        send_frame1();send_frame2();
        if(pixels1!=1 || pixels2!=1 || frames1!=1 || frames2!=1 || frame_id1!=1 || frame_id2!=1)
            $fatal(1,"post-startup PCLK capture mismatch");
        enable2=0;@(negedge clk);rst_n=0;#1;
        if(valid1 || valid2 || frame_id1!==0 || frame_id2!==0)
            $fatal(1,"reset did not assert with PCLK stopped");
        $display("TEST_PASS: init-gated independent PCLK capture, stopped-clock reset and RGB565 markers");$finish;
    end
    initial begin #10000000;$fatal(1,"capture shell watchdog");end
endmodule
