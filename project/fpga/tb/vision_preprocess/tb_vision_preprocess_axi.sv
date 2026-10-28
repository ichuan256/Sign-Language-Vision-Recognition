`timescale 1ns/1ps
module tb_vision_preprocess_axi;
    reg clk=0;
    always #5 clk=~clk;
    reg reset_n=0;
    reg [7:0] s_axi_control_awaddr=0, s_axi_control_araddr=0;
    reg s_axi_control_awvalid=0, s_axi_control_wvalid=0, s_axi_control_arvalid=0;
    wire s_axi_control_awready, s_axi_control_wready, s_axi_control_arready;
    reg [31:0] s_axi_control_wdata=0;
    reg [3:0] s_axi_control_wstrb=0;
    wire [1:0] s_axi_control_bresp, s_axi_control_rresp;
    wire s_axi_control_bvalid, s_axi_control_rvalid;
    reg s_axi_control_bready=0, s_axi_control_rready=0;
    wire [31:0] s_axi_control_rdata;
    wire [0:0] m_axi_read_arid;
    wire [31:0] m_axi_read_araddr;
    wire [7:0] m_axi_read_arlen;
    wire [2:0] m_axi_read_arsize;
    wire [1:0] m_axi_read_arburst;
    wire m_axi_read_arlock;
    wire [3:0] m_axi_read_arcache;
    wire [2:0] m_axi_read_arprot;
    wire m_axi_read_arvalid;
    wire m_axi_read_arready;
    reg [0:0] m_axi_read_rid=0;
    reg [31:0] m_axi_read_rdata=0;
    reg [1:0] m_axi_read_rresp=0;
    reg m_axi_read_rlast=0, m_axi_read_rvalid=0;
    wire m_axi_read_rready;
    wire [31:0] m_axis_tdata;
    wire [3:0] m_axis_tkeep;
    wire m_axis_tuser, m_axis_tlast, m_axis_tvalid;
    reg m_axis_tready=0;
    vision_preprocess_axi dut (.*);
    integer phase=0;
    initial begin #2000000; $fatal(1,"watchdog phase=%0d",phase); end
    integer cycles=0;
    reg ar_gate=1;
    reg [1:0] error_mode=0;
    reg mem_pending=0;
    reg [31:0] saved_addr=0;
    reg [1:0] saved_mode=0;
    reg second_beat=0;
    integer delay_left=0, requests=0, drain_beats=0;
    assign m_axi_read_arready=ar_gate && !mem_pending && ((cycles%4)==0);
    // Deterministic DDR model: two rows [red,green] and [blue,white].
    // The malformed transaction deliberately returns two R beats for ARLEN=0.
    always @(posedge clk) begin
        if (!reset_n) begin
            cycles<=0; mem_pending<=0; m_axi_read_rvalid<=0;
            m_axi_read_rlast<=0; m_axi_read_rresp<=0; requests<=0;
            delay_left<=0; second_beat<=0; drain_beats<=0;
        end else begin
            cycles<=cycles+1;
            if (m_axi_read_arvalid && m_axi_read_arready) begin
                if (mem_pending) $fatal(1,"more than one AXI request outstanding");
                if (m_axi_read_araddr[1:0]!=0 || m_axi_read_arlen!=0 || m_axi_read_arsize!=2 || m_axi_read_arburst!=1 || m_axi_read_arid!=0)
                    $fatal(1,"AXI read attributes/address invalid");
                if (m_axi_read_araddr<32'h1000 || m_axi_read_araddr>=32'h1008)
                    $fatal(1,"DDR address outside fixture: %h",m_axi_read_araddr);
                saved_addr<=m_axi_read_araddr; saved_mode<=error_mode;
                mem_pending<=1; delay_left<=5; second_beat<=0; requests<=requests+1;
            end
            if (mem_pending && !m_axi_read_rvalid) begin
                if (delay_left>0) delay_left<=delay_left-1;
                else begin
                    m_axi_read_rvalid<=1;
                    m_axi_read_rdata<=saved_addr==32'h1000 ? 32'h07e0f800 : 32'hffff001f;
                    m_axi_read_rresp<=(saved_mode==1) ? 2'b10 : 2'b00;
                    m_axi_read_rlast<=(saved_mode!=2 || second_beat);
                end
            end
            if (mem_pending && saved_mode==2 && second_beat && m_axis_tvalid)
                $fatal(1,"sampler received error before malformed R transaction drained");
            if (m_axi_read_rvalid && m_axi_read_rready) begin
                m_axi_read_rvalid<=0;
                if (m_axi_read_rlast) mem_pending<=0;
                else begin second_beat<=1; delay_left<=7; drain_beats<=drain_beats+1; end
            end
        end
    end
    reg [7:0] expected [0:63];
    integer expected_bytes=0, seen_bytes=0, seen_frames=0;
    reg check_stream=0;
    integer lane;
    // Protocol stability checks sample both the stall cycle and release cycle.
    reg prev_axis_stall=0, prev_ar_stall=0, prev_b_stall=0, prev_r_stall=0;
    reg [37:0] held_axis;
    reg [31:0] held_ar;
    reg [1:0] held_b;
    reg [33:0] held_r;
    always @(posedge clk) begin
        if (!reset_n) begin
            prev_axis_stall<=0; prev_ar_stall<=0; prev_b_stall<=0; prev_r_stall<=0;
        end else begin
            if (prev_axis_stall && (!m_axis_tvalid || {m_axis_tlast,m_axis_tuser,m_axis_tkeep,m_axis_tdata}!==held_axis)) $fatal(1,"AXIS changed under backpressure");
            if (prev_ar_stall && (!m_axi_read_arvalid || m_axi_read_araddr!==held_ar)) $fatal(1,"AR changed under backpressure");
            if (prev_b_stall && (!s_axi_control_bvalid || s_axi_control_bresp!==held_b)) $fatal(1,"B changed under backpressure");
            if (prev_r_stall && (!s_axi_control_rvalid || {s_axi_control_rresp,s_axi_control_rdata}!==held_r)) $fatal(1,"R changed under backpressure");
            prev_axis_stall<=m_axis_tvalid && !m_axis_tready;
            prev_ar_stall<=m_axi_read_arvalid && !m_axi_read_arready;
            prev_b_stall<=s_axi_control_bvalid && !s_axi_control_bready;
            prev_r_stall<=s_axi_control_rvalid && !s_axi_control_rready;
            held_axis<={m_axis_tlast,m_axis_tuser,m_axis_tkeep,m_axis_tdata}; held_ar<=m_axi_read_araddr;
            held_b<=s_axi_control_bresp; held_r<={s_axi_control_rresp,s_axi_control_rdata};
            if (m_axis_tvalid && m_axis_tready) begin
                if (!check_stream) $fatal(1,"unexpected stream output phase=%0d",phase);
                if (m_axis_tuser !== (seen_bytes==0)) $fatal(1,"incorrect SOF");
                if (m_axis_tkeep!==4'b1111) $fatal(1,"FP32 TKEEP must always be full");
                for (lane=0;lane<4;lane=lane+1) if (m_axis_tkeep[lane]) begin
                    if (seen_bytes>=expected_bytes) $fatal(1,"too many output bytes");
                    if (m_axis_tdata[8*lane+:8]!==expected[seen_bytes]) $fatal(1,"byte %0d expected %h got %h phase=%0d",seen_bytes,expected[seen_bytes],m_axis_tdata[8*lane+:8],phase);
                    seen_bytes=seen_bytes+1;
                end
                if (m_axis_tlast !== (seen_bytes==expected_bytes)) $fatal(1,"incorrect frame TLAST bytes=%0d expected=%0d",seen_bytes,expected_bytes);
                if (m_axis_tlast) seen_frames=seen_frames+1;
            end
        end
    end
    task automatic aw(input [7:0] addr);
        begin @(negedge clk); s_axi_control_awaddr=addr; s_axi_control_awvalid=1;
            do @(posedge clk); while (!s_axi_control_awready);
            @(negedge clk); s_axi_control_awvalid=0;
        end
    endtask
    task automatic wd(input [31:0] value,input [3:0] strobe);
        begin @(negedge clk); s_axi_control_wdata=value; s_axi_control_wstrb=strobe; s_axi_control_wvalid=1;
            do @(posedge clk); while (!s_axi_control_wready);
            @(negedge clk); s_axi_control_wvalid=0;
        end
    endtask
    task automatic wr(input [7:0] addr,input [31:0] value,input [3:0] strobe,input integer ordering,input [1:0] resp);
        begin
            if (ordering==0) begin aw(addr); repeat(3) @(negedge clk); wd(value,strobe); end
            else if (ordering==1) begin wd(value,strobe); repeat(3) @(negedge clk); aw(addr); end
            else fork aw(addr); wd(value,strobe); join
            wait(s_axi_control_bvalid);
            repeat(4) @(negedge clk);
            if (s_axi_control_bresp!==resp) $fatal(1,"BRESP addr=%h expected=%h got=%h",addr,resp,s_axi_control_bresp);
            s_axi_control_bready=1; @(posedge clk); @(negedge clk); s_axi_control_bready=0;
        end
    endtask
    task automatic rd(input [7:0] addr,input [1:0] resp,output [31:0] value);
        begin
            @(negedge clk); s_axi_control_araddr=addr; s_axi_control_arvalid=1;
            do @(posedge clk); while (!s_axi_control_arready);
            @(negedge clk); s_axi_control_arvalid=0;
            wait(s_axi_control_rvalid); repeat(4) @(negedge clk);
            if (s_axi_control_rresp!==resp) $fatal(1,"RRESP addr=%h",addr);
            value=s_axi_control_rdata;
            s_axi_control_rready=1; @(posedge clk); @(negedge clk); s_axi_control_rready=0;
        end
    endtask
    reg [31:0] value;
    task automatic checkreg(input [7:0] addr,input [31:0] wanted);
        begin rd(addr,0,value); if(value!==wanted) $fatal(1,"register %h expected %h got %h",addr,wanted,value); end
    endtask
    task automatic config_identity(input integer width,input integer height);
        begin
            wr('h10,'h1000,15,0,0); wr('h14,4,15,1,0);
            wr('h18,2,15,2,0); wr('h1c,2,15,0,0);
            wr('h20,width,15,1,0); wr('h24,height,15,2,0);
            wr('h28,'h10000,15,0,0); wr('h2c,0,15,1,0); wr('h30,0,15,2,0);
            wr('h34,0,15,0,0); wr('h38,'h10000,15,1,0); wr('h3c,0,15,2,0);
        end
    endtask
    task automatic expect_image(input integer count,input integer black);
        integer n;
        begin
            @(negedge clk); seen_bytes=0; seen_frames=0; expected_bytes=count; check_stream=1;
            for(n=0;n<count;n=n+1) expected[n]=0;
            if (!black) begin
                // IEEE754 1.0 = little-endian 00 00 80 3f; zeros stay +0.
                expected[2]=8'h80; expected[3]=8'h3f;
                if(count==48) begin
                    expected[18]=8'h80; expected[19]=8'h3f; // green
                    expected[34]=8'h80; expected[35]=8'h3f; // blue
                    expected[38]=8'h80; expected[39]=8'h3f;
                    expected[42]=8'h80; expected[43]=8'h3f;
                    expected[46]=8'h80; expected[47]=8'h3f;
                end
            end
        end
    endtask
    task automatic await_done(input [7:0] err,input integer count);
        integer timeout_count;
        begin
            timeout_count=0; value=0;
            while(!value[1]) begin
                rd('h04,0,value); timeout_count=timeout_count+1;
                if(timeout_count>1000) $fatal(1,"completion poll timed out phase=%0d",phase);
            end
            if(value[0] || value[2]!=(err!=0) || !value[3]) $fatal(1,"completion status %h",value);
            checkreg('h08,err); checkreg('h0c,count);
            if(count>0 && (seen_bytes!=count || seen_frames!=1)) $fatal(1,"incomplete stream");
            rd('h48,0,value); if(value==0) $fatal(1,"cycle counter did not run");
            @(negedge clk); check_stream=0;
        end
    endtask
    integer req_before, n;
    initial begin
        repeat(5) @(negedge clk); reset_n=1;
        phase=1;
        checkreg('h40,'h20000); checkreg('h04,8);
        wr('h10,'h12345678,15,0,0); wr('h10,'haabbccdd,5,1,0); checkreg('h10,'h12bb56dd);
        wr('h10,0,0,2,0); checkreg('h10,'h12bb56dd);
        wr('h40,0,15,0,2); wr('h7c,0,15,1,2); wr('h11,0,15,2,2);
        rd('h7c,2,value); rd('h11,2,value);
        phase=2;
        config_identity(2,2); expect_image(48,0); req_before=requests;
        ar_gate=0; m_axis_tready=0;
        wr(0,1,15,0,0);
        wait(m_axi_read_arvalid); repeat(10) @(negedge clk);
        wr(0,3,15,1,2); // busy START must not clear current status or restart
        wr('h20,1,15,2,0); wr('h24,1,15,0,0); // next-task shadow only
        checkreg('h20,1); checkreg('h24,1);
        ar_gate=1;
        // First FP32 word holds until consumer resumes.
        wait(m_axis_tvalid); repeat(12) @(negedge clk); rd('h04,0,value);
        if(!value[0] || value[1]) $fatal(1,"busy cleared while output stalled");
        @(negedge clk); m_axis_tready=1;
        // Stop specifically at final beat, after sampler has completed.
        wait(seen_bytes==44); @(negedge clk); m_axis_tready=0;
        wait(m_axis_tvalid && m_axis_tlast); repeat(10) @(negedge clk);
        rd('h04,0,value); if(!value[0] || value[1]) $fatal(1,"completion preceded final B-channel TLAST handshake");
        checkreg('h0c,44); // Last B has not been consumed yet.
        wr(0,1,15,2,2);
        @(negedge clk); m_axis_tready=1; await_done(0,48);
        rd('h44,0,value); if(value!=requests-req_before || value<1 || value>4) $fatal(1,"AR counter unreasonable %d",value);
        wr(0,2,15,0,0); checkreg('h04,8); checkreg('h08,0);
        wr(0,1,2,1,0); checkreg('h04,8); // CTRL requires the low-byte strobe
        phase=3;
        expect_image(12,0); wr(0,1,15,1,0); await_done(0,12); // shadow applies; three full FP32 beats
        phase=4;
        wr('h20,'h10001,15,0,0); req_before=requests; wr(0,1,15,1,0); await_done(1,0);
        if(requests!=req_before) $fatal(1,"dimension high bits were silently truncated");
        wr('h20,0,15,0,0); req_before=requests; wr(0,1,15,2,0); await_done(1,0);
        if(requests!=req_before) $fatal(1,"invalid size accessed memory");
        wr('h20,1,15,1,0); wr('h10,'h1002,15,0,0); wr(0,1,15,2,0); await_done(2,0);
        wr('h10,'hfffffffc,15,1,0); wr(0,1,15,0,0); await_done(3,0);
        phase=5;
        config_identity(2,2); expect_image(48,1); error_mode=1; req_before=requests;
        wr(0,1,15,2,0); await_done(4,48);
        if(requests!=req_before+1) $fatal(1,"RRESP failure did not stop later reads");
        checkreg('h44,1);
        phase=6;
        expect_image(48,1); error_mode=2; req_before=requests;
        wr(0,1,15,0,0); await_done(4,48);
        if(requests!=req_before+1 || drain_beats!=1 || mem_pending) $fatal(1,"missing RLAST transaction was not drained exactly once");
        checkreg('h44,1);
        phase=7;
        // Coordinated system reset during a held AR resets both DUT and model.
        error_mode=0; expect_image(48,0); ar_gate=0;
        wr(0,1,15,1,0); wait(m_axi_read_arvalid); repeat(3) @(negedge clk);
        reset_n=0; check_stream=0; repeat(5) @(negedge clk); reset_n=1; ar_gate=1;
        checkreg('h04,8); checkreg('h0c,0); checkreg('h44,0);
        config_identity(1,1); expect_image(12,0); wr(0,1,15,2,0); await_done(0,12);
        $display("TEST_PASS tb_vision_preprocess_axi: AXI-Lite skew/strobes/backpressure, shadow/start, FP32 RGB order/tail byte count, AXI read stalls/errors/drain, completion, reset");
        $finish;
    end
endmodule
