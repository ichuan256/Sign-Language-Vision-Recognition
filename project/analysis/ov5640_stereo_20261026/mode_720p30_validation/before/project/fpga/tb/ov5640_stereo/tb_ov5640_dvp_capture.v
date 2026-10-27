`timescale 1ns/1ps

module tb_ov5640_dvp_capture;
    localparam integer WIDTH = 2;
    localparam integer HEIGHT = 2;

    reg rst_n = 1'b0;
    reg cam_pclk = 1'b0;
    reg cam_vsync = 1'b0;
    reg cam_href = 1'b0;
    reg [7:0] cam_data = 8'h00;

    wire pixel_valid;
    wire [15:0] pixel_data;
    wire pixel_sof;
    wire pixel_eol;
    wire frame_start;
    wire frame_done;
    wire frame_error;
    wire [31:0] frame_id;

    integer pixels_seen = 0;
    integer frame_starts = 0;
    integer frames_done = 0;
    integer errors_seen = 0;

    always #5 cam_pclk = ~cam_pclk;

    ov5640_dvp_capture #(
        .FRAME_WIDTH(WIDTH),
        .FRAME_HEIGHT(HEIGHT),
        .VSYNC_ACTIVE_LEVEL(1'b1)
    ) dut (
        .rst_n(rst_n),
        .cam_pclk(cam_pclk),
        .cam_vsync(cam_vsync),
        .cam_href(cam_href),
        .cam_data(cam_data),
        .pixel_valid(pixel_valid),
        .pixel_data(pixel_data),
        .pixel_sof(pixel_sof),
        .pixel_eol(pixel_eol),
        .frame_start(frame_start),
        .frame_done(frame_done),
        .frame_error(frame_error),
        .frame_id(frame_id)
    );

    always @(posedge cam_pclk) begin
        #1;
        if (pixel_valid) begin
            if (pixels_seen < 4) case (pixels_seen)
                0: begin
                    if (pixel_data !== 16'hF800 || !pixel_sof || pixel_eol)
                        $fatal(1, "pixel 0 mismatch data=%h sof=%b eol=%b",
                               pixel_data, pixel_sof, pixel_eol);
                end
                1: begin
                    if (pixel_data !== 16'h07E0 || pixel_sof || !pixel_eol)
                        $fatal(1, "pixel 1 mismatch data=%h sof=%b eol=%b",
                               pixel_data, pixel_sof, pixel_eol);
                end
                2: begin
                    if (pixel_data !== 16'h001F || pixel_sof || pixel_eol)
                        $fatal(1, "pixel 2 mismatch data=%h sof=%b eol=%b",
                               pixel_data, pixel_sof, pixel_eol);
                end
                3: begin
                    if (pixel_data !== 16'hFFFF || pixel_sof || !pixel_eol)
                        $fatal(1, "pixel 3 mismatch data=%h sof=%b eol=%b",
                               pixel_data, pixel_sof, pixel_eol);
                end
                default: $fatal(1, "unexpected pixel %0d: %h", pixels_seen, pixel_data);
            endcase
            pixels_seen = pixels_seen + 1;
        end
        if (frame_start)
            frame_starts = frame_starts + 1;
        if (frame_done) begin
            frames_done = frames_done + 1;
            if (frame_error)
                errors_seen = errors_seen + 1;
        end
    end

    task set_byte;
        input [7:0] value;
        begin
            @(negedge cam_pclk);
            cam_data = value;
            @(posedge cam_pclk);
            #2;
        end
    endtask

    task start_frame;
        begin
            @(negedge cam_pclk);
            cam_vsync = 1'b1;
            repeat (2) @(posedge cam_pclk);
            @(negedge cam_pclk);
            cam_vsync = 1'b0;
            repeat (3) @(posedge cam_pclk);
        end
    endtask

    task start_line;
        input [7:0] first_byte;
        begin
            @(negedge cam_pclk);
            cam_href = 1'b1;
            cam_data = first_byte;
            @(posedge cam_pclk);
            #2;
        end
    endtask

    task end_line;
        begin
            @(negedge cam_pclk);
            cam_href = 1'b0;
            cam_data = 8'h00;
            @(posedge cam_pclk);
            #2;
        end
    endtask

    task finish_frame;
        begin
            @(negedge cam_pclk);
            cam_vsync = 1'b1;
            repeat (3) @(posedge cam_pclk);
            #2;
        end
    endtask

    initial begin
        repeat (4) @(posedge cam_pclk);
        @(negedge cam_pclk);
        rst_n = 1'b1;
        repeat (4) @(posedge cam_pclk);

        // Valid 2x2 RGB565 frame. Manual states low byte arrives first.
        start_frame();
        start_line(8'h00); set_byte(8'hF8); // red: F800
        set_byte(8'hE0); set_byte(8'h07);   // green: 07E0
        end_line();
        start_line(8'h1F); set_byte(8'h00); // blue: 001F
        set_byte(8'hFF); set_byte(8'hFF);   // white: FFFF
        end_line();
        finish_frame();

        if (pixels_seen != 4)
            $fatal(1, "expected 4 pixels, got %0d", pixels_seen);
        if (frame_starts != 1 || frames_done != 1 || errors_seen != 0)
            $fatal(1, "valid frame status start=%0d done=%0d error=%0d",
                   frame_starts, frames_done, errors_seen);
        if (frame_id != 1)
            $fatal(1, "frame_id expected 1 after first completed frame, got %0d", frame_id);

        // A one-byte line has no complete RGB565 pixel; the frame is marked
        // bad, and the following frame must start from a clean byte phase.
        start_frame();
        start_line(8'hAA);
        end_line();
        start_line(8'h11); set_byte(8'h22); set_byte(8'h33); set_byte(8'h44);
        end_line();
        finish_frame();
        if (frames_done != 2 || errors_seen != 1)
            $fatal(1, "odd-byte frame was not rejected: done=%0d error=%0d",
                   frames_done, errors_seen);

        // One exact frame after a malformed frame verifies recovery.
        start_frame();
        start_line(8'h00); set_byte(8'hF8); set_byte(8'hE0); set_byte(8'h07);
        end_line();
        start_line(8'h1F); set_byte(8'h00); set_byte(8'hFF); set_byte(8'hFF);
        end_line();
        finish_frame();
        if (frames_done != 3 || errors_seen != 1)
            $fatal(1, "capture did not recover after malformed frame");
        if (frame_id != 3)
            $fatal(1, "frame_id expected 3, got %0d", frame_id);

        // Excess pixels must be suppressed after configured width, while
        // the frame is marked bad at completion.
        start_frame();
        start_line(8'h00); set_byte(8'hF8); set_byte(8'hE0); set_byte(8'h07);
        set_byte(8'h1F); set_byte(8'h00); // third pixel pair exceeds width
        end_line();
        start_line(8'hFF); set_byte(8'hFF); set_byte(8'h00); set_byte(8'h00);
        end_line();
        finish_frame();
        if (pixels_seen != 14)
            $fatal(1, "over-width pixels were not suppressed, total=%0d", pixels_seen);
        if (frames_done != 4 || errors_seen != 2 || frame_id != 4)
            $fatal(1, "over-width frame status done=%0d error=%0d id=%0d",
                   frames_done, errors_seen, frame_id);

        $display("TEST_PASS: RGB565 order, SOF/EOL, odd/over-width error, suppression, recovery");
        $finish;
    end

    initial begin
        #200000;
        $fatal(1, "watchdog timeout");
    end
endmodule
