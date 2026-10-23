// =============================================================================
// 妙手通言 · 单手 SPI 总线调度器（sensor_if_spi · W3 正式版 v2）
// 方案 v2.1 §4.1 / 接口冻结 ② ③：
//   100Hz 节拍（ts_align tick）驱动，每帧固定时隙：
//     T0: IMU#0 连读 1+14B（CS0）
//     T1: IMU#1 连读 1+14B（CS1）
//     T2: ADC 保留 8 个结果槽；仅 ADC_SAMPLE_MASK 标记的通道发 SPI 命令
//     T3: 4B 硬件时戳（大端），末字节 tlast
//   输出单手负载 48B → AXI-Stream（merge_stream 保留 100B 帧结构）
// 初始化（复位后、首帧前）：每颗 IMU 配置写、量程回读及 WHO_AM_I 校验；
//   连续 WHO_RETRY_MAX 次仍失败标记 absent，该设备负载段填 0xEE（帧定长不变）。
// 字节引擎：B_TX(发) → B_WAIT(等) → B_EMIT(推流/推进)，B_GAP 做事务间隔离。
// 参数 IMU_ICM：0=MPU6500（正式选型，默认） 1=ICM-42688（历史点亮兼容，
//   两型号的 14B 顺序不同；当前帧 v1 与解析器均按 MPU 原始顺序）。
// =============================================================================
`timescale 1ns/1ps

module sensor_if_spi #(
    parameter CLK_FREQ_HZ  = 100_000_000,
    parameter SCLK_FREQ_HZ = 1_000_000,
    parameter IMU_ICM      = 0,
    parameter [1:0] MPU_ACCEL_FS_SEL = 2'd2, // MPU6500: +/-8g, 4096 LSB/g
    parameter [1:0] MPU_GYRO_FS_SEL  = 2'd3, // MPU6500: +/-2000 dps, 16.4 LSB/dps
    parameter [3:0] ADC_MASK = 4'h3,           // MCP3008=0x3, MCP3208=0xF
    parameter [7:0] ADC_SAMPLE_MASK = 8'h1F, // 每手 CH0–CH4 实采；CH5–CH7 帧槽填 0
    parameter GAP_CYCLES   = 100,              // 事务间隔离 ≥1µs @100MHz
    parameter WHO_RETRY_MAX= 255
)(
    input  wire        clk,
    input  wire        rst_n,
    input  wire        tick,
    input  wire [31:0] timestamp,

    output wire        sclk,
    output wire        mosi,
    input  wire        miso,
    output reg  [2:0]  cs_n,                   // [0]=IMU#0 [1]=IMU#1 [2]=ADC

    output reg  [7:0]  m_axis_tdata,
    output reg         m_axis_tvalid,
    output reg         m_axis_tlast,
    input  wire        m_axis_tready,

    output reg  [1:0]  imu_absent,
    output reg         busy
);

// ---- 主状态 ----
localparam S_INIT = 4'd0, S_IDLE = 4'd1,
           S_IMU0 = 4'd2, S_GAP0 = 4'd3,
           S_IMU1 = 4'd4, S_GAP1 = 4'd5,
           S_ADC  = 4'd6, S_TS   = 4'd7, S_DONE = 4'd8;
// ---- 字节引擎子状态 ----
localparam B_TX = 3'd0, B_WAIT = 3'd1, B_EMIT = 3'd2, B_GAP = 3'd3;

reg [3:0] state;
reg [2:0] bstate;
reg [4:0] bcnt;          // 时隙内字节序号（含命令字节）
reg [3:0] ch;            // ADC 通道
reg [1:0] init_dev;      // 0=IMU#0 1=IMU#1
reg [2:0] init_step;     // MPU: wake, SPI, gyro, accel, read gyro/accel, WHO
reg [7:0] who_retry, who_rx, gap_cnt;
reg       gyro_range_ok, accel_range_ok;
reg [31:0] ts_reg;
reg       cur_push;      // 当前字节是否需要推流
reg [7:0] push_data;     // 待推数据（B_WAIT 捕获 / absent 填 0xEE）
reg       push_last;     // 待推字节的 tlast
wire      adc_selected = ADC_SAMPLE_MASK[ch];

// ---- 底层 SPI master（板级验证版） ----
reg       spi_start;
reg [7:0] spi_tx;
wire [7:0] spi_rx;
wire      spi_busy, spi_done;
spi_master #(.CLK_FREQ_HZ(CLK_FREQ_HZ), .SCLK_FREQ_HZ(SCLK_FREQ_HZ),
             .CPOL(0), .CPHA(0), .WIDTH(8)) u_spi (
    .clk(clk), .rst_n(rst_n),
    .start(spi_start), .tx_data(spi_tx), .rx_data(spi_rx),
    .busy(spi_busy), .done(spi_done),
    .sclk(sclk), .mosi(mosi), .miso(miso)
);

// ---- 命令编码（接口冻结 ②） ----
localparam [7:0] CMD_DATA = IMU_ICM ? 8'h9D : 8'hBB;
localparam [7:0] CMD_WHO  = 8'hF5;
localparam [7:0] WHO_EXP  = IMU_ICM ? 8'h47 : 8'h70;
localparam [2:0] INIT_WHO_STEP = IMU_ICM ? 3'd3 : 3'd6;
wire init_config_ok = IMU_ICM || (gyro_range_ok && accel_range_ok);

function [15:0] cfg_of(input [2:0] step);
    case (step)
        3'd0: cfg_of = IMU_ICM ? {8'h4E, 8'h0F} : {8'h6B, 8'h00};
        3'd1: cfg_of = IMU_ICM ? {8'h4F, 8'h66} : {8'h6A, 8'h10};
        3'd2: cfg_of = IMU_ICM ? {8'h50, 8'h66} :
                               {8'h1B, 3'b000, MPU_GYRO_FS_SEL, 3'b000};
        3'd3: cfg_of = {8'h1C, 3'b000, MPU_ACCEL_FS_SEL, 3'b000};
        3'd4: cfg_of = {8'h9B, 8'h00}; // Read GYRO_CONFIG.
        3'd5: cfg_of = {8'h9C, 8'h00}; // Read ACCEL_CONFIG.
        default: cfg_of = 16'h0000;
    endcase
endfunction

// 当前字节要发什么
function [7:0] tx_of(input [3:0] st, input [4:0] b, input [3:0] c,
                     input [2:0] istep);
    reg [15:0] cfg;   // 函数返回值位选需经中间变量（Verilog 语法限制）
    begin
        cfg = cfg_of(istep);
        case (st)
            S_INIT: tx_of = (b == 5'd0)
                            ? (istep == INIT_WHO_STEP ? CMD_WHO : cfg[15:8])
                            : (istep == INIT_WHO_STEP ? 8'h00   : cfg[7:0]);
            S_IMU0, S_IMU1: tx_of = (b == 5'd0) ? CMD_DATA : 8'h00;
            S_ADC: begin
                case (b % 3)
                    // MCP3008: seven leading zeros align B9:B8 with RX1[1:0].
                    // Preserve the separate MCP3208 command when ADC_MASK=0xF.
                    5'd0:    tx_of = (ADC_MASK == 4'h3)
                                    ? 8'h01 : (8'h06 | {5'd0, c[2]});
                    5'd1:    tx_of = (ADC_MASK == 4'h3)
                                    ? {1'b1, c[2:0], 4'd0} : {c[1:0], 6'd0};
                    default: tx_of = 8'h00;
                endcase
            end
            default: tx_of = 8'h00;
        endcase
    end
endfunction

// 该字节是否推流（IMU 数据 14B / ADC 每通道后 2B / TS 4B）
function push_of(input [3:0] st, input [4:0] b);
    case (st)
        S_IMU0, S_IMU1: push_of = (b != 5'd0);
        S_ADC:          push_of = (b % 3 != 5'd0);
        S_TS:           push_of = 1'b1;
        default:        push_of = 1'b0;
    endcase
endfunction

// 当前设备是否缺席（仅 IMU 判定）
wire dev_absent = (state == S_IMU0 && imu_absent[0]) ||
                  (state == S_IMU1 && imu_absent[1]);

wire stream_accept = m_axis_tvalid && m_axis_tready;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        state <= S_INIT; bstate <= B_GAP;
        cs_n <= 3'b111; spi_start <= 1'b0; spi_tx <= 8'h00;
        bcnt <= 5'd0; ch <= 4'd0;
        init_dev <= 2'd0; init_step <= 3'd0;
        who_retry <= 8'd0; who_rx <= 8'h00; gap_cnt <= 8'd0;
        gyro_range_ok <= 1'b0; accel_range_ok <= 1'b0;
        ts_reg <= 32'd0; cur_push <= 1'b0;
        push_data <= 8'd0; push_last <= 1'b0;
        m_axis_tdata <= 8'd0; m_axis_tvalid <= 1'b0; m_axis_tlast <= 1'b0;
        imu_absent <= 2'b00; busy <= 1'b1;
    end else begin
        spi_start <= 1'b0;
        if (stream_accept) m_axis_tvalid <= 1'b0;

        // ================= 字节引擎 =================
        case (bstate)
            B_GAP:   // 事务间隔离计时（也用于复位后上电延时）
                if (gap_cnt == GAP_CYCLES[7:0]) begin
                    gap_cnt <= 8'd0;
                    bstate  <= B_TX;
                    // 出间隙时按当前状态/设备拉低对应 CS（入间隙时已抬 111）
                    if (state == S_INIT)
                        cs_n <= init_dev == 2'd0 ? 3'b110 : 3'b101;
                    else if (state == S_ADC && adc_selected)
                        cs_n <= 3'b011;
                end else gap_cnt <= gap_cnt + 8'd1;

            B_TX: begin
                cur_push  <= push_of(state, bcnt);
                push_last <= (state == S_TS && bcnt == 5'd3);
                if (state == S_TS || dev_absent ||
                    (state == S_ADC && !adc_selected)) begin
                    // 时戳 / 缺席设备 / 未接 ADC 通道：不发 SPI，仍保留帧槽
                    if (state == S_ADC && !adc_selected)
                        push_data <= 8'h00;
                    bstate <= B_EMIT;
                end else if ((state == S_INIT || state == S_IMU0 ||
                              state == S_IMU1 || state == S_ADC) &&
                             !spi_busy && !m_axis_tvalid) begin
                    spi_tx    <= tx_of(state, bcnt, ch, init_step);
                    spi_start <= 1'b1;
                    bstate    <= B_WAIT;
                end
            end

            B_WAIT: if (spi_done) begin
                // ADC 高字节要先掩码；WHO 回读单独捕获
                if (state == S_ADC && bcnt % 3 == 5'd1)
                    push_data <= {4'd0, spi_rx[3:0] & ADC_MASK};
                else
                    push_data <= spi_rx;
                if (state == S_INIT && bcnt == 5'd1) begin
                    if (init_step == INIT_WHO_STEP)
                        who_rx <= spi_rx;
                    if (!IMU_ICM && init_step == 3'd4)
                        gyro_range_ok <= (spi_rx[4:3] == MPU_GYRO_FS_SEL);
                    if (!IMU_ICM && init_step == 3'd5)
                        accel_range_ok <= (spi_rx[4:3] == MPU_ACCEL_FS_SEL);
                end
                bstate <= B_EMIT;
            end

            B_EMIT: begin
                // 装填推流数据（等上一字节被接收后）
                if (cur_push && !m_axis_tvalid) begin
                    m_axis_tdata  <= dev_absent ? 8'hEE :
                        (state == S_TS) ?
                            (bcnt == 5'd0 ? ts_reg[31:24] :
                             bcnt == 5'd1 ? ts_reg[23:16] :
                             bcnt == 5'd2 ? ts_reg[15:8]  : ts_reg[7:0])
                        : push_data;
                    m_axis_tvalid <= 1'b1;
                    m_axis_tlast  <= push_last;
                end
                // 推进条件：无需推流且无挂起数据，或推流被接收
                // （仅在事务状态时推进；GAP/IDLE/DONE 由主状态机接管）
                if (((!cur_push && !m_axis_tvalid) || stream_accept) &&
                    (state == S_INIT || state == S_IMU0 || state == S_IMU1 ||
                     state == S_ADC  || state == S_TS)) begin
                    cur_push <= 1'b0;
                    case (state)
                        S_INIT: begin
                            if (bcnt == 5'd1) begin
                                // 事务结束：一律先抬 CS（真实芯片靠 CS 上升沿锁存），
                                // 下一事务的 CS 由 B_GAP 出口按 init_dev 重新拉低
                                bcnt <= 5'd0;
                                cs_n <= 3'b111;
                                bstate <= B_GAP;
                                if (init_step == INIT_WHO_STEP) begin
                                    // Identity and both range readbacks must match.
                                    if ((who_rx == WHO_EXP && init_config_ok) ||
                                        who_retry == WHO_RETRY_MAX) begin
                                        if (who_rx != WHO_EXP || !init_config_ok)
                                            imu_absent[init_dev[0]] <= 1'b1;
                                        who_retry <= 8'd0;
                                        init_step <= 3'd0;
                                        gyro_range_ok <= 1'b0;
                                        accel_range_ok <= 1'b0;
                                        if (init_dev == 2'd0) begin
                                            init_dev <= 2'd1;
                                        end else begin
                                            state <= S_IDLE;
                                            busy  <= 1'b0;
                                        end
                                    end else begin
                                        who_retry <= who_retry + 1'b1;
                                        init_step <= 3'd0;
                                        gyro_range_ok <= 1'b0;
                                        accel_range_ok <= 1'b0;
                                    end
                                end else begin
                                    init_step <= init_step + 3'd1;
                                end
                            end else begin
                                bcnt   <= bcnt + 5'd1;
                                bstate <= B_TX;
                            end
                        end
                        S_IMU0, S_IMU1: begin
                            if (bcnt == 5'd14) begin
                                bcnt <= 5'd0;
                                cs_n <= 3'b111;
                                state <= (state == S_IMU0) ? S_GAP0 : S_GAP1;
                            end else begin
                                bcnt   <= bcnt + 5'd1;
                                bstate <= B_TX;   // B_TX 内对 absent 自动转 B_EMIT
                            end
                        end
                        S_ADC: begin
                            if (bcnt == 5'd23) begin
                                bcnt <= 5'd0; ch <= 4'd0;
                                cs_n <= 3'b111;
                                state  <= S_TS;
                                bstate <= B_TX;
                            end else if (bcnt % 3 == 5'd2) begin
                                // 每通道 3B 结束：抬 CS 复位 ADC 采样状态机，
                                // 经 B_GAP 短隔离后由 B_GAP 出口按需拉低
                                bcnt   <= bcnt + 5'd1;
                                ch     <= ch + 4'd1;
                                cs_n   <= 3'b111;
                                bstate <= ADC_SAMPLE_MASK[ch + 4'd1]
                                          ? B_GAP : B_TX;
                            end else begin
                                bcnt   <= bcnt + 5'd1;
                                bstate <= B_TX;
                            end
                        end
                        S_TS: begin
                            if (bcnt == 5'd3) begin
                                bcnt  <= 5'd0;
                                state <= S_DONE;
                            end else begin
                                bcnt   <= bcnt + 5'd1;
                                bstate <= B_TX;
                            end
                        end
                        default: state <= S_DONE;
                    endcase
                end
            end
            default: bstate <= B_TX;
        endcase

        // ================= 主状态（非字节态） =================
        case (state)
            S_IDLE: if (tick) begin
                busy   <= 1'b1;
                ts_reg <= timestamp;
                bcnt   <= 5'd0; ch <= 4'd0;
                cs_n   <= 3'b110;
                bstate <= B_TX;
                state  <= S_IMU0;
            end
            S_GAP0, S_GAP1:
                if (gap_cnt == GAP_CYCLES[7:0]) begin
                    gap_cnt <= 8'd0;
                    bstate  <= B_TX;
                    cs_n    <= (state == S_GAP0) ? 3'b101 :
                               (ADC_SAMPLE_MASK[0] ? 3'b011 : 3'b111);
                    state   <= (state == S_GAP0) ? S_IMU1 : S_ADC;
                end else gap_cnt <= gap_cnt + 8'd1;
            S_DONE: begin
                busy   <= 1'b0;
                bstate <= B_TX;
                state  <= S_IDLE;
            end
            default: ;
        endcase
    end
end

endmodule
