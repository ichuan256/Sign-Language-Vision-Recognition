// =============================================================================
// 妙手通言 · sensor_if_spi testbench（W3 · xsim）
// 从机模型：
//   默认 MPU6500 ×2：WHO(F5)→0x70；连读(BB)→14B 图案
//   兼容路径：-DTB_ICM 切换 ICM-42688（WHO=0x47，命令=9D）
//       IMU#0: 10..1D，IMU#1: 40..4D；配置写忽略
//   MCP3008（CS2）：每通道 3B，回高字节（ch），低字节=A0+ch
// 本文件保留固定字节图案的冒烟检查；真实 ADC 位时序由独立的
// tb_mcp3008_protocol.v 验证，该模型不读取 DUT 内部状态。
// 每手读取 ADC CH0..CH4；CH5..CH7 为 0，帧长为 48B。
// 运行：Vivado → Flow → Run Simulation（或 xsim 批处理，见注释末）
// =============================================================================
`timescale 1ns/1ps

module tb_sensor_if_spi;

localparam CLK_T = 10;   // 100MHz
`ifdef TB_ICM
localparam IMU_SELECT = 1;
localparam [3:0] ADC_SELECT = 4'hF;
localparam [7:0] WHO_VALUE = 8'h47;
`else
localparam IMU_SELECT = 0;
localparam [3:0] ADC_SELECT = 4'h3;
localparam [7:0] WHO_VALUE = 8'h70;
`endif

reg clk = 0, rst_n = 0;
always #(CLK_T/2) clk = ~clk;

// ---- 快速节拍：TICK_HZ=1MHz → 100 clk 一帧，加速仿真 ----
wire        tick;
wire [31:0] timestamp;
ts_align #(.CLK_FREQ_HZ(100_000_000), .TICK_HZ(1_000_000)) u_ts (
    .clk(clk), .rst_n(rst_n), .tick(tick), .timestamp(timestamp)
);

// ---- DUT ----
wire       sclk, mosi;
wire [2:0] cs_n;
wire [7:0] m_axis_tdata;
wire       m_axis_tvalid, m_axis_tlast;
wire [1:0] imu_absent;
wire       busy;
reg        miso = 0;
wire       m_axis_tready = 1'b1;   // DMA 简化模型：永远就绪

sensor_if_spi #(.CLK_FREQ_HZ(100_000_000), .SCLK_FREQ_HZ(10_000_000),
                .IMU_ICM(IMU_SELECT), .ADC_MASK(ADC_SELECT),
                .ADC_SAMPLE_MASK(8'h1F), .GAP_CYCLES(10),
                .WHO_RETRY_MAX(20)) dut (
    .clk(clk), .rst_n(rst_n),
    .tick(tick), .timestamp(timestamp),
    .sclk(sclk), .mosi(mosi), .miso(miso), .cs_n(cs_n),
    .m_axis_tdata(m_axis_tdata), .m_axis_tvalid(m_axis_tvalid),
    .m_axis_tlast(m_axis_tlast), .m_axis_tready(m_axis_tready),
    .imu_absent(imu_absent), .busy(busy)
);

// ---- SPI 从机模型（Mode 0：上升沿采 MOSI，下降沿换 MISO） ----
// 通用于 ICM/ADC：解析首字节命令，准备应答字节流
reg [4:0] byte_idx[2:0];

wire [2:0] cs_act = ~cs_n;  // 高有效

// ---- 关键：SCLK 空闲（CS 高）时没有时钟沿，复位不能写在 sclk 块的 else 里！
// ---- 用 clk 域检测 CS 下降沿 = 事务开始，在此归零所有跨字节状态
reg [2:0] cs_n_d = 3'b111;
wire [2:0] cs_fall = cs_n_d & ~cs_n;       // CS 拉低沿 = 新事务开始
integer adc_transactions = 0;
always @(posedge clk) begin
    cs_n_d <= cs_n;
    if (cs_fall[2]) adc_transactions <= adc_transactions + 1;
end

