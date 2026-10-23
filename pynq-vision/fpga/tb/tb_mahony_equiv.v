`timescale 1ns / 1ps
// Bit-exact equivalence against an independent parallel reference datapath for
// W5's +/-8g / +/-1000dps input contract.
// The frozen FIX_SEED=0 variant is a negative
// control: it must reproduce the original X failure at extreme acceleration.
// The two implementations may have different latency. Every output is captured
// on its own out_valid, then all sixteen quaternion bytes are compared exactly.
// No floating-point tolerance and no dependency on internal DUT state names.
// Define MAHONY_EQUIV_OLD_VS_OLD to validate the testbench before replacing RTL.
//
// Under OLD_VS_OLD both instances are the same reference module, so FIX_SEED=0
// would make DUT and REF fail identically and the comparison could never fail.
// The broken-seed negative control therefore always pins REF to FIX_SEED=1:
// the frozen old seed must diverge from the corrected one at extreme acc.
module tb_mahony_equiv;
`ifdef MAHONY_EQUIV_BROKEN_SEED
    localparam FIX_SEED = 0;
    localparam REF_FIX_SEED = 1;
`else
    localparam FIX_SEED = 1;
    localparam REF_FIX_SEED = 1;
`endif
    localparam integer N_FRAMES = 1024;
    localparam integer N_CONFIGS = 8;
    localparam integer FRAME_WATCHDOG = 2048;

    reg clk = 0, rst_n = 0, in_valid = 0;
    always #5 clk = ~clk;
    reg signed [15:0] ax = 0, ay = 0, az = 0;
    reg signed [15:0] gx = 0, gy = 0, gz = 0;
    wire [N_CONFIGS-1:0] dut_valid, ref_valid;
    wire signed [31:0] dut_w [0:N_CONFIGS-1];
    wire signed [31:0] dut_x [0:N_CONFIGS-1];
    wire signed [31:0] dut_y [0:N_CONFIGS-1];
    wire signed [31:0] dut_z [0:N_CONFIGS-1];
    wire signed [31:0] ref_w [0:N_CONFIGS-1];
    wire signed [31:0] ref_x [0:N_CONFIGS-1];
    wire signed [31:0] ref_y [0:N_CONFIGS-1];
    wire signed [31:0] ref_z [0:N_CONFIGS-1];

    function automatic signed [31:0] kp_for(input integer cfg);
        begin
            case (cfg)
                0: kp_for = 32'sh40000000; // default 1.0 / 0.05
                1: kp_for = 32'sh00000000; // pure gyro
                2: kp_for = 32'sh20000000; // proportional only, 0.5
                3: kp_for = 32'sh60000000; // 1.5 / 0.1
                4: kp_for = 32'shc0000000; // signed negative coefficients
                5: kp_for = 32'sh7fffffff; // largest positive int32
                6: kp_for = 32'sh80000000; // smallest negative int32
                7: kp_for = 32'sh00000000; // integral only
                default: kp_for = 0;
            endcase
        end
    endfunction
    function automatic signed [31:0] ki_for(input integer cfg);
        begin
            case (cfg)
                0: ki_for = 32'sh03333333;
                1, 2: ki_for = 32'sh00000000;
                3: ki_for = 32'sh06666666;
                4: ki_for = 32'shfccccccd;
                5: ki_for = 32'sh7fffffff;
                6: ki_for = 32'sh80000000;
                7: ki_for = 32'sh40000000;
                default: ki_for = 0;
            endcase
        end
    endfunction

    genvar g;
    generate for (g = 0; g < N_CONFIGS; g = g + 1) begin : cfg
        // Explicit constant expressions retain compatibility with Verilog-2005
        // simulators that do not elaborate automatic constant functions.
        localparam signed [31:0] CFG_KP =
            (g == 0) ? 32'sh40000000 : (g == 1) ? 32'sh00000000 :
            (g == 2) ? 32'sh20000000 : (g == 3) ? 32'sh60000000 :
            (g == 4) ? 32'shc0000000 : (g == 5) ? 32'sh7fffffff :
            (g == 6) ? 32'sh80000000 : 32'sh00000000;
        localparam signed [31:0] CFG_KI =
            (g == 0) ? 32'sh03333333 : (g == 1 || g == 2) ? 32'sh00000000 :
            (g == 3) ? 32'sh06666666 : (g == 4) ? 32'shfccccccd :
            (g == 5) ? 32'sh7fffffff : (g == 6) ? 32'sh80000000 :
            32'sh40000000;
