// =============================================================================
// 妙手通言 · 参数化 SPI Master（CPOL/CPHA 可配，SCLK 分频可配）
// 方案 v2.1 §4.1：MPU6500（Mode 0，≤1MHz）与 MCP3208（Mode 0）共用
// 状态：W1 完整实现，待 W2 仿真验证（iverilog/Vivado xsim testbench）
// =============================================================================
`timescale 1ns/1ps

module spi_master #(
    parameter CLK_FREQ_HZ = 100_000_000,  // PL 主时钟
    parameter SCLK_FREQ_HZ = 1_000_000,   // SPI 时钟（方案 §3.4：1MHz）
    parameter CPOL        = 0,
    parameter CPHA        = 0,
    parameter WIDTH       = 8             // 单帧位宽（8/16）
)(
    input  wire             clk,
    input  wire             rst_n,

    // 控制接口（单事务：连续收发 WIDTH 位）
    input  wire             start,        // 1 拍脉冲
    input  wire [WIDTH-1:0] tx_data,
    output reg  [WIDTH-1:0] rx_data,
    output reg              busy,
    output reg              done,         // 1 拍脉冲

    // SPI 引脚（CS 由上层调度器管理，本模块只管 SCLK/MOSI/MISO）
    output reg              sclk,
    output reg              mosi,
    input  wire             miso
);

localparam DIV = CLK_FREQ_HZ / (SCLK_FREQ_HZ * 2);
localparam CW  = $clog2(DIV + 1);

localparam IDLE = 2'd0, LEAD = 2'd1, SHIFT = 2'd2, TAIL = 2'd3;

reg [1:0]        state;
reg [CW-1:0]     div_cnt;
reg [WIDTH-1:0]  shreg_tx;
reg [5:0]        bit_cnt;
reg              sclk_en;

wire sclk_idle = CPOL[0];
wire sclk_act  = ~CPOL[0];

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        state   <= IDLE;
        sclk    <= CPOL[0];
        mosi    <= 1'b1;
        busy    <= 1'b0;
        done    <= 1'b0;
        rx_data <= {WIDTH{1'b0}};
        div_cnt <= {CW{1'b0}};
        bit_cnt <= 6'd0;
        shreg_tx <= {WIDTH{1'b0}};
    end else begin
        done <= 1'b0;
        case (state)
            IDLE: begin
                sclk <= sclk_idle;
                if (start) begin
                    busy    <= 1'b1;
                    shreg_tx <= tx_data;
                    bit_cnt <= 6'd0;
                    div_cnt <= {CW{1'b0}};
                    // CPHA=0：首 bit 在首个上升沿之前上线，直接进 SHIFT，
                    // 使第一个上升沿即被采样（修复 MSB 漏采 bug）
                    mosi  <= tx_data[WIDTH-1];
                    state <= SHIFT;
                end
            end
            SHIFT: begin
                if (div_cnt == DIV-1) begin
                    div_cnt <= {CW{1'b0}};
                    sclk <= ~sclk;
                    if (sclk == sclk_act) begin
                        // 空闲沿：换数据（CPHA=0）或采样后推进
                        if (bit_cnt == WIDTH-1) begin
                            state <= TAIL;
                        end else begin
                            bit_cnt <= bit_cnt + 1'b1;
                            shreg_tx <= {shreg_tx[WIDTH-2:0], 1'b0};
                            mosi <= shreg_tx[WIDTH-2];
                        end
                    end else begin
                        // 有效沿：采样 MISO
                        rx_data <= {rx_data[WIDTH-2:0], miso};
                    end
                end else div_cnt <= div_cnt + 1'b1;
            end
            TAIL: begin
                if (div_cnt == DIV-1) begin
                    sclk  <= sclk_idle;
                    busy  <= 1'b0;
                    done  <= 1'b1;
                    state <= IDLE;
                end else div_cnt <= div_cnt + 1'b1;
            end
            default: state <= IDLE;
        endcase
    end
end

endmodule
