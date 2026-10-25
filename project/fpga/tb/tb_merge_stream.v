// =============================================================================
// 妙手通言 · merge_stream testbench（W3 · xsim）
// 校验点（接口冻结 ③ v1.0）：
//   1. 正常帧：AA + seq(=左手末字节) + L48 + R48 + 55 5A，tlast@99
//   2. 右手超时：只发左手 → 右手段填 0xEE，stat_r_timeout=1
//   3. 连发 2 帧：seq 各自正确（缓冲不串帧）
// 运行：Vivado → set_property top tb_merge_stream [get_filesets sim_1] → 仿真
// =============================================================================
`timescale 1ns/1ps

module tb_merge_stream;

localparam CLK_T = 10;   // 100MHz

reg clk = 0, rst_n = 0;
always #(CLK_T/2) clk = ~clk;

// ---- DUT ----
reg  [7:0] l_tdata = 0; reg l_tvalid = 0, l_tlast = 0; wire l_tready;
reg  [7:0] r_tdata = 0; reg r_tvalid = 0, r_tlast = 0; wire r_tready;
wire [7:0] m_tdata; wire m_tvalid, m_tlast;
reg        m_tready = 1;                 // DMA 简化模型：永远就绪
wire [15:0] stat_r_timeout;

merge_stream #(.TIMEOUT_CYCLES(500)) dut (
    .clk(clk), .rst_n(rst_n),
    .s_axis_l_tdata(l_tdata), .s_axis_l_tvalid(l_tvalid),
    .s_axis_l_tlast(l_tlast), .s_axis_l_tready(l_tready),
    .s_axis_r_tdata(r_tdata), .s_axis_r_tvalid(r_tvalid),
    .s_axis_r_tlast(r_tlast), .s_axis_r_tready(r_tready),
    .m_axis_tdata(m_tdata), .m_axis_tvalid(m_tvalid),
    .m_axis_tlast(m_tlast), .m_axis_tready(m_tready),
    .stat_r_timeout(stat_r_timeout), .busy()
);

// ---- 激励任务：发一只手的 48B 帧（base+i 图案，末字节=seq_low） ----
// 下降沿阻塞驱动，DUT 上升沿采样，1 字节/clk，无竞争
task automatic send_hand(input left, input [7:0] base, input [7:0] seq_low);
    integer i;
    begin
        for (i = 0; i < 48; i = i + 1) begin
            @(negedge clk);
            if (left) begin
                l_tdata  = (i == 47) ? seq_low : ((i >= 44) ? 8'd0 : base + i);
                l_tvalid = 1'b1;
                l_tlast  = (i == 47);
            end else begin
                r_tdata  = (i == 47) ? seq_low : ((i >= 44) ? 8'd0 : base + i);
                r_tvalid = 1'b1;
                r_tlast  = (i == 47);
            end
        end
        @(negedge clk);
        if (left) begin l_tvalid = 1'b0; l_tlast = 1'b0; end
        else      begin r_tvalid = 1'b0; r_tlast = 1'b0; end
        $display("[%0t] 激励：%s手 48B 发送完成（seq=%02x）",
                 $time, left ? "左" : "右", seq_low);
    end
endtask

// ---- DUT 内部状态追踪（只在状态变化时打印，防爆日志） ----
reg [5:0] trc_prev = 0;
always @(posedge clk) begin
    if (rst_n) begin
        trc_prev <= {dut.got_l, dut.got_r, dut.r_miss, dut.emitting,
                     m_tvalid, (|dut.emit_cnt)};
        if ({dut.got_l, dut.got_r, dut.r_miss, dut.emitting,
             m_tvalid, (|dut.emit_cnt)} != trc_prev)
            $display("[%0t] TRC got_l=%b got_r=%b r_miss=%b emitting=%b cnt=%0d tvalid=%b",
                     $time, dut.got_l, dut.got_r, dut.r_miss,
                     dut.emitting, dut.emit_cnt, m_tvalid);
    end
end

// ---- 接收通路逐字节追踪 ----
always @(posedge clk) begin
    if (l_tvalid)
        $display("[%0t] RX-L d=%02x last=%b rdy=%b rcv_l=%0d got_l=%b",
                 $time, l_tdata, l_tlast, l_tready, dut.rcv_l, dut.got_l);
    if (r_tvalid)
        $display("[%0t] RX-R d=%02x last=%b rdy=%b rcv_r=%0d got_r=%b",
                 $time, r_tdata, r_tlast, r_tready, dut.rcv_r, dut.got_r);
end

// ---- 记分板 ----
reg [7:0] frame [0:99];
integer   fcnt = 0;
integer   frames_checked = 0;
integer   errors = 0;

always @(posedge clk) begin
    if (m_tvalid && m_tready) begin
        frame[fcnt] = m_tdata;          // tb 内阻塞赋值，末字节立即可见
        if (m_tlast) begin
            if (fcnt != 99) begin
                $display("ERROR: 帧长 %0d != 100", fcnt + 1); errors = errors + 1;
            end
            check_frame();
            fcnt <= 0;
        end else fcnt <= fcnt + 1;
    end
end

// 期望值由测试步骤写入
reg [7:0] exp_seq;
reg       exp_r_miss;
reg [7:0] exp_l_base, exp_r_base;

task check_frame;
    integer i;
    begin
        frames_checked = frames_checked + 1;
        if (frame[0] !== 8'hAA) begin
            $display("ERROR: 帧头 %02x != AA", frame[0]); errors = errors + 1;
        end
        if (frame[1] !== exp_seq) begin
            $display("ERROR: seq %02x != %02x", frame[1], exp_seq); errors = errors + 1;
        end
        for (i = 0; i < 48; i = i + 1) begin
            if (frame[2+i] !== ((i == 47) ? exp_seq : ((i >= 44) ? 8'd0 : exp_l_base + i))) begin
                $display("ERROR: L[%0d]=%02x", i, frame[2+i]); errors = errors + 1;
            end
            if (frame[50+i] !== (exp_r_miss ? 8'hEE :
                                 ((i == 47) ? exp_seq : ((i >= 44) ? 8'd0 : exp_r_base + i)))) begin
                $display("ERROR: R[%0d]=%02x", i, frame[50+i]); errors = errors + 1;
            end
        end
        if (frame[98] !== 8'h55 || frame[99] !== 8'h5A) begin
            $display("ERROR: 帧尾 %02x %02x", frame[98], frame[99]);
            errors = errors + 1;
        end
        $display("帧 %0d 校验完成（seq=%02x, r_miss=%0d）",
                 frames_checked, exp_seq, exp_r_miss);
    end
endtask

// ---- 仿真流程 ----
initial begin
    repeat (20) @(posedge clk);
    rst_n <= 1;
    repeat (10) @(posedge clk);
    $display("[%0t] 复位完成，开始用例1", $time);

    // 用例 1：双手正常（右手故意晚到几十拍，验证等待逻辑）
    exp_l_base = 8'h10; exp_r_base = 8'h40; exp_seq = 8'hA5; exp_r_miss = 0;
    fork
        send_hand(1, 8'h10, 8'hA5);
        begin repeat (30) @(posedge clk); send_hand(0, 8'h40, 8'hA5); end
    join
    $display("[%0t] 用例1发送完毕，等帧", $time);
    wait (frames_checked == 1);
    $display("[%0t] 用例1完成", $time);

    // 用例 2：右手超时（只发左手）
    exp_seq = 8'h5A; exp_r_miss = 1;
    send_hand(1, 8'h10, 8'h5A);
    wait (frames_checked == 2);
    repeat (5) @(posedge clk);   // stat_r_timeout 在 tlast 拍 NBA 更新，隔几拍再读
    if (stat_r_timeout != 16'd1) begin
        $display("ERROR: stat_r_timeout=%0d != 1", stat_r_timeout);
        errors = errors + 1;
    end

    // 用例 3：双手恢复正常（缓冲不串帧）
    exp_seq = 8'h66; exp_r_miss = 0;
    fork
        send_hand(1, 8'h10, 8'h66);
        send_hand(0, 8'h40, 8'h66);
    join
    wait (frames_checked == 3);

    repeat (100) @(posedge clk);
    if (errors == 0)
        $display("==== TEST PASSED: %0d 帧全部正确，timeout=%0d ====",
                 frames_checked, stat_r_timeout);
    else
        $display("==== TEST FAILED: %0d 个错误 ====", errors);
    $finish;
end

// 看门狗
initial begin
    #5_000_000;
    $display("==== TEST FAILED: 超时（frames=%0d errors=%0d）====",
             frames_checked, errors);
    $finish;
end

endmodule
