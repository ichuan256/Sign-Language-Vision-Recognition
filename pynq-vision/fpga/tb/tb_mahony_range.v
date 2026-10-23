`timescale 1ns/1ps

// Independent physical-unit checks for the W5 +/-8g / +/-1000dps contract.
// Expected motion is computed from MPU scaling and quaternion geometry, not
// from the DUT's internal fixed-point state or a mirrored arithmetic model.
module tb_mahony_range;
    localparam integer Q = 536870912;
    localparam real PI = 3.14159265358979323846;
    localparam integer MAX_WAIT = 2048;

    reg clk = 0, rst_n = 0, in_valid = 0;
    always #5 clk = ~clk;
    reg signed [15:0] ax = 0, ay = 0, az = 0;
    reg signed [15:0] gx = 0, gy = 0, gz = 0;
    wire out_valid;
    wire signed [31:0] qw, qx, qy, qz;

    mahony_pe dut (
        .clk(clk), .rst_n(rst_n), .in_valid(in_valid),
        .ax(ax), .ay(ay), .az(az), .gx(gx), .gy(gy), .gz(gz),
        .out_valid(out_valid), .qw(qw), .qx(qx), .qy(qy), .qz(qz)
    );

    integer cases = 0, samples = 0, errors = 0, timeout, i;
    integer acceleration_cases = 0, gyro_cases = 0;
    real max_angle_error_deg = 0.0;
    real max_discrete_lag_deg = 0.0;

    task fail(input [1023:0] reason);
        begin
            errors = errors + 1;
            $display("TEST FAILED: %0s at case=%0d raw=(%0d,%0d,%0d;%0d,%0d,%0d)",
                     reason, cases, ax, ay, az, gx, gy, gz);
            $finish;
        end
    endtask

    task reset_core;
        begin
            @(negedge clk);
            rst_n = 0;
            in_valid = 0;
            repeat (3) @(negedge clk);
            rst_n = 1;
            repeat (2) @(negedge clk);
        end
    endtask

    task sample_once;
        begin
            @(negedge clk);
            in_valid = 1;
            @(negedge clk);
            in_valid = 0;
            timeout = 0;
            while (out_valid !== 1'b1 && timeout < MAX_WAIT) begin
                @(negedge clk);
                timeout = timeout + 1;
            end
            if (timeout >= MAX_WAIT) fail("bounded output wait expired");
            if ((^{qw,qx,qy,qz}) === 1'bx) fail("quaternion contains X/Z");
            samples = samples + 1;
        end
    endtask

    task observed_quaternion(output real ow, ox, oy, oz);
        begin
            ow = $itor(qw) / Q;
            ox = $itor(qx) / Q;
            oy = $itor(qy) / Q;
            oz = $itor(qz) / Q;
        end
    endtask

    task check_expected(
        input real ew, ex, ey, ez,
        input real tolerance_deg,
        input [1023:0] label
    );
        real ow, ox, oy, oz, dotp, norm;
        real angle_error, expected_norm;
        begin
            observed_quaternion(ow, ox, oy, oz);
            norm = $sqrt(ow*ow + ox*ox + oy*oy + oz*oz);
            expected_norm = $sqrt(ew*ew + ex*ex + ey*ey + ez*ez);
            if (norm < 0.98 || norm > 1.02) fail("quaternion norm outside 2% band");
            if (expected_norm < 0.999 || expected_norm > 1.001)
                fail("testbench expected quaternion is not normalized");
            dotp = (ow*ew + ox*ex + oy*ey + oz*ez) / (norm*expected_norm);
            if (dotp < 0.0) dotp = -dotp; // q and -q represent the same pose.
            if (dotp > 1.0) dotp = 1.0;
            angle_error = 2.0 * $acos(dotp) * 180.0 / PI;
            if (angle_error > max_angle_error_deg) max_angle_error_deg = angle_error;
            if (angle_error > tolerance_deg) begin
                $display("physical mismatch %0s: angle_error=%0.6f deg tol=%0.3f",
                         label, angle_error, tolerance_deg);
                $display("  observed=(%0.8f,%0.8f,%0.8f,%0.8f)",
                         ow, ox, oy, oz);
                $display("  expected=(%0.8f,%0.8f,%0.8f,%0.8f)",
                         ew, ex, ey, ez);
                fail("physical quaternion outside angular tolerance");
            end
            cases = cases + 1;
        end
    endtask

    task run_gyro_case(
        input integer rx, ry, rz, input integer count,
        input [1023:0] label
    );
        real wx, wy, wz, speed, axisx, axisy, axisz, angle_step, angle;
        real ew, ex, ey, ez, discrete_lag;
        begin
            reset_core();
            ax = 0; ay = 0; az = 0;
            gx = rx; gy = ry; gz = rz;
            wx = (rx / 32.8) * PI / 180.0;
            wy = (ry / 32.8) * PI / 180.0;
            wz = (rz / 32.8) * PI / 180.0;
            speed = $sqrt(wx*wx + wy*wy + wz*wz);
            for (i = 0; i < count; i = i + 1) sample_once();
            if (speed == 0.0) begin
                ew = 1.0; ex = 0.0; ey = 0.0; ez = 0.0;
            end else begin
                axisx = wx / speed; axisy = wy / speed; axisz = wz / speed;
                // Exact normalized-Euler rotation for constant angular rate:
                // each 10ms update rotates by 2*atan(|omega|*dt/2).
                angle_step = 2.0 * $atan(speed * 0.005);
                angle = count * angle_step;
                discrete_lag = (count * speed * 0.01 - angle) * 180.0 / PI;
                if (discrete_lag > max_discrete_lag_deg)
                    max_discrete_lag_deg = discrete_lag;
                ew = $cos(angle / 2.0);
                ex = axisx * $sin(angle / 2.0);
                ey = axisy * $sin(angle / 2.0);
                ez = axisz * $sin(angle / 2.0);
            end
            check_expected(ew, ex, ey, ez, 0.05, label);
            gyro_cases = gyro_cases + 1;
            $display("gyro %0s raw=(%0d,%0d,%0d), physical=(%0.2f,%0.2f,%0.2f) dps, steps=%0d Euler-lag=%0.4f deg PASS",
                     label, rx, ry, rz, rx/32.8, ry/32.8, rz/32.8, count, discrete_lag);
        end
    endtask

    task run_tilt_case(
        input integer rx, ry, rz, input integer count,
        input [1023:0] label, output [127:0] final_quat
    );
        real norm_raw, tx, ty, tz, axisx, axisy, axisz, transverse;
        real target_angle, theta, err, integral, omega, step_angle;
        real ew, ex, ey, ez, snorm;
        begin
            reset_core();
            ax = rx; ay = ry; az = rz;
            gx = 0; gy = 0; gz = 0;
            // Promote before multiplying: three int16 squares can overflow
            // a signed 32-bit Verilog integer even though the true norm fits.
            norm_raw = $sqrt(rx*1.0*rx + ry*1.0*ry + rz*1.0*rz);
            if (norm_raw == 0.0) begin
                tx = 0.0; ty = 0.0; tz = 1.0;
            end else begin
                tx = rx/norm_raw; ty = ry/norm_raw; tz = rz/norm_raw;
            end
            transverse = $sqrt(tx*tx + ty*ty);
            if (transverse == 0.0) begin
                axisx = 1.0; axisy = 0.0; target_angle = 0.0;
            end else begin
                axisx = ty/transverse;
                axisy = -tx/transverse;
                target_angle = $acos(tz);
            end
            theta = 0.0; integral = 0.0;
            if (norm_raw > 2048.0) begin
                for (i = 0; i < count; i = i + 1) begin
                    err = $sin(target_angle - theta);
                    integral = integral + err * 0.01;
                    omega = err + 0.05 * integral;
                    step_angle = 2.0 * $atan(omega * 0.005);
                    theta = theta + step_angle;
                    sample_once();
                end
            end else begin
                for (i = 0; i < count; i = i + 1) sample_once();
            end
            ew = $cos(theta/2.0);
            ex = axisx * $sin(theta/2.0);
            ey = axisy * $sin(theta/2.0);
            ez = 0.0;
            check_expected(ew, ex, ey, ez, 0.05, label);
            final_quat = {qw,qx,qy,qz};
            snorm = norm_raw/4096.0;
            acceleration_cases = acceleration_cases + 1;
            $display("tilt %0s raw=(%0d,%0d,%0d), |a|=%0.4f g, expected tilt=%0.2f deg, steps=%0d PASS",
                     label, rx, ry, rz, snorm, theta*180.0/PI, count);
        end
    endtask

    reg [127:0] q_scale_1, q_scale_2, q_scale_4, q_scale_8;
    reg [127:0] q_zero;
    initial begin
        reset_core();

        // 1g rest and zero acceleration both leave identity unchanged.
        run_tilt_case(0,0,4096,32,"1g-rest",q_zero);
        if (q_zero !== {32'h20000000,96'd0}) fail("1g rest was not identity");
        run_tilt_case(0,0,0,32,"zero-acceleration",q_zero);
        if (q_zero !== {32'h20000000,96'd0}) fail("zero acceleration was not skipped");

        // Values immediately below, exactly at and above the strict 0.5g gate.
        run_tilt_case(2047,0,0,48,"gate-2047",q_zero);
        if (q_zero !== {32'h20000000,96'd0}) fail("below-threshold gravity was used");
        run_tilt_case(2048,0,0,48,"gate-2048",q_zero);
        if (q_zero !== {32'h20000000,96'd0}) fail("threshold gravity was not strict");
        run_tilt_case(2049,0,0,48,"gate-2049",q_zero);
        run_tilt_case(1448,1448,0,48,"diagonal-gate-below",q_zero);
        if (q_zero !== {32'h20000000,96'd0}) fail("below-threshold diagonal gravity was used");
        run_tilt_case(1449,1449,0,48,"diagonal-gate-above",q_zero);

        // Same direction at four magnitudes must take the exact same normalized
        // input path; this detects a scale-dependent gravity direction/overflow.
        run_tilt_case(0,2048,2048,96,"scale-0.707g",q_scale_1);
        run_tilt_case(0,4096,4096,96,"scale-1.414g",q_scale_2);
        run_tilt_case(0,8192,8192,96,"scale-2.828g",q_scale_4);
        run_tilt_case(0,16384,16384,96,"scale-5.657g",q_scale_8);
        if (q_scale_1 !== q_scale_2 || q_scale_1 !== q_scale_4 ||
            q_scale_1 !== q_scale_8)
            fail("shared acceleration scale changed normalized direction");

        // 30-degree tilts and signed full-range vectors include abs(-32768)
        // and three simultaneous maximum-magnitude axes.
        run_tilt_case(0,2048,3547,128,"tilt-y-30deg",q_zero);
        run_tilt_case(2048,0,3547,128,"tilt-x-30deg",q_zero);
        run_tilt_case(32767,-32768,32767,128,"full-range-mixed",q_zero);
        run_tilt_case(-32768,-32768,-32768,128,"full-range-all-negative",q_zero);
        run_tilt_case(32767,32767,32767,128,"full-range-all-positive",q_zero);

        // Signed gyro integration at ±900 dps, near full-scale and three axes.
        run_gyro_case(29520,0,0,64,"+900-x");
        run_gyro_case(-29520,0,0,64,"-900-x");
        run_gyro_case(0,29520,0,64,"+900-y");
        run_gyro_case(0,-29520,0,64,"-900-y");
        run_gyro_case(0,0,29520,64,"+900-z");
        run_gyro_case(0,0,-29520,64,"-900-z");
        run_gyro_case(32767,0,0,64,"near-full-positive");
        run_gyro_case(-32768,0,0,64,"near-full-negative");
        run_gyro_case(29520,-29520,29520,64,"three-axis-positive-negative");
        run_gyro_case(-29520,29520,-29520,64,"three-axis-reverse");
        run_gyro_case(32767,-32768,32767,64,"three-axis-near-full");
        run_gyro_case(-32768,32767,-32768,64,"three-axis-near-full-reverse");
        if (acceleration_cases != 16 || gyro_cases != 12)
            fail("physical category count mismatch");

        $display("physical coverage: %0d cases (%0d accel/rest/tilt/gate/scale/extreme, %0d gyro signed/range), %0d sample updates, max angular error=%0.6f deg",
                 cases, acceleration_cases, gyro_cases, samples, max_angle_error_deg);
        $display("physical-rate note: max normalized-Euler lag vs continuous rotation=%0.6f deg over 64 updates",
                 max_discrete_lag_deg);
        if (errors == 0)
            $display("TEST PASSED: independent MPU range, physical gyro and acceleration checks");
        else
            $display("TEST FAILED: %0d errors", errors);
        $finish;
    end

    initial begin
        #500000000;
        fail("global watchdog");
    end
endmodule
