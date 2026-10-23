// TEST ONLY: Parallel reference based on the pre-resource-refactor datapath.
// The W5 input range, safe acceleration scaling and gyro fractional width are
// shared with the current contract, while multiplication remains parallel.
// The 32-bit wire matches Vivado xsim and avoids Icarus 0.9.7 width expansion.
// FIX_SEED=0 reproduces the original extreme-input X failure; default 1 applies
// the mathematical seed correction while retaining the old parallel datapath.
// =============================================================================
// 妙手通言 · mahony_pe.v — Mahony 六轴姿态解算核（定点版，竞赛 PL 加速主体）
//
// 功能：与 algo/attitude_mahony.py 的 MahonyAHRS.update_imu() 逐帧等价。
//   每帧输入 1 组 IMU 原始值（int16：ax,ay,az,gx,gy,gz），
//   ~24 拍后输出归一化四元数 q = [w,x,y,z]（Q2.29 有符号定点）。
//
// 定点格式（int32 有符号）：
//   四元数 q / 归一化加速度   Q2.29（|值| ≤ 1 左右，寄存器量程 ±4）
//   角速度 gyro / 积分项 e     signed32 * 2^26（约 ±32 rad/s）
//   kp / ki                   Q1.30（参数，默认 1.0 / 0.05）
//
// 原始值：MPU6500 ±8g / ±1000dps，4096 LSB/g、32.8 LSB/dps。
//   acc：三轴同乘二次幂，使最大绝对分量落在 [0.5,1)，再归一化；
//        物理 norm > 0.5g 的门限结合记录的缩放指数判断。
//   gyro：raw × 35709（round(π/(180·32.8)·2^26)）。
//
// 乘法缩放链（64 位中间积，>>> 数为两操作数量化指数之和减目标指数）：
//   m29(x,y)   : Q2.29·Q2.29 → Q2.29（>>>29）
//   kp·err     : 29+30-26 = 33 位右移
//   ki·e       : 26+30-26 = 30 位右移
//   err·dt     : 29+25-26 = 28 位右移（DT_MUL=335544 ≈ 0.01·2^25）
//   q·ω        : >>>26 → Q2.29，再 (×HDT_MUL >>>25) 即 ×0.005
//
// invsqrt：平方和（Q2.29，∈(2^27, 2^31)）→ 2 的幂初值（误差 <41%）→ 4 次 NR
//   NR：y' = y·(3 - x·y²)/2，误差按 1.5ε² 收敛，4 次后 <1%。
//
// 时序：100Hz 帧（10ms）下延迟 ~24 拍 @100MHz，裕量 >4 万倍。
// 资源：~28 DSP48（xc7z020 约 13%），无 BRAM。
// =============================================================================
`timescale 1ns / 1ps

module mahony_pe_reference #(
    parameter signed [31:0] KP = 32'h4000_0000,   // Q1.30：1.0
    parameter signed [31:0] KI = 32'h0333_3333,   // Q1.30：0.05
    parameter FIX_SEED = 1
)(
    input  wire        clk,
    input  wire        rst_n,

    // 帧输入（单拍脉冲）
    input  wire        in_valid,
    input  wire signed [15:0] ax, ay, az,
    input  wire signed [15:0] gx, gy, gz,

    // 四元数输出（单拍脉冲，Q2.29）
    output reg         out_valid,
    output reg  signed [31:0] qw, qx, qy, qz
);

    localparam [19:0] DT_MUL   = 20'd335544;      // 0.01  × 2^25
    localparam [19:0] HDT_MUL  = 20'd167772;      // 0.005 × 2^25
    localparam [17:0] GYR_GAIN = 18'd35709;       // π/(180·32.8) × 2^26

    // ---- 状态 ----
    localparam S_IDLE  = 4'd0,
               S_SSQ_A = 4'd1,    // acc 平方和 + acc_ok 判定
               S_SEED  = 4'd2,    // invsqrt 初值（acc/q 共用）
               S_NR    = 4'd3,    // NR ×4（计数器）
               S_ACCN  = 4'd4,    // acc 归一化
               S_ERR   = 4'd5,    // 重力估计 + 叉积 + PI
               S_INT   = 4'd6,    // 四元数积分
               S_SSQ_Q = 4'd7,    // q 平方和
               S_QNORM = 4'd8,    // q 归一化 + 输出
               S_DONE  = 4'd9;
    reg [3:0]  st;
    reg [2:0]  nr_cnt;
    reg        norm_q;            // 0=归一化 acc，1=归一化 q

    // ---- 寄存器 ----
    reg signed [31:0] e0, e1, e2;                 // PI 积分项（*2^26）
    reg signed [31:0] a0, a1, a2;                 // 加速度（Q2.29）
    reg signed [31:0] w0, w1, w2;                 // 角速度（*2^26，PI 修正后）
    reg signed [31:0] sumsq;                      // 待归一化向量的模方（Q2.29）
    reg signed [31:0] isq;                        // invsqrt（Q2.29）
    reg signed [31:0] qw_n, qx_n, qy_n, qz_n;     // 积分后未归一 q
    reg               acc_ok;
    reg [4:0]         acc_lshift;

    function automatic [4:0] acceleration_shift(
        input signed [15:0] x, y, z
    );
        reg [16:0] mx, my, mz, largest;
        reg signed [16:0] sx, sy, sz;
        integer p;
        begin
            sx = {x[15], x}; sy = {y[15], y}; sz = {z[15], z};
            mx = x[15] ? -sx : sx;
            my = y[15] ? -sy : sy;
            mz = z[15] ? -sz : sz;
            largest = mx;
            if (my > largest) largest = my;
            if (mz > largest) largest = mz;
            acceleration_shift = 5'd31;
            for (p = 0; p < 17; p = p + 1)
                if (largest[p]) acceleration_shift = 28 - p;
        end
    endfunction
    wire [4:0] input_acc_shift = acceleration_shift(ax, ay, az);

    function automatic acceleration_valid(
        input signed [31:0] squared, input [4:0] shift
    );
        integer threshold_shift;
        begin
            if (shift == 31 || shift > 18) acceleration_valid = 0;
            else if (shift <= 16) acceleration_valid = 1;
            else begin
                threshold_shift = (2 * shift) - 7;
                acceleration_valid = squared > (32'sd1 <<< threshold_shift);
            end
        end
    endfunction

    // Q2.29 × Q2.29 → Q2.29
    function automatic signed [31:0] m29(input signed [31:0] x,
                                         input signed [31:0] y);
        reg signed [63:0] p;
        begin p = x * y; m29 = p >>> 29; end
    endfunction

    wire signed [31:0] acc_sumsq = m29(a0,a0) + m29(a1,a1) + m29(a2,a2);

    // invsqrt 初值：取 x 最高置位 p（27..31），y0 = 2^(29+floor((29-p)/2))
    // 输入范数平方为 [0.25,3)，各区间均保证 0 < x*y0² < 3；
    // p=27 的初值略小于 2，避免 y²=4 在 signed32 Q2.29 域溢出。
    // （2026-10-05 修复：原公式 seed 可达真值 2 倍，NR 收敛到负根致 q 翻号）
    function automatic signed [31:0] isq_seed(input signed [31:0] x);
        integer i; reg [5:0] p;
        begin
            p = 6'd27;
            for (i = 27; i <= 31; i = i + 1)
                if (x[i]) p = i[5:0];                       // 最高置位
            if (p == 6'd27)
                isq_seed = 32'sh3FFF_FFFF;                  // 2^30 - 1（钳位）
            else if (FIX_SEED)
                isq_seed = (p >= 6'd30) ? (32'sd1 <<< 28) : (32'sd1 <<< 29);
            else if (p >= 6'd30)
                // 负控专用分支。旧公式的 (29-p) 是无符号相减，p≥30 时下溢成
                // 2147483676 左右，再按该位数左移属于未定义行为：Icarus 0.9.7
                // 返回 X，V13 起按标准“移位数≥位宽”返回 0，负控会退化成
                // “全零但仍与参考一致”的假通过。这里显式给 X，使负控不依赖
                // 仿真器的未定义行为。
                isq_seed = 32'hxxxx_xxxx;
            else
                isq_seed = 32'sd1 <<< (29 + ((29 - p) >>> 1));
        end
    endfunction

    // NR：y' = y·(3 - x·y²)/2（全 Q2.29 域）；负值保护——结果非正则退回 y/2
    function automatic signed [31:0] nr(input signed [31:0] x,
                                        input signed [31:0] y);
        reg signed [31:0] y2, t, yn;
        begin
            y2 = m29(y, y);
            t  = m29(x, y2);
            yn = m29(y, (32'sd3 <<< 29) - t) >>> 1;
            nr = (yn > 0) ? yn : (y >>> 1);
        end
    endfunction

    // S_ERR / S_INT 的组合中间量（本拍内阻塞赋值，仅供下一拍寄存）
    reg signed [31:0] vx, vy, vz, ex, ey, ez;
    reg signed [31:0] en0, en1, en2;   // 积分新值：与 Python 模型一致，ki 修正用新值
    reg signed [63:0] dq0, dq1, dq2, dq3;
    // 64 位乘积暂存：Verilog 按"操作数与 LHS 最大位宽"定乘法位宽，
    // 32×32 直接写会被截成 32 位（2026-10-05 帧 51 漂移根因），必须先落 64 位再移位
    reg signed [63:0] pkp0, pkp1, pkp2, pki0, pki1, pki2;
    reg signed [63:0] pdt0, pdt1, pdt2;
    reg signed [63:0] ph0, ph1, ph2, ph3;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            st <= S_IDLE; out_valid <= 1'b0;
            qw <= 32'sd1 <<< 29; qx <= 0; qy <= 0; qz <= 0;
            e0 <= 0; e1 <= 0; e2 <= 0; acc_ok <= 1'b0;
            acc_lshift <= 5'd31;
        end else begin
            out_valid <= 1'b0;
            case (st)
            // ------------------------------------------------------------------
            S_IDLE: if (in_valid) begin
                acc_lshift <= input_acc_shift;
                a0 <= $signed({{16{ax[15]}}, ax}) <<< input_acc_shift;
                a1 <= $signed({{16{ay[15]}}, ay}) <<< input_acc_shift;
                a2 <= $signed({{16{az[15]}}, az}) <<< input_acc_shift;
                w0 <= gx * $signed({1'b0, GYR_GAIN});       // → signed32 * 2^26
                w1 <= gy * $signed({1'b0, GYR_GAIN});
                w2 <= gz * $signed({1'b0, GYR_GAIN});
                norm_q <= 1'b0;
                st <= S_SSQ_A;
            end
            // ------------------------------------------------------------------
            S_SSQ_A: begin
                sumsq  <= m29(a0,a0) + m29(a1,a1) + m29(a2,a2);
                acc_ok <= acceleration_valid(acc_sumsq, acc_lshift);
                st <= (acc_lshift == 5'd31) ? S_INT : S_SEED;
            end
            // ------------------------------------------------------------------
            S_SEED: begin
                isq    <= isq_seed(sumsq);
                nr_cnt <= 3'd0;
                st     <= S_NR;
            end
            S_NR: begin
                isq <= nr(sumsq, isq);
                if (nr_cnt == 3'd3)
                    st <= norm_q ? S_QNORM : S_ACCN;
                else
                    nr_cnt <= nr_cnt + 3'd1;
            end
            // ------------------------------------------------------------------
            S_ACCN: begin
                a0 <= m29(a0, isq); a1 <= m29(a1, isq); a2 <= m29(a2, isq);
                st <= S_ERR;
            end
            // ------------------------------------------------------------------
            S_ERR: begin
                // 估计重力方向 v（机体系）
                vx = (m29(qx, qz) - m29(qw, qy)) <<< 1;
                vy = (m29(qw, qx) + m29(qy, qz)) <<< 1;
                vz = m29(qw,qw) - m29(qx,qx) - m29(qy,qy) + m29(qz,qz);
                // 误差 = a × v（叉积，Q2.29 域）
                ex = m29(a1, vz) - m29(a2, vy);
                ey = m29(a2, vx) - m29(a0, vz);
                ez = m29(a0, vy) - m29(a1, vx);
                if (acc_ok) begin
                    // e += err·dt：结果有 26 个小数位，ki 用更新后的 e。
                    pdt0 = ex * $signed({1'b0,DT_MUL});
                    pdt1 = ey * $signed({1'b0,DT_MUL});
                    pdt2 = ez * $signed({1'b0,DT_MUL});
                    en0 = e0 + (pdt0 >>> 28);
                    en1 = e1 + (pdt1 >>> 28);
                    en2 = e2 + (pdt2 >>> 28);
                    e0 <= en0; e1 <= en1; e2 <= en2;
                    // gyro_corr = gyro + kp·err(>>>33) + ki·e新值(>>>30)
                    pkp0 = ex * KP;  pki0 = en0 * KI;
                    pkp1 = ey * KP;  pki1 = en1 * KI;
                    pkp2 = ez * KP;  pki2 = en2 * KI;
                    w0 <= w0 + (pkp0 >>> 33) + (pki0 >>> 30);
                    w1 <= w1 + (pkp1 >>> 33) + (pki1 >>> 30);
                    w2 <= w2 + (pkp2 >>> 33) + (pki2 >>> 30);
                end
                st <= S_INT;
            end
            // ------------------------------------------------------------------
            S_INT: begin
                // Δq = 0.5·dt·(q⊗ω)：q·ω>>>26 → Q2.29，×HDT>>>25
                dq0 = (-qx*w0 - qy*w1 - qz*w2) >>> 26;
                dq1 = ( qw*w0 + qy*w2 - qz*w1) >>> 26;
                dq2 = ( qw*w1 - qx*w2 + qz*w0) >>> 26;
                dq3 = ( qw*w2 + qx*w1 - qy*w0) >>> 26;
                ph0 = dq0 * $signed({1'b0,HDT_MUL});
                ph1 = dq1 * $signed({1'b0,HDT_MUL});
                ph2 = dq2 * $signed({1'b0,HDT_MUL});
                ph3 = dq3 * $signed({1'b0,HDT_MUL});
                qw_n <= qw + (ph0 >>> 25);
                qx_n <= qx + (ph1 >>> 25);
                qy_n <= qy + (ph2 >>> 25);
                qz_n <= qz + (ph3 >>> 25);
                norm_q <= 1'b1;
                st <= S_SSQ_Q;
            end
            // ------------------------------------------------------------------
            S_SSQ_Q: begin
                sumsq <= m29(qw_n,qw_n) + m29(qx_n,qx_n)
                       + m29(qy_n,qy_n) + m29(qz_n,qz_n);
                st <= S_SEED;
            end
            S_QNORM: begin
                qw <= m29(qw_n, isq); qx <= m29(qx_n, isq);
                qy <= m29(qy_n, isq); qz <= m29(qz_n, isq);
                st <= S_DONE;
            end
            // ------------------------------------------------------------------
            S_DONE: begin
                out_valid <= 1'b1;
                st <= S_IDLE;
            end
            default: st <= S_IDLE;
            endcase
        end
    end

endmodule
