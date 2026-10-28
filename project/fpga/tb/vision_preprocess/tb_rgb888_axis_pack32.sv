`timescale 1ns/1ps
module tb_rgb888_axis_pack32;
    reg clk=0; always #5 clk=~clk;
    reg reset_n=0;
    reg [23:0] s_axis_tdata=0;
    reg s_axis_tvalid=0, s_axis_tuser=0, s_axis_tlast=0;
    wire s_axis_tready;
    wire [31:0] m_axis_tdata;
    wire [3:0] m_axis_tkeep;
    wire m_axis_tvalid, m_axis_tuser, m_axis_tlast;
    reg m_axis_tready=0;
    rgb888_axis_pack32 dut(.*);
    reg [31:0] rng=32'h13579bdf;
    reg active=0, stalled=0;
    reg [38:0] held_output;
    integer frame_id=0, frame_pixels=0, frame_bytes=0, received=0;
    integer beats=0, checked_frames=0, stalls=0, cycles=0;
    integer byte_index, valid_bytes, n, p, bubble;
    reg [7:0] expected_bytes [0:4095];
    function [7:0] payload;
        input integer f, pixel, channel;
        begin payload=(f*53+pixel*17+channel*71)&255; end
    endfunction
    always @(posedge clk) begin
        cycles=cycles+1;
        if (cycles>200000) $fatal(1,"packer watchdog frame=%0d time=%0t",frame_id,$time);
        if (!reset_n) begin
            rng<=32'h13579bdf; m_axis_tready<=0; stalled<=0;
        end else begin
            rng<={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};
            // Deterministic ready gaps, including runs of several stalled clocks.
            m_axis_tready<=rng[0] && (rng[6:4]!=0);
            if (stalled && {m_axis_tvalid,m_axis_tlast,m_axis_tuser,m_axis_tkeep,m_axis_tdata}!==held_output)
                $fatal(1,"packer output changed under backpressure at %0t",$time);
            stalled<=m_axis_tvalid && !m_axis_tready;
            held_output<={m_axis_tvalid,m_axis_tlast,m_axis_tuser,m_axis_tkeep,m_axis_tdata};
            if (m_axis_tvalid && !m_axis_tready) stalls=stalls+1;
            if (m_axis_tvalid && m_axis_tready) begin
                if (!active) $fatal(1,"packer unexpected output");
                valid_bytes=frame_bytes-received;
                if (valid_bytes>4) valid_bytes=4;
                if (m_axis_tkeep!==((1<<valid_bytes)-1))
                    $fatal(1,"packer keep frame=%0d beat=%0d got=%h bytes=%0d",frame_id,beats,m_axis_tkeep,valid_bytes);
                if (m_axis_tuser!==(received==0) || m_axis_tlast!==((received+valid_bytes)==frame_bytes))
                    $fatal(1,"packer metadata frame=%0d offset=%0d user=%b last=%b",frame_id,received,m_axis_tuser,m_axis_tlast);
                for (byte_index=0;byte_index<valid_bytes;byte_index=byte_index+1)
                    if (m_axis_tdata[byte_index*8+:8]!==expected_bytes[received+byte_index])
                        $fatal(1,"packer byte order frame=%0d byte=%0d got=%h expected=%h",frame_id,received+byte_index,m_axis_tdata[byte_index*8+:8],expected_bytes[received+byte_index]);
                received=received+valid_bytes; beats=beats+1;
            end
        end
    end
    task run_frame;
        input integer pixels;
        integer j, wait_cycles;
        begin
            frame_pixels=pixels; frame_bytes=pixels*3; received=0; beats=0;
            for (j=0;j<pixels;j=j+1) begin
                expected_bytes[j*3]=payload(frame_id,j,0);
                expected_bytes[j*3+1]=payload(frame_id,j,1);
                expected_bytes[j*3+2]=payload(frame_id,j,2);
            end
            active=1;
            for (j=0;j<pixels;j=j+1) begin
                // Valid pauses and data changes only before/after handshakes.
                bubble=(j*7+frame_id)%4;
                repeat(bubble) @(negedge clk);
                s_axis_tdata={payload(frame_id,j,2),payload(frame_id,j,1),payload(frame_id,j,0)};
                s_axis_tuser=(j==0); s_axis_tlast=(j==pixels-1); s_axis_tvalid=1;
                @(posedge clk);
                while (!s_axis_tready) @(posedge clk);
                @(negedge clk); s_axis_tvalid=0;
            end
            wait_cycles=0;
            while (received<frame_bytes) begin
                @(negedge clk); wait_cycles=wait_cycles+1;
                if (wait_cycles>10000) $fatal(1,"packer frame drain timeout");
            end
            active=0; checked_frames=checked_frames+1; frame_id=frame_id+1;
            repeat(2) @(negedge clk);
            if (m_axis_tvalid) $fatal(1,"packer emitted extra/padding beat");
        end
    endtask
    initial begin
        $display("PACKER deterministic seed=13579bdf");
        repeat(5) @(negedge clk); reset_n=1;
        run_frame(1); run_frame(2); run_frame(3); run_frame(4);
        run_frame(5); run_frame(7); run_frame(8); run_frame(17); run_frame(33);
        for (n=0;n<40;n=n+1) run_frame(1+(n*29)%127);
        if (stalls==0) $fatal(1,"packer backpressure not exercised");
        $display("TEST_PASS tb_rgb888_axis_pack32 frames=%0d stalled_cycles=%0d",checked_frames,stalls);
        $finish;
    end
endmodule
