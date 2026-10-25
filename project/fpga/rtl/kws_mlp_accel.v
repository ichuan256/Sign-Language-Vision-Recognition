// Hand-written KWS MLP accelerator (no HLS).
// The PS computes MFCC + normalization and writes 26 signed Q4.12 features.
// The PL evaluates a 26->64->3 ReLU MLP with 64 parallel hidden MAC lanes
// and three parallel output MAC lanes. Weights are generated from kws_model.npz
// into kws_mlp_weights.vh by algo/kws/kws_rtl_export.py.
`timescale 1ns/1ps

module kws_mlp_accel #(
    parameter C_S_AXI_ADDR_WIDTH = 8
) (
    (* X_INTERFACE_INFO = "xilinx.com:signal:clock:1.0 s_axi_aclk CLK",
       X_INTERFACE_PARAMETER = "XIL_INTERFACENAME s_axi_aclk, ASSOCIATED_BUSIF S_AXI, ASSOCIATED_RESET s_axi_aresetn, FREQ_HZ 100000000, FREQ_TOLERANCE_HZ 0" *)
    input wire s_axi_aclk,
    (* X_INTERFACE_INFO = "xilinx.com:signal:reset:1.0 s_axi_aresetn RST",
       X_INTERFACE_PARAMETER = "XIL_INTERFACENAME s_axi_aresetn, POLARITY ACTIVE_LOW" *)
    input wire s_axi_aresetn,

    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI AWADDR",
       X_INTERFACE_PARAMETER = "XIL_INTERFACENAME S_AXI, PROTOCOL AXI4LITE, DATA_WIDTH 32, ADDR_WIDTH 8, FREQ_HZ 100000000" *)
    input wire [C_S_AXI_ADDR_WIDTH-1:0] s_axi_awaddr,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI AWVALID" *) input wire s_axi_awvalid,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI AWREADY" *) output wire s_axi_awready,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI WDATA" *) input wire [31:0] s_axi_wdata,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI WSTRB" *) input wire [3:0] s_axi_wstrb,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI WVALID" *) input wire s_axi_wvalid,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI WREADY" *) output wire s_axi_wready,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI BRESP" *) output reg [1:0] s_axi_bresp,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI BVALID" *) output reg s_axi_bvalid,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI BREADY" *) input wire s_axi_bready,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI ARADDR" *) input wire [C_S_AXI_ADDR_WIDTH-1:0] s_axi_araddr,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI ARVALID" *) input wire s_axi_arvalid,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI ARREADY" *) output wire s_axi_arready,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI RDATA" *) output reg [31:0] s_axi_rdata,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI RRESP" *) output reg [1:0] s_axi_rresp,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI RVALID" *) output reg s_axi_rvalid,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI RREADY" *) input wire s_axi_rready
);

localparam [7:0] REG_CONTROL = 8'h00;
localparam [7:0] REG_MAGIC   = 8'h04;
localparam [7:0] REG_CYCLES  = 8'h08;
localparam [7:0] REG_VALID   = 8'h0c;
localparam [7:0] REG_FEATURE = 8'h10;
localparam [7:0] REG_SCORE0  = 8'h80;
localparam [7:0] REG_CLASS   = 8'h8c;
localparam [25:0] ALL_FEATURES_VALID = 26'h3ffffff;

localparam [2:0] ST_IDLE = 3'd0, ST_HIDDEN = 3'd1,
                 ST_OUTPUT = 3'd2, ST_DONE = 3'd3,
                 ST_RELU = 3'd4, ST_SCORE = 3'd5, ST_CLASS = 3'd6;

reg [2:0] state;
reg [1:0] mac_phase;
reg done;
reg input_error;
reg [31:0] cycle_count;
reg [5:0] feature_index;
reg [6:0] hidden_index;
reg [25:0] feature_valid;
reg signed [15:0] feature_reg [0:25];
reg signed [15:0] hidden_reg [0:63];
reg signed [47:0] accum1 [0:63];
reg signed [47:0] accum2 [0:2];
reg signed [31:0] scores [0:2];
reg [1:0] class_reg;
reg signed [15:0] w1_rom [0:1663];
reg signed [15:0] w2_rom [0:191];
reg signed [31:0] b1_rom [0:63];
reg signed [31:0] b2_rom [0:2];

reg aw_pending, w_pending;
reg [C_S_AXI_ADDR_WIDTH-1:0] awaddr_hold;
reg [31:0] wdata_hold;
reg [3:0] wstrb_hold;
wire wr_addr_valid = aw_pending || (s_axi_awvalid && s_axi_awready);
wire wr_data_valid = w_pending || (s_axi_wvalid && s_axi_wready);
wire [C_S_AXI_ADDR_WIDTH-1:0] wr_addr = aw_pending ? awaddr_hold : s_axi_awaddr;
wire [31:0] wr_data = w_pending ? wdata_hold : s_axi_wdata;
wire [3:0] wr_strb = w_pending ? wstrb_hold : s_axi_wstrb;

assign s_axi_awready = !aw_pending && !s_axi_bvalid;
assign s_axi_wready = !w_pending && !s_axi_bvalid;
assign s_axi_arready = !s_axi_rvalid;

wire [7:0] wr_addr_low = wr_addr[7:0];
wire [7:0] rd_addr_low = s_axi_araddr[7:0];
wire [5:0] feature_write_index = (wr_addr_low - REG_FEATURE) >> 2;
wire feature_write = (wr_addr_low >= REG_FEATURE && wr_addr_low <= 8'h74 &&
                      wr_addr_low[1:0] == 2'b00);
wire control_write = (wr_addr_low == REG_CONTROL);
wire start_write = control_write && wr_data[0] && wr_strb[0];
wire core_busy = (state != ST_IDLE) && (state != ST_DONE);
wire write_known = control_write || feature_write;
wire write_reject = !write_known || (wr_strb != 4'hf) ||
                    (feature_write && core_busy) ||
                    (start_write && (core_busy || feature_valid != ALL_FEATURES_VALID));
wire write_fire = wr_addr_valid && wr_data_valid && !s_axi_bvalid;

integer i;

reg signed [15:0] operand1;
reg signed [15:0] operand2;
reg signed [15:0] weight1 [0:63];
reg signed [15:0] weight2 [0:2];
reg signed [31:0] product1 [0:63];
reg signed [31:0] product2 [0:2];
genvar lane;
generate
    for (lane = 0; lane < 64; lane = lane + 1) begin: hidden_lane
        always @(posedge s_axi_aclk) begin
            if (state == ST_HIDDEN && mac_phase == 0)
                weight1[lane] <= w1_rom[lane * 26 + feature_index];
            if (state == ST_HIDDEN && mac_phase == 1)
                product1[lane] <= operand1 * weight1[lane];
        end
    end
    for (lane = 0; lane < 3; lane = lane + 1) begin: output_lane
        always @(posedge s_axi_aclk) begin
            if (state == ST_OUTPUT && mac_phase == 0)
                weight2[lane] <= w2_rom[lane * 64 + hidden_index];
            if (state == ST_OUTPUT && mac_phase == 1)
                product2[lane] <= operand2 * weight2[lane];
        end
    end
endgenerate

`include "kws_mlp_weights.vh"

