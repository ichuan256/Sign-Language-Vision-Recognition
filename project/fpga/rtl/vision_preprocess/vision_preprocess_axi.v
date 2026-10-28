`timescale 1ns/1ps
// Independent, single-clock RGB565 preprocessing peripheral. Reset is a system
// reset: the interconnect and AXIS consumer must reset with this peripheral.
module vision_preprocess_axi (
    (* X_INTERFACE_INFO = "xilinx.com:signal:clock:1.0 clk CLK", X_INTERFACE_PARAMETER = "XIL_INTERFACENAME clk, ASSOCIATED_BUSIF s_axi_control:m_axi_read:m_axis, ASSOCIATED_RESET reset_n, FREQ_HZ 100000000" *)
    input wire clk,
    (* X_INTERFACE_INFO = "xilinx.com:signal:reset:1.0 reset_n RST", X_INTERFACE_PARAMETER = "XIL_INTERFACENAME reset_n, POLARITY ACTIVE_LOW" *)
    input wire reset_n,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 s_axi_control AWADDR", X_INTERFACE_PARAMETER = "XIL_INTERFACENAME s_axi_control, PROTOCOL AXI4LITE, DATA_WIDTH 32, ADDR_WIDTH 8, FREQ_HZ 100000000" *) input wire [7:0] s_axi_control_awaddr,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 s_axi_control AWVALID" *) input wire s_axi_control_awvalid,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 s_axi_control AWREADY" *) output wire s_axi_control_awready,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 s_axi_control WDATA" *) input wire [31:0] s_axi_control_wdata,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 s_axi_control WSTRB" *) input wire [3:0] s_axi_control_wstrb,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 s_axi_control WVALID" *) input wire s_axi_control_wvalid,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 s_axi_control WREADY" *) output wire s_axi_control_wready,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 s_axi_control BRESP" *) output reg [1:0] s_axi_control_bresp,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 s_axi_control BVALID" *) output reg s_axi_control_bvalid,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 s_axi_control BREADY" *) input wire s_axi_control_bready,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 s_axi_control ARADDR" *) input wire [7:0] s_axi_control_araddr,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 s_axi_control ARVALID" *) input wire s_axi_control_arvalid,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 s_axi_control ARREADY" *) output wire s_axi_control_arready,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 s_axi_control RDATA" *) output reg [31:0] s_axi_control_rdata,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 s_axi_control RRESP" *) output reg [1:0] s_axi_control_rresp,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 s_axi_control RVALID" *) output reg s_axi_control_rvalid,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 s_axi_control RREADY" *) input wire s_axi_control_rready,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 m_axi_read ARID", X_INTERFACE_PARAMETER = "XIL_INTERFACENAME m_axi_read, PROTOCOL AXI4, DATA_WIDTH 32, ADDR_WIDTH 32, ID_WIDTH 1, READ_WRITE_MODE READ_ONLY, NUM_READ_OUTSTANDING 1, MAX_BURST_LENGTH 1, SUPPORTS_NARROW_BURST 0, FREQ_HZ 100000000" *) output wire [0:0] m_axi_read_arid,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 m_axi_read ARADDR" *) output reg [31:0] m_axi_read_araddr,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 m_axi_read ARLEN" *) output wire [7:0] m_axi_read_arlen,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 m_axi_read ARSIZE" *) output wire [2:0] m_axi_read_arsize,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 m_axi_read ARBURST" *) output wire [1:0] m_axi_read_arburst,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 m_axi_read ARLOCK" *) output wire m_axi_read_arlock,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 m_axi_read ARCACHE" *) output wire [3:0] m_axi_read_arcache,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 m_axi_read ARPROT" *) output wire [2:0] m_axi_read_arprot,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 m_axi_read ARVALID" *) output wire m_axi_read_arvalid,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 m_axi_read ARREADY" *) input wire m_axi_read_arready,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 m_axi_read RID" *) input wire [0:0] m_axi_read_rid,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 m_axi_read RDATA" *) input wire [31:0] m_axi_read_rdata,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 m_axi_read RRESP" *) input wire [1:0] m_axi_read_rresp,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 m_axi_read RLAST" *) input wire m_axi_read_rlast,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 m_axi_read RVALID" *) input wire m_axi_read_rvalid,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 m_axi_read RREADY" *) output wire m_axi_read_rready,
    (* X_INTERFACE_INFO = "xilinx.com:interface:axis:1.0 m_axis TDATA", X_INTERFACE_PARAMETER = "XIL_INTERFACENAME m_axis, TDATA_NUM_BYTES 4, HAS_TKEEP 1, HAS_TLAST 1, TUSER_WIDTH 1, FREQ_HZ 100000000" *) output wire [31:0] m_axis_tdata,
    (* X_INTERFACE_INFO = "xilinx.com:interface:axis:1.0 m_axis TKEEP" *) output wire [3:0] m_axis_tkeep,
    (* X_INTERFACE_INFO = "xilinx.com:interface:axis:1.0 m_axis TVALID" *) output wire m_axis_tvalid,
    (* X_INTERFACE_INFO = "xilinx.com:interface:axis:1.0 m_axis TREADY" *) input wire m_axis_tready,
    (* X_INTERFACE_INFO = "xilinx.com:interface:axis:1.0 m_axis TUSER" *) output wire m_axis_tuser,
    (* X_INTERFACE_INFO = "xilinx.com:interface:axis:1.0 m_axis TLAST" *) output wire m_axis_tlast
);
    reg [31:0] shadow [0:11];
    reg [31:0] active [0:11];
    reg busy, done_sticky, error_sticky;
    reg [7:0] error_code;
    reg [31:0] byte_count, ar_count, cycle_count;
    reg start_core;
    wire core_done;
    wire [7:0] core_error;
    wire [23:0] pixel_data;
    wire pixel_valid, pixel_ready, pixel_user, pixel_last;
    wire req_valid, req_ready, rsp_ready;
    wire [31:0] req_addr;
    reg [31:0] rsp_data;
    reg rsp_error;
    localparam RD_IDLE=0, RD_AR=1, RD_WAIT=2, RD_DRAIN=3, RD_RESP=4;
    reg [2:0] read_state;
    wire rsp_valid = (read_state == RD_RESP);
    assign req_ready = (read_state == RD_IDLE);
    // This adapter deliberately uses one 32-bit incrementing beat per read.
    assign m_axi_read_arid=1'b0;
    assign m_axi_read_arlen=8'd0;
    assign m_axi_read_arsize=3'd2;
    assign m_axi_read_arburst=2'b01;
    assign m_axi_read_arlock=1'b0;
    assign m_axi_read_arcache=4'b0011;
    assign m_axi_read_arprot=3'b000;
    assign m_axi_read_arvalid=(read_state==RD_AR);
    assign m_axi_read_rready=(read_state==RD_WAIT || read_state==RD_DRAIN);
    vision_rgb565_affine sampler (
        .clk(clk), .reset_n(reset_n), .start(start_core), .busy(), .done(core_done), .error_code(core_error),
        .cfg_src_base(active[0]), .cfg_src_stride(active[1]), .cfg_src_width(active[2][15:0]), .cfg_src_height(active[3][15:0]),
        .cfg_dst_width(active[4][15:0]), .cfg_dst_height(active[5][15:0]),
        .cfg_a(active[6]), .cfg_b(active[7]), .cfg_c(active[8]), .cfg_d(active[9]), .cfg_e(active[10]), .cfg_f(active[11]),
        .rd_req_valid(req_valid), .rd_req_ready(req_ready), .rd_req_addr(req_addr),
        .rd_rsp_valid(rsp_valid), .rd_rsp_ready(rsp_ready), .rd_rsp_data(rsp_data), .rd_rsp_error(rsp_error),
        .m_axis_tdata(pixel_data), .m_axis_tvalid(pixel_valid), .m_axis_tready(pixel_ready), .m_axis_tuser(pixel_user), .m_axis_tlast(pixel_last)
    );
    rgb888_axis_pack32 packer (
        .clk(clk), .reset_n(reset_n), .s_axis_tdata(pixel_data), .s_axis_tvalid(pixel_valid), .s_axis_tready(pixel_ready), .s_axis_tuser(pixel_user), .s_axis_tlast(pixel_last),
        .m_axis_tdata(m_axis_tdata), .m_axis_tkeep(m_axis_tkeep), .m_axis_tvalid(m_axis_tvalid), .m_axis_tready(m_axis_tready), .m_axis_tuser(m_axis_tuser), .m_axis_tlast(m_axis_tlast)
    );
    // One request is retained through AR stall, R delay, malformed-burst drain,
    // and response backpressure. No new AR can escape before the last R beat.
    always @(posedge clk) begin
        if (!reset_n) begin
            read_state<=RD_IDLE; m_axi_read_araddr<=0; rsp_data<=0; rsp_error<=0;
        end else case (read_state)
            RD_IDLE: if (req_valid) begin m_axi_read_araddr<=req_addr; read_state<=RD_AR; end
            RD_AR: if (m_axi_read_arready) read_state<=RD_WAIT;
            RD_WAIT: if (m_axi_read_rvalid) begin
                rsp_data<=m_axi_read_rdata;
                rsp_error<=(m_axi_read_rresp!=0 || !m_axi_read_rlast || m_axi_read_rid!=0);
                if (m_axi_read_rlast) read_state<=RD_RESP;
                else read_state<=RD_DRAIN;
            end
            RD_DRAIN: if (m_axi_read_rvalid && m_axi_read_rlast) begin rsp_error<=1; read_state<=RD_RESP; end
            RD_RESP: if (rsp_ready) read_state<=RD_IDLE;
            default: read_state<=RD_IDLE;
        endcase
    end
    reg aw_full, w_full;
    reg [7:0] aw_addr;
    reg [31:0] w_data;
    reg [3:0] w_strb;
    assign s_axi_control_awready=!aw_full && !s_axi_control_bvalid;
    assign s_axi_control_wready=!w_full && !s_axi_control_bvalid;
    assign s_axi_control_arready=!s_axi_control_rvalid;
    integer i, j;
    reg [31:0] read_value;
    reg [1:0] read_resp;
    always @* begin
        read_value=0; read_resp=0;
        case (s_axi_control_araddr)
            8'h00: read_value=0;
            8'h04: read_value={28'd0,(read_state==RD_IDLE),error_sticky,done_sticky,busy};
            8'h08: read_value={24'd0,error_code};
            8'h0c: read_value=byte_count;
            8'h40: read_value=32'h00010000;
            8'h44: read_value=ar_count;
            8'h48: read_value=cycle_count;
            default: begin
                if (s_axi_control_araddr>=8'h10 && s_axi_control_araddr<=8'h3c && s_axi_control_araddr[1:0]==0)
                    read_value=shadow[(s_axi_control_araddr-8'h10)>>2];
                else read_resp=2'b10;
            end
        endcase
    end
    function [2:0] keep_count;
        input [3:0] keep;
        begin
            case (keep)
                4'b0000: keep_count=3'd0;
                4'b0001,4'b0010,4'b0100,4'b1000: keep_count=3'd1;
                4'b0011,4'b0101,4'b0110,4'b1001,4'b1010,4'b1100: keep_count=3'd2;
                4'b0111,4'b1011,4'b1101,4'b1110: keep_count=3'd3;
                default: keep_count=3'd4;
            endcase
        end
    endfunction
    wire [2:0] bytes_this_beat = keep_count(m_axis_tkeep);
    always @(posedge clk) begin
        if (!reset_n) begin
            busy<=0; done_sticky<=0; error_sticky<=0; error_code<=0;
            byte_count<=0; ar_count<=0; cycle_count<=0; start_core<=0;
            aw_full<=0; w_full<=0; aw_addr<=0; w_data<=0; w_strb<=0;
            s_axi_control_bvalid<=0; s_axi_control_bresp<=0;
            s_axi_control_rvalid<=0; s_axi_control_rdata<=0; s_axi_control_rresp<=0;
            for (i=0;i<12;i=i+1) begin shadow[i]<=0; active[i]<=0; end
        end else begin
            start_core<=0;
            if (busy && cycle_count!=32'hffffffff) cycle_count<=cycle_count+1;
            if (m_axi_read_arvalid && m_axi_read_arready) ar_count<=ar_count+1;
            if (m_axis_tvalid && m_axis_tready) byte_count<=byte_count+bytes_this_beat;
            if (busy && core_done) begin
                if (core_error!=0) begin error_code<=core_error; error_sticky<=1; end
                if (core_error>=1 && core_error<=3) begin busy<=0; done_sticky<=1; end
            end
            if (busy && m_axis_tvalid && m_axis_tready && m_axis_tlast) begin
                busy<=0; done_sticky<=1;
                if (core_error!=0) begin error_code<=core_error; error_sticky<=1; end
            end
            if (s_axi_control_bvalid && s_axi_control_bready) s_axi_control_bvalid<=0;
            if (s_axi_control_awvalid && s_axi_control_awready) begin aw_addr<=s_axi_control_awaddr; aw_full<=1; end
            if (s_axi_control_wvalid && s_axi_control_wready) begin w_data<=s_axi_control_wdata; w_strb<=s_axi_control_wstrb; w_full<=1; end
            if (aw_full && w_full && !s_axi_control_bvalid) begin
                aw_full<=0; w_full<=0; s_axi_control_bvalid<=1; s_axi_control_bresp<=0;
                if (aw_addr==0) begin
                    if (w_strb[0] && w_data[0] && busy) s_axi_control_bresp<=2'b10;
                    else begin
                        if (w_strb[0] && w_data[1]) begin done_sticky<=0; error_sticky<=0; error_code<=0; end
                        if (w_strb[0] && w_data[0]) begin
                            busy<=1; done_sticky<=0; error_sticky<=0; error_code<=0;
                            byte_count<=0; ar_count<=0; cycle_count<=0; start_core<=1;
                            // Retain complete register words, but reject dimension
                            // bits that cannot fit the core's 16-bit input ports.
                            if (shadow[2][31:16]!=0 || shadow[3][31:16]!=0 || shadow[4][31:16]!=0 || shadow[5][31:16]!=0) begin
                                start_core<=0; busy<=0; done_sticky<=1;
                                error_code<=1; error_sticky<=1; cycle_count<=1;
                            end
                            for (i=0;i<12;i=i+1) active[i]<=shadow[i];
                        end
                    end
                end else if (aw_addr>=8'h10 && aw_addr<=8'h3c && aw_addr[1:0]==0) begin
                    for (j=0;j<4;j=j+1) if (w_strb[j]) shadow[(aw_addr-8'h10)>>2][8*j+:8]<=w_data[8*j+:8];
                end else s_axi_control_bresp<=2'b10;
            end
            if (s_axi_control_rvalid && s_axi_control_rready) s_axi_control_rvalid<=0;
            if (s_axi_control_arvalid && s_axi_control_arready) begin
                s_axi_control_rvalid<=1; s_axi_control_rdata<=read_value; s_axi_control_rresp<=read_resp;
            end
        end
    end
endmodule
