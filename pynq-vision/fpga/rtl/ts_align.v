// =============================================================================
// 妙手通言 · 统一时基与硬件时戳（ts_align）
// 方案 v2.1 §4.2：单一 PL 100Hz 采样节拍（硬件分频，非软件定时器）
// 状态：W1 完整实现
// =============================================================================
`timescale 1ns/1ps

module ts_align #(
    parameter CLK_FREQ_HZ = 100_000_000,
    parameter TICK_HZ     = 100
)(
    input  wire        clk,
    input  wire        rst_n,
    output reg         tick,        // 100Hz，1 个 clk 宽脉冲
    output reg  [31:0] timestamp    // 自复位起的帧计数（即硬件时戳）
);

localparam DIV = CLK_FREQ_HZ / TICK_HZ;   // 1_000_000
localparam CW  = $clog2(DIV);

reg [CW-1:0] cnt;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        cnt <= {CW{1'b0}};
        tick <= 1'b0;
        timestamp <= 32'd0;
    end else begin
        tick <= 1'b0;
        if (cnt == DIV-1) begin
            cnt <= {CW{1'b0}};
            tick <= 1'b1;
            timestamp <= timestamp + 1'b1;
        end else begin
            cnt <= cnt + 1'b1;
        end
    end
end

endmodule
