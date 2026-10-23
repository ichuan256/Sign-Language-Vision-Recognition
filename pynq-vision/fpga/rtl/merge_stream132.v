// =============================================================================
// W5 frame merger with four independent Mahony pose cores.
//
// Input: one 48-byte frame per hand. Output: a fixed 164-byte frame:
//   0       0xAA
//   1       left timestamp low byte
//   2..49   left 48-byte payload
//   50..97  right 48-byte payload, or EE when no right frame is paired
//   98..113 left IMU0 quaternion, Q2.29 signed int32 big-endian
//   114..129 left IMU1 quaternion
//   130..145 right IMU0 quaternion
//   146..161 right IMU1 quaternion
//   162..163 0x55, 0x5A (TLAST on byte 163)
//
// Each 48-byte input payload contains two 14-byte IMU blocks followed by
// 16 ADC bytes and a 32-bit timestamp. An all-EE IMU block is absent; its
// quaternion segment is EE while the rest of that hand payload is preserved.
// A hand's two pose cores restart together after a timestamp gap, a missing
// paired frame, or a partial-IMU frame. The four PEs calculate in parallel.
// =============================================================================
`timescale 1ns/1ps

module merge_stream132 #(
    parameter integer TIMEOUT_CYCLES = 200_000
)(
    input  wire       clk,
    input  wire       rst_n,

    input  wire [7:0] s_axis_l_tdata,
    input  wire       s_axis_l_tvalid,
    input  wire       s_axis_l_tlast,
    output wire       s_axis_l_tready,

    input  wire [7:0] s_axis_r_tdata,
    input  wire       s_axis_r_tvalid,
    input  wire       s_axis_r_tlast,
    output wire       s_axis_r_tready,

    output reg  [7:0] m_axis_tdata,
    output reg        m_axis_tvalid,
    output reg        m_axis_tlast,
    input  wire       m_axis_tready,

    output reg  [15:0] stat_r_timeout,
    output wire        busy
);

localparam integer INPUT_BYTES = 48;
localparam integer FRAME_BYTES = 164;
localparam [7:0] FRAME_LAST = FRAME_BYTES - 1;

reg [7:0] buf_l [0:INPUT_BYTES-1];
reg [7:0] buf_r [0:INPUT_BYTES-1];
reg [5:0] rcv_l, rcv_r;
reg got_l, got_r;
reg [7:0] seq_reg;

assign s_axis_l_tready = !got_l;
assign s_axis_r_tready = !got_r;
assign busy = m_axis_tvalid;

reg emitting;
reg [7:0] emit_cnt;
reg r_miss;
wire emit_accept = m_axis_tvalid && m_axis_tready;
wire emit_done = emitting && emit_accept && (emit_cnt == FRAME_LAST);

wire [31:0] ts_l = {buf_l[44], buf_l[45], buf_l[46], buf_l[47]};
wire [31:0] ts_r = {buf_r[44], buf_r[45], buf_r[46], buf_r[47]};
wire [31:0] right_delta = ts_r - ts_l;
wire right_match = got_r && (right_delta == 32'd0);
wire right_future = got_r && !right_delta[31] && (right_delta != 32'd0);
wire discard_r = got_l && got_r && right_delta[31] && !emitting;

// Presence is tracked per 14-byte IMU block, not per hand.
wire imu_l0_ok = {buf_l[0], buf_l[1], buf_l[2], buf_l[3], buf_l[4], buf_l[5],
                  buf_l[6], buf_l[7], buf_l[8], buf_l[9], buf_l[10], buf_l[11],
                  buf_l[12], buf_l[13]} != {14{8'hEE}};
wire imu_l1_ok = {buf_l[14], buf_l[15], buf_l[16], buf_l[17], buf_l[18], buf_l[19],
                  buf_l[20], buf_l[21], buf_l[22], buf_l[23], buf_l[24], buf_l[25],
                  buf_l[26], buf_l[27]} != {14{8'hEE}};
wire imu_r0_ok = {buf_r[0], buf_r[1], buf_r[2], buf_r[3], buf_r[4], buf_r[5],
                  buf_r[6], buf_r[7], buf_r[8], buf_r[9], buf_r[10], buf_r[11],
                  buf_r[12], buf_r[13]} != {14{8'hEE}};
wire imu_r1_ok = {buf_r[14], buf_r[15], buf_r[16], buf_r[17], buf_r[18], buf_r[19],
                  buf_r[20], buf_r[21], buf_r[22], buf_r[23], buf_r[24], buf_r[25],
                  buf_r[26], buf_r[27]} != {14{8'hEE}};
wire [1:0] imu_ok_l = {imu_l1_ok, imu_l0_ok};
wire [1:0] imu_ok_r = {imu_r1_ok, imu_r0_ok};

// Frame collection. Left is the master; each side holds one complete frame.
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        rcv_l <= 0;
        got_l <= 0;
        seq_reg <= 0;
    end else if (s_axis_l_tvalid && s_axis_l_tready) begin
        buf_l[rcv_l] <= s_axis_l_tdata;
        if (s_axis_l_tlast) begin
            rcv_l <= 0;
            got_l <= 1;
            seq_reg <= s_axis_l_tdata;
        end else begin
            rcv_l <= rcv_l + 1'b1;
        end
    end else if (emit_done) begin
        got_l <= 0;
    end
end

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        rcv_r <= 0;
        got_r <= 0;
    end else if (s_axis_r_tvalid && s_axis_r_tready) begin
        buf_r[rcv_r] <= s_axis_r_tdata;
        if (s_axis_r_tlast) begin
            rcv_r <= 0;
            got_r <= 1;
        end else begin
            rcv_r <= rcv_r + 1'b1;
        end
    end else if ((emit_done && !r_miss) || discard_r) begin
        got_r <= 0;
    end
end

// One feed bit and one valid-result bit per PE. The feed vector is set on the
// same edge the PEs accept their samples, so the segment timestamp cannot
// advance while a sibling core is still waiting for its first feed.
reg [1:0] fed_l, fed_r;
reg [1:0] qready_l, qready_r;
reg segment_l, segment_r;
reg [31:0] previous_l, previous_r;
reg reset_l, reset_r;
reg reset_done_l, reset_done_r;
wire qv_l0, qv_l1, qv_r0, qv_r1;

wire restart_l = !segment_l || (ts_l != previous_l + 32'd1);
wire restart_r = !segment_r || (ts_r != previous_r + 32'd1);
wire [1:0] need_l = imu_ok_l & ~fed_l;
wire [1:0] need_r = right_match ? (imu_ok_r & ~fed_r) : 2'b00;
wire want_l = got_l && (need_l != 2'b00) && !emitting;
wire want_r = got_l && right_match && (need_r != 2'b00) && !emitting;
wire [1:0] feed_l = (want_l && !reset_l && (!restart_l || reset_done_l)) ? need_l : 2'b00;
wire [1:0] feed_r = (want_r && !reset_r && (!restart_r || reset_done_r)) ? need_r : 2'b00;
wire all_left_quats_ready = (qready_l & imu_ok_l) == imu_ok_l;
wire all_right_quats_ready = !right_match || ((qready_r & imu_ok_r) == imu_ok_r);

reg [31:0] tmo_cnt;
wire tmo_fire = got_l && !right_match && (tmo_cnt >= TIMEOUT_CYCLES);
wire emit_go = got_l && (right_match || right_future || tmo_fire) && !emitting
               && all_left_quats_ready && all_right_quats_ready;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        fed_l <= 0;
        fed_r <= 0;
        qready_l <= 0;
        qready_r <= 0;
        segment_l <= 0;
        segment_r <= 0;
        previous_l <= 0;
        previous_r <= 0;
        reset_l <= 0;
        reset_r <= 0;
        reset_done_l <= 0;
        reset_done_r <= 0;
    end else begin
        reset_l <= 0;
        reset_r <= 0;

        if (want_l && restart_l && !reset_done_l) begin
            reset_l <= 1;
            reset_done_l <= 1;
        end
        if (want_r && restart_r && !reset_done_r) begin
            reset_r <= 1;
            reset_done_r <= 1;
        end

        if (feed_l != 2'b00) begin
            fed_l <= fed_l | feed_l;
            previous_l <= ts_l;
            segment_l <= 1;
        end
        if (feed_r != 2'b00) begin
            fed_r <= fed_r | feed_r;
            previous_r <= ts_r;
            segment_r <= 1;
        end

        if (qv_l0) qready_l[0] <= 1;
        if (qv_l1) qready_l[1] <= 1;
        if (qv_r0) qready_r[0] <= 1;
        if (qv_r1) qready_r[1] <= 1;

        if (emit_done) begin
            fed_l <= 0;
            qready_l <= 0;
            reset_done_l <= 0;
            if (imu_ok_l != 2'b11) segment_l <= 0;
        end
        if (emit_done || discard_r) begin
            fed_r <= 0;
            qready_r <= 0;
            reset_done_r <= 0;
            if (emit_done && r_miss) segment_r <= 0;
            else if (imu_ok_r != 2'b11) segment_r <= 0;
        end
    end
end

wire signed [31:0] qw_l0, qx_l0, qy_l0, qz_l0;
wire signed [31:0] qw_l1, qx_l1, qy_l1, qz_l1;
wire signed [31:0] qw_r0, qx_r0, qy_r0, qz_r0;
wire signed [31:0] qw_r1, qx_r1, qy_r1, qz_r1;
mahony_pe mahony_l0 (
    .clk(clk), .rst_n(rst_n && !reset_l), .in_valid(feed_l[0]),
    .ax({buf_l[0], buf_l[1]}), .ay({buf_l[2], buf_l[3]}), .az({buf_l[4], buf_l[5]}),
    .gx({buf_l[8], buf_l[9]}), .gy({buf_l[10], buf_l[11]}), .gz({buf_l[12], buf_l[13]}),
    .out_valid(qv_l0), .qw(qw_l0), .qx(qx_l0), .qy(qy_l0), .qz(qz_l0)
);
mahony_pe mahony_l1 (
    .clk(clk), .rst_n(rst_n && !reset_l), .in_valid(feed_l[1]),
    .ax({buf_l[14], buf_l[15]}), .ay({buf_l[16], buf_l[17]}), .az({buf_l[18], buf_l[19]}),
    .gx({buf_l[22], buf_l[23]}), .gy({buf_l[24], buf_l[25]}), .gz({buf_l[26], buf_l[27]}),
    .out_valid(qv_l1), .qw(qw_l1), .qx(qx_l1), .qy(qy_l1), .qz(qz_l1)
);
mahony_pe mahony_r0 (
    .clk(clk), .rst_n(rst_n && !reset_r), .in_valid(feed_r[0]),
    .ax({buf_r[0], buf_r[1]}), .ay({buf_r[2], buf_r[3]}), .az({buf_r[4], buf_r[5]}),
    .gx({buf_r[8], buf_r[9]}), .gy({buf_r[10], buf_r[11]}), .gz({buf_r[12], buf_r[13]}),
    .out_valid(qv_r0), .qw(qw_r0), .qx(qx_r0), .qy(qy_r0), .qz(qz_r0)
);
mahony_pe mahony_r1 (
    .clk(clk), .rst_n(rst_n && !reset_r), .in_valid(feed_r[1]),
    .ax({buf_r[14], buf_r[15]}), .ay({buf_r[16], buf_r[17]}), .az({buf_r[18], buf_r[19]}),
    .gx({buf_r[22], buf_r[23]}), .gy({buf_r[24], buf_r[25]}), .gz({buf_r[26], buf_r[27]}),
    .out_valid(qv_r1), .qw(qw_r1), .qx(qx_r1), .qy(qy_r1), .qz(qz_r1)
);

reg [127:0] quat_l0, quat_l1, quat_r0, quat_r1;
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        quat_l0 <= 0;
        quat_l1 <= 0;
        quat_r0 <= 0;
        quat_r1 <= 0;
    end else begin
        if (qv_l0) quat_l0 <= {qw_l0, qx_l0, qy_l0, qz_l0};
        if (qv_l1) quat_l1 <= {qw_l1, qx_l1, qy_l1, qz_l1};
        if (qv_r0) quat_r0 <= {qw_r0, qx_r0, qy_r0, qz_r0};
        if (qv_r1) quat_r1 <= {qw_r1, qx_r1, qy_r1, qz_r1};
    end
end

function automatic [7:0] quat_byte(input [127:0] q, input [3:0] offset);
    reg [127:0] shifted;
    begin
        shifted = q >> ((15 - offset) * 8);
        quat_byte = shifted[7:0];
    end
endfunction

function automatic [7:0] frame_byte(input [7:0] index);
    begin
        if (index == 0) frame_byte = 8'hAA;
        else if (index == 1) frame_byte = seq_reg;
        else if (index <= 49) frame_byte = buf_l[index - 2];
        else if (index <= 97) frame_byte = r_miss ? 8'hEE : buf_r[index - 50];
        else if (index <= 113)
            frame_byte = imu_l0_ok ? quat_byte(quat_l0, index - 98) : 8'hEE;
        else if (index <= 129)
            frame_byte = imu_l1_ok ? quat_byte(quat_l1, index - 114) : 8'hEE;
        else if (index <= 145)
            frame_byte = (r_miss || !imu_r0_ok) ? 8'hEE : quat_byte(quat_r0, index - 130);
        else if (index <= 161)
            frame_byte = (r_miss || !imu_r1_ok) ? 8'hEE : quat_byte(quat_r1, index - 146);
        else if (index == 162) frame_byte = 8'h55;
        else frame_byte = 8'h5A;
    end
endfunction

// Wait until all needed per-core results exist, snapshot via quat_* above, and
// then hold each output byte stable until its AXI handshake.
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        tmo_cnt <= 0;
        r_miss <= 0;
        stat_r_timeout <= 0;
        emitting <= 0;
        emit_cnt <= 0;
        m_axis_tdata <= 0;
        m_axis_tvalid <= 0;
        m_axis_tlast <= 0;
    end else begin
        if (got_l && !right_match && !emitting) begin
            if (tmo_cnt < TIMEOUT_CYCLES) tmo_cnt <= tmo_cnt + 1'b1;
        end else begin
            tmo_cnt <= 0;
        end

        if (emit_done) begin
            emitting <= 0;
            emit_cnt <= 0;
            m_axis_tvalid <= 0;
            m_axis_tlast <= 0;
            r_miss <= 0;
            if (r_miss) stat_r_timeout <= stat_r_timeout + 1'b1;
        end else if (emit_go) begin
            emitting <= 1;
            emit_cnt <= 0;
            r_miss <= !right_match;
        end else if (emitting && !m_axis_tvalid) begin
            m_axis_tdata <= frame_byte(emit_cnt);
            m_axis_tvalid <= 1;
            m_axis_tlast <= (emit_cnt == FRAME_LAST);
        end else if (emit_accept && (emit_cnt != FRAME_LAST)) begin
            emit_cnt <= emit_cnt + 1'b1;
            m_axis_tdata <= frame_byte(emit_cnt + 1'b1);
            m_axis_tlast <= (emit_cnt + 1'b1 == FRAME_LAST);
        end
    end
end

endmodule
