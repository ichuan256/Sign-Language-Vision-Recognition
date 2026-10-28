`timescale 1ns/1ps
// Standalone snapshot peripheral. Only selected SCCB transport is instantiated.
// The proven dual startup controller sees two copies of that ONE transport;
// its duplicate error bits are remapped to the selected physical camera.
module ov5640_snapshot #(parameter integer CAMERA=1, SYS_CLK_HZ=100000000,
    FRAME_WIDTH=1280, FRAME_HEIGHT=720,
    PWDN_CYCLES=SYS_CLK_HZ/50, RESET_CYCLES=SYS_CLK_HZ/50,
    SCCB_HALF_CYCLES=SYS_CLK_HZ/200000, TIMEOUT_CYCLES=SYS_CLK_HZ/100)(
    (* X_INTERFACE_INFO="xilinx.com:signal:clock:1.0 sys_clk CLK",
       X_INTERFACE_PARAMETER="ASSOCIATED_BUSIF M_AXIS, ASSOCIATED_RESET sys_reset_n, FREQ_HZ 100000000" *) input wire sys_clk,
    (* X_INTERFACE_INFO="xilinx.com:signal:reset:1.0 sys_reset_n RST", X_INTERFACE_PARAMETER="POLARITY ACTIVE_LOW" *) input wire sys_reset_n,
    input wire [9:0] control, output reg [31:0] status,
    input wire ov1_pclk,ov1_vsync,ov1_href, input wire [7:0] ov1_data,
    input wire ov2_pclk,ov2_vsync,ov2_href, input wire [7:0] ov2_data,
    inout wire ov1_scl,ov1_sda,ov2_scl,ov2_sda,
    output wire ov1_reset_n,ov1_pwdn,ov2_reset_n,ov2_pwdn,
    (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 M_AXIS TDATA" *) output wire [31:0] m_axis_tdata,
    (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 M_AXIS TKEEP" *) output wire [3:0] m_axis_tkeep,
    (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 M_AXIS TVALID" *) output wire m_axis_tvalid,
    (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 M_AXIS TREADY" *) input wire m_axis_tready,
    (* X_INTERFACE_INFO="xilinx.com:interface:axis:1.0 M_AXIS TLAST" *) output wire m_axis_tlast
);
    // GPIO is synchronous to sys_clk. Keep software reset off asynchronous
    // reset pins: only the clean system reset may assert this register async.
    reg rst_n = 1'b0;
    always @(posedge sys_clk or negedge sys_reset_n)
        if (!sys_reset_n) rst_n <= 1'b0;
        else rst_n <= control[0];
    reg start_d;
    always @(posedge sys_clk or negedge rst_n) if(!rst_n) start_d<=0; else start_d<=control[1];
    wire init_busy,init_done,init_error; wire [3:0] error_code; wire [1:0] failed;
    wire [9:0] idx; wire valid,last; wire [15:0] addr,delay_ms; wire [7:0] val,mask;
    wire tx_start,tx_read,transport_reset_n,tx_busy,tx_done;
    wire [15:0] tx_addr; wire [7:0] tx_value,tx_mask,read_data;
    wire cam_reset_n,cam_pwdn;
    ov5640_startup_table u_table(.index(idx),.valid(valid),.reg_addr(addr),.reg_value(val),
        .write_mask(mask),.post_delay_ms(delay_ms),.last(last));
    ov5640_stereo_startup_controller #(.SYS_CLK_HZ(SYS_CLK_HZ),
        .PWDN_SETTLE_CYCLES(PWDN_CYCLES),.RESET_RELEASE_WAIT_CYCLES(RESET_CYCLES),
        .SCCB_TIMEOUT_CYCLES(TIMEOUT_CYCLES)) u_init(
        .clk(sys_clk),.rst_n(rst_n),.start(control[1] && !start_d),
        .ov1_reset_n(cam_reset_n),.ov1_pwdn(cam_pwdn),.ov2_reset_n(),.ov2_pwdn(),
        .busy(init_busy),.init_done(init_done),.init_error(init_error),.error_code(error_code),.failed_cameras(failed),
        .table_index(idx),.table_valid(valid),.table_last(last),.table_addr(addr),.table_value(val),
        .table_mask(mask),.table_delay_ms(delay_ms),.tx_start(tx_start),.tx_read_only(tx_read),
        .tx_addr(tx_addr),.tx_value(tx_value),.tx_mask(tx_mask),
        .tx_busy({2{tx_busy}}),.tx_done({2{tx_done}}),
        .read_data_ov1(read_data),.read_data_ov2(read_data),.transport_rst_n(transport_reset_n));
    generate if(CAMERA==1) begin:g_left
        assign ov1_reset_n=cam_reset_n; assign ov1_pwdn=cam_pwdn;
        assign ov2_reset_n=0; assign ov2_pwdn=1; assign ov2_scl=1'bz; assign ov2_sda=1'bz;
        ov5640_sccb_register_access #(.HALF_PERIOD_CYCLES(SCCB_HALF_CYCLES)) u_sccb(
            .clk(sys_clk),.rst_n(transport_reset_n),.start(tx_start),.read_only(tx_read),
            .reg_addr(tx_addr),.reg_value(tx_value),.write_mask(tx_mask),.busy(tx_busy),.done(tx_done),
            .read_data(read_data),.sccb_scl(ov1_scl),.sccb_sda(ov1_sda));
    end else begin:g_right
        assign ov2_reset_n=cam_reset_n; assign ov2_pwdn=cam_pwdn;
        assign ov1_reset_n=0; assign ov1_pwdn=1; assign ov1_scl=1'bz; assign ov1_sda=1'bz;
        ov5640_sccb_register_access #(.HALF_PERIOD_CYCLES(SCCB_HALF_CYCLES)) u_sccb(
            .clk(sys_clk),.rst_n(transport_reset_n),.start(tx_start),.read_only(tx_read),
            .reg_addr(tx_addr),.reg_value(tx_value),.write_mask(tx_mask),.busy(tx_busy),.done(tx_done),
            .read_data(read_data),.sccb_scl(ov2_scl),.sccb_sda(ov2_sda));
    end endgenerate
    wire pclk=(CAMERA==1)?ov1_pclk:ov2_pclk;
    (* ASYNC_REG="TRUE", SHREG_EXTRACT="NO" *) reg [1:0] p_reset;
    // Bits 8/9 invert physical VSYNC/HREF; configure only while capture is idle.
    (* ASYNC_REG="TRUE", SHREG_EXTRACT="NO" *) reg [1:0] vs_inv_sync, href_inv_sync;
    always @(posedge pclk or negedge p_reset[1]) begin
        if (!p_reset[1]) begin vs_inv_sync<=0; href_inv_sync<=0; end
        else begin vs_inv_sync<={vs_inv_sync[0],control[8]}; href_inv_sync<={href_inv_sync[0],control[9]}; end
    end
    wire vsync=((CAMERA==1)?ov1_vsync:ov2_vsync) ^ vs_inv_sync[1];
    wire href=((CAMERA==1)?ov1_href:ov2_href) ^ href_inv_sync[1];
    wire [7:0] data=(CAMERA==1)?ov1_data:ov2_data;
    reg capture_reset_n;
    always @(posedge sys_clk or negedge rst_n) if(!rst_n) capture_reset_n<=0; else capture_reset_n<=init_done && !init_error;
    always @(posedge pclk or negedge capture_reset_n) if(!capture_reset_n) p_reset<=0; else p_reset<={p_reset[0],1'b1};
    wire pv,sof,eol,fd,fs; wire [15:0] px;
    wire packet_busy,packet_done,packet_error,packet_overflow;
    ov5640_dvp_capture #(.FRAME_WIDTH(FRAME_WIDTH),.FRAME_HEIGHT(FRAME_HEIGHT)) u_capture(
        .rst_n(p_reset[1]),.cam_pclk(pclk),.cam_vsync(vsync),.cam_href(href),.cam_data(data),
        .pixel_valid(pv),.pixel_sof(sof),.pixel_eol(eol),.pixel_data(px),
        .frame_start(fs),.frame_done(fd),.frame_error(),.frame_id());
    wire fifo_full,empty,wr_busy,rd_busy,wr_en; wire [33:0] din,dout;
    // Register the BRAM boundary without asynchronous resets. The camera may
    // stop PCLK during reset; p_reset holds the request until it restarts.
    // XPM requires rst synchronous to wr_clk, including assertion.
    reg fifo_reset = 1'b1;
    reg fifo_write = 1'b0;
    reg [33:0] fifo_data = 34'b0;
    reg fifo_read_allowed = 1'b0;
    reg fifo_read_reset_seen = 1'b0;
    always @(posedge pclk) begin
        fifo_reset <= !p_reset[1];
        if (!p_reset[1] || fifo_reset || wr_busy) fifo_write <= 1'b0;
        else fifo_write <= wr_en;
        fifo_data <= din;
    end
    always @(posedge sys_clk) begin
        if (!capture_reset_n) begin
            fifo_read_reset_seen <= 1'b0;
            fifo_read_allowed <= 1'b0;
        end else begin
            if (rd_busy) fifo_read_reset_seen <= 1'b1;
            fifo_read_allowed <= fifo_read_reset_seen && !rd_busy;
        end
    end
    ov5640_snapshot_packet #(.PIXELS(FRAME_WIDTH*FRAME_HEIGHT)) u_packet(
        .pclk(pclk),.rst_n(p_reset[1]),.arm_toggle(control[2]),.frame_start(fs),
        .pixel_valid(pv),.pixel_sof(sof),.pixel_data(px),.frame_done(fd),
        .fifo_full(fifo_full || fifo_write),.fifo_busy(wr_busy || fifo_reset),.fifo_wr_en(wr_en),.fifo_din(din),
        .busy(packet_busy),.done(packet_done),.error(packet_error),.overflow(packet_overflow));
    xpm_fifo_async #(.FIFO_MEMORY_TYPE("block"),.FIFO_WRITE_DEPTH(4096),
        .WRITE_DATA_WIDTH(34),.READ_DATA_WIDTH(34),.READ_MODE("fwft"),.FIFO_READ_LATENCY(0),
        .CDC_SYNC_STAGES(2),.DOUT_RESET_VALUE("0"),.ECC_MODE("no_ecc"),
        .PROG_EMPTY_THRESH(10),.PROG_FULL_THRESH(4086),.RD_DATA_COUNT_WIDTH(13),
        .WR_DATA_COUNT_WIDTH(13),.RELATED_CLOCKS(0),.SIM_ASSERT_CHK(1),.USE_ADV_FEATURES("0000")) u_fifo(
        .rst(fifo_reset),.wr_clk(pclk),.wr_en(fifo_write),.din(fifo_data),.full(fifo_full),.wr_rst_busy(wr_busy),
        .rd_clk(sys_clk),.rd_en(m_axis_tvalid && m_axis_tready),.dout(dout),.empty(empty),.rd_rst_busy(rd_busy),
        .sleep(1'b0),.injectsbiterr(1'b0),.injectdbiterr(1'b0),
        .almost_empty(),.almost_full(),.data_valid(),.dbiterr(),.overflow(),.prog_empty(),.prog_full(),
        .rd_data_count(),.sbiterr(),.underflow(),.wr_ack(),.wr_data_count());
    assign m_axis_tdata=dout[31:0]; assign m_axis_tlast=dout[32];
    assign m_axis_tkeep=dout[33] ? 4'b0011 : 4'hf;
    assign m_axis_tvalid=!empty && !rd_busy && fifo_read_allowed;
    reg [20:0] heartbeat;
    always @(posedge pclk or negedge p_reset[1]) if(!p_reset[1]) heartbeat<=0; else heartbeat<=heartbeat+1'b1;
    (* ASYNC_REG="TRUE", SHREG_EXTRACT="NO" *) reg [4:0] flags_meta,flags_sync;
    always @(posedge sys_clk or negedge rst_n) begin
        if(!rst_n) begin flags_meta<=0; flags_sync<=0; end
        else begin flags_meta<={heartbeat[20],packet_overflow,packet_error,packet_done,packet_busy}; flags_sync<=flags_meta; end
    end
    reg arm_d,pending,accepted,done_latched,error_latched,overflow_latched;
    always @(posedge sys_clk or negedge rst_n) begin
        if(!rst_n) begin arm_d<=0;pending<=0;accepted<=0;done_latched<=0;error_latched<=0;overflow_latched<=0; end
        else begin
            arm_d<=control[2];
            if(control[2]!=arm_d) begin pending<=1;accepted<=0;done_latched<=0;error_latched<=0;overflow_latched<=0; end
            else if(pending) begin
                if(flags_sync[0]) accepted<=1;
                if(flags_sync[2]) begin pending<=0;error_latched<=1;overflow_latched<=flags_sync[3]; end
                else if(accepted && flags_sync[1]) begin pending<=0;done_latched<=1; end
            end
        end
    end
    wire [31:0] normal_status={15'b0,flags_sync[4],2'b0,
        (init_error?((CAMERA==1)?2'b01:2'b10):2'b00),error_code,1'b0,overflow_latched,error_latched,
        done_latched,pending,init_error,init_done,init_busy};
    // Page 0 is the capture status. Other pages are reserved.
    always @* status = (control[5:3] == 0) ? normal_status : 32'b0;
endmodule
