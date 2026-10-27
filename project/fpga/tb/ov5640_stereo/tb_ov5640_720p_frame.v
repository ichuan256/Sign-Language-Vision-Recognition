`timescale 1ns/1ps
// Full production geometry; input changes on falling PCLK and is sampled rising.
module tb_ov5640_720p_frame;
    reg pclk=0,rst_n=0,vsync=0,href=0;
    reg [7:0] data=0;
    wire valid,sof,eol,done,bad;
    wire [15:0] pixel; wire [31:0] frame_id;
    integer seen=0,eols=0,sofs=0,frames=0,errors=0,x,y;
    reg [15:0] expected;
    always #5.952381 pclk=~pclk; // ~84MHz; behavioral, not an STA proof
    ov5640_dvp_capture dut (.rst_n(rst_n),.cam_pclk(pclk),.cam_vsync(vsync),
        .cam_href(href),.cam_data(data),.pixel_valid(valid),.pixel_data(pixel),
        .pixel_sof(sof),.pixel_eol(eol),.frame_start(),.frame_done(done),
        .frame_error(bad),.frame_id(frame_id));
    ov5640_stereo_startup_capture defaults (.sys_clk(1'b0),.rst_n(1'b0),.start(1'b0),
        .ov1_pclk(1'b0),.ov1_vsync(1'b0),.ov1_href(1'b0),.ov1_data(8'd0),
        .ov2_pclk(1'b0),.ov2_vsync(1'b0),.ov2_href(1'b0),.ov2_data(8'd0));
    ov5640_stereo_camera_top legacy_defaults (.sys_clk(1'b0),.rst_n(1'b0),.start_init(1'b0),
        .cfg_valid(1'b0),.cfg_reg_addr(16'd0),.cfg_reg_data(8'd0),.cfg_last(1'b0),
        .ov1_pclk(1'b0),.ov1_vsync(1'b0),.ov1_href(1'b0),.ov1_data(8'd0),
        .ov2_pclk(1'b0),.ov2_vsync(1'b0),.ov2_href(1'b0),.ov2_data(8'd0));
    always @(posedge pclk) begin
        #0.1;
        if(valid) begin
            expected=((seen/1280)<<5) ^ (seen%1280);
            if(pixel!==expected || sof!==(seen==0) || eol!==((seen%1280)==1279))
                $fatal(1,"720p pixel/marker mismatch frame=%0d index=%0d",frames,seen);
            seen=seen+1; if(sof) sofs=sofs+1; if(eol) eols=eols+1;
        end
        if(done) begin frames=frames+1; if(bad)errors=errors+1; end
    end
    task begin_frame;
        begin
            @(negedge pclk);vsync=1;href=0;
            repeat(3)@(negedge pclk);vsync=0;
            repeat(3)@(negedge pclk);
        end
    endtask
    task send_frame;
        input integer short_last;
        reg [15:0] value;
        begin
            seen=0;eols=0;sofs=0;begin_frame();
            for(y=0;y<720;y=y+1) begin
                for(x=0;x<1280-((short_last && y==719)?1:0);x=x+1) begin
                    value=(y<<5)^x;
                    @(negedge pclk);href=1;data=value[7:0];
                    @(negedge pclk);data=value[15:8];
                end
                @(negedge pclk);href=0;repeat(4)@(negedge pclk);
            end
            @(negedge pclk);vsync=1;repeat(3)@(negedge pclk);
            if(seen!=921600-short_last || sofs!=1 || eols!=720-short_last)
                $fatal(1,"720p count mismatch pixels=%0d eols=%0d",seen,eols);
        end
    endtask
    initial begin
        #1;
        if(dut.FRAME_WIDTH!=1280 || dut.FRAME_HEIGHT!=720 || defaults.FRAME_WIDTH!=1280 ||
           defaults.FRAME_HEIGHT!=720 || legacy_defaults.FRAME_WIDTH!=1280 || legacy_defaults.FRAME_HEIGHT!=720)
            $fatal(1,"camera shell defaults differ from 720p mode");
        repeat(5)@(negedge pclk);rst_n=1;repeat(5)@(negedge pclk);
        send_frame(0); if(frames!=1 || errors || frame_id!=1)$fatal(1,"first full 720p frame");
        send_frame(1); if(frames!=2 || errors!=1)$fatal(1,"short last line not rejected");
        send_frame(0); if(frames!=3 || errors!=1 || frame_id!=3)$fatal(1,"recovery after short 720p frame");
        $display("TEST_PASS: 1280x720 RGB565 LE at 84MHz, 921600 pixels/720 EOL/one SOF, short-line error and clean next-frame recovery");
        $finish;
    end
    initial begin #100000000; $fatal(1,"full 720p frame watchdog");end
endmodule
