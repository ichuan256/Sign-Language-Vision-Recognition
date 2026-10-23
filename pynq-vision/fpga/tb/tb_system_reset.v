`timescale 1ns/1ps
// Actual Vivado-generated proc_sys_reset wrapper, not a behavioral substitute.
//
// NOT part of `tests/run_w3_regression.py --rtl`: that runner uses Icarus
// Verilog at -g2005 and cannot compile the VHDL IP wrapper
// (system_proc_sys_reset_0_0.vhd) generated into a W3 Vivado project. Run this
// testbench from a project that contains the generated IP, with xsim:
//
//   xvlog/xvhdl the generated system_proc_sys_reset_0_0 sources, then
//   xelab tb_system_reset -s reset_sim && xsim reset_sim -R
//
// The polarity check that *is* automated on every run lives in
// tests/test_reset_config.py (Tcl substitutes) and in tb_system_reset's
// archived result at analysis/reset_fix_20261015/.
module tb_system_reset;
    reg clk = 0;
    always #5 clk = ~clk;
    reg ext_n = 0, aux = 0, debug_rst = 0, locked = 1;
    wire [0:0] peripheral_n, interconnect_n;
    wire [0:0] bus_reset, peripheral_reset;
    wire mb_reset;
    integer errors = 0;
    system_proc_sys_reset_0_0 dut (
        .slowest_sync_clk(clk), .ext_reset_in(ext_n), .aux_reset_in(aux),
        .mb_debug_sys_rst(debug_rst), .dcm_locked(locked),
        .peripheral_aresetn(peripheral_n), .interconnect_aresetn(interconnect_n),
        .bus_struct_reset(bus_reset), .peripheral_reset(peripheral_reset), .mb_reset(mb_reset)
    );
    task settle;
        begin repeat (256) @(negedge clk); end
    endtask
    task check;
        input active;
        input [255:0] label;
        begin
            settle;
            if (peripheral_n !== !active || interconnect_n !== !active ||
                bus_reset !== active || peripheral_reset !== active || mb_reset !== active) begin
                $display("ERROR %0s peripheral_n=%b interconnect_n=%b mb_reset=%b", label, peripheral_n, interconnect_n, mb_reset);
                errors = errors + 1;
            end else $display("PASS %0s", label);
        end
    endtask
    initial begin
        check(1, "power-up external reset");
        ext_n = 1; check(0, "grounded aux releases reset");
        ext_n = 0; check(1, "external reassert");
        ext_n = 1; check(0, "external release");
        aux = 1; check(1, "auxiliary high asserts");
        aux = 0; check(0, "auxiliary low releases");
        debug_rst = 1; check(1, "debug asserts");
        debug_rst = 0; check(0, "debug releases");
        locked = 0; check(1, "clock lock lost");
        locked = 1; check(0, "clock lock restored");
        if (errors) $display("TEST FAILED reset errors=%0d", errors);
        else $display("TEST PASSED reset polarity and recovery");
        $finish;
    end
endmodule
