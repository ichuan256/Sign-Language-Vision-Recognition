// Mahony fixed-point PE: one registered multiplier reused by a micro-FSM.
// Operation order, truncation points and PI update sequence are retained while
// internal units are adapted to the W5 sensor range. Outputs commit with
// out_valid. 100 Hz inputs allow
// the longer computation (about 240 clocks); never issue while a frame is busy.
// W5 input is MPU6500 +/-8g / +/-1000 dps (4096 / 32.8 LSB per unit).
`timescale 1ns/1ps
module mahony_pe #(
    parameter signed [31:0] KP = 32'h4000_0000,
    parameter signed [31:0] KI = 32'h0333_3333
)(
    input wire clk, rst_n, in_valid,
    input wire signed [15:0] ax, ay, az, gx, gy, gz,
    output reg out_valid,
    output reg signed [31:0] qw, qx, qy, qz
);
    // Raw gyro -> rad/s in signed32 * 2^26. +/-1000 dps fits +/-32 rad/s;
    // the former 2^27 representation would wrap near the new full scale.
    localparam signed [31:0] GYR_GAIN = 32'sd35709; // round(pi/(180*32.8)*2^26)
    localparam signed [31:0] DT_MUL = 32'sd335544;
    localparam signed [31:0] HDT_MUL = 32'sd167772;
    reg running;
    reg [6:0] op;
    reg [1:0] phase;
    reg [2:0] nr_cnt;
    reg norm_q, acc_ok;
    reg [4:0] acc_lshift;
    // Input normalization is deliberately staged.  The raw sample is first
    // registered, then its magnitude/shift is derived over two idle cycles;
    // this keeps the high-fanout max/priority logic out of the AXI-to-PE
    // capture path while preserving the exact normalized vector.
    reg signed [15:0] raw_ax, raw_ay, raw_az;
    reg [16:0] acc_max_reg;
    reg signed [31:0] a[0:2], w[0:2], e[0:2], graw[0:2];
    reg signed [31:0] q[0:3], qn[0:3], v[0:2], err[0:2];
    reg signed [31:0] sum32, tmp32, sumsq, isq;
    reg signed [63:0] sum64, dq;
    reg signed [63:0] operand_a, mul_a;
    reg signed [31:0] operand_b, mul_b;
    (* use_dsp = "yes" *) reg signed [63:0] mul_p;
    wire signed [31:0] term29 = mul_p >>> 29;
    wire signed [31:0] next_sum32 = sum32 + term29;
    wire signed [31:0] nr_value = term29 >>> 1;
    integer i;

    // Apply one shared power-of-two scale to all three acceleration axes.
    // abs(-32768) needs 17 bits. Scaling the largest component into [0.5, 1)
    // keeps the 32-bit Q2.29 square sum bounded by 3 without changing direction.
    wire signed [16:0] ax_ext = {raw_ax[15], raw_ax};
    wire signed [16:0] ay_ext = {raw_ay[15], raw_ay};
    wire signed [16:0] az_ext = {raw_az[15], raw_az};
    wire [16:0] abs_ax = ax_ext[16] ? -ax_ext : ax_ext;
    wire [16:0] abs_ay = ay_ext[16] ? -ay_ext : ay_ext;
    wire [16:0] abs_az = az_ext[16] ? -az_ext : az_ext;
    wire [16:0] acc_max = (abs_ax > abs_ay) ?
                          ((abs_ax > abs_az) ? abs_ax : abs_az) :
                          ((abs_ay > abs_az) ? abs_ay : abs_az);
    function automatic [4:0] scale_for_acc_max(input [16:0] magnitude);
        integer bit_index;
        begin
            if (magnitude == 0) scale_for_acc_max = 5'd31;
            else begin
                scale_for_acc_max = 0;
                for (bit_index = 0; bit_index <= 16; bit_index = bit_index + 1)
                    if (magnitude[bit_index])
                        scale_for_acc_max = 5'd28 - bit_index;
            end
        end
    endfunction
    // MPU6500 +/-8g is 4096 LSB/g. `a` is scale-normalized, so its raw norm
    // must be compared to the physical 0.5g gate using the recorded exponent.
    // For shift k=28-p (p is the largest raw axis's top bit), the encoded
    // 0.5g threshold is 2^(49-2p) = 2^(2k-7). p<10 cannot pass; p>=12 always
    // passes; p=10 or 11 requires comparing the scaled square sum.
    function automatic acc_magnitude_valid(
        input signed [31:0] norm_squared,
        input [4:0] scale_shift
    );
        integer threshold_shift;
        begin
            if (scale_shift == 5'd31 || scale_shift > 5'd18)
                acc_magnitude_valid = 0;
            else if (scale_shift <= 5'd16)
                acc_magnitude_valid = 1;
            else begin
                threshold_shift = (2 * scale_shift) - 7;
                acc_magnitude_valid = norm_squared > (32'sd1 <<< threshold_shift);
            end
        end
    endfunction

    // Explicit exponents avoid unsigned (29-p) underflow for p=30/31.
    // These are 29+floor((29-p)/2); p=27 is clamped to avoid y*y overflow.
    function automatic signed [31:0] isq_seed(input signed [31:0] x);
        integer j; reg [5:0] p;
        begin
            p = 6'd27;
            for (j = 27; j <= 31; j = j + 1)
                if (x[j]) p = j[5:0];
            if (p == 6'd27) isq_seed = 32'sh3FFF_FFFF;
            else if (p >= 6'd30) isq_seed = 32'sd1 <<< 28;
            else isq_seed = 32'sd1 <<< 29;
        end
    endfunction

    // A is 64 bits only for the derivative/time-scale product; B is always 32.
    // The product remains 64 bits, exactly like the original intermediate regs.
    always @(*) begin
        operand_a = 0; operand_b = 0;
        case (op)
            0,1,2: begin operand_a=graw[op]; operand_b=GYR_GAIN; end
            3,4,5: begin operand_a=a[op-3]; operand_b=a[op-3]; end
            7: begin operand_a=isq; operand_b=isq; end
            8: begin operand_a=sumsq; operand_b=tmp32; end
            9: begin operand_a=isq; operand_b=(32'sd3 <<< 29)-tmp32; end
            10,11,12: begin operand_a=a[op-10]; operand_b=isq; end
            13: begin operand_a=q[1]; operand_b=q[3]; end
            14: begin operand_a=q[0]; operand_b=q[2]; end
            15: begin operand_a=q[0]; operand_b=q[1]; end
            16: begin operand_a=q[2]; operand_b=q[3]; end
            17,18,19,20: begin operand_a=q[op-17]; operand_b=q[op-17]; end
            21: begin operand_a=a[1]; operand_b=v[2]; end
            22: begin operand_a=a[2]; operand_b=v[1]; end
            23: begin operand_a=a[2]; operand_b=v[0]; end
            24: begin operand_a=a[0]; operand_b=v[2]; end
            25: begin operand_a=a[0]; operand_b=v[1]; end
            26: begin operand_a=a[1]; operand_b=v[0]; end
            27,28,29: begin operand_a=err[op-27]; operand_b=DT_MUL; end
            30,32,34: begin operand_a=err[(op-30)>>1]; operand_b=KP; end
            31,33,35: begin operand_a=e[(op-31)>>1]; operand_b=KI; end
            36: begin operand_a=q[1]; operand_b=w[0]; end
            37: begin operand_a=q[2]; operand_b=w[1]; end
            38: begin operand_a=q[3]; operand_b=w[2]; end
            40: begin operand_a=q[0]; operand_b=w[0]; end
            41: begin operand_a=q[2]; operand_b=w[2]; end
            42: begin operand_a=q[3]; operand_b=w[1]; end
            44: begin operand_a=q[0]; operand_b=w[1]; end
            45: begin operand_a=q[1]; operand_b=w[2]; end
            46: begin operand_a=q[3]; operand_b=w[0]; end
            48: begin operand_a=q[0]; operand_b=w[2]; end
            49: begin operand_a=q[1]; operand_b=w[1]; end
            50: begin operand_a=q[2]; operand_b=w[0]; end
            39,43,47,51: begin operand_a=dq; operand_b=HDT_MUL; end
            52,53,54,55: begin operand_a=qn[op-52]; operand_b=qn[op-52]; end
            56,57,58,59: begin operand_a=qn[op-56]; operand_b=isq; end
            default: begin operand_a=0; operand_b=0; end
        endcase
    end

    // These datapath regs need no reset: every retire follows a fresh issue and
    // multiply. Clocked operand/product regs let Vivado use DSP pipeline regs.
    always @(posedge clk) begin
        if (running && phase == 0 && op != 6 && op != 60 && op < 61) begin
            mul_a <= operand_a; mul_b <= operand_b;
        end
        if (running && phase == 1) mul_p <= mul_a * mul_b;
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            running<=0; op<=0; phase<=0; out_valid<=0;
            norm_q<=0; acc_ok<=0; nr_cnt<=0;
            sum32<=0; tmp32<=0; sumsq<=0; isq<=0; sum64<=0; dq<=0;
            acc_lshift<=5'd31;
            raw_ax<=0; raw_ay<=0; raw_az<=0; acc_max_reg<=0;
            qw<=32'sd1 <<< 29; qx<=0; qy<=0; qz<=0;
            for (i=0;i<3;i=i+1) begin
                a[i]<=0; w[i]<=0; e[i]<=0; graw[i]<=0;
                v[i]<=0; err[i]<=0;
            end
            q[0]<=32'sd1 <<< 29; q[1]<=0; q[2]<=0; q[3]<=0;
            for (i=0;i<4;i=i+1) qn[i]<=0;
        end else begin
            out_valid<=0;
            if (!running) begin
                if (in_valid) begin
                    raw_ax<=ax; raw_ay<=ay; raw_az<=az;
                    graw[0]<=gx; graw[1]<=gy; graw[2]<=gz;
                    norm_q<=0; running<=1; op<=61; phase<=0;
                end
            end else if (phase == 0) begin
                if (op == 6) begin
                    isq<=isq_seed(sumsq); nr_cnt<=0; op<=7;
                end else if (op == 61) begin
                    acc_max_reg <= acc_max;
                    op <= 62;
                end else if (op == 62) begin
                    acc_lshift <= scale_for_acc_max(acc_max_reg);
                    op <= 63;
                end else if (op == 63) begin
                    a[0] <= $signed({{16{raw_ax[15]}}, raw_ax}) <<< acc_lshift;
                    a[1] <= $signed({{16{raw_ay[15]}}, raw_ay}) <<< acc_lshift;
                    a[2] <= $signed({{16{raw_az[15]}}, raw_az}) <<< acc_lshift;
                    op <= 0;
                end else if (op == 60) begin
                    qw<=q[0]; qx<=q[1]; qy<=q[2]; qz<=q[3];
                    out_valid<=1; running<=0;
                end else phase<=1;
            end else if (phase == 1) phase<=2;
            else begin
                phase<=0; op<=op+1;
                case (op)
                    0,1,2: w[op]<=mul_p;
                    3,17,52: sum32<=term29;
                    4,53,54: sum32<=next_sum32;
                    5: begin
                        sumsq <= next_sum32;
                        acc_ok <= acc_magnitude_valid(next_sum32, acc_lshift);
                        if (acc_lshift == 5'd31) op <= 36; // no gravity vector
                    end
                    7,8: tmp32<=term29;
                    9: begin
                        isq<=nr_value > 0 ? nr_value : (isq >>> 1);
                        if (nr_cnt == 3) op<=norm_q ? 56 : 10;
                        else begin nr_cnt<=nr_cnt+1; op<=7; end
                    end
                    10,11,12: a[op-10]<=term29;
                    13,15,21,23,25: tmp32<=term29;
                    14: v[0]<=(tmp32-term29) <<< 1;
                    16: v[1]<=(tmp32+term29) <<< 1;
                    18,19: sum32<=sum32-term29;
                    20: v[2]<=next_sum32;
                    22: err[0]<=tmp32-term29;
                    24: err[1]<=tmp32-term29;
                    26: begin err[2]<=tmp32-term29; if (!acc_ok) op<=36; end
                    27,28,29: e[op-27]<=e[op-27]+(mul_p >>> 28);
                    30,32,34: tmp32<=mul_p >>> 33;
                    31,33,35: w[(op-31)>>1]<=w[(op-31)>>1]+tmp32+(mul_p >>> 30);
                    36: sum64<=-mul_p;
                    37,45: sum64<=sum64-mul_p;
                    38,42,50: dq<=(sum64-mul_p) >>> 26;
                    40,44,48: sum64<=mul_p;
                    41,49: sum64<=sum64+mul_p;
                    46: dq<=(sum64+mul_p) >>> 26;
                    39,43,47,51: qn[(op-39)>>2]<=q[(op-39)>>2]+(mul_p >>> 25);
                    55: begin sumsq<=next_sum32; norm_q<=1; op<=6; end
                    56,57,58,59: q[op-56]<=term29;
                    default: begin end
                endcase
            end
        end
    end
endmodule
