`timescale 1ns/1ps

// One OV5640 8-bit DVP receiver.
//
// All pixel and frame status outputs are synchronous to cam_pclk. They must
// cross into another clock domain through an asynchronous FIFO; this module
// intentionally has no backpressure because the camera cannot be stalled.
module ov5640_dvp_capture #(
    parameter integer FRAME_WIDTH = 1280,
    parameter integer FRAME_HEIGHT = 720,
    parameter         VSYNC_ACTIVE_LEVEL = 1'b1
) (
    input  wire        rst_n,
    input  wire        cam_pclk,
    input  wire        cam_vsync,
    input  wire        cam_href,
    input  wire [7:0]  cam_data,

    output reg         pixel_valid,
    output reg  [15:0] pixel_data,
    output reg         pixel_sof,
    output reg         pixel_eol,

    output reg         frame_start,
    output reg         frame_done,
    output reg         frame_error,
    output reg  [31:0] frame_id
);

    localparam integer PIX_COUNT_WIDTH =
        (FRAME_WIDTH < 1) ? 1 : $clog2(FRAME_WIDTH + 2);
    localparam integer LINE_COUNT_WIDTH =
        (FRAME_HEIGHT < 1) ? 1 : $clog2(FRAME_HEIGHT + 2);

    // Assert reset asynchronously and release it synchronously in this
    // camera's pixel-clock domain.
    reg [1:0] reset_sync;
    always @(posedge cam_pclk or negedge rst_n) begin
        if (!rst_n)
            reset_sync <= 2'b00;
        else
            reset_sync <= {reset_sync[0], 1'b1};
    end
    wire pclk_rst_n = reset_sync[1];

    reg cam_vsync_d;
    reg cam_href_d;
    reg in_frame;
    reg line_in_progress;
    reg byte_phase;
    reg [7:0] low_byte;
    reg [PIX_COUNT_WIDTH-1:0] line_pixel_count;
    reg [LINE_COUNT_WIDTH-1:0] lines_seen;
    reg frame_bad_latched;

    wire vsync_active = (cam_vsync == VSYNC_ACTIVE_LEVEL);
    wire vsync_active_d = (cam_vsync_d == VSYNC_ACTIVE_LEVEL);
    wire vsync_active_rise = vsync_active && !vsync_active_d;
    wire vsync_active_fall = !vsync_active && vsync_active_d;
    wire href_rise = cam_href && !cam_href_d;
    wire href_fall = !cam_href && cam_href_d;

    always @(posedge cam_pclk or negedge pclk_rst_n) begin
        if (!pclk_rst_n) begin
            cam_vsync_d       <= ~VSYNC_ACTIVE_LEVEL;
            cam_href_d        <= 1'b0;
            in_frame          <= 1'b0;
            line_in_progress  <= 1'b0;
            byte_phase        <= 1'b0;
            low_byte          <= 8'h00;
            line_pixel_count  <= {PIX_COUNT_WIDTH{1'b0}};
            lines_seen        <= {LINE_COUNT_WIDTH{1'b0}};
            frame_bad_latched <= 1'b0;

            pixel_valid       <= 1'b0;
            pixel_data        <= 16'h0000;
            pixel_sof         <= 1'b0;
            pixel_eol         <= 1'b0;
            frame_start       <= 1'b0;
            frame_done        <= 1'b0;
            frame_error       <= 1'b0;
            frame_id          <= 32'd0;
        end else begin
            cam_vsync_d <= cam_vsync;
            cam_href_d  <= cam_href;

            // These are one-cam_pclk-cycle events/data-valid qualifiers.
            pixel_valid <= 1'b0;
            pixel_sof   <= 1'b0;
            pixel_eol   <= 1'b0;
            frame_start <= 1'b0;
            frame_done  <= 1'b0;
            frame_error <= 1'b0;

            // The configured VSYNC pulse closes the preceding image and the
            // trailing edge begins the next active image interval.
            if (vsync_active_rise) begin
                if (in_frame) begin
                    frame_done <= 1'b1;
                    frame_error <= frame_bad_latched || line_in_progress ||
                                   (lines_seen != FRAME_HEIGHT);
                    frame_id <= frame_id + 32'd1;
                end
                in_frame         <= 1'b0;
                line_in_progress <= 1'b0;
                byte_phase       <= 1'b0;
            end

            if (vsync_active_fall) begin
                in_frame          <= 1'b1;
                line_in_progress  <= 1'b0;
                byte_phase        <= 1'b0;
                line_pixel_count  <= {PIX_COUNT_WIDTH{1'b0}};
                lines_seen        <= {LINE_COUNT_WIDTH{1'b0}};
                frame_bad_latched <= 1'b0;
                frame_start       <= 1'b1;
            end

            // HREF rises on the first valid byte, so capture that byte here
            // rather than waiting for the following pixel-clock edge.
            if (href_rise && in_frame && !vsync_active) begin
                if (line_in_progress || (lines_seen >= FRAME_HEIGHT))
                    frame_bad_latched <= 1'b1;
                line_in_progress <= 1'b1;
                line_pixel_count <= {PIX_COUNT_WIDTH{1'b0}};
                low_byte   <= cam_data; // ATK module RGB565 sends low byte first
                byte_phase <= 1'b1;
            end else if (cam_href && line_in_progress && in_frame &&
                         !vsync_active) begin
                if (!byte_phase) begin
                    low_byte   <= cam_data;
                    byte_phase <= 1'b1;
                end else begin
                    byte_phase <= 1'b0;

                    if ((lines_seen < FRAME_HEIGHT) &&
                        (line_pixel_count < FRAME_WIDTH)) begin
                        pixel_data  <= {cam_data, low_byte};
                        pixel_valid <= 1'b1;
                        pixel_sof   <= (lines_seen == 0) &&
                                       (line_pixel_count == 0);
                        pixel_eol   <= (line_pixel_count == FRAME_WIDTH - 1);
                    end else begin
                        // Suppress over-width/over-height pixels so a bad
                        // frame cannot write beyond its expected image size.
                        frame_bad_latched <= 1'b1;
                    end

                    // Saturate at expected width + 1. This preserves the
                    // distinction between an exact line and an overlong one.
                    if (line_pixel_count <= FRAME_WIDTH)
                        line_pixel_count <= line_pixel_count + 1'b1;
                end
            end

            if (href_fall && line_in_progress && in_frame) begin
                if (byte_phase || (line_pixel_count != FRAME_WIDTH))
                    frame_bad_latched <= 1'b1;
                line_in_progress <= 1'b0;
                byte_phase       <= 1'b0;
                if (lines_seen <= FRAME_HEIGHT)
                    lines_seen <= lines_seen + 1'b1;
            end
        end
    end

endmodule
