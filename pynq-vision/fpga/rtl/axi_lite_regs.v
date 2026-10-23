// =============================================================================
// 妙手通言 · AXI4-Lite 只读寄存器组（点亮用，16×32bit）
// 地址映射（字地址，PS 侧偏移 = 字地址×4）：
//   0  frame_cnt      1  who_am_i(bit31=who_ok)
//   2  imu_ax(s16)    3  imu_ay      4  imu_az      5  imu_temp
//   6  imu_gx         7  imu_gy      8  imu_gz
//   9  adc_ch0        10 status(bit0=busy)   11-15 预留(读0)
// =============================================================================
`timescale 1ns/1ps

module axi_lite_regs #(
    parameter C_S_AXI_DATA_WIDTH = 32,
    parameter C_S_AXI_ADDR_WIDTH = 6      // 16 字 = 64B
)(
    input  wire        s_axi_aclk,
    input  wire        s_axi_aresetn,
    input  wire [C_S_AXI_ADDR_WIDTH-1:0]   s_axi_araddr,
    input  wire        s_axi_arvalid,
    output reg         s_axi_arready,
    output reg  [C_S_AXI_DATA_WIDTH-1:0]   s_axi_rdata,
    output reg         s_axi_rvalid,
    input  wire        s_axi_rready,
    // 写通道：吸收但忽略（只读寄存器）
    input  wire [C_S_AXI_ADDR_WIDTH-1:0]   s_axi_awaddr,
    input  wire        s_axi_awvalid,
    output reg         s_axi_awready,
    input  wire [C_S_AXI_DATA_WIDTH-1:0]   s_axi_wdata,
    input  wire        s_axi_wvalid,
    output reg         s_axi_wready,
    output reg         s_axi_bvalid,
    input  wire        s_axi_bready,

    // 来自 bringup_seq
    input  wire [31:0] frame_cnt,
    input  wire [7:0]  who_am_i,
    input  wire        who_ok,
    input  wire [15:0] imu_ax, imu_ay, imu_az, imu_temp,
    input  wire [15:0] imu_gx, imu_gy, imu_gz,
    input  wire [15:0] adc_ch0,
    input  wire        busy
);

wire [3:0] addr = s_axi_araddr[C_S_AXI_ADDR_WIDTH-1:2];

// ---- 读通道 ----
always @(posedge s_axi_aclk or negedge s_axi_aresetn) begin
    if (!s_axi_aresetn) begin
        s_axi_arready <= 1'b0; s_axi_rvalid <= 1'b0; s_axi_rdata <= 32'd0;
    end else begin
        if (s_axi_arvalid && !s_axi_arready) begin
            s_axi_arready <= 1'b1;
            s_axi_rvalid  <= 1'b1;
            case (addr)
                4'd0:  s_axi_rdata <= frame_cnt;
                4'd1:  s_axi_rdata <= {who_ok, 23'd0, who_am_i};
                4'd2:  s_axi_rdata <= {{16{imu_ax[15]}},   imu_ax};
                4'd3:  s_axi_rdata <= {{16{imu_ay[15]}},   imu_ay};
                4'd4:  s_axi_rdata <= {{16{imu_az[15]}},   imu_az};
                4'd5:  s_axi_rdata <= {{16{imu_temp[15]}}, imu_temp};
                4'd6:  s_axi_rdata <= {{16{imu_gx[15]}},   imu_gx};
                4'd7:  s_axi_rdata <= {{16{imu_gy[15]}},   imu_gy};
                4'd8:  s_axi_rdata <= {{16{imu_gz[15]}},   imu_gz};
                4'd9:  s_axi_rdata <= {16'd0, adc_ch0};
                4'd10: s_axi_rdata <= {31'd0, busy};
                default: s_axi_rdata <= 32'hDEAD_0000 | addr;
            endcase
        end else begin
            s_axi_arready <= 1'b0;
            if (s_axi_rvalid && s_axi_rready) s_axi_rvalid <= 1'b0;
        end
    end
end

// ---- 写通道：直接吞掉 ----
always @(posedge s_axi_aclk or negedge s_axi_aresetn) begin
    if (!s_axi_aresetn) begin
        s_axi_awready <= 1'b0; s_axi_wready <= 1'b0; s_axi_bvalid <= 1'b0;
    end else begin
        s_axi_awready <= s_axi_awvalid && !s_axi_bvalid;
        s_axi_wready  <= s_axi_wvalid  && !s_axi_bvalid;
        if (s_axi_awvalid && s_axi_wvalid && !s_axi_bvalid)
            s_axi_bvalid <= 1'b1;
        else if (s_axi_bvalid && s_axi_bready)
            s_axi_bvalid <= 1'b0;
    end
end

endmodule
