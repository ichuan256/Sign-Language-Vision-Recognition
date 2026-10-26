`timescale 1ns/1ps

module tb_ov5640_stereo_top;
    localparam integer WIDTH = 2;
    localparam integer HEIGHT = 1;

    reg sys_clk = 1'b0;
    reg rst_n = 1'b0;
    reg ov1_pclk = 1'b0;
    reg ov1_vsync = 1'b0;
    reg ov1_href = 1'b0;
    reg [7:0] ov1_data = 8'h00;
    reg ov2_pclk = 1'b0;
    reg ov2_vsync = 1'b0;
    reg ov2_href = 1'b0;
    reg [7:0] ov2_data = 8'h00;
    reg sccb_start_ov1 = 1'b0;
    reg sccb_start_ov2 = 1'b0;
    reg [15:0] sccb_reg_addr = 16'h0000;
    reg [7:0] sccb_reg_data = 8'h00;

    wire ov1_pixel_valid;
    wire [15:0] ov1_pixel_data;
    wire ov1_pixel_sof;
    wire ov1_pixel_eol;
    wire ov1_frame_start;
    wire ov1_frame_done;
    wire ov1_frame_error;
    wire [31:0] ov1_frame_id;
    wire ov2_pixel_valid;
    wire [15:0] ov2_pixel_data;
    wire ov2_pixel_sof;
    wire ov2_pixel_eol;
    wire ov2_frame_start;
    wire ov2_frame_done;
    wire ov2_frame_error;
    wire [31:0] ov2_frame_id;
    wire sccb_busy_ov1;
    wire sccb_done_ov1;
    wire sccb_busy_ov2;
    wire sccb_done_ov2;
    tri1 ov1_scl;
    tri1 ov1_sda;
    tri1 ov2_scl;
    tri1 ov2_sda;

    integer ov1_pixels_seen = 0;
    integer ov2_pixels_seen = 0;
    integer ov1_frames_done = 0;
    integer ov2_frames_done = 0;

    always #5 sys_clk = ~sys_clk;
    always #4 ov1_pclk = ~ov1_pclk;
    always #7 ov2_pclk = ~ov2_pclk;

    ov5640_stereo_top #(
        .FRAME_WIDTH(WIDTH),
        .FRAME_HEIGHT(HEIGHT),
        .SCCB_HALF_PERIOD_CYCLES(2)
    ) dut (
        .sys_clk(sys_clk),
        .rst_n(rst_n),
        .ov1_pclk(ov1_pclk),
        .ov1_vsync(ov1_vsync),
        .ov1_href(ov1_href),
        .ov1_data(ov1_data),
        .ov1_pixel_valid(ov1_pixel_valid),
        .ov1_pixel_data(ov1_pixel_data),
        .ov1_pixel_sof(ov1_pixel_sof),
        .ov1_pixel_eol(ov1_pixel_eol),
        .ov1_frame_start(ov1_frame_start),
        .ov1_frame_done(ov1_frame_done),
        .ov1_frame_error(ov1_frame_error),
        .ov1_frame_id(ov1_frame_id),
        .ov2_pclk(ov2_pclk),
        .ov2_vsync(ov2_vsync),
        .ov2_href(ov2_href),
        .ov2_data(ov2_data),
        .ov2_pixel_valid(ov2_pixel_valid),
        .ov2_pixel_data(ov2_pixel_data),
        .ov2_pixel_sof(ov2_pixel_sof),
        .ov2_pixel_eol(ov2_pixel_eol),
        .ov2_frame_start(ov2_frame_start),
        .ov2_frame_done(ov2_frame_done),
        .ov2_frame_error(ov2_frame_error),
        .ov2_frame_id(ov2_frame_id),
        .sccb_start_ov1(sccb_start_ov1),
        .sccb_start_ov2(sccb_start_ov2),
        .sccb_reg_addr(sccb_reg_addr),
        .sccb_reg_data(sccb_reg_data),
        .sccb_busy_ov1(sccb_busy_ov1),
        .sccb_done_ov1(sccb_done_ov1),
        .ov1_scl(ov1_scl),
        .ov1_sda(ov1_sda),
        .sccb_busy_ov2(sccb_busy_ov2),
        .sccb_done_ov2(sccb_done_ov2),
        .ov2_scl(ov2_scl),
        .ov2_sda(ov2_sda)
    );

    always @(posedge ov1_pclk) begin
        #1;
        if (ov1_pixel_valid) begin
            case (ov1_pixels_seen)
                0: if (ov1_pixel_data !== 16'hF800 ||
                       !ov1_pixel_sof || ov1_pixel_eol)
                       $fatal(1, "OV1 pixel 0 mismatch");
                1: if (ov1_pixel_data !== 16'h07E0 ||
                       ov1_pixel_sof || !ov1_pixel_eol)
                       $fatal(1, "OV1 pixel 1 mismatch");
                default: $fatal(1, "unexpected OV1 pixel %0d", ov1_pixels_seen);
            endcase
            ov1_pixels_seen = ov1_pixels_seen + 1;
        end
        if (ov1_frame_done) begin
            if (ov1_frame_error)
                $fatal(1, "OV1 frame was marked bad");
            ov1_frames_done = ov1_frames_done + 1;
        end
    end

    always @(posedge ov2_pclk) begin
        #1;
        if (ov2_pixel_valid) begin
            case (ov2_pixels_seen)
                0: if (ov2_pixel_data !== 16'h001F ||
                       !ov2_pixel_sof || ov2_pixel_eol)
                       $fatal(1, "OV2 pixel 0 mismatch");
                1: if (ov2_pixel_data !== 16'hFFFF ||
                       ov2_pixel_sof || !ov2_pixel_eol)
                       $fatal(1, "OV2 pixel 1 mismatch");
                default: $fatal(1, "unexpected OV2 pixel %0d", ov2_pixels_seen);
            endcase
            ov2_pixels_seen = ov2_pixels_seen + 1;
        end
        if (ov2_frame_done) begin
            if (ov2_frame_error)
                $fatal(1, "OV2 frame was marked bad");
            ov2_frames_done = ov2_frames_done + 1;
        end
    end

    task send_ov1_frame;
        begin
            @(negedge ov1_pclk); ov1_vsync = 1'b1;
            repeat (3) @(posedge ov1_pclk);
            @(negedge ov1_pclk); ov1_vsync = 1'b0;
            repeat (3) @(posedge ov1_pclk);
            @(negedge ov1_pclk); ov1_href = 1'b1; ov1_data = 8'h00;
            @(posedge ov1_pclk); #2;
            @(negedge ov1_pclk); ov1_data = 8'hF8;
            @(posedge ov1_pclk); #2;
            @(negedge ov1_pclk); ov1_data = 8'hE0;
            @(posedge ov1_pclk); #2;
            @(negedge ov1_pclk); ov1_data = 8'h07;
            @(posedge ov1_pclk); #2;
            @(negedge ov1_pclk); ov1_href = 1'b0; ov1_data = 8'h00;
            @(posedge ov1_pclk); #2;
            @(negedge ov1_pclk); ov1_vsync = 1'b1;
            repeat (3) @(posedge ov1_pclk);
        end
    endtask

    task send_ov2_frame;
        begin
            @(negedge ov2_pclk); ov2_vsync = 1'b1;
            repeat (3) @(posedge ov2_pclk);
            @(negedge ov2_pclk); ov2_vsync = 1'b0;
            repeat (3) @(posedge ov2_pclk);
            @(negedge ov2_pclk); ov2_href = 1'b1; ov2_data = 8'h1F;
            @(posedge ov2_pclk); #2;
            @(negedge ov2_pclk); ov2_data = 8'h00;
            @(posedge ov2_pclk); #2;
            @(negedge ov2_pclk); ov2_data = 8'hFF;
            @(posedge ov2_pclk); #2;
            @(negedge ov2_pclk); ov2_data = 8'hFF;
            @(posedge ov2_pclk); #2;
            @(negedge ov2_pclk); ov2_href = 1'b0; ov2_data = 8'h00;
            @(posedge ov2_pclk); #2;
            @(negedge ov2_pclk); ov2_vsync = 1'b1;
            repeat (3) @(posedge ov2_pclk);
        end
    endtask

    initial begin
        repeat (5) @(posedge sys_clk);
        @(negedge sys_clk); rst_n = 1'b1;

        @(negedge sys_clk);
        sccb_reg_addr = 16'h3008;
        sccb_reg_data = 8'h82;
        sccb_start_ov1 = 1'b1;
        sccb_start_ov2 = 1'b1;
        @(negedge sys_clk);
        sccb_start_ov1 = 1'b0;
        sccb_start_ov2 = 1'b0;

        fork
            send_ov1_frame();
            send_ov2_frame();
        join

        wait(ov1_frames_done == 1 && ov2_frames_done == 1);
        wait(sccb_done_ov1 && sccb_done_ov2);
        #1;
        if (ov1_pixels_seen != 2 || ov2_pixels_seen != 2)
            $fatal(1, "top pixel totals differ: OV1=%0d OV2=%0d",
                   ov1_pixels_seen, ov2_pixels_seen);
        if (ov1_frame_id != 1 || ov2_frame_id != 1)
            $fatal(1, "top frame counters mismatch: OV1=%0d OV2=%0d",
                   ov1_frame_id, ov2_frame_id);
        if (sccb_busy_ov1 || sccb_busy_ov2)
            $fatal(1, "top SCCB busy remained asserted after completion");

        $display("TEST_PASS: top integrates independent DVP PCLKs and dual SCCB writes");
        $finish;
    end

    initial begin
        #200000;
        $fatal(1, "watchdog timeout");
    end
endmodule
