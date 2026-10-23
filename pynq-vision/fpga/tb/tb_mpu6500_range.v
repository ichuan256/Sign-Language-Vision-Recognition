// Pin-only MPU6500 register model: configuration writes must actually reach the
// selected device, and failed FS_SEL readback must retry or mark only it absent.
// MPU6500 RM-MPU-6500A-00: GYRO_CONFIG=0x1B, ACCEL_CONFIG=0x1C, FS_SEL=[4:3].
`timescale 1ns/1ps
module tb_mpu6500_range;
`ifdef TB_RANGE_LEGACY
localparam [1:0] ACCEL_FS = 0, GYRO_FS = 0;
localparam [7:0] ACCEL_CFG = 8'h00, GYRO_CFG = 8'h00;
localparam [15:0] ONE_G = 16'h4000;
`elsif TB_RANGE_MID
localparam [1:0] ACCEL_FS = 2, GYRO_FS = 1;
localparam [7:0] ACCEL_CFG = 8'h10, GYRO_CFG = 8'h08;
localparam [15:0] ONE_G = 16'h1000;
`elsif TB_RANGE_16G
localparam [1:0] ACCEL_FS = 3, GYRO_FS = 3;
localparam [7:0] ACCEL_CFG = 8'h18, GYRO_CFG = 8'h18;
localparam [15:0] ONE_G = 16'h0800;
`elsif TB_RANGE_W5
localparam [1:0] ACCEL_FS = 2, GYRO_FS = 2;
localparam [7:0] ACCEL_CFG = 8'h10, GYRO_CFG = 8'h10;
localparam [15:0] ONE_G = 16'h1000;
`else
localparam [1:0] ACCEL_FS = 2, GYRO_FS = 3;
localparam [7:0] ACCEL_CFG = 8'h10, GYRO_CFG = 8'h18;
localparam [15:0] ONE_G = 16'h1000;
`endif
`ifdef TB_RANGE_GYRO_FAIL
localparam FAULT = 1, EXPECT_ATTEMPTS = 2;
localparam [1:0] EXPECT_ABSENT = 2'b01;
`elsif TB_RANGE_ACCEL_FAIL
localparam FAULT = 2, EXPECT_ATTEMPTS = 2;
localparam [1:0] EXPECT_ABSENT = 2'b01;
`elsif TB_RANGE_RETRY
localparam FAULT = 3, EXPECT_ATTEMPTS = 2;
localparam [1:0] EXPECT_ABSENT = 2'b00;
`elsif TB_RANGE_WHO_FAIL
localparam FAULT = 4, EXPECT_ATTEMPTS = 2;
localparam [1:0] EXPECT_ABSENT = 2'b01;
`else
localparam FAULT = 0, EXPECT_ATTEMPTS = 1;
localparam [1:0] EXPECT_ABSENT = 2'b00;
`endif

reg clk = 0, rst_n = 0, tick = 0;
always #5 clk = ~clk;
reg [31:0] timestamp = 32'h12345678;
wire sclk, mosi, busy, valid, last;
wire [2:0] cs_n;
wire [7:0] data;
wire [1:0] absent;
wire miso0, miso1;
wire miso = !cs_n[0] ? miso0 : !cs_n[1] ? miso1 : 1'b0;
reg ready = 0;
reg [15:0] lfsr = 16'hACE1;
integer errors = 0, frames = 0, count = 0;
reg [7:0] frame [0:47];

sensor_if_spi #(.SCLK_FREQ_HZ(10_000_000), .GAP_CYCLES(10),
    .MPU_ACCEL_FS_SEL(ACCEL_FS), .MPU_GYRO_FS_SEL(GYRO_FS),
    .ADC_SAMPLE_MASK(8'h1F), .WHO_RETRY_MAX(1)) dut (
    .clk(clk), .rst_n(rst_n), .tick(tick), .timestamp(timestamp),
    .sclk(sclk), .mosi(mosi), .miso(miso), .cs_n(cs_n),
    .m_axis_tdata(data), .m_axis_tvalid(valid), .m_axis_tlast(last),
    .m_axis_tready(ready), .imu_absent(absent), .busy(busy));

wire [31:0] errors0, errors1, attempts0, attempts1, samples0, samples1;
mpu6500_range_device #(.DEVICE(0), .FAULT(FAULT),
    .ACCEL_CFG(ACCEL_CFG), .GYRO_CFG(GYRO_CFG), .ONE_G(ONE_G)) dev0 (
    .rst_n(rst_n), .cs_n(cs_n[0]), .sclk(sclk), .mosi(mosi), .miso(miso0),
    .errors(errors0), .attempts(attempts0), .samples(samples0));
mpu6500_range_device #(.DEVICE(1), .FAULT(0),
    .ACCEL_CFG(ACCEL_CFG), .GYRO_CFG(GYRO_CFG), .ONE_G(ONE_G)) dev1 (
    .rst_n(rst_n), .cs_n(cs_n[1]), .sclk(sclk), .mosi(mosi), .miso(miso1),
    .errors(errors1), .attempts(attempts1), .samples(samples1));

always @(negedge clk) begin
    lfsr <= {lfsr[14:0], lfsr[15]^lfsr[13]^lfsr[12]^lfsr[10]};
    ready <= rst_n && (lfsr[0] || lfsr[3]);
end
reg stalled = 0, held_last = 0;
reg [7:0] held_data = 0;
always @(posedge clk) begin
    if (rst_n && stalled && (!valid || data !== held_data || last !== held_last)) begin
        $display("ERROR output changed while blocked"); errors = errors + 1;
    end
    stalled <= valid && !ready;
    held_data <= data; held_last <= last;
    if (valid && ready) begin
        if (count >= 48) begin $display("TEST FAILED: frame overflow"); $finish; end
        frame[count] = data; count = count + 1;
        if (last) begin
            check_frame;
            count = 0; frames = frames + 1;
        end
    end
end

function [7:0] expected_byte(input integer device, input integer index);
    begin
        case (index)
            0: expected_byte = device ? 8'hFF : 8'h01;
            1: expected_byte = device ? 8'h80 : 8'h80;
            4: expected_byte = ONE_G[15:8];
            5: expected_byte = ONE_G[7:0];
            8: expected_byte = 8'h01;
            9: expected_byte = 8'h48;
            10: expected_byte = 8'hFE;
            11: expected_byte = 8'hB8;
            12: expected_byte = 8'h80;
            default: expected_byte = 8'h00;
        endcase
    end
endfunction
task check_frame;
    integer dev, i;
    reg [7:0] expected;
    begin
        if (count != 48 || absent !== EXPECT_ABSENT) begin
            $display("ERROR frame length=%0d absent=%b expected=%b", count, absent, EXPECT_ABSENT);
            errors = errors + 1;
        end
        for (dev = 0; dev < 2; dev = dev + 1)
            for (i = 0; i < 14; i = i + 1) begin
                expected = EXPECT_ABSENT[dev] ? 8'hEE : expected_byte(dev, i);
                if (frame[14*dev+i] !== expected) begin
                    $display("ERROR IMU%0d byte%0d=%02x expected=%02x", dev, i, frame[14*dev+i], expected);
                    errors = errors + 1;
                end
            end
        // ADC replies are zero in this model. The independent MCP3008 test
        // validates real conversion values; here ensure the slots survive.
        for (i = 28; i < 44; i = i + 1) if (frame[i] !== 0) begin
            $display("ERROR ADC slot byte%0d=%02x", i, frame[i]); errors = errors + 1;
        end
        if ({frame[44], frame[45], frame[46], frame[47]} !== timestamp) begin
            $display("ERROR timestamp changed"); errors = errors + 1;
        end
    end
endtask

integer f;
initial begin
    repeat (10) @(negedge clk); rst_n = 1;
    wait (!busy);
    @(negedge clk); // Allow the final CS edge to reach the independent model.
    if (attempts0 != EXPECT_ATTEMPTS || attempts1 != 1 || absent !== EXPECT_ABSENT) begin
        $display("ERROR initialization attempts=%0d/%0d absent=%b", attempts0, attempts1, absent);
        errors = errors + 1;
    end
    for (f = 0; f < 2; f = f + 1) begin
        @(negedge clk); tick = 1;
        @(negedge clk); tick = 0;
        wait (frames == f+1); wait (!busy);
        timestamp = timestamp + 1;
    end
    if (samples0 != (EXPECT_ABSENT[0] ? 0 : 2) || samples1 != 2) begin
        $display("ERROR sampling transactions=%0d/%0d", samples0, samples1); errors = errors + 1;
    end
    errors = errors + errors0 + errors1;
    if (errors)
        $display("TEST FAILED: MPU6500 range errors=%0d", errors);
    else
        $display("TEST PASSED: MPU6500 gyro=%02x accel=%02x fault=%0d attempts=%0d/%0d absent=%b frames=%0d",
            GYRO_CFG, ACCEL_CFG, FAULT, attempts0, attempts1, absent, frames);
    $finish;
end
initial begin #10_000_000; $display("TEST FAILED: MPU6500 range timeout"); $finish; end
endmodule

module mpu6500_range_device #(
    parameter DEVICE = 0, FAULT = 0,
    parameter [7:0] ACCEL_CFG = 8'h10, GYRO_CFG = 8'h18,
    parameter [15:0] ONE_G = 16'h1000
)(input rst_n, cs_n, sclk, mosi, output reg miso,
  output reg [31:0] errors, attempts, samples);
integer clocks = 0, byte_index = 0, phase = 0, gyro_reads = 0;
reg [7:0] shift = 0, command = 0, gyro = 0, accel = 0, reply = 0;
reg [7:0] expected_command;
initial begin miso = 0; errors = 0; attempts = 0; samples = 0; end
function [7:0] sample_byte(input integer index);
    begin
        case (index)
            0: sample_byte = DEVICE ? 8'hFF : 8'h01;
            1: sample_byte = 8'h80;
            4: sample_byte = ONE_G[15:8];
            5: sample_byte = ONE_G[7:0];
            8: sample_byte = 8'h01;
            9: sample_byte = 8'h48;
            10: sample_byte = 8'hFE;
            11: sample_byte = 8'hB8;
            12: sample_byte = 8'h80;
            default: sample_byte = 8'h00;
        endcase
    end
endfunction
always @(negedge cs_n) begin clocks = 0; shift = 0; command = 0; miso = 0; end
always @(posedge sclk) if (!cs_n) begin
    clocks = clocks + 1; shift = {shift[6:0], mosi};
    if (clocks == 8) begin
        command = shift;
        if (command == 8'hBB) begin
            if (phase != 0 || attempts == 0 || gyro !== GYRO_CFG || accel !== ACCEL_CFG) begin
                $display("ERROR device%0d sampled before completed configuration", DEVICE); errors = errors + 1;
            end
            samples = samples + 1;
        end else begin
            case (phase)
                0: expected_command = 8'h6B;
                1: expected_command = 8'h6A;
                2: expected_command = 8'h1B;
                3: expected_command = 8'h1C;
                4: expected_command = 8'h9B;
                5: expected_command = 8'h9C;
                default: expected_command = 8'hF5;
            endcase
            if (command !== expected_command) begin
                $display("ERROR device%0d init phase%0d command=%02x expected=%02x", DEVICE, phase, command, expected_command);
                errors = errors + 1;
            end
            if (command == 8'h9B) gyro_reads = gyro_reads + 1;
        end
    end
    if (clocks == 16) case (command)
        8'h6B: if (shift !== 8'h00) begin $display("ERROR wake value"); errors = errors + 1; end
        8'h6A: if (shift !== 8'h10) begin $display("ERROR SPI enable value"); errors = errors + 1; end
        8'h1B: begin
            gyro = shift;
            if (gyro !== GYRO_CFG) begin $display("ERROR device%0d gyro write=%02x", DEVICE, gyro); errors = errors + 1; end
        end
        8'h1C: begin
            accel = shift;
            if (accel !== ACCEL_CFG) begin $display("ERROR device%0d accel write=%02x", DEVICE, accel); errors = errors + 1; end
        end
        8'h9B, 8'h9C, 8'hF5: if (shift !== 0) begin $display("ERROR read dummy byte"); errors = errors + 1; end
        default: ;
    endcase
end
always @(negedge sclk or posedge cs_n) begin
    if (cs_n || clocks < 8) miso = 0;
    else begin
        case (command)
            8'h9B: reply = (FAULT == 1 || (FAULT == 3 && gyro_reads == 1)) ? (gyro ^ 8'h08) : gyro;
            8'h9C: reply = (FAULT == 2) ? (accel ^ 8'h08) : accel;
            8'hF5: reply = (FAULT == 4) ? 8'h00 : 8'h70;
            8'hBB: reply = sample_byte((clocks / 8) - 1);
            default: reply = 0;
        endcase
        miso = reply[7-(clocks%8)];
    end
end
always @(posedge cs_n) if (rst_n && clocks != 0) begin
    if (clocks != ((command == 8'hBB) ? 120 : 16)) begin
        $display("ERROR device%0d command=%02x clocks=%0d", DEVICE, command, clocks); errors = errors + 1;
    end
    if (command != 8'hBB) begin
        if (phase == 6) begin phase = 0; attempts = attempts + 1; end
        else phase = phase + 1;
    end
end
endmodule
