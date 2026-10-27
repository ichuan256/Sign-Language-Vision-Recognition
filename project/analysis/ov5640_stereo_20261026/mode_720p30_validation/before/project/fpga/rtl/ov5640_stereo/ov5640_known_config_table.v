`timescale 1ns/1ps

// Confirmed configuration SUBSET for 24 MHz XCLK / 8-bit DVP RGB565.
// A complete startup must insert compatible global analog/ISP setup AFTER
// hardware reset and BEFORE this subset (the subset wrapper alone omits it).
// 1920x1080, HTS=2500, VTS=1120 remain a candidate mode contract, not a
// validated complete 1080p30 startup sequence. No crop or stream-on is implied.
// Sources and unresolved polarity differences: configuration_choices.md.
module ov5640_known_config_table (
    input wire [5:0] index,
    output reg valid,
    output reg [15:0] reg_addr,
    output reg [7:0] reg_value,
    output reg [7:0] write_mask,
    output reg [15:0] post_delay_ms,
    output reg last
);
    always @* begin
        valid = 1'b1;
        reg_addr = 16'h0000;
        reg_value = 8'h00;
        write_mask = 8'hff;
        post_delay_ms = 16'd0;
        last = 1'b0;
        case (index)
            0: begin reg_addr=16'h3034; reg_value=8'h18; end
            1: begin reg_addr=16'h3035; reg_value=8'h10; end
            2: begin reg_addr=16'h3036; reg_value=8'h54; end
            3: begin reg_addr=16'h3037; reg_value=8'h13; end
            4: begin reg_addr=16'h3108; reg_value=8'h01; end
            5: begin reg_addr=16'h3808; reg_value=8'h07; end
            6: begin reg_addr=16'h3809; reg_value=8'h80; end
            7: begin reg_addr=16'h380a; reg_value=8'h04; end
            8: begin reg_addr=16'h380b; reg_value=8'h38; end
            9: begin reg_addr=16'h380c; reg_value=8'h09; end
            10: begin reg_addr=16'h380d; reg_value=8'hc4; end
            11: begin reg_addr=16'h380e; reg_value=8'h04; end
            12: begin reg_addr=16'h380f; reg_value=8'h60; end
            13: begin reg_addr=16'h4300; reg_value=8'h6f; end
            14: begin reg_addr=16'h501f; reg_value=8'h01; end
            // Falling-edge camera data update; preserve VSYNC/HREF and all
            // other bits independently on each physical camera.
            15: begin reg_addr=16'h4740; reg_value=8'h20; write_mask=8'h20; end
            // Camera sysclk=84MHz, HTS=2500, VTS=1120: 50Hz step=336,
            // 60Hz step=280, floor((VTS-4)/step)=3 for both frequencies.
            16: begin reg_addr=16'h3a08; reg_value=8'h01; end
            17: begin reg_addr=16'h3a09; reg_value=8'h50; end
            18: begin reg_addr=16'h3a0a; reg_value=8'h01; end
            19: begin reg_addr=16'h3a0b; reg_value=8'h18; end
            20: begin reg_addr=16'h3a0d; reg_value=8'h03; end
            21: begin reg_addr=16'h3a0e; reg_value=8'h03; end
            22: begin reg_addr=16'h3c01; reg_value=8'h80; write_mask=8'h80; end
            23: begin reg_addr=16'h3a00; reg_value=8'h20; write_mask=8'h24; end
            24: begin reg_addr=16'h3503; reg_value=8'h00; write_mask=8'h03; end
            25: begin reg_addr=16'h3406; reg_value=8'h00; write_mask=8'h01; end
            // Preserve the traced global-table settling interval; this subset
            // does not reproduce that global table or prove image readiness.
            26: begin reg_addr=16'h3c00; reg_value=8'h04; write_mask=8'h04;
                      post_delay_ms=16'd300; last=1'b1; end
            default: begin valid=1'b0; write_mask=8'h00; end
        endcase
    end
endmodule
