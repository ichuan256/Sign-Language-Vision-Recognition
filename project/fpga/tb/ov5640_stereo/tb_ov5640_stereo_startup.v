`timescale 1ns/1ps

module startup_bus_case #(
    parameter integer CASE_ID=0, BAD_CAMERA=0, FAULT=0,
    parameter [7:0] DVP_VALUE=8'h22
) (output reg completed=0);
    reg clk=0, rst_n=0, start=0;
    wire reset1,reset2,pwdn1,pwdn2,busy,done,error_flag;
    wire [3:0] error_code;
    wire [1:0] failed_cameras;
    tri1 scl1,sda1,scl2,sda2;
    wire [31:0] writes1,writes2,reads1,reads2,streams1,streams2;
    wire [15:0] address1,address2;
    wire [7:0] value1,value2;
    integer cycles=0, start_cycle=0, reset_cycle=0, last_table_cycle=0;
    integer seen1=0, seen2=0, table_rows=0, terminal_writes1=0,terminal_writes2=0;
    integer completed_cycle=-1, required_delay=0;
    reg [2:0] fault1=0,fault2=0;
    always #5 clk=~clk;
    always @(posedge clk) cycles=cycles+1;
    ov5640_stereo_startup #(.SYS_CLK_HZ(1000), .PWDN_SETTLE_CYCLES(3),
        .RESET_RELEASE_WAIT_CYCLES(4), .SCCB_HALF_PERIOD_CYCLES(2),
        .SCCB_TIMEOUT_CYCLES(2000),.DVP_POLARITY_VALUE(DVP_VALUE)) dut (
        .sys_clk(clk),.rst_n(rst_n),.start(start),
        .ov1_reset_n(reset1),.ov1_pwdn(pwdn1),.ov2_reset_n(reset2),.ov2_pwdn(pwdn2),
        .ov1_scl(scl1),.ov1_sda(sda1),.ov2_scl(scl2),.ov2_sda(sda2),
        .busy(busy),.init_done(done),.init_error(error_flag),
        .error_code(error_code),.failed_cameras(failed_cameras));
    ov5640_startup_sensor_model #(.CAMERA(1)) sensor1 (
        .scl(scl1),.sda(sda1),.reset_n(reset1),.fault(fault1),
        .writes(writes1),.reads(reads1),.stream_writes(streams1),
        .last_address(address1),.last_value(value1));
    ov5640_startup_sensor_model #(.CAMERA(2)) sensor2 (
        .scl(scl2),.sda(sda2),.reset_n(reset2),.fault(fault2),
        .writes(writes2),.reads(reads2),.stream_writes(streams2),
        .last_address(address2),.last_value(value2));
    always @(negedge clk) if(rst_n) begin
        if(scl1===1'bx || sda1===1'bx || scl2===1'bx || sda2===1'bx)
            $fatal(1,"case%0d bus contention",CASE_ID);
        if((dut.u_ov1.read_busy && dut.u_ov1.write_busy) ||
           (dut.u_ov2.read_busy && dut.u_ov2.write_busy))
            $fatal(1,"case%0d overlapping cores",CASE_ID);
        if(dut.tx_start && dut.u_control.phase==2) begin
            table_rows=table_rows+1;
        end
        if(dut.tx_start && completed_cycle>=0) begin
            if(cycles-completed_cycle<required_delay)
                $fatal(1,"case%0d table post-delay shorter than %0d cycles",CASE_ID,required_delay);
            completed_cycle=-1;
        end
        if(dut.u_control.phase==2 && dut.done1 && dut.done2) begin
            completed_cycle=cycles;
            required_delay=dut.table_delay;
        end
        if(dut.u_control.phase==2 && dut.table_last && dut.done1 && dut.done2)
            last_table_cycle=cycles;
        if((streams1 || streams2) && dut.u_control.phase<4)
            $fatal(1,"case%0d stream-on before ID/table/readback",CASE_ID);
        if(writes1!=seen1) begin
            seen1=writes1;
            if(address1==16'h3008 && value1==8'h02 && cycles-last_table_cycle<300)
                $fatal(1,"case%0d final table delay bypassed",CASE_ID);
        end
        if(writes2!=seen2) seen2=writes2;
    end
    task launch;
        begin @(negedge clk); start=1; @(negedge clk); start=0; end
    endtask
    initial begin
        repeat(3) @(negedge clk);
        if(reset1 || reset2 || !pwdn1 || !pwdn2) $fatal(1,"safe reset pins");
        if(BAD_CAMERA==1) fault1=FAULT;
        if(BAD_CAMERA==2) fault2=FAULT;
        rst_n=1;
        launch(); start_cycle=cycles;
        wait(reset1); #1; reset_cycle=cycles;
        if(cycles-start_cycle!=3 || !reset2 || pwdn1 || pwdn2) $fatal(1,"power wait");
        wait(dut.tx_start); #1;
        if(cycles-reset_cycle<4) $fatal(1,"reset release wait");
        launch(); // A busy start must not restart power sequencing or writes.
        wait(done || error_flag); #1;
        if(FAULT==0) begin
            if(!done || error_flag || busy || streams1!=1 || streams2!=1 || table_rows!=308 ||
                writes1!=309 || writes2!=309 || reads1!=30 || reads2!=30)
                $fatal(1,"normal startup did not complete table/stream %0d",table_rows);
            if((sensor1.memory[16'h4740] & 8'h2f)!==(DVP_VALUE & 8'h23) ||
                (sensor2.memory[16'h4740] & 8'h2f)!==(DVP_VALUE & 8'h23))
                $fatal(1,"configured polarity/gating contract %h/%h",sensor1.memory[16'h4740],sensor2.memory[16'h4740]);
        end else begin
            if(done || busy || !error_flag || failed_cameras!==(BAD_CAMERA==1 ? 2'b01 : 2'b10) ||
                error_code!==((FAULT<=2) ? 4'd1 : 4'd2))
                $fatal(1,"case%0d wrong error/mask %d/%b",CASE_ID,error_code,failed_cameras);
            if(FAULT<=3 && (streams1 || streams2)) $fatal(1,"failure allowed stream-on");
            if(FAULT<=2 && (writes1 || writes2)) $fatal(1,"ID failure allowed configuration writes");
            if(scl1!==1 || sda1!==1 || scl2!==1 || sda2!==1) $fatal(1,"failed bus not released");
            if(reset1 || reset2 || !pwdn1 || !pwdn2) $fatal(1,"failed sensor controls not safe");
        end
        // A new start cannot clear a terminal result. Global reset can.
        terminal_writes1=writes1;terminal_writes2=writes2;
        launch(); repeat(10) @(negedge clk);
        if(FAULT==0 ? !done : (!error_flag || done)) $fatal(1,"terminal status not sticky");
        if(writes1!=terminal_writes1 || writes2!=terminal_writes2 || dut.tx_start)
            $fatal(1,"terminal start triggered repeated writes");
        rst_n=0; #1;
        if(done || error_flag || busy || reset1 || reset2 || !pwdn1 || !pwdn2)
            $fatal(1,"reset did not clear status/restore pins");
        if(CASE_ID==1) begin
            // Recover a complete physical-bus startup after clearing ID fault.
            fault1=0;fault2=0;
            repeat(3) @(negedge clk);rst_n=1;launch();
            wait(done || error_flag);#1;
            if(!done || error_flag || streams1!=1 || streams2!=1 || writes1!=309 || writes2!=309)
                $fatal(1,"complete restart after ID failure did not recover");
            $display("BUS_RESET_RECOVERY_PASS case=1");
        end
        $display("BUS_CASE_PASS case=%0d fault=%0d camera=%0d rows=%0d reads=%0d/%0d",CASE_ID,FAULT,BAD_CAMERA,table_rows,reads1,reads2);
        completed=1;
    end
endmodule

module tb_ov5640_stereo_startup;
    wire [7:0] completed;
    startup_bus_case #(.CASE_ID(0)) c0(completed[0]);
    startup_bus_case #(.CASE_ID(1),.BAD_CAMERA(1),.FAULT(1)) c1(completed[1]);
    startup_bus_case #(.CASE_ID(2),.BAD_CAMERA(2),.FAULT(2)) c2(completed[2]);
    startup_bus_case #(.CASE_ID(3),.BAD_CAMERA(1),.FAULT(3)) c3(completed[3]);
    startup_bus_case #(.CASE_ID(4),.BAD_CAMERA(2),.FAULT(3)) c4(completed[4]);
    startup_bus_case #(.CASE_ID(5),.BAD_CAMERA(1),.FAULT(4)) c5(completed[5]);
    startup_bus_case #(.CASE_ID(6),.BAD_CAMERA(2),.FAULT(4)) c6(completed[6]);
    startup_bus_case #(.CASE_ID(7),.DVP_VALUE(8'hff)) c7(completed[7]);
    initial begin
        wait(&completed); $display("TEST_PASS: physical dual SCCB startup, ID/readback faults, mask preservation, stream order and reset"); $finish;
    end
    initial begin #10000000; $fatal(1,"startup bus watchdog"); end
endmodule
