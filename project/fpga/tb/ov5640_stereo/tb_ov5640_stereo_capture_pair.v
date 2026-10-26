`timescale 1ns/1ps

module tb_ov5640_stereo_capture_pair;
    reg rst_n = 1'b0;
    reg ov1_pclk = 1'b0;
    reg ov2_pclk = 1'b0;
    reg ov1_vsync = 1'b0;
    reg ov2_vsync = 1'b0;
    reg ov1_href = 1'b0;
    reg ov2_href = 1'b0;
    reg [7:0] ov1_data = 8'h00;
    reg [7:0] ov2_data = 8'h00;

    wire ov1_pixel_valid, ov1_pixel_sof, ov1_pixel_eol;
    wire [15:0] ov1_pixel_data;
    wire ov1_frame_start, ov1_frame_done, ov1_frame_error;
    wire [31:0] ov1_frame_id;
    wire ov2_pixel_valid, ov2_pixel_sof, ov2_pixel_eol;
    wire [15:0] ov2_pixel_data;
    wire ov2_frame_start, ov2_frame_done, ov2_frame_error;
    wire [31:0] ov2_frame_id;

    integer ov1_pixels = 0;
    integer ov2_pixels = 0;
    integer ov1_done = 0;
    integer ov2_done = 0;
    integer ov1_errors = 0;
    integer ov2_errors = 0;

    always #5 ov1_pclk = ~ov1_pclk;
    always #7 ov2_pclk = ~ov2_pclk;

    ov5640_stereo_capture_pair #(
        .FRAME_WIDTH(1),
        .FRAME_HEIGHT(1)
    ) dut (
        .rst_n(rst_n),
        .ov1_pclk(ov1_pclk), .ov1_vsync(ov1_vsync),
        .ov1_href(ov1_href), .ov1_data(ov1_data),
        .ov1_pixel_valid(ov1_pixel_valid), .ov1_pixel_data(ov1_pixel_data),
        .ov1_pixel_sof(ov1_pixel_sof), .ov1_pixel_eol(ov1_pixel_eol),
        .ov1_frame_start(ov1_frame_start), .ov1_frame_done(ov1_frame_done),
        .ov1_frame_error(ov1_frame_error), .ov1_frame_id(ov1_frame_id),
        .ov2_pclk(ov2_pclk), .ov2_vsync(ov2_vsync),
        .ov2_href(ov2_href), .ov2_data(ov2_data),
        .ov2_pixel_valid(ov2_pixel_valid), .ov2_pixel_data(ov2_pixel_data),
        .ov2_pixel_sof(ov2_pixel_sof), .ov2_pixel_eol(ov2_pixel_eol),
        .ov2_frame_start(ov2_frame_start), .ov2_frame_done(ov2_frame_done),
        .ov2_frame_error(ov2_frame_error), .ov2_frame_id(ov2_frame_id)
    );

    always @(posedge ov1_pclk) begin
        #1;
        if (ov1_pixel_valid) begin
            if (ov1_pixel_data !== 16'hBEEF || !ov1_pixel_sof || !ov1_pixel_eol)
                $fatal(1, "OV1 unexpected pixel/status: %h sof=%b eol=%b",
                       ov1_pixel_data, ov1_pixel_sof, ov1_pixel_eol);
            ov1_pixels = ov1_pixels + 1;
        end
        if (ov1_frame_done) begin
            ov1_done = ov1_done + 1;
            if (ov1_frame_error)
                ov1_errors = ov1_errors + 1;
        end
    end

    always @(posedge ov2_pclk) begin
        #1;
        if (ov2_pixel_valid) begin
            if (ov2_pixel_data !== 16'h1234 || !ov2_pixel_sof || !ov2_pixel_eol)
                $fatal(1, "OV2 unexpected pixel/status: %h sof=%b eol=%b",
                       ov2_pixel_data, ov2_pixel_sof, ov2_pixel_eol);
            ov2_pixels = ov2_pixels + 1;
        end
        if (ov2_frame_done) begin
            ov2_done = ov2_done + 1;
            if (ov2_frame_error)
                ov2_errors = ov2_errors + 1;
        end
    end

    task ov1_frame;
        begin
            @(negedge ov1_pclk); ov1_vsync = 1'b1;
            repeat (2) @(posedge ov1_pclk);
            @(negedge ov1_pclk); ov1_vsync = 1'b0;
            repeat (3) @(posedge ov1_pclk);
            @(negedge ov1_pclk); ov1_href = 1'b1; ov1_data = 8'hEF;
            @(posedge ov1_pclk); #2;
            @(negedge ov1_pclk); ov1_data = 8'hBE;
            @(posedge ov1_pclk); #2;
            @(negedge ov1_pclk); ov1_href = 1'b0;
            @(posedge ov1_pclk); #2;
            @(negedge ov1_pclk); ov1_vsync = 1'b1;
            repeat (3) @(posedge ov1_pclk);
        end
    endtask

    task ov2_frame;
        begin
            @(negedge ov2_pclk); ov2_vsync = 1'b1;
            repeat (2) @(posedge ov2_pclk);
            @(negedge ov2_pclk); ov2_vsync = 1'b0;
            repeat (3) @(posedge ov2_pclk);
            @(negedge ov2_pclk); ov2_href = 1'b1; ov2_data = 8'h34;
            @(posedge ov2_pclk); #2;
            @(negedge ov2_pclk); ov2_data = 8'h12;
            @(posedge ov2_pclk); #2;
            @(negedge ov2_pclk); ov2_href = 1'b0;
            @(posedge ov2_pclk); #2;
            @(negedge ov2_pclk); ov2_vsync = 1'b1;
            repeat (3) @(posedge ov2_pclk);
        end
    endtask

    initial begin
        repeat (5) @(posedge ov1_pclk);
        @(negedge ov1_pclk); rst_n = 1'b1;
        repeat (5) @(posedge ov1_pclk);
        fork
            ov1_frame();
            begin
                repeat (4) @(posedge ov2_pclk);
                ov2_frame();
            end
        join
        repeat (4) @(posedge ov1_pclk);
        repeat (4) @(posedge ov2_pclk);
        if (ov1_pixels != 1 || ov2_pixels != 1)
            $fatal(1, "per-eye pixel counts wrong: OV1=%0d OV2=%0d", ov1_pixels, ov2_pixels);
        if (ov1_done != 1 || ov2_done != 1 || ov1_errors || ov2_errors)
            $fatal(1, "per-eye status wrong: done=%0d/%0d error=%0d/%0d",
                   ov1_done, ov2_done, ov1_errors, ov2_errors);
        if (ov1_frame_id != 1 || ov2_frame_id != 1)
            $fatal(1, "per-eye frame IDs wrong: OV1=%0d OV2=%0d", ov1_frame_id, ov2_frame_id);
        $display("TEST_PASS: independent OV1/OV2 PCLK domains capture separately");
        $finish;
    end

    initial begin
        #200000;
        $fatal(1, "watchdog timeout");
    end
endmodule
