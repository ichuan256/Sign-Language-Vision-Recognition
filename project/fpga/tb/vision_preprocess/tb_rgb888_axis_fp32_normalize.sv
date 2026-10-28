`timescale 1ns/1ps
module tb_rgb888_axis_fp32_normalize;
    reg clk=0; always #5 clk=~clk;
    reg reset_n=0;
    reg [23:0] s_axis_tdata=0;
    reg s_axis_tvalid=0, s_axis_tuser=0, s_axis_tlast=0;
    wire s_axis_tready;
    wire [31:0] m_axis_tdata;
    wire [3:0] m_axis_tkeep;
    wire m_axis_tvalid, m_axis_tuser, m_axis_tlast;
    reg m_axis_tready=0;
    rgb888_axis_fp32_normalize dut(.*);
    string vectors;
    // NumPy float32 division oracle from generate_vectors.py. The RTL table
    // is generated separately using exact integer rational rounding.
    reg [31:0] oracle [0:255];
    reg [31:0] expected [0:8191];
    reg expected_user [0:8191], expected_last [0:8191];
    reg [38:0] held;
    reg stalled=0;
    reg [31:0] rng=32'h2468ace1;
    integer ready_mode=0, cycles=0, queued=0, received=0;
    integer frame_id=0, completed=0, stalls=0, reset_tests=0;
    integer accepted_while_last=0;
    reg [255:0] covered_r=0, covered_g=0, covered_b=0;
    function [7:0] payload(input integer pixel, input integer channel);
        begin
            // Each odd affine permutation visits every uint8 value over 256 pixels.
            case(channel)
                0: payload=(pixel+frame_id*13)&255;
                1: payload=(pixel*73+31+frame_id*7)&255;
                default: payload=(pixel*151+97+frame_id*11)&255;
            endcase
        end
    endfunction
    always @(posedge clk) begin
        cycles=cycles+1;
        if(cycles>100000) $fatal(1,"normalizer watchdog received=%0d queued=%0d",received,queued);
        if(!reset_n) begin
            received=0; stalled<=0; m_axis_tready<=0;
        end else begin
            rng<={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};
            case(ready_mode)
                0: m_axis_tready<=0;
                1: m_axis_tready<=1;
                default: m_axis_tready<=rng[0] && rng[3:1]!=0;
            endcase
            if(stalled && {m_axis_tvalid,m_axis_tlast,m_axis_tuser,m_axis_tkeep,m_axis_tdata}!==held)
                $fatal(1,"normalizer output changed during or leaving backpressure");
            stalled<=m_axis_tvalid && !m_axis_tready;
            held<={m_axis_tvalid,m_axis_tlast,m_axis_tuser,m_axis_tkeep,m_axis_tdata};
            if(m_axis_tvalid && !m_axis_tready) stalls=stalls+1;
            if(s_axis_tvalid && s_axis_tready) begin
                covered_r[s_axis_tdata[7:0]]=1;
                covered_g[s_axis_tdata[15:8]]=1;
                covered_b[s_axis_tdata[23:16]]=1;
                if(m_axis_tvalid && m_axis_tready) accepted_while_last=accepted_while_last+1;
            end
            if(m_axis_tvalid && m_axis_tready) begin
                if(received>=queued) $fatal(1,"unexpected normalizer output");
                if(m_axis_tkeep!==4'hf || m_axis_tdata!==expected[received])
                    $fatal(1,"normalizer beat=%0d got=%h expected=%h keep=%h",received,m_axis_tdata,expected[received],m_axis_tkeep);
                if(m_axis_tuser!==expected_user[received] || m_axis_tlast!==expected_last[received])
                    $fatal(1,"normalizer frame metadata beat=%0d",received);
                if(m_axis_tlast) completed=completed+1;
                received=received+1;
            end
        end
    end
    task automatic send_frame(input integer pixels, input integer bubbles);
        integer pixel, channel, offset;
        begin
            offset=queued;
            // Queue the whole frame before the first input can be consumed.
            for(pixel=0;pixel<pixels;pixel=pixel+1)
                for(channel=0;channel<3;channel=channel+1) begin
                    expected[offset+pixel*3+channel]=oracle[payload(pixel,channel)];
                    expected_user[offset+pixel*3+channel]=(pixel==0 && channel==0);
                    expected_last[offset+pixel*3+channel]=(pixel==pixels-1 && channel==2);
                end
            queued=queued+pixels*3;
            for(pixel=0;pixel<pixels;pixel=pixel+1) begin
                if(bubbles) repeat((pixel*7+frame_id)%4) @(negedge clk);
                s_axis_tdata={payload(pixel,2),payload(pixel,1),payload(pixel,0)};
                s_axis_tuser=(pixel==0); s_axis_tlast=(pixel==pixels-1); s_axis_tvalid=1;
                do @(posedge clk); while(!s_axis_tready);
                @(negedge clk); s_axis_tvalid=0;
            end
            frame_id=frame_id+1;
        end
    endtask
    task automatic drain;
        begin
            wait(received==queued);
            repeat(3) @(negedge clk);
            if(m_axis_tvalid) $fatal(1,"extra normalizer output after frame drain");
        end
    endtask
    task automatic reset_during_channel(input integer channel);
        integer base;
        begin
            ready_mode=(channel==0) ? 0 : 1;
            if(channel==0) m_axis_tready=0;
            base=received;
            send_frame(1,0);
            if(channel>0) wait(received==base+channel);
            if(channel>0) @(negedge clk);
            ready_mode=0; m_axis_tready=0;
            wait(m_axis_tvalid); repeat(8) @(negedge clk);
            reset_n=0; s_axis_tvalid=0; queued=0;
            repeat(4) @(negedge clk);
            if(m_axis_tvalid) $fatal(1,"reset retained old output");
            reset_n=1; ready_mode=1; reset_tests=reset_tests+1;
            send_frame(1,0); drain();
        end
    endtask
    initial begin
        if(!$value$plusargs("VECTORS=%s",vectors)) $fatal(1,"VECTORS plusarg required");
        $readmemh({vectors,"/normalize_expected.mem"},oracle);
        repeat(5) @(negedge clk); reset_n=1; ready_mode=1;
        send_frame(256,0); drain(); // exhaustive R/G/B, always-ready
        if(covered_r!=={256{1'b1}} || covered_g!=={256{1'b1}} || covered_b!=={256{1'b1}})
            $fatal(1,"not every uint8 value exercised in each color channel");
        ready_mode=2;
        send_frame(256,1); send_frame(1,0); send_frame(17,1); drain();
        // Hold a complete single pixel for a prolonged output stall.
        ready_mode=0; m_axis_tready=0; send_frame(1,0);
        wait(m_axis_tvalid); repeat(100) @(negedge clk);
        ready_mode=2; drain();
        ready_mode=1;
        // Consecutive frames with no reset or explicit drain between them.
        send_frame(2,0); send_frame(3,0); send_frame(1,0); drain();
        reset_during_channel(0); reset_during_channel(1); reset_during_channel(2);
        if(stalls<100 || accepted_while_last==0 || reset_tests!=3)
            $fatal(1,"normalizer protocol scenarios were not exercised");
        $display("TEST_PASS tb_rgb888_axis_fp32_normalize: all 256 values per RGB channel, NumPy oracle, input bubbles, prolonged/random backpressure, consecutive/single-pixel frames, reset at R/G/B; completed=%0d stalls=%0d",completed,stalls);
        $finish;
    end
endmodule
