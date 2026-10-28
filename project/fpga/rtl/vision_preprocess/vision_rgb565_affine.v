`timescale 1ns/1ps
// Integer RGB565_LE inverse-affine sampler. See board/vision_preprocess/CONTRACT.md.
// Small word cache only: no frame/line buffer and at most one read outstanding.
module vision_rgb565_affine (
    input wire clk, input wire reset_n, input wire start,
    output reg busy, output reg done, output reg [7:0] error_code,
    input wire [31:0] cfg_src_base, input wire [31:0] cfg_src_stride,
    input wire [15:0] cfg_src_width, input wire [15:0] cfg_src_height,
    input wire [15:0] cfg_dst_width, input wire [15:0] cfg_dst_height,
    input wire signed [31:0] cfg_a, cfg_b, cfg_c, cfg_d, cfg_e, cfg_f,
    output wire rd_req_valid, input wire rd_req_ready,
    output wire [31:0] rd_req_addr,
    input wire rd_rsp_valid, output wire rd_rsp_ready,
    input wire [31:0] rd_rsp_data, input wire rd_rsp_error,
    output reg [23:0] m_axis_tdata, output wire m_axis_tvalid,
    input wire m_axis_tready, output reg m_axis_tuser, output reg m_axis_tlast
);
    localparam [3:0] IDLE=0, COORD=1, PREPARE=2, ADDRESS_ROW=3,
                     ADDRESS_BASE=4, ADDRESS_PIXEL=5, LOOKUP=6,
                     REQUEST=7, RESPONSE=8, MULTIPLY=9,
                     ACCUMULATE=10, RESULT=11, OUTPUT=12,
                     FRAME_SPAN=13, FRAME_CHECK=14;
    reg [3:0] state;
    reg [31:0] src_base, src_stride;
    reg [15:0] src_width, src_height, dst_width, dst_height;
    reg [47:0] frame_span;
    reg signed [47:0] step_x_x, step_y_x, step_x_y, step_y_y;
    reg signed [47:0] row_x, row_y, coord_x, coord_y;
    reg signed [47:0] floor_x, floor_y;
    reg [4:0] frac_x, frac_y;
    reg [15:0] out_x, out_y;
    reg [1:0] neighbor;
    reg [17:0] sum_r, sum_g, sum_b;
    reg [17:0] product_r, product_g, product_b;
    reg [11:0] sample_x_reg, sample_y_reg;
    reg [43:0] sample_row_offset;
    reg [44:0] sample_frame_base;
    reg [10:0] sample_weight;
    reg [15:0] sample_pixel;
    reg [31:0] pending_addr;
    reg pending_upper;
    reg [3:0] cache_valid;
    reg [31:0] cache_addr [0:3];
    reg [31:0] cache_data [0:3];
    reg [1:0] cache_replace;
    integer i;

    wire [31:0] required_stride = (({16'd0,cfg_src_width} << 1)+32'd3)
                                  & 32'hfffffffc;
    wire [47:0] frame_span_product = {16'd0,src_stride} * {32'd0,src_height};
    wire [48:0] frame_end_checked = {17'd0,src_base} + {1'b0,frame_span};
    wire frame_extent_overflow = |frame_end_checked[48:33]
                              || (frame_end_checked[32] && |frame_end_checked[31:0]);
    wire invalid_size = cfg_src_width==0 || cfg_src_width>4096
                      || cfg_src_height==0 || cfg_src_height>4096
                      || cfg_dst_width==0 || cfg_dst_width>2048
                      || cfg_dst_height==0 || cfg_dst_height>2048
                      || cfg_src_stride<required_stride;
    wire invalid_alignment = |cfg_src_base[1:0] || |cfg_src_stride[1:0];

    // Explicit 48-bit signed operands preserve negative floor and avoid the
    // 32-bit overflow which appears for large affine coefficients/destinations.
    wire signed [47:0] quant_x = (coord_x + 48'sd1024) >>> 11;
    wire signed [47:0] quant_y = (coord_y + 48'sd1024) >>> 11;
    wire signed [47:0] sample_x = floor_x + (neighbor[0] ? 48'sd1 : 48'sd0);
    wire signed [47:0] sample_y = floor_y + (neighbor[1] ? 48'sd1 : 48'sd0);
    wire in_bounds = sample_x>=48'sd0 && sample_y>=48'sd0
                   && sample_x<$signed({32'd0,src_width})
                   && sample_y<$signed({32'd0,src_height});
    wire [5:0] weight_x = neighbor[0] ? {1'b0,frac_x} : 6'd32-{1'b0,frac_x};
    wire [5:0] weight_y = neighbor[1] ? {1'b0,frac_y} : 6'd32-{1'b0,frac_y};
    wire [10:0] weight = weight_x * weight_y;
    // Keep each address operation in its own clock stage.  The full products
    // and sums retain their carry bits so the final 32-bit address cannot wrap.
    wire [43:0] sample_row_product = {12'd0,src_stride} * {32'd0,sample_y_reg};
    wire [44:0] sample_frame_sum = {13'd0,src_base} + {1'b0,sample_row_offset};
    wire [44:0] sample_address_full = sample_frame_base
                              + {32'd0,sample_x_reg,1'b0};
    wire [31:0] sample_word_addr = {sample_address_full[31:2],2'b00};
    reg cache_hit;
    reg [31:0] cached_word;
    integer k;
    always @* begin
        cache_hit=1'b0;
        cached_word=32'd0;
        for (k=0;k<4;k=k+1) begin
            if (cache_valid[k] && cache_addr[k]==pending_addr) begin
                cache_hit=1'b1;
                cached_word=cache_data[k];
            end
        end
    end
    wire [15:0] cached_pixel = pending_upper ? cached_word[31:16] : cached_word[15:0];
    wire [15:0] response_pixel = pending_upper ? rd_rsp_data[31:16] : rd_rsp_data[15:0];
    function [7:0] red8;
        input [15:0] p;
        begin red8={p[15:11],p[15:13]}; end
    endfunction
    function [7:0] green8;
        input [15:0] p;
        begin green8={p[10:5],p[10:9]}; end
    endfunction
    function [7:0] blue8;
        input [15:0] p;
        begin blue8={p[4:0],p[4:2]}; end
    endfunction
    wire [7:0] rounded_r = sum_r[17:10] + {7'd0,sum_r[9]};
    wire [7:0] rounded_g = sum_g[17:10] + {7'd0,sum_g[9]};
    wire [7:0] rounded_b = sum_b[17:10] + {7'd0,sum_b[9]};
    wire [17:0] product_r_next = red8(sample_pixel) * sample_weight;
    wire [17:0] product_g_next = green8(sample_pixel) * sample_weight;
    wire [17:0] product_b_next = blue8(sample_pixel) * sample_weight;
    assign rd_req_valid = state==REQUEST;
    assign rd_req_addr = pending_addr;
    assign rd_rsp_ready = state==RESPONSE;
    assign m_axis_tvalid = state==OUTPUT;

    always @(posedge clk) begin
        if (!reset_n) begin
            state<=IDLE; busy<=0; done<=0; error_code<=0;
            src_base<=0; src_stride<=0; src_width<=0; src_height<=0;
            frame_span<=0;
            dst_width<=0; dst_height<=0;
            step_x_x<=0; step_y_x<=0; step_x_y<=0; step_y_y<=0;
            row_x<=0; row_y<=0; coord_x<=0; coord_y<=0;
            floor_x<=0; floor_y<=0; frac_x<=0; frac_y<=0;
            out_x<=0; out_y<=0; neighbor<=0;
            sum_r<=0; sum_g<=0; sum_b<=0;
            product_r<=0; product_g<=0; product_b<=0;
            sample_x_reg<=0; sample_y_reg<=0;
            sample_row_offset<=0; sample_frame_base<=0; sample_weight<=0;
            sample_pixel<=0; pending_addr<=0; pending_upper<=0;
            cache_valid<=0; cache_replace<=0;
            m_axis_tdata<=0; m_axis_tuser<=0; m_axis_tlast<=0;
            for (i=0;i<4;i=i+1) begin cache_addr[i]<=0; cache_data[i]<=0; end
        end else begin
            done<=1'b0;
            case (state)
                IDLE: if (start) begin
                    error_code<=0; cache_valid<=0; cache_replace<=0;
                    src_base<=cfg_src_base; src_stride<=cfg_src_stride;
                    src_width<=cfg_src_width; src_height<=cfg_src_height;
                    dst_width<=cfg_dst_width; dst_height<=cfg_dst_height;
                    step_x_x<={{16{cfg_a[31]}},cfg_a};
                    step_y_x<={{16{cfg_b[31]}},cfg_b};
                    step_x_y<={{16{cfg_d[31]}},cfg_d};
                    step_y_y<={{16{cfg_e[31]}},cfg_e};
                    row_x<={{16{cfg_c[31]}},cfg_c};
                    row_y<={{16{cfg_f[31]}},cfg_f};
                    coord_x<={{16{cfg_c[31]}},cfg_c};
                    coord_y<={{16{cfg_f[31]}},cfg_f};
                    out_x<=0; out_y<=0;
                    if (invalid_size) begin error_code<=1; done<=1; busy<=0; end
                    else if (invalid_alignment) begin error_code<=2; done<=1; busy<=0; end
                    else begin busy<=1; state<=FRAME_SPAN; end
                end
                FRAME_SPAN: begin
                    frame_span<=frame_span_product;
                    state<=FRAME_CHECK;
                end
                FRAME_CHECK: begin
                    if (frame_extent_overflow) begin
                        error_code<=3; done<=1; busy<=0; state<=IDLE;
                    end else state<=COORD;
                end
                COORD: begin
                    floor_x<=quant_x >>> 5; floor_y<=quant_y >>> 5;
                    frac_x<=quant_x[4:0]; frac_y<=quant_y[4:0];
                    sum_r<=0; sum_g<=0; sum_b<=0; neighbor<=0;
                    state<=PREPARE;
                end
                PREPARE: begin
                    if (error_code!=0 || !in_bounds || weight==0) begin
                        if (neighbor==3) state<=RESULT;
                        else neighbor<=neighbor+1'b1;
                    end else begin
                        // Signed bounds are checked before narrowing to 12 bits.
                        sample_x_reg<=sample_x[11:0];
                        sample_y_reg<=sample_y[11:0];
                        sample_weight<=weight;
                        state<=ADDRESS_ROW;
                    end
                end
                ADDRESS_ROW: begin
                    sample_row_offset<=sample_row_product;
                    state<=ADDRESS_BASE;
                end
                ADDRESS_BASE: begin
                    sample_frame_base<=sample_frame_sum;
                    state<=ADDRESS_PIXEL;
                end
                ADDRESS_PIXEL: begin
                    if (sample_address_full[0] || |sample_address_full[44:32]) begin
                        // Defensive guard; legal full-frame validation makes
                        // this unreachable for an in-bounds neighbor.
                        error_code<=sample_address_full[0] ? 8'd2 : 8'd3;
                        sum_r<=0; sum_g<=0; sum_b<=0;
                        state<=RESULT;
                    end else begin
                        pending_addr<=sample_word_addr;
                        pending_upper<=sample_address_full[1];
                        state<=LOOKUP;
                    end
                end
                LOOKUP: begin
                    if (cache_hit) begin
                        sample_pixel<=cached_pixel;
                        state<=MULTIPLY;
                    end else state<=REQUEST;
                end
                REQUEST: if (rd_req_ready) state<=RESPONSE;
                RESPONSE: if (rd_rsp_valid) begin
                    if (rd_rsp_error) begin
                        error_code<=4;
                        // This pixel and every not-yet-emitted pixel are black.
                        sum_r<=0; sum_g<=0; sum_b<=0;
                        state<=RESULT;
                    end else begin
                        cache_valid[cache_replace]<=1;
                        cache_addr[cache_replace]<=pending_addr;
                        cache_data[cache_replace]<=rd_rsp_data;
                        cache_replace<=cache_replace+1'b1;
                        sample_pixel<=response_pixel;
                        state<=MULTIPLY;
                    end
                end
                MULTIPLY: begin
                    product_r<=product_r_next;
                    product_g<=product_g_next;
                    product_b<=product_b_next;
                    state<=ACCUMULATE;
                end
                ACCUMULATE: begin
                    sum_r<=sum_r+product_r;
                    sum_g<=sum_g+product_g;
                    sum_b<=sum_b+product_b;
                    if (neighbor==3) state<=RESULT;
                    else begin neighbor<=neighbor+1'b1; state<=PREPARE; end
                end
                RESULT: begin
                    m_axis_tdata<=error_code!=0 ? 24'd0
                                  : {rounded_b,rounded_g,rounded_r};
                    m_axis_tuser<=out_x==0 && out_y==0;
                    m_axis_tlast<=out_x==dst_width-1'b1 && out_y==dst_height-1'b1;
                    state<=OUTPUT;
                end
                OUTPUT: if (m_axis_tready) begin
                    if (m_axis_tlast) begin busy<=0; done<=1; state<=IDLE; end
                    else begin
                        if (out_x==dst_width-1'b1) begin
                            out_x<=0; out_y<=out_y+1'b1;
                            row_x<=row_x+step_y_x; row_y<=row_y+step_y_y;
                            coord_x<=row_x+step_y_x; coord_y<=row_y+step_y_y;
                        end else begin
                            out_x<=out_x+1'b1;
                            coord_x<=coord_x+step_x_x; coord_y<=coord_y+step_x_y;
                        end
                        state<=COORD;
                    end
                end
                default: begin state<=IDLE; busy<=0; end
            endcase
        end
    end
endmodule
