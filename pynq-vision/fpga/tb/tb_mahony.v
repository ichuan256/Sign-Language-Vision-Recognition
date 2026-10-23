// =============================================================================
// 妙手通言 · tb_mahony.v — mahony_pe 与 Python golden（MahonyAHRS）逐帧对拍
//
// 激励：mahony_stim.hex（每行 6×int16 hex：ax ay az gx gy gz）
// 参考：mahony_golden.hex（每行 4×int32 Q2.29 hex：qw qx qy qz）
// 两者由 algo/mahony_gen_vectors.py 生成（300 帧：静止→俯仰→偏航→静止）。
//
// 判据：逐帧比较 DUT 与 golden 四元数各分量，Q2.29 域绝对误差 ≤ TOL（默认
//       5_000_000 ≈ 0.0093）为通过；任一帧超差即 FAIL 并打印帧号。
// =============================================================================
`timescale 1ns / 1ps

module tb_mahony;
    localparam N_FRAMES = 300;
    localparam integer TOL = 5_000_000;      // Q2.29 域容差 ≈ 0.93%

    reg clk = 0, rst_n = 0;
    always #5 clk = ~clk;                     // 100MHz

    reg         in_valid = 0;
    reg  signed [15:0] ax, ay, az, gx, gy, gz;
    wire        out_valid;
    wire signed [31:0] qw, qx, qy, qz;

    mahony_pe dut (
        .clk(clk), .rst_n(rst_n),
        .in_valid(in_valid),
        .ax(ax), .ay(ay), .az(az),
        .gx(gx), .gy(gy), .gz(gz),
        .out_valid(out_valid),
        .qw(qw), .qx(qx), .qy(qy), .qz(qz)
    );

    // ---- 激励与 golden 存储（一维展开，先行声明供 $readmemh 使用） ----
    reg [15:0] stim_flat [0:N_FRAMES*6-1];
    reg [31:0] gold_flat [0:N_FRAMES*4-1];

    initial begin
        $readmemh("mahony_stim.hex", stim_flat);
        $readmemh("mahony_golden.hex", gold_flat);
    end

    function automatic [63:0] absdiff(input signed [31:0] a, input signed [31:0] b);
        reg signed [63:0] delta;
        begin
            delta = {{32{a[31]}}, a} - {{32{b[31]}}, b};
            absdiff = delta < 0 ? -delta : delta;
        end
    endfunction

    integer timeout;
    integer i, errors;
    reg [63:0] d0, d1, d2, d3;
    integer fd;
    initial begin
        fd = $fopen("dut_dump.txt", "w");
        // Missing or malformed vectors must not produce a false PASS via X.
        #1;
        if (!fd) begin $display("TEST FAILED: cannot open dump"); $finish; end
        for (i = 0; i < N_FRAMES*6; i = i + 1)
            if ((^stim_flat[i]) === 1'bx) begin
                $display("TEST FAILED: missing/invalid stimulus word %0d", i); $finish;
            end
        for (i = 0; i < N_FRAMES*4; i = i + 1)
            if ((^gold_flat[i]) === 1'bx) begin
                $display("TEST FAILED: missing/invalid golden word %0d", i); $finish;
            end
        // 复位
        repeat (10) @(posedge clk);
        rst_n <= 1;
        repeat (5) @(posedge clk);

        errors = 0;
        for (i = 0; i < N_FRAMES; i = i + 1) begin
            // 驱动一帧
            @(negedge clk);
            ax = stim_flat[i*6+0]; ay = stim_flat[i*6+1]; az = stim_flat[i*6+2];
            gx = stim_flat[i*6+3]; gy = stim_flat[i*6+4]; gz = stim_flat[i*6+5];
            in_valid <= 1;
            @(negedge clk);
            in_valid <= 0;

            // 等待输出（带超时）
            timeout = 0;
            while (!out_valid && timeout < 2048) begin
                @(posedge clk); timeout = timeout + 1;
            end
            if (timeout >= 2048) begin
                $display("ERROR: 帧 %0d 超时无输出", i);
                errors = errors + 1;
            end else begin
                $fdisplay(fd, "%08x %08x %08x %08x", qw, qx, qy, qz);
                if ((^{qw,qx,qy,qz}) === 1'bx) begin
                    $display("ERROR: quaternion contains X/Z at frame %0d", i);
                    errors = errors + 1;
                end
                d0 = absdiff(qw, gold_flat[i*4+0]);
                d1 = absdiff(qx, gold_flat[i*4+1]);
                d2 = absdiff(qy, gold_flat[i*4+2]);
                d3 = absdiff(qz, gold_flat[i*4+3]);
                if (d0 > TOL || d1 > TOL || d2 > TOL || d3 > TOL) begin
                    errors = errors + 1;
                    if (errors <= 10)
                        $display("帧 %0d 超差：DUT q=(%h %h %h %h) GOLD=(%h %h %h %h)",
                                 i, qw, qx, qy, qz,
                                 gold_flat[i*4+0], gold_flat[i*4+1],
                                 gold_flat[i*4+2], gold_flat[i*4+3]);
                end
            end
            repeat (10) @(posedge clk);     // 帧间隔（模拟节拍，非必须）
        end

        if (errors == 0)
            $display("==== TEST PASSED: %0d 帧全部在容差内（TOL=%0d）====", N_FRAMES, TOL);
        else
            $display("==== TEST FAILED: %0d 帧超差 ====", errors);
        $fclose(fd);
        $finish;
    end

endmodule