// ADC 通道图案：B1 回 {4'b0, ch}，B2 回 A0+ch；跟踪 ADC 字节序
reg [3:0] adc_ch_m = 0;
reg [1:0] adc_b    = 0;
reg [7:0] rx_sh    = 8'h00;
reg [3:0] bc       = 4'd0;      // SCLK idle has no edge that could clear X
integer adc_command_errors = 0;

// 事务开始：字节计数/移位清零；ADC 模型按本次选中的通道给出不同图案。
always @(posedge clk) begin
    if (|cs_fall) begin
        byte_idx[0] <= 5'd0;
        bc          <= 4'd0;
        rx_sh       <= 8'h00;
    end
    if (cs_fall[2]) adc_ch_m <= dut.ch;
    if (cs_fall[0]) adc_b <= 2'd0;
end

// 逐从机收发移位
reg [7:0] tx_sh = 8'h00;

// 统一从机时序逻辑（按当前激活 CS 路由）
always @(posedge sclk) begin
    if (cs_act != 3'b000) begin
        rx_sh <= {rx_sh[6:0], mosi};
        bc <= bc + 4'd1;
        if (bc == 4'd7) begin
            // 完整收一字节
            bc <= 4'd0;
            byte_idx[0] <= byte_idx[0] + 5'd1;
        end
    end else begin
        bc <= 4'd0;
        byte_idx[0] <= 5'd0;
        rx_sh <= 8'h00;
    end
end

// 命令锁存与应答装载（每字节首个下降沿装新字节，之后逐位移出）
reg [7:0] cur_cmd;
reg [7:0] nxt_byte;
always @(negedge sclk) begin
    if (cs_act != 3'b000) begin
        if (bc == 4'd0) begin
            if (cs_act[2]) begin
                // ADC：按字节位置回图案
                case (adc_b)
                    2'd0:    nxt_byte = 8'h00;
                    2'd1:    nxt_byte = {4'd0, adc_ch_m};
                    default: nxt_byte = 8'hA0 + {4'd0, adc_ch_m};
                endcase
            end else if (byte_idx[0] == 5'd0) begin
                nxt_byte = 8'h00;                       // 命令字节期间从机不发
            end else if (cur_cmd == 8'hF5) begin
                nxt_byte = WHO_VALUE;                    // WHO_AM_I
            end else if (!IMU_SELECT && cur_cmd == 8'h9B) begin
                nxt_byte = 8'h18;                        // gyro +/-2000 dps
            end else if (!IMU_SELECT && cur_cmd == 8'h9C) begin
                nxt_byte = 8'h10;                        // accel +/-8g
            end else begin
                // 连读(9D)：现算图案，不经过 memory，杜绝 X
                nxt_byte = (cs_act[0] ? 8'h10 : 8'h40) + (byte_idx[0] - 5'd1);
            end
            miso   <= nxt_byte[7];
            tx_sh  <= {nxt_byte[6:0], 1'b0};
        end else begin
            miso   <= tx_sh[7];
            tx_sh  <= {tx_sh[6:0], 1'b0};
        end
    end else begin
        miso <= 1'b0;      // CS 高：总线释放（adc_ch_m/byte_idx 复位见 clk 域块）
    end
end

// ---- 调试：CS0 事务逐字节打印（从机视角）----
always @(negedge sclk) begin
    if (cs_act[0] && bc == 4'd0)
        $display("[%0t] SLV CS0 装载 nxt=%02x (byte_idx=%0d cur_cmd=%02x)",
                 $time, nxt_byte, byte_idx[0], cur_cmd);
end
always @(posedge sclk) begin
    if (cs_act[0] && bc == 4'd7)
        $display("[%0t] SLV CS0 收满 byte%0d rx=%02x",
                 $time, byte_idx[0], {rx_sh[6:0], mosi});
end

// 命令捕获（每字节结束）
always @(posedge sclk) begin
    if (cs_act != 3'b000 && bc == 4'd7) begin
        if (cs_act[2] && adc_b == 2'd0 &&
            {rx_sh[6:0], mosi} !== ((ADC_SELECT == 4'h3) ? 8'h01 : (8'h06 | {5'd0, dut.ch[2]}))) begin
            $display("ERROR: ADC ch%0d command B0=%02x", dut.ch, {rx_sh[6:0], mosi});
            adc_command_errors = adc_command_errors + 1;
        end
        if (cs_act[2] && adc_b == 2'd1 &&
            {rx_sh[6:0], mosi} !== ((ADC_SELECT == 4'h3) ? {1'b1, dut.ch[2:0], 4'd0} : {dut.ch[1:0], 6'd0})) begin
            $display("ERROR: ADC ch%0d command B1=%02x", dut.ch, {rx_sh[6:0], mosi});
            adc_command_errors = adc_command_errors + 1;
        end
        if (byte_idx[0] == 5'd0 && !cs_act[2])
            cur_cmd <= {rx_sh[6:0], mosi};
        if (cs_act[2]) begin
            if (adc_b == 2'd2) begin
                adc_b <= 2'd0;
            end else adc_b <= adc_b + 2'd1;
        end
    end
end

// ================= 记分板 =================
reg [7:0] frame [0:63];
integer   fcnt = 0;
integer   frames_checked = 0;
integer   errors = 0;
reg [31:0] ts_seen;

always @(posedge clk) begin
    if (m_axis_tvalid && m_axis_tready) begin
        frame[fcnt] = m_axis_tdata;              // tb 内用阻塞赋值，末字节立即可见
        if (m_axis_tlast) begin
            check_frame(fcnt + 1);
            fcnt <= 0;
        end else fcnt <= fcnt + 1;
    end
end

task check_frame(input integer n);
    integer i;
    begin
        frames_checked = frames_checked + 1;
        if (n != 48) begin
            $display("ERROR: 帧长 %0d != 48", n); errors = errors + 1;
        end
        for (i = 0; i < 14; i = i + 1) begin
            if (frame[i] !== (8'h10 + i)) begin
                $display("ERROR: IMU0[%0d]=%02x 期望 %02x", i, frame[i], 8'h10+i);
                errors = errors + 1;
            end
            if (frame[14+i] !== (8'h40 + i)) begin
                $display("ERROR: IMU1[%0d]=%02x 期望 %02x", i, frame[14+i], 8'h40+i);
                errors = errors + 1;
            end
        end
        for (i = 0; i < 8; i = i + 1) begin
            if (frame[28+2*i] !== ((i <= 4) ? (i & ADC_SELECT) : 0) ||
                frame[29+2*i] !== ((i <= 4) ? (8'hA0 + i) : 0)) begin
                $display("ERROR: ADC ch%0d = %02x %02x", i, frame[28+2*i], frame[29+2*i]);
                errors = errors + 1;
            end
        end
        ts_seen = {frame[44], frame[45], frame[46], frame[47]};
        $display("帧 %0d 校验完成，时戳 = %0d", frames_checked, ts_seen);
    end
endtask

// ================= 仿真流程 =================
initial begin
    repeat (20) @(posedge clk);
    rst_n <= 1;
    // 等初始化完成
    wait (busy == 1'b0);
    $display("初始化完成 @%0t，imu_absent=%b，who_rx=%02x", $time, imu_absent, dut.who_rx);
    // 跑 3 帧
    wait (frames_checked == 3);
    repeat (100) @(posedge clk);
    if (adc_transactions != 15) begin
        $display("ERROR: ADC SPI transactions=%0d != 15 (CH0..CH4 x 3 frames)",
                 adc_transactions);
        errors = errors + 1;
    end
    errors = errors + adc_command_errors;
    if (errors == 0)
        $display("==== TEST PASSED: %0d 帧全部正确，absent=%b ====",
                 frames_checked, imu_absent);
    else
        $display("==== TEST FAILED: %0d 个错误 ====", errors);
    $finish;
end

// 看门狗
initial begin
    #50_000_000;
    $display("==== TEST FAILED: 超时（frames=%0d errors=%0d）====",
             frames_checked, errors);
    $finish;
end

endmodule
