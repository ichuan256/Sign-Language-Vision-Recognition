`timescale 1ns/1ps
// W5 merge integration: exact reference quaternions, matching and invalid IMUs.
// mahony_pe arithmetic is checked separately by its numerical-vector regression.
//
// 2026-10-18: frame extended 132B -> 164B so each hand carries BOTH IMU
// quaternions (IMU#0 wrist/back-of-hand + IMU#1 forearm). Four reference cores
// mirror the four DUT cores so the forearm half is checked independently.
// Gyro stimulus below uses the current W5 32.8 LSB/(deg/s) conversion:
// 1640/3280/4920/6560 are +50/+100/+150/+200 deg/s.
module tb_merge132;

reg clk = 0, rst_n = 0;
always #5 clk = ~clk;

reg [7:0] l_tdata = 0, r_tdata = 0;
reg l_tvalid = 0, l_tlast = 0, r_tvalid = 0, r_tlast = 0;
wire l_tready, r_tready;
wire [7:0] m_tdata;
wire m_tvalid, m_tlast;
reg m_tready = 1;
wire [15:0] stat_r_timeout;

merge_stream132 #(.TIMEOUT_CYCLES(500)) dut (
    .clk(clk), .rst_n(rst_n),
    .s_axis_l_tdata(l_tdata), .s_axis_l_tvalid(l_tvalid),
    .s_axis_l_tlast(l_tlast), .s_axis_l_tready(l_tready),
    .s_axis_r_tdata(r_tdata), .s_axis_r_tvalid(r_tvalid),
    .s_axis_r_tlast(r_tlast), .s_axis_r_tready(r_tready),
    .m_axis_tdata(m_tdata), .m_axis_tvalid(m_tvalid),
    .m_axis_tlast(m_tlast), .m_axis_tready(m_tready),
    .stat_r_timeout(stat_r_timeout), .busy()
);

// The reference cores see only the samples accepted by the intended contract.
// Reference resets follow merged-frame history, independently of DUT state.
// Four cores: index 0=left IMU#0, 1=left IMU#1, 2=right IMU#0, 3=right IMU#1.
reg [3:0] ref_rst_n = 4'b0000;
reg [3:0] ref_valid = 0;
reg signed [15:0] ref_gz [0:3];
wire [3:0] ref_out_valid;
wire signed [31:0] ref_w [0:3], ref_x [0:3], ref_y [0:3], ref_z [0:3];
reg [1:0] ref_segment = 2'b00;
reg [31:0] ref_previous [0:1];

genvar gi;
generate
    for (gi = 0; gi < 4; gi = gi + 1) begin : gen_ref
        mahony_pe ref_pe (
            .clk(clk), .rst_n(ref_rst_n[gi]), .in_valid(ref_valid[gi]),
            .ax(16'sd0), .ay(16'sd0), .az(16'sd4096),
            .gx(16'sd0), .gy(16'sd0), .gz(ref_gz[gi]),
            .out_valid(ref_out_valid[gi]),
            .qw(ref_w[gi]), .qx(ref_x[gi]), .qy(ref_y[gi]), .qz(ref_z[gi])
        );
    end
endgenerate

integer errors = 0, frames_checked = 0, fcnt = 0;
localparam integer FRAME_BYTES = 164;
reg [7:0] frame [0:FRAME_BYTES-1];
reg [31:0] exp_ts;
reg exp_r_miss;
reg [1:0] exp_l_absent, exp_r_absent;
// Per-IMU signed z gyro used to build the stimulus (index 0..3 as above).
reg signed [15:0] exp_gz [0:3];
reg [127:0] exp_quat [0:3];
// A scenario is configured once; both the input driver and reference model
// consume these same values. This prevents expected-vs-driven IMU drift.
reg [31:0] cfg_ts;
reg cfg_r_missing;
reg [1:0] cfg_l_absent, cfg_r_absent;
reg signed [15:0] cfg_gz [0:3];
reg stalled = 0, held_last;
reg [7:0] held_data;
integer stalled_cycles = 0, quat_stalled_cycles = 0, last_stalled_cycles = 0;

// IMU#0 = bytes [0..13], IMU#1 = bytes [14..27] (each 7x int16: ax ay az temp gx gy gz).
// acc = (0,0,1g), nonzero temperature, signed z gyro per device.
// ADC samples distinguish both hands and the five active channels. Every raw
// byte is checked, including the inactive channels and the full timestamp.
function automatic [7:0] stim_byte(
    input integer i, input [7:0] base, input [31:0] ts,
    input signed [15:0] gz0, input signed [15:0] gz1, input [1:0] absent
);
    reg [15:0] adc_value;
    reg signed [15:0] gz;
    integer rel;
    begin
        if ((i < 14 && absent[0]) ||
            (i >= 14 && i < 28 && absent[1]))
            stim_byte = 8'hEE;
        else if (i >= 28 && i < 44) begin
            // Five sampled MCP3008 channels: 0..1023; CH5..CH7 are zero.
            adc_value = (i < 38) ? base + ((i - 28) / 2) * 137 : 0;
            stim_byte = i[0] ? adc_value[7:0] : adc_value[15:8];
        end
        else if (i >= 44) begin
            case (i)
                44: stim_byte = ts[31:24];
                45: stim_byte = ts[23:16];
                46: stim_byte = ts[15:8];
                47: stim_byte = ts[7:0];
                default: stim_byte = base + i[7:0];
            endcase
        end
        else begin
            // Position of this byte inside its own 14B IMU block.
            rel = (i >= 14) ? (i - 14) : i;
            gz  = (i >= 14) ? gz1 : gz0;
            case (rel)
                0,1,2,3,5,8,9,10,11: stim_byte = 0;
                4:  stim_byte = 8'h10; // 1g at MPU6500 +/-8g
                6:  stim_byte = 8'hA1;
                7:  stim_byte = 8'hB2;
                12: stim_byte = gz[15:8];
                13: stim_byte = gz[7:0];
                default: stim_byte = base + i[7:0];
            endcase
        end
    end
endfunction

// Configure each logical merged frame exactly once. The driver and model
// tasks below both use this shared scenario state.
task configure_left(
    input [31:0] ts, input right_missing, input [1:0] absent,
    input signed [15:0] gz0, input signed [15:0] gz1
);
    begin
        cfg_ts = ts; cfg_r_missing = right_missing;
        cfg_l_absent = absent;
        cfg_gz[0] = gz0; cfg_gz[1] = gz1;
    end
endtask

task configure_frame(
    input [31:0] ts, input right_missing,
    input [1:0] left_absent, input [1:0] right_absent,
    input signed [15:0] l0gz, input signed [15:0] l1gz,
    input signed [15:0] r0gz, input signed [15:0] r1gz
);
    begin
        configure_left(ts, right_missing, left_absent, l0gz, l1gz);
        cfg_r_absent = right_absent;
        cfg_gz[2] = r0gz; cfg_gz[3] = r1gz;
    end
endtask

// Hold each source byte until a real input handshake. Waits are bounded so a
// broken ready path fails at the scenario that exposed it, rather than hanging.
task automatic send_hand_payload(
    input left, input [31:0] ts,
    input signed [15:0] gz0, input signed [15:0] gz1,
    input [1:0] absent
);
    integer i, ticks, accepted;
    begin
        for (i = 0; i < 48; i = i + 1) begin
            @(negedge clk);
            if (left) begin
                l_tdata = stim_byte(i, 8'h10, ts, gz0, gz1, absent);
                l_tvalid = 1;
                l_tlast = (i == 47);
            end else begin
                r_tdata = stim_byte(i, 8'h40, ts, gz0, gz1, absent);
                r_tvalid = 1;
                r_tlast = (i == 47);
            end
            ticks = 0;
            accepted = 0;
            while (!accepted && ticks < 4096) begin
                @(posedge clk);
                if ((left ? l_tready : r_tready) === 1'b1)
                    accepted = 1;
                else
                    ticks = ticks + 1;
            end
            if (!accepted) begin
                $display("TEST FAILED: input ready timeout side=%0d byte=%0d",left,i);
                $finish;
            end
        end
        @(negedge clk);
        if (left) begin l_tvalid = 0; l_tlast = 0; end
        else begin r_tvalid = 0; r_tlast = 0; end
    end
endtask

task automatic send_hand_at(input left, input [31:0] ts);
    begin
        if (left)
            send_hand_payload(1, ts, cfg_gz[0], cfg_gz[1], cfg_l_absent);
        else
            send_hand_payload(0, ts, cfg_gz[2], cfg_gz[3], cfg_r_absent);
    end
endtask

task automatic send_hand(input left);
    begin
        send_hand_at(left, cfg_ts);
    end
endtask

task wait_for_frames(input integer target);
    integer ticks;
    begin
        ticks = 0;
        while (frames_checked < target && ticks < 20000) begin
            @(negedge clk);
            ticks = ticks + 1;
        end
        if (frames_checked < target) begin
            $display("TEST FAILED: frame wait timeout target=%0d got=%0d",target,frames_checked);
            $finish;
        end
    end
endtask

task wait_for_output_byte(input integer target);
    integer ticks;
    begin
        ticks = 0;
        while (!(fcnt == target && m_tvalid) && ticks < 20000) begin
            @(negedge clk);
            ticks = ticks + 1;
        end
        if (!(fcnt == target && m_tvalid)) begin
            $display("TEST FAILED: output wait timeout byte=%0d fcnt=%0d",target,fcnt);
            $finish;
        end
    end
endtask

task wait_for_last_output_byte;
    integer ticks;
    begin
        ticks = 0;
        while (!(fcnt == FRAME_BYTES-1 && m_tvalid && m_tlast) && ticks < 20000) begin
            @(negedge clk);
            ticks = ticks + 1;
        end
        if (!(fcnt == FRAME_BYTES-1 && m_tvalid && m_tlast)) begin
            $display("TEST FAILED: TLAST wait timeout fcnt=%0d",fcnt);
            $finish;
        end
    end
endtask

// Drive one reference core and capture the quaternion it produces.
task automatic reference_step(
    input integer core, input reset_first, input signed [15:0] gz,
    output [127:0] quat
);
    integer ticks;
    begin
        if (reset_first) begin
            @(negedge clk);
            ref_rst_n[core] = 0;
            repeat (2) @(negedge clk);
            ref_rst_n[core] = 1;
        end
        @(negedge clk);
        ref_gz[core] = gz;
        ref_valid[core] = 1;
        @(negedge clk);
        ref_valid[core] = 0;
        ticks = 0;
        while (ref_out_valid[core] !== 1'b1 && ticks < 2048) begin
            @(negedge clk);
            ticks = ticks + 1;
        end
        if (ticks == 2048) begin
            $display("TEST FAILED: reference core %0d timeout", core);
            $finish;
        end
        quat = {ref_w[core], ref_x[core], ref_y[core], ref_z[core]};
        @(negedge clk);
    end
endtask

// One independent reference state per physical IMU. Restart is derived from
// the logical merged-frame history, not caller-supplied per-core reset flags.
task automatic model_hand(
    input integer hand, input [31:0] ts, input [1:0] absent,
    input signed [15:0] gz0, input signed [15:0] gz1,
    output [127:0] quat0, output [127:0] quat1
);
    reg [1:0] present;
    reg restart_hand;
    integer base;
    begin
        present = ~absent;
        base = hand * 2;
        if (present != 2'b00) begin
            restart_hand = !ref_segment[hand] ||
                           (ts != ref_previous[hand] + 32'd1);
            if (present[0]) reference_step(base, restart_hand, gz0, quat0);
            else quat0 = {16{8'hEE}};
            if (present[1]) reference_step(base + 1, restart_hand, gz1, quat1);
            else quat1 = {16{8'hEE}};
            ref_previous[hand] = ts;
            // A partial IMU frame ends the shared two-sensor segment.
            ref_segment[hand] = (present == 2'b11);
        end else begin
            quat0 = {16{8'hEE}};
            quat1 = {16{8'hEE}};
            ref_segment[hand] = 1'b0;
        end
    end
endtask

// Called exactly once for each expected merged output. Right-hand model state
// advances only when that timestamp matched; late/future/timed-out frames do
// not alter its quaternion history.
task automatic model_frame;
    begin
        exp_ts = cfg_ts; exp_r_miss = cfg_r_missing;
        exp_l_absent = cfg_l_absent; exp_r_absent = cfg_r_absent;
        exp_gz[0] = cfg_gz[0]; exp_gz[1] = cfg_gz[1];
        exp_gz[2] = cfg_gz[2]; exp_gz[3] = cfg_gz[3];
        model_hand(0, cfg_ts, cfg_l_absent, cfg_gz[0], cfg_gz[1],
                   exp_quat[0], exp_quat[1]);
        if (cfg_r_missing) begin
            exp_quat[2] = {16{8'hEE}};
            exp_quat[3] = {16{8'hEE}};
            ref_segment[1] = 1'b0;
        end else begin
            model_hand(1, cfg_ts, cfg_r_absent, cfg_gz[2], cfg_gz[3],
                       exp_quat[2], exp_quat[3]);
        end
    end
endtask

function automatic [127:0] frame_quat(input integer offset);
    integer i;
    begin
        for (i = 0; i < 16; i = i + 1)
            frame_quat[127 - i*8 -: 8] = frame[offset+i];
    end
endfunction

// Quaternion segment offsets: 98, 114, 130, 146 (16B each).
task check_quat_segment(input integer idx, input integer offset, input [255:0] name);
    begin
        if (frame_quat(offset) !== exp_quat[idx]) begin
            $display("ERROR: %0s quat ts=%08x got=%032x expected=%032x",
                     name, exp_ts, frame_quat(offset), exp_quat[idx]);
            errors = errors + 1;
        end
    end
endtask

task check_frame;
    integer i;
    begin
        if (frame[0] !== 8'hAA || frame[1] !== exp_ts[7:0] ||
            frame[162] !== 8'h55 || frame[163] !== 8'h5A) begin
            $display("ERROR: frame markers/seq ts=%08x", exp_ts);
            errors = errors + 1;
        end
        for (i = 0; i < 48; i = i + 1) begin
            if (frame[2+i] !==
                stim_byte(i,8'h10,exp_ts,exp_gz[0],exp_gz[1],exp_l_absent)) begin
                $display("ERROR: left payload[%0d] ts=%08x", i, exp_ts);
                errors = errors + 1;
            end
            if (frame[50+i] !== (exp_r_miss ? 8'hEE :
                stim_byte(i,8'h40,exp_ts,exp_gz[2],exp_gz[3],exp_r_absent))) begin
                $display("ERROR: right payload[%0d] ts=%08x", i, exp_ts);
                errors = errors + 1;
            end
        end
        // Case inequality also rejects X/Z in quaternion arithmetic or packing.
        check_quat_segment(0,  98, "left imu0");
        check_quat_segment(1, 114, "left imu1");
        check_quat_segment(2, 130, "right imu0");
        check_quat_segment(3, 146, "right imu1");
        frames_checked = frames_checked + 1;
        $write("RAW ");
        for (i = 0; i < FRAME_BYTES; i = i + 1) $write("%02x",frame[i]);
        $display("");
        $display("frame %0d checked ts=%08x right_missing=%0d imu_absent=%b/%b",
                 frames_checked,exp_ts,exp_r_miss,exp_l_absent,exp_r_absent);
    end
endtask

always @(posedge clk) if (rst_n) begin
    if (stalled && (!m_tvalid || m_tdata !== held_data ||
                    m_tlast !== held_last)) begin
        $display("ERROR: output changed under backpressure");
        errors = errors + 1;
    end
    stalled = m_tvalid && !m_tready;
    if (stalled) begin
        stalled_cycles = stalled_cycles + 1;
        if (fcnt == 98) quat_stalled_cycles = quat_stalled_cycles + 1;
        if (m_tlast) last_stalled_cycles = last_stalled_cycles + 1;
    end
    held_data = m_tdata; held_last = m_tlast;
    if (m_tvalid && m_tready) begin
        if (fcnt > FRAME_BYTES-1) begin
            $display("ERROR: output exceeded %0d bytes", FRAME_BYTES);
            errors = errors + 1;
        end else frame[fcnt] = m_tdata;
        if (m_tlast) begin
            if (fcnt != FRAME_BYTES-1) begin
                $display("ERROR: TLAST at byte %0d",fcnt);
                errors = errors + 1;
            end
            check_frame();
            fcnt = 0;
        end else fcnt = fcnt + 1;
    end
end

initial begin
    repeat (20) @(negedge clk);
    rst_n = 1; ref_rst_n = 4'b1111;

    // Matching static frame and a delayed right-hand arrival.
    configure_frame(10,0,0,0,0,0,0,0); model_frame();
    fork
        send_hand(1);
        begin repeat(30) @(negedge clk); send_hand(0); end
    join
    wait_for_frames(1);

    // Timeout keeps left quaternions and fills 48 raw + 32 pose right bytes EE.
    configure_frame(11,1,0,0,0,0,0,0); model_frame();
    send_hand(1);
    wait_for_frames(2);

    // Recovery resets the right reference after its missing counter.
    configure_frame(12,0,0,0, 1640,1640, 1640,1640); model_frame();
    fork send_hand(1); send_hand(0); join
    wait_for_frames(3);

    // Buffer a stale right frame before the left arrives. It must be discarded
    // without advancing the right reference core or leaking into frame 14.
    send_hand_payload(0,13,-1640,-1640,0);
    configure_frame(14,0,0,0, -3280,-3280, -3280,-3280); model_frame();
    fork
        send_hand(1);
        send_hand(0);
    join
    wait_for_frames(4);

    // Keep right ts=16 while left ts=15 arrives. The future frame lets ts=15
    // emit as right-missing, then pairs with left ts=16 using the same sample.
    configure_frame(15,1,0,0, 4920,4920, -4920,-4920); model_frame();
    send_hand_at(0,16);
    send_hand(1);
    wait_for_frames(5);
    // Only advance the left input; right configuration still describes the
    // exact future frame just sent, so its reference cannot diverge.
    configure_left(16,0,0,-3280,-3280); model_frame();
    send_hand(1);
    wait_for_frames(6);

    // Right arrives after timeout while the left quaternion byte is stalled.
    // No late raw/quaternion bytes may leak into this already missing output.
    configure_frame(17,1,0,0, 1640,1640, 6560,-6560); model_frame();
    send_hand(1);
    wait_for_output_byte(98);
    m_tready = 0;
    send_hand(0);
    repeat(40) @(negedge clk);
    m_tready = 1;
    wait_for_frames(7);

    // Discard that late frame, then validate the newest matched dynamic frame.
    configure_frame(18,0,0,0, -1640,-1640, -1640,-1640); model_frame();
    fork
        send_hand(1);
        send_hand(0);
    join
    wait_for_frames(8);

    // IMU#0 is absent on the left while the other three cores receive distinct
    // gyro values. This checks each lane uses its own bytes and state.
    configure_frame(19,0,1,0, 0,1640,-3280,4920); model_frame();
    fork send_hand(1); send_hand(0); join
    wait_for_frames(9);
    // Right IMU#0 is absent. Its IMU#1 gyro is +100 dps on driver and model.
    configure_frame(20,0,0,1, 3280,3280, 3280,3280); model_frame();
    fork send_hand(1); send_hand(0); join
    wait_for_frames(10);
    // Both hands lose IMU#0; ADC, timestamps and IMU#1 remain present.
    configure_frame(21,0,1,1, 0,0, 0,0); model_frame();
    fork send_hand(1); send_hand(0); join
    wait_for_frames(11);

    // The first valid sample after missing IMU0 starts from identity.
    configure_frame(22,0,0,0, 0,0, 0,0); model_frame();
    fork send_hand(1); send_hand(0); join
    wait_for_frames(12);

    // Missing IMU1 does not invalidate IMU0; then remove every IMU on both
    // hands and verify the following complete sample resets all four cores.
    configure_frame(23,0,2,2, 1640,1640, 1640,1640); model_frame();
    fork send_hand(1); send_hand(0); join
    wait_for_frames(13);
    configure_frame(24,0,3,3, 0,0, 0,0); model_frame();
    fork send_hand(1); send_hand(0); join
    wait_for_frames(14);
    configure_frame(25,0,0,0, -1640,1640, -3280,3280); model_frame();
    fork send_hand(1); send_hand(0); join
    wait_for_frames(15);

    // Large counter gap resets each core; UINT32 wrap itself is continuous.
    configure_frame(32'hFFFFFFFF,0,0,0, -3280,-3280, -3280,-3280); model_frame();
    fork
        send_hand(1);
        send_hand(0);
    join
    wait_for_frames(16);
    configure_frame(0,0,0,0, -3280,-3280, -3280,-3280); model_frame();
    fork
        send_hand(1);
        send_hand(0);
    join
    wait_for_last_output_byte;
    m_tready = 0;
    repeat(25) @(negedge clk);
    m_tready = 1;
    wait_for_frames(17);

    repeat(5) @(negedge clk);
    if (stat_r_timeout !== 16'd3) begin
        $display("ERROR: missing-right output count=%0d expected=3",stat_r_timeout);
        errors = errors + 1;
    end
    if (quat_stalled_cycles < 40 || last_stalled_cycles < 25) begin
        $display("ERROR: insufficient backpressure coverage quat=%0d last=%0d",
                 quat_stalled_cycles,last_stalled_cycles);
        errors = errors + 1;
    end
    $display("backpressure cycles total=%0d quat=%0d last=%0d",
             stalled_cycles,quat_stalled_cycles,last_stalled_cycles);
    if (errors == 0)
        $display("TEST PASSED: 17 frames x 164B, four independent quaternions, stale/future/late/absence recovery/wrap/stalls");
    else $display("TEST FAILED: %0d errors",errors);
    $finish;
end

initial begin
    #5_000_000;
    $display("TEST FAILED: watchdog frames=%0d errors=%0d",frames_checked,errors);
    $finish;
end

endmodule
