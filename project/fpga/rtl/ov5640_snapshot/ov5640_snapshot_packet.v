`timescale 1ns/1ps
// AXI DMA packet: TLAST marks the final frame word, never a line ending.
module ov5640_snapshot_packet #(parameter integer PIXELS=1280*720)(
    input wire pclk, rst_n, arm_toggle,
    input wire pixel_valid, pixel_sof, input wire [15:0] pixel_data,
    input wire frame_done, frame_error, fifo_full, fifo_busy,
    output wire fifo_wr_en, output wire [32:0] fifo_din,
    output reg busy, done, error, overflow
);
    (* ASYNC_REG="TRUE", SHREG_EXTRACT="NO" *) reg [1:0] arm_sync;
    reg arm_seen, waiting, receiving, low_valid;
    reg [15:0] low_pixel;
    localparam integer CW=$clog2(PIXELS+1);
    reg [CW-1:0] count;
    wire take=busy && pixel_valid && (receiving || (waiting && pixel_sof));
    wire accept=take && count<PIXELS && !(receiving && pixel_sof) && !fifo_busy;
    assign fifo_wr_en=accept && low_valid && !fifo_full && !error;
    assign fifo_din={count==PIXELS-1,pixel_data,low_pixel};
    always @(posedge pclk or negedge rst_n) begin
        if (!rst_n) begin
            arm_sync<=0; arm_seen<=0; waiting<=0; receiving<=0;
            low_valid<=0; low_pixel<=0; count<=0; busy<=0; done<=0; error<=0; overflow<=0;
        end else begin
            arm_sync<={arm_sync[0],arm_toggle};
            if (arm_sync[1]!=arm_seen) begin
                arm_seen<=arm_sync[1];
                if (!busy && !error) begin
                    waiting<=1; receiving<=0; low_valid<=0; count<=0; busy<=1; done<=0; overflow<=0;
                end else begin error<=1; busy<=0; waiting<=0; receiving<=0; end
            end else if (busy) begin
                if (take) begin
                    if (fifo_busy || (low_valid && fifo_full) || count>=PIXELS || (receiving && pixel_sof)) begin
                        error<=1; overflow<=fifo_busy || fifo_full; busy<=0;
                        receiving<=0; waiting<=0; low_valid<=0;
                    end else begin
                        waiting<=0; receiving<=1; count<=count+1'b1;
                        if (!low_valid) begin low_pixel<=pixel_data; low_valid<=1; end
                        else low_valid<=0;
                    end
                end
                if (frame_done && receiving) begin
                    busy<=0; receiving<=0; waiting<=0;
                    if (frame_error || count!=PIXELS || low_valid) error<=1;
                    else done<=1;
                end
            end
        end
    end
endmodule
