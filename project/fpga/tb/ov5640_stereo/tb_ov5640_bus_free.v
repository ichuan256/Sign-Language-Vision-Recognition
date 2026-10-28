`timescale 1ns/1ps
// Datasheet table 8-6: tBUF >= 1.3us. 100MHz system, 100kHz SCCB.
module tb_ov5640_bus_free;
    reg clk=0,rst_n=0,start=0,rd=0;
    wire busy,done; wire [7:0] value; tri1 scl,sda;
    realtime last_stop=0; integer stops=0,starts=0;
    always #5 clk=~clk;
    ov5640_sccb_register_access #(.HALF_PERIOD_CYCLES(500)) dut(
        .clk(clk),.rst_n(rst_n),.start(start),.read_only(rd),
        .reg_addr(16'h3034),.reg_value(8'h18),.write_mask(8'hff),
        .busy(busy),.done(done),.read_data(value),.sccb_scl(scl),.sccb_sda(sda));
    always @(posedge sda) if(rst_n && scl===1'b1) begin last_stop=$realtime;stops=stops+1;end
    always @(negedge sda) if(rst_n && scl===1'b1) begin
        starts=starts+1;
        if(stops>0 && ($realtime-last_stop)<1300.0)
            $fatal(1,"tBUF violated: %0.1f ns, required >=1300 ns",$realtime-last_stop);
    end
    task request;begin @(negedge clk);start=1;@(negedge clk);start=0;wait(done);end endtask
    initial begin
        repeat(4)@(negedge clk);rst_n=1;
        request();request();rd=1;request();rd=0;request();
        if(starts<4 || stops<4)$fatal(1,"missing transactions");
        $display("TEST_PASS: SCCB inter-transaction tBUF >=1.3us");$finish;
    end
    initial begin #5000000;$fatal(1,"bus-free watchdog");end
endmodule