`ifdef MAHONY_EQUIV_OLD_VS_OLD
        mahony_pe_reference #(.KP(CFG_KP), .KI(CFG_KI), .FIX_SEED(FIX_SEED)) dut (
`else
        mahony_pe #(.KP(CFG_KP), .KI(CFG_KI)) dut (
`endif
            .clk(clk), .rst_n(rst_n), .in_valid(in_valid),
            .ax(ax), .ay(ay), .az(az), .gx(gx), .gy(gy), .gz(gz),
            .out_valid(dut_valid[g]), .qw(dut_w[g]), .qx(dut_x[g]),
            .qy(dut_y[g]), .qz(dut_z[g])
        );
        mahony_pe_reference #(.KP(CFG_KP), .KI(CFG_KI), .FIX_SEED(REF_FIX_SEED)) reference (
            .clk(clk), .rst_n(rst_n), .in_valid(in_valid),
            .ax(ax), .ay(ay), .az(az), .gx(gx), .gy(gy), .gz(gz),
            .out_valid(ref_valid[g]), .qw(ref_w[g]), .qx(ref_x[g]),
            .qy(ref_y[g]), .qz(ref_z[g])
        );
    end endgenerate

    integer frame_id = -1, compared_frames = 0, byte_comparisons = 0;
    integer reset_count = 0, aborted_frames = 0;
    integer config_id, ticks;
    integer acc_coverage [0:63];
    integer gyro_coverage [0:7];
    integer max_dut_ticks [0:N_CONFIGS-1];
    integer max_ref_ticks [0:N_CONFIGS-1];
    integer dut_outputs [0:N_CONFIGS-1];
    integer ref_outputs [0:N_CONFIGS-1];
    reg [N_CONFIGS-1:0] dut_seen, ref_seen;
    reg [127:0] got_dut [0:N_CONFIGS-1];
    reg [127:0] got_ref [0:N_CONFIGS-1];
    reg signed [15:0] sent_ax, sent_ay, sent_az, sent_gx, sent_gy, sent_gz;
    reg [31:0] prng = 32'h7b4d91e3;

    task automatic fail(input [1023:0] reason, input integer bad_cfg);
        begin
            $display("TEST FAILED: %0s frame=%0d cfg=%0d ticks=%0d time=%0t",
                     reason, frame_id, bad_cfg, ticks, $time);
            $display("  sent acc=(%0d,%0d,%0d) gyro=(%0d,%0d,%0d)",
                     sent_ax, sent_ay, sent_az, sent_gx, sent_gy, sent_gz);
            $display("  input hex=%04x %04x %04x %04x %04x %04x",
                     sent_ax, sent_ay, sent_az, sent_gx, sent_gy, sent_gz);
            if (bad_cfg >= 0 && bad_cfg < N_CONFIGS) begin
                $display("  KP=%08x KI=%08x dut_seen=%b ref_seen=%b",
                         kp_for(bad_cfg), ki_for(bad_cfg),
                         dut_seen[bad_cfg], ref_seen[bad_cfg]);
                $display("  DUT=%032x REF=%032x",
                         got_dut[bad_cfg], got_ref[bad_cfg]);
            end
            $finish;
        end
    endtask

    task automatic random_next;
        begin
            prng = prng ^ (prng << 13);
            prng = prng ^ (prng >> 17);
            prng = prng ^ (prng << 5);
        end
    endtask

    task automatic drive_sample(input integer number);
        integer acc_mode, gyro_mode;
        begin
            acc_mode = number % 64;
            // Each fixed acceleration case crosses several gyro patterns over
            // the uninterrupted stateful sequence, rather than one fixed pair.
            gyro_mode = (number / 64 + number) % 8;
            ax = 0; ay = 0; az = 0;
            case (acc_mode)
                0: begin ax = 0; ay = 0; az = 0; end
                1: begin ax = 1; ay = -1; az = 2; end
                // Physical accel gate is strictly norm^2 > (0.5g)^2;
                // 2048 raw counts is exactly 0.5g at 4096 LSB/g.
                2: ax = 2047;
                3: ax = 2048;
                4: ax = 2049;
                5: ax = -2048;
                6: ax = -2047;
                7: ax = -2049;
                8: ay = 2048;
                9: az = 2048;
                10: ay = 2047;
                11: az = 2049;
                12: begin ax = 2048; ay = 1; end
                13: begin ax = 2048; ay = -1; end
                14: begin ax = 1448; ay = 1448; end
                15: begin ax = 1449; ay = 1449; end
                16: ax = 4096;
                17: ax = -4096;
                18: ay = 4096;
                19: ay = -4096;
                20: az = 4096;
                21: az = -4096;
                22: begin ax = 2896; ay = 2896; end
                23: begin ax = -2896; ay = 2896; end
                24: begin ax = 2896; az = -2896; end
                25: begin ax = -2896; az = -2896; end
                26: begin ay = 2896; az = 2896; end
                27: begin ay = -2896; az = 2896; end
                28: begin ax = 2365; ay = 2365; az = 2365; end
                29: begin ax = -2365; ay = 2365; az = -2365; end
                30: begin ax = 2365; ay = -2365; az = -2365; end
                31: begin ax = -2365; ay = -2365; az = 2365; end
                32: begin ax = 32767; ay = -32768; az = 1; end
                33: begin ax = -32768; ay = -32768; az = -32768; end
                34: begin ax = 32767; ay = 32767; az = 32767; end
                35: ax = 32767;
                36: ax = -32768;
                37: ay = -32768;
                38: az = -32768;
                39: begin ax = -32768; ay = 32767; az = -32768; end
                40: begin ax = 256; ay = -256; az = 4064; end
                41: begin ax = -512; ay = 512; az = 4032; end
                42: begin ax = 1024; ay = -1024; az = 3840; end
                43: begin ax = -1536; ay = 1536; az = 3456; end
                44: begin ax = 2048; ay = -2048; az = 2896; end
                45: begin ax = -2896; ay = 2048; az = 2048; end
                46: begin ax = 3072; ay = -1024; az = -2560; end
                47: begin ax = -3584; ay = 1536; az = -1024; end
                default: begin
                    random_next(); ax = prng[15:0];
                    random_next(); ay = prng[15:0];
                    random_next(); az = prng[15:0];
                end
            endcase
            case (gyro_mode)
                0: begin gx = 0; gy = 0; gz = 0; end
                1: begin gx = 1; gy = -1; gz = 1; end
                2: begin gx = -1; gy = 1; gz = -1; end
                3: begin gx = 1640; gy = -3280; gz = 4920; end // +50,-100,+150 dps
                4: begin gx = -6560; gy = 3280; gz = -1640; end // -200,+100,-50 dps
                5: begin gx = 32767; gy = -32768; gz = 32767; end
                6: begin gx = -32768; gy = 32767; gz = -32768; end
                7: begin
                    random_next(); gx = prng[15:0];
                    random_next(); gy = prng[15:0];
                    random_next(); gz = prng[15:0];
                end
            endcase
            acc_coverage[acc_mode] = acc_coverage[acc_mode] + 1;
            gyro_coverage[gyro_mode] = gyro_coverage[gyro_mode] + 1;
            sent_ax = ax; sent_ay = ay; sent_az = az;
            sent_gx = gx; sent_gy = gy; sent_gz = gz;
        end
    endtask

    task automatic idle_guard(input integer cycles);
        integer n, c;
        begin
            for (n = 0; n < cycles; n = n + 1) begin
                @(negedge clk);
                for (c = 0; c < N_CONFIGS; c = c + 1)
                    if (dut_valid[c] !== 1'b0 || ref_valid[c] !== 1'b0)
                        fail("unsolicited output or out_valid wider than one cycle", c);
            end
        end
    endtask

    task automatic reset_both;
        integer c;
        begin
            @(negedge clk); rst_n = 0; in_valid = 0;
            repeat (3) @(negedge clk);
            for (c = 0; c < N_CONFIGS; c = c + 1) begin
                if ({dut_w[c], dut_x[c], dut_y[c], dut_z[c]} !==
                    {32'h20000000, 96'd0} ||
                    {ref_w[c], ref_x[c], ref_y[c], ref_z[c]} !==
                    {32'h20000000, 96'd0})
                    fail("reset did not restore identity quaternion", c);
                if (dut_valid[c] !== 1'b0 || ref_valid[c] !== 1'b0)
                    fail("out_valid asserted during reset", c);
            end
            rst_n = 1;
            reset_count = reset_count + 1;
            idle_guard(3);
        end
    endtask

    task automatic abort_and_reset;
        begin
            // Reset an accepted frame before either core can complete it.
            // Wait a full watchdog interval without input after reset, so an
            // uncancelled transaction cannot hide behind the next valid frame.
            @(negedge clk);
            ax = 2896; ay = -2896; az = 1;
            gx = -32768; gy = 32767; gz = 3280; in_valid = 1;
            @(negedge clk); in_valid = 0;
            repeat (5) @(negedge clk);
            aborted_frames = aborted_frames + 1;
            reset_both();
            idle_guard(FRAME_WATCHDOG);
        end
    endtask

    task automatic compare_one_frame;
        integer c, b;
        reg [127:0] sampled;
        begin
            dut_seen = 0; ref_seen = 0; ticks = 0;
            for (c = 0; c < N_CONFIGS; c = c + 1) begin
                got_dut[c] = 0; got_ref[c] = 0;
            end
            @(negedge clk); drive_sample(frame_id); in_valid = 1;
            @(negedge clk); in_valid = 0;
            // Change every external data port immediately after acceptance.
            // Both kernels must use the latched sample throughout processing.
            ax = ~sent_ax; ay = ~sent_ay; az = ~sent_az;
            gx = ~sent_gx; gy = ~sent_gy; gz = ~sent_gz;
            while (dut_seen != {N_CONFIGS{1'b1}} ||
                   ref_seen != {N_CONFIGS{1'b1}}) begin
                @(negedge clk); ticks = ticks + 1;
                for (c = 0; c < N_CONFIGS; c = c + 1) begin
                    if (dut_valid[c] === 1'b1) begin
                        if (dut_seen[c]) fail("duplicate DUT output", c);
                        sampled = {dut_w[c], dut_x[c], dut_y[c], dut_z[c]};
                        got_dut[c] = sampled;
                        if ((^sampled) === 1'bx) fail("DUT quaternion contains X/Z", c);
                        dut_seen[c] = 1;
                        dut_outputs[c] = dut_outputs[c] + 1;
                        if (ticks > max_dut_ticks[c]) max_dut_ticks[c] = ticks;
                    end else if (dut_valid[c] !== 1'b0)
                        fail("DUT out_valid contains X/Z", c);
                    if (ref_valid[c] === 1'b1) begin
                        if (ref_seen[c]) fail("duplicate reference output", c);
                        sampled = {ref_w[c], ref_x[c], ref_y[c], ref_z[c]};
                        got_ref[c] = sampled;
                        if ((^sampled) === 1'bx) fail("reference quaternion contains X/Z", c);
                        ref_seen[c] = 1;
                        ref_outputs[c] = ref_outputs[c] + 1;
                        if (ticks > max_ref_ticks[c]) max_ref_ticks[c] = ticks;
                    end else if (ref_valid[c] !== 1'b0)
                        fail("reference out_valid contains X/Z", c);
                end
                if (ticks >= FRAME_WATCHDOG) begin
                    for (c = 0; c < N_CONFIGS; c = c + 1)
                        if (!dut_seen[c] || !ref_seen[c])
                            fail("watchdog: missing output", c);
                end
            end
            for (c = 0; c < N_CONFIGS; c = c + 1) begin
                for (b = 0; b < 16; b = b + 1) begin
                    if (got_dut[c][127 - b*8 -: 8] !==
                        got_ref[c][127 - b*8 -: 8]) begin
                        $display("  first differing byte=%0d component=%0d DUT=%02x REF=%02x",
                                 b, b / 4, got_dut[c][127 - b*8 -: 8],
                                 got_ref[c][127 - b*8 -: 8]);
                        fail("quaternion byte mismatch", c);
                    end
                    byte_comparisons = byte_comparisons + 1;
                end
            end
            compared_frames = compared_frames + 1;
            // Zero extra gap exercises successive stateful updates. A few
            // varying gaps also check that idle time does not change state.
            idle_guard(1 + (frame_id % 4 == 0 ? frame_id % 7 : 0));
        end
    endtask

    initial begin
        for (config_id = 0; config_id < N_CONFIGS; config_id = config_id + 1) begin
            max_dut_ticks[config_id] = 0; max_ref_ticks[config_id] = 0;
            dut_outputs[config_id] = 0; ref_outputs[config_id] = 0;
            got_dut[config_id] = 0; got_ref[config_id] = 0;
        end
        for (config_id = 0; config_id < 64; config_id = config_id + 1)
            acc_coverage[config_id] = 0;
        for (config_id = 0; config_id < 8; config_id = config_id + 1)
            gyro_coverage[config_id] = 0;
        reset_both();
        for (frame_id = 0; frame_id < N_FRAMES; frame_id = frame_id + 1) begin
            if (frame_id == 256 || frame_id == 768) reset_both();
            if (frame_id == 512) abort_and_reset();
            compare_one_frame();
            if ((frame_id + 1) % 256 == 0)
                $display("equivalence progress: %0d/%0d frames, %0d byte comparisons",
                         frame_id + 1, N_FRAMES, byte_comparisons);
        end
        idle_guard(FRAME_WATCHDOG);
        for (config_id = 0; config_id < 64; config_id = config_id + 1)
            if (acc_coverage[config_id] != N_FRAMES / 64)
                fail("acceleration coverage incomplete", -1);
        for (config_id = 0; config_id < 8; config_id = config_id + 1)
            if (gyro_coverage[config_id] == 0)
                fail("gyro coverage incomplete", -1);
        for (config_id = 0; config_id < N_CONFIGS; config_id = config_id + 1) begin
            if (dut_outputs[config_id] != N_FRAMES ||
                ref_outputs[config_id] != N_FRAMES)
                fail("per-configuration output count mismatch", config_id);
            $display("config %0d: KP=%08x KI=%08x compared=%0d max_wait_dut=%0d max_wait_ref=%0d",
                     config_id, kp_for(config_id), ki_for(config_id),
                     dut_outputs[config_id], max_dut_ticks[config_id],
                     max_ref_ticks[config_id]);
        end
        $display("coverage: 64 acceleration cases x %0d, 8 gyro patterns, reset_count=%0d aborted=%0d",
                 N_FRAMES / 64, reset_count, aborted_frames);
        $display("TEST PASSED: %0d stateful frames x %0d KP/KI configs, %0d exact quaternion bytes",
                 compared_frames, N_CONFIGS, byte_comparisons);
        $finish;
    end



    initial begin
        // Independent global watchdog also covers reset and harness deadlocks.
        #(10 * (N_FRAMES + 10) * (FRAME_WATCHDOG + 20));
        fail("global watchdog", -1);
    end
endmodule
