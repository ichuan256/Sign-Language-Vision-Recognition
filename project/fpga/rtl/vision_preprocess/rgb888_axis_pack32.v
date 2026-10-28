`timescale 1ns/1ps
// Compact R,G,B byte packing for frame packets; no valid padding bytes.
module rgb888_axis_pack32 (
    input wire clk, input wire reset_n,
    input wire [23:0] s_axis_tdata, input wire s_axis_tvalid,
    output wire s_axis_tready, input wire s_axis_tuser, input wire s_axis_tlast,
    output wire [31:0] m_axis_tdata, output wire [3:0] m_axis_tkeep,
    output wire m_axis_tvalid, input wire m_axis_tready,
    output wire m_axis_tuser, output wire m_axis_tlast
);
    reg [63:0] bytes;
    reg [3:0] count;
    reg frame_end, first_pending;
    reg [63:0] next_bytes;
    reg [3:0] next_count;
    wire pop = m_axis_tvalid && m_axis_tready;
    wire push = s_axis_tvalid && s_axis_tready;
    assign s_axis_tready = !frame_end && count<=5;
    assign m_axis_tvalid = count>=4 || (frame_end && count!=0);
    assign m_axis_tdata = bytes[31:0];
    assign m_axis_tkeep = count>=4 ? 4'b1111 : (4'b0001 << count)-1'b1;
    assign m_axis_tlast = frame_end && count<=4;
    assign m_axis_tuser = first_pending;
    always @* begin
        next_bytes=bytes;
        next_count=count;
        if (pop) begin
            next_bytes=bytes >> 32;
            next_count=count>=4 ? count-4 : 0;
        end
        if (push) begin
            next_bytes=next_bytes | ({40'd0,s_axis_tdata} << (next_count*8));
            next_count=next_count+3;
        end
    end
    always @(posedge clk) begin
        if (!reset_n) begin
            bytes<=0; count<=0; frame_end<=0; first_pending<=0;
        end else begin
            bytes<=next_bytes; count<=next_count;
            if (pop) begin
                first_pending<=0;
                if (m_axis_tlast) frame_end<=0;
            end
            if (push) begin
                if (s_axis_tuser) first_pending<=1;
                if (s_axis_tlast) frame_end<=1;
            end
        end
    end
endmodule
