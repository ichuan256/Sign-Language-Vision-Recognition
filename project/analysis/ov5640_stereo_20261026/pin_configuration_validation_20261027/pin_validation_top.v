// Verification only: board oscillator/buttons, no bitstream or deployment.
module pin_validation_top (
    input wire sys_clk, input wire [1:0] buttons,
    output wire [3:0] leds,
    input wire ov1_pclk, ov1_vsync, ov1_href,
    input wire [7:0] ov1_data,
    input wire ov2_pclk, ov2_vsync, ov2_href,
    input wire [7:0] ov2_data,
    inout wire ov1_scl, ov1_sda, ov2_scl, ov2_sda,
    output wire ov1_reset_n, ov1_pwdn, ov2_reset_n, ov2_pwdn
);
    wire rst_n = ~buttons[0];
    (* ASYNC_REG = "TRUE" *) reg [2:0] start_sync;
    always @(posedge sys_clk or negedge rst_n)
        if (!rst_n) start_sync <= 0;
        else start_sync <= {start_sync[1:0], buttons[1]};
    wire busy, init_done, init_error;
    wire [3:0] error_code;
    wire [1:0] failed_cameras;
    wire ov1_pixel_valid, ov1_pixel_sof, ov1_pixel_eol;
    wire ov2_pixel_valid, ov2_pixel_sof, ov2_pixel_eol;
    wire [15:0] ov1_pixel_data, ov2_pixel_data;
    wire ov1_frame_start, ov1_frame_done, ov1_frame_error;
    wire ov2_frame_start, ov2_frame_done, ov2_frame_error;
    wire [31:0] ov1_frame_id, ov2_frame_id;
    (* DONT_TOUCH = "TRUE" *) ov5640_stereo_startup_capture #(
        .SYS_CLK_HZ(125000000)
    ) u_camera (
        .sys_clk(sys_clk), .rst_n(rst_n),
        .start(start_sync[1] & ~start_sync[2]),
        .ov1_reset_n(ov1_reset_n), .ov1_pwdn(ov1_pwdn),
        .ov2_reset_n(ov2_reset_n), .ov2_pwdn(ov2_pwdn),
        .ov1_scl(ov1_scl), .ov1_sda(ov1_sda),
        .ov2_scl(ov2_scl), .ov2_sda(ov2_sda),
        .busy(busy), .init_done(init_done), .init_error(init_error),
        .error_code(error_code), .failed_cameras(failed_cameras),
        .ov1_pclk(ov1_pclk), .ov1_vsync(ov1_vsync), .ov1_href(ov1_href),
        .ov1_data(ov1_data), .ov1_pixel_valid(ov1_pixel_valid),
        .ov1_pixel_sof(ov1_pixel_sof), .ov1_pixel_eol(ov1_pixel_eol),
        .ov1_pixel_data(ov1_pixel_data), .ov1_frame_start(ov1_frame_start),
        .ov1_frame_done(ov1_frame_done), .ov1_frame_error(ov1_frame_error),
        .ov1_frame_id(ov1_frame_id),
        .ov2_pclk(ov2_pclk), .ov2_vsync(ov2_vsync), .ov2_href(ov2_href),
        .ov2_data(ov2_data), .ov2_pixel_valid(ov2_pixel_valid),
        .ov2_pixel_sof(ov2_pixel_sof), .ov2_pixel_eol(ov2_pixel_eol),
        .ov2_pixel_data(ov2_pixel_data), .ov2_frame_start(ov2_frame_start),
        .ov2_frame_done(ov2_frame_done), .ov2_frame_error(ov2_frame_error),
        .ov2_frame_id(ov2_frame_id)
    );
    // Keep real capture logic; LED reductions are observations, not data CDC.
    (* DONT_TOUCH = "TRUE" *) reg [31:0] sink1, sink2;
    always @(posedge ov1_pclk or negedge rst_n)
        if (!rst_n) sink1 <= 0;
        else sink1 <= sink1 ^ ov1_frame_id ^ {12'b0,ov1_frame_start,
            ov1_frame_done,ov1_frame_error,ov1_pixel_valid,ov1_pixel_data};
    always @(posedge ov2_pclk or negedge rst_n)
        if (!rst_n) sink2 <= 0;
        else sink2 <= sink2 ^ ov2_frame_id ^ {12'b0,ov2_frame_start,
            ov2_frame_done,ov2_frame_error,ov2_pixel_valid,ov2_pixel_data};
    assign leds = {^sink1 ^ ov1_pixel_sof ^ ov1_pixel_eol,
                   ^sink2 ^ ov2_pixel_sof ^ ov2_pixel_eol,
                   busy ^ ^error_code, init_done ^ init_error ^ ^failed_cameras};
endmodule
