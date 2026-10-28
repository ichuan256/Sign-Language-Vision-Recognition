`timescale 1ns/1ps
// Pack RGB565 pixels into AXI words. A short frame is terminated with TLAST;
// the one-pixel final word uses the low two TKEEP bytes.
module ov5640_snapshot_packet #(parameter integer PIXELS=1280*720)(
    input wire pclk, rst_n, arm_toggle, frame_start,
    input wire pixel_valid, pixel_sof, input wire [15:0] pixel_data,
    input wire frame_done, fifo_full, fifo_busy,
    output wire fifo_wr_en, output wire [33:0] fifo_din,
    output reg busy, done, error, overflow
);
    (* ASYNC_REG="TRUE", SHREG_EXTRACT="NO" *) reg [1:0] arm_sync;
    reg arm_seen, waiting, receiving, closing, armed_frame_seen;
    reg half_valid;
    reg [15:0] half_pixel;
    reg word_valid;
    reg [31:0] word_data;
    reg [31:0] count;

    wire pixel_accepted = busy && pixel_valid && (receiving || (waiting && pixel_sof));
    // Hold the newest packed word until either another pair proves it is not
    // final, or frame_done lets it carry TLAST.
    wire output_ready = word_valid && (closing || (pixel_accepted && half_valid)) &&
                        !fifo_full && !fifo_busy;
    wire half_output_ready = !word_valid && closing && half_valid && !fifo_full && !fifo_busy;
    wire output_last = closing && word_valid && !half_valid;
    assign fifo_wr_en = output_ready || half_output_ready;
    // fifo_din[33] marks a one-pixel final word; fifo_din[32] is TLAST.
    assign fifo_din = half_output_ready
                    ? {1'b1,1'b1,16'b0,half_pixel}
                    : {1'b0,output_last,word_data};

    always @(posedge pclk or negedge rst_n) begin
        if (!rst_n) begin
            arm_sync<=0; arm_seen<=0; waiting<=0; receiving<=0; closing<=0; armed_frame_seen<=0;
            half_valid<=0; half_pixel<=0; word_valid<=0; word_data<=0; count<=0;
            busy<=0; done<=0; error<=0; overflow<=0;
        end else begin
            arm_sync<={arm_sync[0],arm_toggle};
            if (arm_sync[1] != arm_seen) begin
                arm_seen <= arm_sync[1];
                if (!busy && !error && !closing) begin
                    waiting<=1; receiving<=0; armed_frame_seen<=0; half_valid<=0; word_valid<=0;
                    count<=0; done<=0; overflow<=0; busy<=1;
                end else begin
                    error<=1; busy<=0; waiting<=0; receiving<=0;
                end
            end else begin
                if (busy && waiting && frame_start) armed_frame_seen<=1;
                if (fifo_wr_en) begin
                    if (half_output_ready) begin
                        half_valid<=0; closing<=0; done<=1;
                    end else begin
                        word_valid<=0;
                        if (output_last) begin closing<=0; done<=1; end
                    end
                end

                if (pixel_accepted) begin
                    if (count >= PIXELS || (receiving && pixel_sof) ||
                        (word_valid && half_valid && !fifo_wr_en)) begin
                        error<=1; overflow<=word_valid && half_valid && !fifo_wr_en;
                        busy<=0; waiting<=0; receiving<=0; closing<=0;
                        half_valid<=0; word_valid<=0;
                    end else begin
                        waiting<=0; receiving<=1; count<=count+1'b1;
                        if (!half_valid) begin
                            half_pixel<=pixel_data;
                            half_valid<=1;
                        end else begin
                            word_data<={pixel_data,half_pixel};
                            word_valid<=1;
                            half_valid<=0;
                        end
                    end
                end

                // Arming may happen mid-frame. Ignore that frame's closing
                // VSYNC while waiting for its next SOF; only close after data
                // from a complete subsequent frame has entered the packet.
                if (busy && frame_done && receiving) begin
                    busy<=0; waiting<=0; receiving<=0; closing<=1;
                    done<=0; // Set only when the final beat reaches FIFO.
                end else if (busy && frame_done && waiting && armed_frame_seen) begin
                    // No SOF/pixels appeared in a complete post-arm frame.
                    busy<=0; waiting<=0; armed_frame_seen<=0;
                    error<=1; overflow<=0;
                end
            end
        end
    end
endmodule
