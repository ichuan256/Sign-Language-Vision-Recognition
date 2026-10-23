// =============================================================================
// 妙手通言 · 点亮轮询序列器（bringup_seq · 双 IMU 兼容版 v2）
// 10Hz 节拍顺序执行五个事务（对应 docs/W2_硬件通路点亮指南.md）：
//   P0: IMU 配置写1       CS0  ICM: 4E/0F(PWR_MGMT0)  MPU: 6B/00(PWR_MGMT_1)
//   P1: IMU 配置写2       CS0  ICM: 4E/0F(重复无害)   MPU: 6A/10(USER_CTRL 禁I2C)
//   P2: IMU WHO_AM_I      CS0  发 F5 收 1B   → ICM=0x47 / MPU=0x70
//   P3: IMU 数据连读 14B  CS0  ICM: 发 9D(temp+acc+gyro)  MPU: 发 BB(acc+temp+gyro)
//   P4: MCP3008 CH0       CS2  发 01/80/00   → 10bit 弯曲值
// 结果通过输出端口送往 axi_lite_regs，PS 直接读。
// 参数 IMU_ICM：0=MPU6500（正式选型，默认）  1=ICM-42688（历史兼容）
// 备注：MCP3008 为 10 位（掩码 0x03）；换 MCP3208 时把 ADC_MASK 改 0x0F。
//       MPU6500 默认量程 ±2g/±250dps（16384 LSB/g, 131 LSB/dps）；
//       ICM-42688 默认量程 ±16g/±2000dps（2048 LSB/g, 16.4 LSB/dps）。
// =============================================================================
`timescale 1ns/1ps

module bringup_seq #(
    parameter CLK_FREQ_HZ = 100_000_000,
    parameter TICK_HZ     = 100,
    parameter TDIV        = CLK_FREQ_HZ / TICK_HZ,  // 分频比（parameter 消 19-587）
    parameter IMU_ICM     = 0,                      // 0=MPU6500 1=ICM-42688
    parameter [7:0] ADC_MASK = 8'h03,               // MCP3008=0x03, MCP3208=0x0F
    parameter SPI_HZ      = 1_000_000,              // SCLK 频率（MPU6500 排障可降 100k）
    parameter SWAP_CS     = 0                       // 1=A/B 交叉：IMU↔ADC 片选对调
)(
    input  wire        clk,
    input  wire        rst_n,

    output wire        sclk,
    output wire        mosi,
    input  wire        miso,
    output reg  [2:0]  cs_n,

    // 结果输出（直通 axi_lite_regs）
    output reg  [31:0] frame_cnt,
    output reg  [7:0]  who_am_i,
    output reg         who_ok,
    output reg  [15:0] imu_ax, imu_ay, imu_az, imu_temp,
    output reg  [15:0] imu_gx, imu_gy, imu_gz,
    output reg  [15:0] adc_ch0,
    output reg         busy
);

// ---- 100MHz/100Hz 节拍（100Hz = 方案 §3.1 正式采样率；10Hz 仅为 W2 点亮观察用） ----
reg [$clog2(TDIV)-1:0] tcnt;
reg tick;
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin tcnt <= 0; tick <= 1'b0; end
    else if (tcnt == TDIV-1) begin tcnt <= 0; tick <= 1'b1; end
    else begin tcnt <= tcnt + 1'b1; tick <= 1'b0; end
end

// ---- 底层 SPI master（板级验证版，MSB 漏采已修复） ----
reg        spi_start;
reg  [7:0] spi_tx;
wire [7:0] spi_rx;
wire       spi_busy, spi_done;
spi_master #(.CLK_FREQ_HZ(CLK_FREQ_HZ), .SCLK_FREQ_HZ(SPI_HZ),
             .CPOL(0), .CPHA(0), .WIDTH(8)) u_spi (
    .clk(clk), .rst_n(rst_n),
    .start(spi_start), .tx_data(spi_tx), .rx_data(spi_rx),
    .busy(spi_busy), .done(spi_done),
    .sclk(sclk), .mosi(mosi), .miso(miso)
);

// ---- 事务描述（5 相）----
// PH_CFG2 的由来（网上案例验证的坑）：MPU6500 上电默认 I2C 模式，
// 必须写 USER_CTRL(0x6A)=0x10 (I2C_IF_DIS) 显式禁用 I2C，否则总线波动
// 可能被误判为 I2C 起始条件导致 SPI 锁死、读回全 0xFF。
// ICM-42688 无此机制，CFG2 相重复写 PWR_MGMT0（无害）。
localparam PH_CFG = 3'd0, PH_CFG2 = 3'd1, PH_WHO = 3'd2,
           PH_IMU = 3'd3, PH_ADC = 3'd4;
reg [2:0] phase;
reg [4:0] bidx;          // 相内字节序号（含命令字节）
reg [7:0] sh_hi;         // ADC/16bit 高字节暂存

function [7:0] cmd_of(input [2:0] ph);
    case (ph)
        PH_CFG:  cmd_of = IMU_ICM ? 8'h4E : 8'h6B;  // PWR_MGMT0 / PWR_MGMT_1
        PH_CFG2: cmd_of = IMU_ICM ? 8'h4E : 8'h6A;  // 重复使能 / USER_CTRL
        PH_WHO:  cmd_of = 8'hF5;                    // 0x75 | 0x80（两芯片同址）
        PH_IMU:  cmd_of = IMU_ICM ? 8'h9D : 8'hBB;  // 0x1D / 0x3B 起连读
        default: cmd_of = 8'h01;                    // MCP3008 start bit
    endcase
endfunction

localparam [7:0] CFG_VAL    = IMU_ICM ? 8'h0F : 8'h00;  // ICM: gyro+acc LN；MPU: 唤醒
localparam [7:0] CFG2_VAL   = IMU_ICM ? 8'h0F : 8'h10;  // ICM: 重复无害；MPU: I2C_IF_DIS
localparam [7:0] WHO_EXPECT = IMU_ICM ? 8'h47 : 8'h70;

function [4:0] nbytes(input [2:0] ph);  // 命令+数据 总字节数
    case (ph)
        PH_CFG:  nbytes = 5'd2;   // reg + value
        PH_CFG2: nbytes = 5'd2;   // reg + value
        PH_WHO:  nbytes = 5'd2;   // cmd + 1B
        PH_IMU:  nbytes = 5'd15;  // cmd + 14B
        default: nbytes = 5'd3;   // 01 / 80 / 00
    endcase
endfunction

function [2:0] cs_of(input [2:0] ph);
    // cs_n 位序：[0]=CS0(针4) [1]=CS1(针7) [2]=CS2(针8)，低有效
    // SWAP_CS=1 时 IMU 改走 CS2、ADC 改走 CS0，用于片选通路 A/B 交叉验证
    case (ph)
        PH_ADC: cs_of = SWAP_CS ? 3'b110 : 3'b011;
        default: cs_of = SWAP_CS ? 3'b011 : 3'b110;
    endcase
endfunction

localparam S_IDLE=3'd0, S_START=3'd1, S_WAIT=3'd2, S_STORE=3'd3,
           S_GAP=3'd4, S_NEXT=3'd5;
reg [2:0] state;
reg [7:0] gap_cnt;

// 统一按 ICM 顺序（temp,acc,gyro）落点；MPU 字节序（acc,temp,gyro）先重排索引
task store_imu(input [4:0] raw_idx, input [7:0] val);
    reg [4:0] idx;
    begin
        if (IMU_ICM) idx = raw_idx;
        else if (raw_idx < 5'd6)  idx = raw_idx + 5'd2;  // acc 0-5 → 2-7
        else if (raw_idx < 5'd8)  idx = raw_idx - 5'd6;  // temp 6-7 → 0-1
        else                      idx = raw_idx;         // gyro 8-13 同位
        case (idx)
            5'd0:  imu_temp[15:8] <= val;
            5'd1:  imu_temp[7:0]  <= val;
            5'd2:  imu_ax[15:8]   <= val;
            5'd3:  imu_ax[7:0]    <= val;
            5'd4:  imu_ay[15:8]   <= val;
            5'd5:  imu_ay[7:0]    <= val;
            5'd6:  imu_az[15:8]   <= val;
            5'd7:  imu_az[7:0]    <= val;
            5'd8:  imu_gx[15:8]   <= val;
            5'd9:  imu_gx[7:0]    <= val;
            5'd10: imu_gy[15:8]   <= val;
            5'd11: imu_gy[7:0]    <= val;
            5'd12: imu_gz[15:8]   <= val;
            5'd13: imu_gz[7:0]    <= val;
            default: ;
        endcase
    end
endtask

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        state <= S_IDLE; phase <= PH_CFG; bidx <= 5'd0;
        cs_n <= 3'b111; spi_start <= 1'b0; spi_tx <= 8'h00;
        frame_cnt <= 32'd0; who_am_i <= 8'h00; who_ok <= 1'b0;
        imu_ax<=0; imu_ay<=0; imu_az<=0; imu_temp<=0;
        imu_gx<=0; imu_gy<=0; imu_gz<=0;
        adc_ch0 <= 16'd0; busy <= 1'b0; gap_cnt <= 8'd0; sh_hi <= 8'h00;
    end else begin
        spi_start <= 1'b0;
        case (state)
            S_IDLE: if (tick) begin
                busy <= 1'b1; phase <= PH_CFG; bidx <= 5'd0;
                cs_n <= cs_of(PH_CFG);
                state <= S_START;
            end
            S_START: if (!spi_busy) begin
                if (bidx == 5'd0)
                    spi_tx <= cmd_of(phase);
                else if (phase == PH_CFG && bidx == 5'd1)
                    spi_tx <= CFG_VAL;
                else if (phase == PH_CFG2 && bidx == 5'd1)
                    spi_tx <= CFG2_VAL;
                else if (phase == PH_ADC && bidx == 5'd1)
                    spi_tx <= 8'h80;            // SGL=1, CH0
                else
                    spi_tx <= 8'h00;            // dummy 读
                spi_start <= 1'b1;
                state <= S_WAIT;
            end
            S_WAIT: if (spi_done) state <= S_STORE;
            S_STORE: begin
                if (bidx != 5'd0 || phase == PH_ADC) begin
                    case (phase)
                        PH_WHO: if (bidx == 5'd1) begin
                            who_am_i <= spi_rx;
                            who_ok   <= (spi_rx == WHO_EXPECT);
                        end
                        PH_IMU: if (bidx >= 5'd1) store_imu(bidx - 5'd1, spi_rx);
                        PH_ADC: begin
                            if (bidx == 5'd1) sh_hi <= spi_rx;
                            if (bidx == 5'd2)
                                adc_ch0 <= (({8'd0, (sh_hi & ADC_MASK)} << 8)
                                            | {8'd0, spi_rx});
                        end
                        default: ;   // PH_CFG 无回读
                    endcase
                end
                if (bidx == nbytes(phase) - 1) begin
                    cs_n <= 3'b111;             // 事务结束抬 CS
                    gap_cnt <= 8'd0;
                    state <= S_GAP;
                end else begin
                    bidx <= bidx + 5'd1;
                    state <= S_START;
                end
            end
            // 设备间隔离：普通相 ≥1µs；配置写后加长到 2.5µs。
            // 注：陀螺仪启动需数十 ms，因每帧重写配置并连续轮询，
            //     首个周期数据可能为 0，从第二帧起即稳定。
            S_GAP: if (((phase == PH_CFG || phase == PH_CFG2) && gap_cnt == 8'd250) ||
                       ((phase != PH_CFG && phase != PH_CFG2) && gap_cnt == 8'd99)) begin
                state <= S_NEXT;
            end else gap_cnt <= gap_cnt + 8'd1;
            S_NEXT: begin
                if (phase == PH_ADC) begin      // 五相全部完成
                    busy <= 1'b0;
                    frame_cnt <= frame_cnt + 1'b1;
                    state <= S_IDLE;
                end else begin
                    phase <= phase + 3'd1;
                    bidx <= 5'd0;
                    cs_n <= cs_of(phase + 3'd1);
                    state <= S_START;
                end
            end
            default: state <= S_IDLE;
        endcase
    end
end

endmodule
