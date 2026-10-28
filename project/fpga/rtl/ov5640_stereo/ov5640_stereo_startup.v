`timescale 1ns/1ps

// Candidate complete startup transport. init_done means ID and selected
// register reads matched and stream-on completed; it does not prove images.
module ov5640_stereo_startup #(
    parameter integer SYS_CLK_HZ = 100000000,
    parameter integer PWDN_SETTLE_CYCLES = ((SYS_CLK_HZ/1000)*20 + ((SYS_CLK_HZ%1000)*20+999)/1000 < 1) ? 1 : ((SYS_CLK_HZ/1000)*20 + ((SYS_CLK_HZ%1000)*20+999)/1000),
    parameter integer RESET_RELEASE_WAIT_CYCLES = ((SYS_CLK_HZ/1000)*20 + ((SYS_CLK_HZ%1000)*20+999)/1000 < 1) ? 1 : ((SYS_CLK_HZ/1000)*20 + ((SYS_CLK_HZ%1000)*20+999)/1000),
    parameter integer SCCB_HALF_PERIOD_CYCLES = ((SYS_CLK_HZ/200000)+((SYS_CLK_HZ%200000)!=0) < 1) ? 1 : ((SYS_CLK_HZ/200000)+((SYS_CLK_HZ%200000)!=0)),
    parameter integer SCCB_TIMEOUT_CYCLES = ((SYS_CLK_HZ/1000)*10 + ((SYS_CLK_HZ%1000)*10+999)/1000 < 1) ? 1 : ((SYS_CLK_HZ/1000)*10 + ((SYS_CLK_HZ%1000)*10+999)/1000),
    parameter [7:0] DVP_POLARITY_VALUE = 8'h22
) (
    input wire sys_clk, rst_n, start,
    output wire ov1_reset_n, ov1_pwdn, ov2_reset_n, ov2_pwdn,
    inout wire ov1_scl, ov1_sda, ov2_scl, ov2_sda,
    output wire busy, init_done, init_error,
    output wire [3:0] error_code,
    output wire [1:0] failed_cameras
);
    wire [9:0] table_index;
    wire table_valid, table_last;
    wire [15:0] table_addr, table_delay;
    wire [7:0] table_value, table_mask;
    wire tx_start, tx_read, transport_rst_n;
    wire [15:0] tx_addr;
    wire [7:0] tx_value, tx_mask, rd1, rd2;
    wire busy1, busy2, done1, done2;
    ov5640_startup_table #(.DVP_POLARITY_VALUE(DVP_POLARITY_VALUE)) u_table (
        .index(table_index), .valid(table_valid), .reg_addr(table_addr),
        .reg_value(table_value), .write_mask(table_mask),
        .post_delay_ms(table_delay), .last(table_last));
    ov5640_stereo_startup_controller #(.SYS_CLK_HZ(SYS_CLK_HZ),
        .PWDN_SETTLE_CYCLES(PWDN_SETTLE_CYCLES),
        .RESET_RELEASE_WAIT_CYCLES(RESET_RELEASE_WAIT_CYCLES),
        .SCCB_TIMEOUT_CYCLES(SCCB_TIMEOUT_CYCLES),
        .DVP_POLARITY_VALUE(DVP_POLARITY_VALUE)) u_control (
        .clk(sys_clk), .rst_n(rst_n), .start(start),
        .ov1_reset_n(ov1_reset_n), .ov1_pwdn(ov1_pwdn),
        .ov2_reset_n(ov2_reset_n), .ov2_pwdn(ov2_pwdn),
        .busy(busy), .init_done(init_done), .init_error(init_error),
        .error_code(error_code), .failed_cameras(failed_cameras),
        .table_index(table_index), .table_valid(table_valid), .table_last(table_last),
        .table_addr(table_addr), .table_value(table_value), .table_mask(table_mask),
        .table_delay_ms(table_delay), .tx_start(tx_start), .tx_read_only(tx_read),
        .tx_addr(tx_addr), .tx_value(tx_value), .tx_mask(tx_mask),
        .tx_busy({busy2,busy1}), .tx_done({done2,done1}),
        .read_data_ov1(rd1), .read_data_ov2(rd2), .transport_rst_n(transport_rst_n));
    ov5640_sccb_register_access #(.HALF_PERIOD_CYCLES(SCCB_HALF_PERIOD_CYCLES)) u_ov1 (
        .clk(sys_clk), .rst_n(transport_rst_n), .start(tx_start), .read_only(tx_read),
        .reg_addr(tx_addr), .reg_value(tx_value), .write_mask(tx_mask),
        .busy(busy1), .done(done1), .read_data(rd1), .sccb_scl(ov1_scl), .sccb_sda(ov1_sda));
    ov5640_sccb_register_access #(.HALF_PERIOD_CYCLES(SCCB_HALF_PERIOD_CYCLES)) u_ov2 (
        .clk(sys_clk), .rst_n(transport_rst_n), .start(tx_start), .read_only(tx_read),
        .reg_addr(tx_addr), .reg_value(tx_value), .write_mask(tx_mask),
        .busy(busy2), .done(done2), .read_data(rd2), .sccb_scl(ov2_scl), .sccb_sda(ov2_sda));
endmodule

// Public transport boundary supports fault-injection without forcing internal
// DUT signals. failed_cameras[0]=OV1, [1]=OV2. Errors stay latched until reset:
// 1=ID mismatch, 2=readback mismatch, 3=transport timeout, 4=invalid ROM.
module ov5640_stereo_startup_controller #(
    parameter integer SYS_CLK_HZ=100000000,
    parameter integer PWDN_SETTLE_CYCLES=2000000,
    parameter integer RESET_RELEASE_WAIT_CYCLES=2000000,
    parameter integer SCCB_TIMEOUT_CYCLES=1000000,
    parameter [7:0] DVP_POLARITY_VALUE=8'h22
) (
    input wire clk, rst_n, start,
    output reg ov1_reset_n, ov1_pwdn, ov2_reset_n, ov2_pwdn,
    output reg busy, init_done, init_error,
    output reg [3:0] error_code,
    output reg [1:0] failed_cameras,
    output reg [9:0] table_index,
    input wire table_valid, table_last,
    input wire [15:0] table_addr,
    input wire [7:0] table_value, table_mask,
    input wire [15:0] table_delay_ms,
    output reg tx_start, tx_read_only,
    output reg [15:0] tx_addr,
    output reg [7:0] tx_value, tx_mask,
    input wire [1:0] tx_busy, tx_done,
    input wire [7:0] read_data_ov1, read_data_ov2,
    output reg transport_rst_n
);
    localparam [3:0] IDLE=0, PWDN_WAIT=1, RESET_WAIT=2, PREPARE=3,
        ISSUE=4, WAIT_TX=5, POST_DELAY=6, FINISHED=7, FAILED=8,
        DELAY_CALC=9, DELAY_ROUND=10;
    localparam [2:0] ID_HI=0, ID_LO=1, TABLE=2, VERIFY=3, STREAM=4, STREAM_VERIFY=5;
    reg [3:0] state;
    reg [2:0] phase;
    reg [4:0] verify_index;
    // Size counters from the entire public 16-bit millisecond range, not just
    // the delays currently present in the ROM. Arithmetic here is elaboration
    // time only; the runtime conversion below has no multiplier or divider.
    localparam [63:0] MAX_DELAY_CYCLES =
        (64'd65535 * SYS_CLK_HZ + 64'd999) / 64'd1000;
    localparam [63:0] MAX_POWER_WAIT = (PWDN_SETTLE_CYCLES > RESET_RELEASE_WAIT_CYCLES)
        ? PWDN_SETTLE_CYCLES : RESET_RELEASE_WAIT_CYCLES;
    localparam [63:0] MAX_WAIT = (MAX_DELAY_CYCLES > MAX_POWER_WAIT)
        ? MAX_DELAY_CYCLES : MAX_POWER_WAIT;
    localparam integer WAIT_WIDTH = (MAX_WAIT < 1) ? 1 : $clog2(MAX_WAIT + 64'd1);
    localparam integer TIMEOUT_WIDTH = (SCCB_TIMEOUT_CYCLES < 2)
        ? 1 : $clog2(SCCB_TIMEOUT_CYCLES);
    reg [WAIT_WIDTH-1:0] wait_count, delay_cycles;
    reg [TIMEOUT_WIDTH-1:0] timeout_count;
    reg [15:0] delay_bits;
    reg [4:0] delay_steps;
    reg [9:0] delay_remainder;
    localparam [WAIT_WIDTH-1:0] CYCLES_PER_MS = SYS_CLK_HZ / 1000;
    localparam [11:0] HZ_REMAINDER = SYS_CLK_HZ % 1000;
    wire [11:0] remainder_sum = {1'b0,delay_remainder,1'b0}
        + (delay_bits[15] ? HZ_REMAINDER : 12'd0);
    wire [1:0] remainder_carry = (remainder_sum >= 12'd2000) ? 2'd2
        : ((remainder_sum >= 12'd1000) ? 2'd1 : 2'd0);
    wire [11:0] remainder_next = remainder_sum
        - ((remainder_carry == 2) ? 12'd2000
        : ((remainder_carry == 1) ? 12'd1000 : 12'd0));
    reg [1:0] done_seen;
    reg [7:0] expected, compare_mask;
    reg entry_last;
    wire [1:0] available = done_seen | tx_done;
    wire [1:0] mismatch = {
        tx_done[1] && tx_read_only && ((read_data_ov2 & compare_mask)!=(expected & compare_mask)),
        tx_done[0] && tx_read_only && ((read_data_ov1 & compare_mask)!=(expected & compare_mask))};
    // Registered transport reset: error decoding must not feed asynchronous
    // reset pins through a LUT. Assert on the same edge that latches failure.
    // Constant/reference helper; never call this with runtime RTL signals.
    function [63:0] ms_cycles;
        input [15:0] milliseconds;
        reg [63:0] product;
        begin
            product = SYS_CLK_HZ;
            product = product * milliseconds;
            ms_cycles = (product + 64'd999) / 64'd1000;
        end
    endfunction
    task enter_failure;
        input [3:0] code;
        input [1:0] cameras;
        begin
            init_error<=1; error_code<=code; failed_cameras<=cameras;
            transport_rst_n<=0;
            busy<=0; init_done<=0; tx_start<=0; state<=FAILED;
            ov1_reset_n<=0; ov2_reset_n<=0; ov1_pwdn<=1; ov2_pwdn<=1;
        end
    endtask
    // Independent readback contract, deliberately not inferred from ROM.
    reg [15:0] verify_addr;
    reg [7:0] verify_value, verify_mask;
    always @* begin
        verify_addr=16'h3034; verify_value=8'h18; verify_mask=8'hff;
        case (verify_index)
            0: begin verify_addr=16'h3034; verify_value=8'h18; end
            1: begin verify_addr=16'h3035; verify_value=8'h20; end
            2: begin verify_addr=16'h3036; verify_value=8'h54; end
            3: begin verify_addr=16'h3037; verify_value=8'h13; end
            4: begin verify_addr=16'h3108; verify_value=8'h01; end
            5: begin verify_addr=16'h3808; verify_value=8'h05; end
            6: begin verify_addr=16'h3809; verify_value=8'h00; end
            7: begin verify_addr=16'h380a; verify_value=8'h02; end
            8: begin verify_addr=16'h380b; verify_value=8'hd0; end
            9: begin verify_addr=16'h380c; verify_value=8'h07; end
            10: begin verify_addr=16'h380d; verify_value=8'h64; end
            11: begin verify_addr=16'h380e; verify_value=8'h02; end
            12: begin verify_addr=16'h380f; verify_value=8'he4; end
            13: begin verify_addr=16'h4300; verify_value=8'h6f; end
            14: begin verify_addr=16'h501f; verify_value=8'h01; end
            15: begin verify_addr=16'h4740; verify_value=DVP_POLARITY_VALUE & 8'h23; verify_mask=8'h2f; end
        endcase
    end
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state<=IDLE; phase<=ID_HI; verify_index<=0; table_index<=0;
            transport_rst_n<=0;
            ov1_reset_n<=0; ov2_reset_n<=0; ov1_pwdn<=1; ov2_pwdn<=1;
            busy<=0; init_done<=0; init_error<=0; error_code<=0; failed_cameras<=0;
            tx_start<=0; tx_read_only<=0; tx_addr<=0; tx_value<=0; tx_mask<=8'hff;
            expected<=0; compare_mask<=8'hff; done_seen<=0;
            wait_count<=0; delay_cycles<=0; timeout_count<=0; entry_last<=0;
            delay_bits<=0; delay_steps<=0; delay_remainder<=0;
        end else begin
            tx_start<=0;
            if (state==IDLE) transport_rst_n<=1;
            case (state)
                IDLE: if (start) begin
                    busy<=1; ov1_pwdn<=0; ov2_pwdn<=0; wait_count<=0; state<=PWDN_WAIT;
                end
                PWDN_WAIT: if (wait_count >= PWDN_SETTLE_CYCLES-1) begin
                    ov1_reset_n<=1; ov2_reset_n<=1; wait_count<=0; state<=RESET_WAIT;
                end else wait_count<=wait_count+1'b1;
                RESET_WAIT: if (wait_count >= RESET_RELEASE_WAIT_CYCLES-1) begin
                    state<=PREPARE; wait_count<=0;
                end else wait_count<=wait_count+1'b1;
                PREPARE: begin
                    tx_read_only<=1; tx_mask<=8'hff; compare_mask<=8'hff;
                    tx_value<=0; delay_cycles<=0;
                    case (phase)
                        ID_HI: begin tx_addr<=16'h300a; expected<=8'h56; state<=ISSUE; end
                        ID_LO: begin tx_addr<=16'h300b; expected<=8'h40; state<=ISSUE; end
                        TABLE: if (!table_valid) begin
                            enter_failure(4'd4,2'b11);
                        end else begin
                            tx_read_only<=0; tx_addr<=table_addr; tx_value<=table_value;
                            tx_mask<=table_mask;
                            delay_bits<=table_delay_ms; delay_steps<=0; delay_remainder<=0;
                            entry_last<=table_last;
                            state<=(table_delay_ms==0) ? ISSUE : DELAY_CALC;
                        end
                        VERIFY: begin tx_addr<=verify_addr; expected<=verify_value;
                            compare_mask<=verify_mask; state<=ISSUE; end
                        STREAM: begin tx_read_only<=0; tx_addr<=16'h3008;
                            tx_value<=8'h02; state<=ISSUE; end
                        STREAM_VERIFY: begin tx_addr<=16'h3008; expected<=8'h02;
                            compare_mask<=8'h42; state<=ISSUE; end
                        default: enter_failure(4'd4,2'b11);
                    endcase
                end
                // Horner conversion, one input bit per clock (MSB first).
                // Invariant: processed_ms * SYS_CLK_HZ = 1000*q + r.
                // Thus q'=2*q + bit*(SYS_CLK_HZ/1000) + carry, r'<1000.
                // Conversion occurs BEFORE SCCB; the full rounded delay still
                // starts only after BOTH camera transactions have completed.
                DELAY_CALC: begin
                    delay_cycles <= (delay_cycles << 1)
                        + (delay_bits[15] ? CYCLES_PER_MS : {WAIT_WIDTH{1'b0}})
                        + remainder_carry;
                    delay_remainder <= remainder_next[9:0];
                    delay_bits <= {delay_bits[14:0],1'b0};
                    if (delay_steps==15) state<=DELAY_ROUND;
                    else delay_steps<=delay_steps+1'b1;
                end
                DELAY_ROUND: begin
                    if (delay_remainder!=0) delay_cycles<=delay_cycles+1'b1;
                    state<=ISSUE;
                end
                ISSUE: begin
                    // All preceding requests must have completed before here.
                    if (tx_busy==0) begin
                        tx_start<=1; done_seen<=0; timeout_count<=0; state<=WAIT_TX;
                    end else begin
                        enter_failure(4'd3,tx_busy);
                    end
                end
                WAIT_TX: begin
                    done_seen<=available;
                    if (mismatch!=0) begin
                        enter_failure((phase==ID_HI || phase==ID_LO) ? 4'd1 : 4'd2,mismatch);
                    end else if (available==2'b11) begin
                        case (phase)
                            ID_HI: begin phase<=ID_LO; state<=PREPARE; end
                            ID_LO: begin phase<=TABLE; table_index<=0; state<=PREPARE; end
                            TABLE: begin wait_count<=0; state<=POST_DELAY; end
                            VERIFY: begin
                                if (verify_index==15) phase<=STREAM;
                                else verify_index<=verify_index+1'b1;
                                state<=PREPARE;
                            end
                            STREAM: begin phase<=STREAM_VERIFY; state<=PREPARE; end
                            STREAM_VERIFY: begin busy<=0; init_done<=1; state<=FINISHED; end
                            default: enter_failure(4'd4,2'b11);
                        endcase
                    end else if (timeout_count >= SCCB_TIMEOUT_CYCLES-1) begin
                        enter_failure(4'd3,~available);
                    end else timeout_count<=timeout_count+1'b1;
                end
                POST_DELAY: if (wait_count >= delay_cycles) begin
                    if (entry_last) begin phase<=VERIFY; verify_index<=0; state<=PREPARE; end
                    else if (table_index==10'd1023) begin
                        enter_failure(4'd4,2'b11);
                    end else begin table_index<=table_index+1'b1; state<=PREPARE; end
                end else wait_count<=wait_count+1'b1;
                FINISHED: begin busy<=0; init_done<=1; end
                FAILED: begin busy<=0; init_done<=0; init_error<=1;
                    ov1_reset_n<=0; ov2_reset_n<=0; ov1_pwdn<=1; ov2_pwdn<=1; end
                default: enter_failure(4'd4,2'b11);
            endcase
        end
    end
endmodule