function signed [15:0] relu_q12;
    input signed [47:0] value;
    reg signed [47:0] shifted;
    begin
        shifted = value >>> 14;
        if (shifted < 0) relu_q12 = 16'sd0;
        else if (shifted > 32767) relu_q12 = 16'sh7fff;
        else relu_q12 = shifted[15:0];
    end
endfunction

// AXI4-Lite writes are buffered independently so AW and W may arrive in either
// order. A transaction is acknowledged only after both handshakes complete.
always @(posedge s_axi_aclk) begin
    if (!s_axi_aresetn) begin
        aw_pending <= 1'b0;
        w_pending <= 1'b0;
        awaddr_hold <= {C_S_AXI_ADDR_WIDTH{1'b0}};
        wdata_hold <= 32'd0;
        wstrb_hold <= 4'd0;
        s_axi_bvalid <= 1'b0;
        s_axi_bresp <= 2'b00;
    end else begin
        if (s_axi_awvalid && s_axi_awready) begin
            aw_pending <= 1'b1;
            awaddr_hold <= s_axi_awaddr;
        end
        if (s_axi_wvalid && s_axi_wready) begin
            w_pending <= 1'b1;
            wdata_hold <= s_axi_wdata;
            wstrb_hold <= s_axi_wstrb;
        end

        if (wr_addr_valid && wr_data_valid && !s_axi_bvalid) begin
            aw_pending <= 1'b0;
            w_pending <= 1'b0;
            s_axi_bvalid <= 1'b1;
            s_axi_bresp <= write_reject ? 2'b10 : 2'b00;
        end else if (s_axi_bvalid && s_axi_bready) begin
            s_axi_bvalid <= 1'b0;
        end
    end
end

// AXI4-Lite reads use one registered response and remain stable under backpressure.
always @(posedge s_axi_aclk) begin
    if (!s_axi_aresetn) begin
        s_axi_rvalid <= 1'b0;
        s_axi_rdata <= 32'd0;
        s_axi_rresp <= 2'b00;
    end else begin
        if (s_axi_arvalid && s_axi_arready) begin
            s_axi_rvalid <= 1'b1;
            s_axi_rresp <= 2'b00;
            case (rd_addr_low)
                REG_CONTROL: s_axi_rdata <= {28'd0, input_error,
                                             (state == ST_IDLE || state == ST_DONE), done, 1'b0};
                REG_MAGIC:   s_axi_rdata <= 32'h4b575301;
                REG_CYCLES:  s_axi_rdata <= cycle_count;
                REG_VALID:   s_axi_rdata <= {6'd0, feature_valid};
                REG_SCORE0:  s_axi_rdata <= scores[0];
                8'h84:       s_axi_rdata <= scores[1];
                8'h88:       s_axi_rdata <= scores[2];
                REG_CLASS:  s_axi_rdata <= {30'd0, class_reg};
                default: begin
                    if (rd_addr_low >= REG_FEATURE && rd_addr_low <= 8'h74 && rd_addr_low[1:0] == 2'b00)
                        s_axi_rdata <= {{16{feature_reg[(rd_addr_low - REG_FEATURE) >> 2][15]}},
                                        feature_reg[(rd_addr_low - REG_FEATURE) >> 2]};
                    else begin
                        s_axi_rdata <= 32'd0;
                        s_axi_rresp <= 2'b10;
                    end
                end
            endcase
        end else if (s_axi_rvalid && s_axi_rready) begin
            s_axi_rvalid <= 1'b0;
        end
    end
end

// Inference datapath. Each hidden neuron has a dedicated multiply/accumulate
// lane; the three output neurons run in parallel in the second phase.
// Operand selection, multiplication and accumulation occupy separate clocks.
// ReLU, score truncation and argmax also have their own registered boundaries.
always @(posedge s_axi_aclk) begin
    if (!s_axi_aresetn) begin
        state <= ST_IDLE;
        done <= 1'b0;
        input_error <= 1'b0;
        cycle_count <= 0;
        feature_index <= 0;
        hidden_index <= 0;
        mac_phase <= 0;
        feature_valid <= 26'd0;
        class_reg <= 0;
        for (i = 0; i < 26; i = i + 1) feature_reg[i] <= 0;
        for (i = 0; i < 64; i = i + 1) begin
            hidden_reg[i] <= 0;
            accum1[i] <= 0;
        end
        for (i = 0; i < 3; i = i + 1) begin
            accum2[i] <= 0;
            scores[i] <= 0;
        end
    end else begin
        // Register writes are committed here, together with the datapath state,
        // so feature/status registers have a single sequential driver.
        if (write_fire) begin
            if (start_write && write_reject)
                input_error <= 1'b1;
            if (!write_reject && feature_write) begin
                feature_reg[feature_write_index] <= $signed(wr_data[15:0]);
                feature_valid[feature_write_index] <= 1'b1;
            end
            if (!write_reject && control_write) begin
                if (wr_data[3]) input_error <= 1'b0;
                if (wr_data[1] && !start_write) done <= 1'b0;
                if (start_write) begin
                    state <= ST_HIDDEN;
                    feature_index <= 0;
                    mac_phase <= 0;
                    cycle_count <= 0;
                    done <= 1'b0;
                    input_error <= 1'b0;
                    feature_valid <= 26'd0;
                    for (i = 0; i < 64; i = i + 1)
                        accum1[i] <= $signed({{16{b1_rom[i][31]}}, b1_rom[i]}) <<< 12;
                end
            end
        end
        if (core_busy) cycle_count <= cycle_count + 1'b1;
        case (state)
            ST_IDLE: begin
                // Wait for a complete feature vector and an accepted start.
            end
            ST_HIDDEN: begin
                if (mac_phase == 0) operand1 <= feature_reg[feature_index];
                if (mac_phase == 2) begin
                    for (i = 0; i < 64; i = i + 1)
                        accum1[i] <= accum1[i] + $signed({{16{product1[i][31]}}, product1[i]});
                    mac_phase <= 0;
                    if (feature_index == 25) state <= ST_RELU;
                    else feature_index <= feature_index + 1'b1;
                end else mac_phase <= mac_phase + 1'b1;
            end
            ST_RELU: begin
                for (i = 0; i < 64; i = i + 1) hidden_reg[i] <= relu_q12(accum1[i]);
                for (i = 0; i < 3; i = i + 1)
                    accum2[i] <= $signed({{16{b2_rom[i][31]}}, b2_rom[i]}) <<< 12;
                hidden_index <= 0;
                state <= ST_OUTPUT;
            end
            ST_OUTPUT: begin
                if (mac_phase == 0) operand2 <= hidden_reg[hidden_index];
                if (mac_phase == 2) begin
                    for (i = 0; i < 3; i = i + 1)
                        accum2[i] <= accum2[i] + $signed({{16{product2[i][31]}}, product2[i]});
                    mac_phase <= 0;
                    if (hidden_index == 63) state <= ST_SCORE;
                    else hidden_index <= hidden_index + 1'b1;
                end else mac_phase <= mac_phase + 1'b1;
            end
            ST_SCORE: begin
                for (i = 0; i < 3; i = i + 1) scores[i] <= accum2[i] >>> 12;
                state <= ST_CLASS;
            end
            ST_CLASS: begin
                if (scores[1] > scores[0] && scores[1] >= scores[2]) class_reg <= 1;
                else if (scores[2] > scores[0] && scores[2] > scores[1]) class_reg <= 2;
                else class_reg <= 0;
                done <= 1'b1;
                state <= ST_DONE;
            end
            ST_DONE: begin
                // Results remain available until the next accepted start.
            end
            default: begin
                state <= ST_IDLE;
            end
        endcase
    end
end

endmodule
