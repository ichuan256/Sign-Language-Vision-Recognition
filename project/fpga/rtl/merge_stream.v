// =============================================================================
// 妙手通言 · merge_stream（W3 · 双手帧封装）
// 功能：左/右手两路 sensor_if_spi 的 48B AXI-Stream 帧 → 合并成 100B 标准帧
//   输出帧（接口冻结 ③ v1.0）：
//     [0]     0xAA        帧头魔数（格式版本 v1）
//     [1]     frame_seq   = 左手时戳低 8bit（左手负载末字节）
//     [2..49] 左手负载 48B 原样透传
//     [50..97]右手负载 48B；超时未到达填 0xEE（帧定长不变）
//     [98]    0x55        帧尾魔数
//     [99]    0x5A        tlast 打在此字节
// 时序基准：左手为帧主（同 tick 驱动，先到）；右手为从，超时判缺席。
// 流水能力：收发解耦——收帧缓冲与发帧并行，100Hz 下裕量 >1000 倍。
// =============================================================================
`timescale 1ns/1ps

module merge_stream #(
    parameter CLK_FREQ_HZ    = 100_000_000,
    parameter TIMEOUT_CYCLES = 200_000        // 右手等待超时，默认 2ms @100MHz
)(
    input  wire        clk,
    input  wire        rst_n,

    // 左手输入（帧主，48B，tlast@47）
    input  wire [7:0]  s_axis_l_tdata,
    input  wire        s_axis_l_tvalid,
    input  wire        s_axis_l_tlast,
    output wire        s_axis_l_tready,

    // 右手输入（帧从，48B，tlast@47）
    input  wire [7:0]  s_axis_r_tdata,
    input  wire        s_axis_r_tvalid,
    input  wire        s_axis_r_tlast,
    output wire        s_axis_r_tready,

    // 合并输出（100B，tlast@99）
    output reg  [7:0]  m_axis_tdata,
    output reg         m_axis_tvalid,
    output reg         m_axis_tlast,
    input  wire        m_axis_tready,

    // 状态观测（AXI-Lite 寄存器/调试用）
    output reg  [15:0] stat_r_timeout,        // 右手超时次数（PS 可读，报告用）
    output wire        busy
);

// ---------------- 收帧缓冲 ----------------
reg [7:0] buf_l [0:47];
reg [7:0] buf_r [0:47];
reg [5:0] rcv_l, rcv_r;        // 收字节计数 0..47
reg       got_l, got_r;        // 帧齐标志
reg [7:0] seq_reg;             // = buf_l[47]（左手时戳低 8bit）

// 发射期间拒收（100Hz 下不会发生，仅兜底）
assign s_axis_l_tready = !got_l;
assign s_axis_r_tready = !got_r;
assign busy = m_axis_tvalid;

wire rcv_l_done = s_axis_l_tvalid && s_axis_l_tready && s_axis_l_tlast;
wire rcv_r_done = s_axis_r_tvalid && s_axis_r_tready && s_axis_r_tlast;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        rcv_l <= 6'd0; got_l <= 1'b0; seq_reg <= 8'd0;
    end else begin
        if (s_axis_l_tvalid && s_axis_l_tready) begin
            buf_l[rcv_l] <= s_axis_l_tdata;
            if (s_axis_l_tlast) begin
                rcv_l   <= 6'd0;
                got_l   <= 1'b1;
                seq_reg <= s_axis_l_tdata;      // 末字节 = ts 低 8bit
            end else rcv_l <= rcv_l + 6'd1;
        end else if (emit_done)
            got_l <= 1'b0;
    end
end

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        rcv_r <= 6'd0; got_r <= 1'b0;
    end else begin
        if (s_axis_r_tvalid && s_axis_r_tready) begin
            buf_r[rcv_r] <= s_axis_r_tdata;
            if (s_axis_r_tlast) begin
                rcv_r <= 6'd0;
                got_r <= 1'b1;
            end else rcv_r <= rcv_r + 6'd1;
        end else if (emit_done)
            got_r <= 1'b0;
    end
end

// ---------------- 右手超时 ----------------
reg [31:0] tmo_cnt;
reg        r_miss;             // 本帧右手缺席（填 0xEE）

wire tmo_fire = got_l && !got_r && (tmo_cnt >= TIMEOUT_CYCLES);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        tmo_cnt <= 32'd0; r_miss <= 1'b0; stat_r_timeout <= 16'd0;
    end else begin
        if (got_l && !got_r && !emitting) begin
            if (tmo_cnt < TIMEOUT_CYCLES)
                tmo_cnt <= tmo_cnt + 32'd1;
        end else tmo_cnt <= 32'd0;

        if (emit_done) begin
            r_miss <= 1'b0;
            if (r_miss) stat_r_timeout <= stat_r_timeout + 16'd1;
        end else if (tmo_fire)
            r_miss <= 1'b1;
    end
end

// ---------------- 发射 FSM ----------------
// 触发条件：左手齐 且（右手齐 或 超时）
reg [6:0] emit_cnt;            // 0..99
reg       emitting;

wire emit_go    = got_l && (got_r || r_miss) && !emitting;
wire emit_accept = m_axis_tvalid && m_axis_tready;
wire emit_done;

assign emit_done = emitting && emit_cnt == 7'd99 && emit_accept;

// 发射字节选择（组合）：装填索引 = 本拍被接收 ? emit_cnt+1 : emit_cnt
wire [6:0] load_cnt = emit_accept ? emit_cnt + 7'd1 : emit_cnt;
reg [7:0] emit_data;
always @(*) begin
    if (load_cnt == 7'd0)       emit_data = 8'hAA;
    else if (load_cnt == 7'd1)  emit_data = seq_reg;
    else if (load_cnt <= 7'd49) emit_data = buf_l[load_cnt - 7'd2];
    else if (load_cnt <= 7'd97) emit_data = r_miss ? 8'hEE
                                                   : buf_r[load_cnt - 7'd50];
    else if (load_cnt == 7'd98) emit_data = 8'h55;
    else                        emit_data = 8'h5A;
end

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        emitting <= 1'b0; emit_cnt <= 7'd0;
        m_axis_tvalid <= 1'b0; m_axis_tlast <= 1'b0; m_axis_tdata <= 8'd0;
    end else begin
        if (emit_done) begin
            emitting      <= 1'b0;
            emit_cnt      <= 7'd0;
            m_axis_tvalid <= 1'b0;
            m_axis_tlast  <= 1'b0;
        end else if (emit_go) begin
            emitting <= 1'b1;
            emit_cnt <= 7'd0;
        end else if (emitting && (!m_axis_tvalid || emit_accept)) begin
            // 装填首字节 / 推进下一字节
            m_axis_tdata  <= emit_data;      // emit_data 按 load_cnt 计算
            m_axis_tvalid <= 1'b1;
            m_axis_tlast  <= (load_cnt == 7'd99);
            emit_cnt      <= load_cnt;
        end
    end
end

endmodule
