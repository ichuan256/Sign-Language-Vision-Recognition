// Free-running ticks, unlike the production test's wait(checked) tick driver.
`timescale 1ns/1ps
module tb_w3_free_running;
reg clk=0,rst_n=0,tick=0,ready_out=0;
always #5 clk=~clk;
reg [31:0] ts=0;
integer cycle=0;
always @(negedge clk) if(rst_n) begin
 cycle=cycle+1;tick=0;
 if(cycle%10000==0) begin ts=ts+1;tick=1;end
 // Delay DMA arming by five sample periods. After that there is no backpressure.
 if(cycle==50000 || cycle==160000) ready_out=1;
 if(cycle==110000) ready_out=0;
end
wire [1:0] sclk,mosi,miso,valid,last,ready;
wire [2:0] cs_l,cs_r;
wire [7:0] dl,dr,md;
wire mv,ml;
sensor_if_spi #(.SCLK_FREQ_HZ(10000000),.GAP_CYCLES(10)) left(
 .clk(clk),.rst_n(rst_n),.tick(tick),.timestamp(ts),.sclk(sclk[0]),.mosi(mosi[0]),.miso(miso[0]),.cs_n(cs_l),
 .m_axis_tdata(dl),.m_axis_tvalid(valid[0]),.m_axis_tlast(last[0]),.m_axis_tready(ready[0]),.busy(),.imu_absent());
sensor_if_spi #(.SCLK_FREQ_HZ(10000000),.GAP_CYCLES(10)) right(
 .clk(clk),.rst_n(rst_n),.tick(tick),.timestamp(ts),.sclk(sclk[1]),.mosi(mosi[1]),.miso(miso[1]),.cs_n(cs_r),
 .m_axis_tdata(dr),.m_axis_tvalid(valid[1]),.m_axis_tlast(last[1]),.m_axis_tready(ready[1]),.busy(),.imu_absent());
w3_spi_devices #(.HAND(0)) lmodel(sclk[0],mosi[0],cs_l,miso[0]);
w3_spi_devices #(.HAND(1)) rmodel(sclk[1],mosi[1],cs_r,miso[1]);
merge_stream merge(.clk(clk),.rst_n(rst_n),
 .s_axis_l_tdata(dl),.s_axis_l_tvalid(valid[0]),.s_axis_l_tlast(last[0]),.s_axis_l_tready(ready[0]),
 .s_axis_r_tdata(dr),.s_axis_r_tvalid(valid[1]),.s_axis_r_tlast(last[1]),.s_axis_r_tready(ready[1]),
 .m_axis_tdata(md),.m_axis_tvalid(mv),.m_axis_tlast(ml),.m_axis_tready(ready_out),.stat_r_timeout(),.busy());
integer n=0,frames=0,i,errors=0;
reg [31:0] expected[0:11];
reg [7:0] bytes[0:99];
always @(posedge clk) if(mv&&ready_out) begin
 bytes[n]=md;
 if(ml) begin
  if(n!=99 || bytes[0]!==8'hAA || bytes[98]!==8'h55 || bytes[99]!==8'h5A
     || {bytes[46],bytes[47],bytes[48],bytes[49]}!==expected[frames]
     || {bytes[94],bytes[95],bytes[96],bytes[97]}!==expected[frames]) begin
   $display("ERROR free-running tick/paired frame=%0d",frames);errors=errors+1;
  end
  $write("RAW ");for(i=0;i<100;i=i+1)$write("%02x",bytes[i]);$write("\n");
  n=0;frames=frames+1;
  if(frames==12) begin
   if(errors==0) $display("TEST PASSED: continuous ticks, delayed DMA and runtime pause");
   else $display("TEST FAILED: %0d errors",errors);
   $finish;
  end
 end else n=n+1;
end
initial begin
expected[0]=1;expected[1]=2;expected[2]=6;expected[3]=7;expected[4]=8;expected[5]=9;
expected[6]=10;expected[7]=11;expected[8]=12;expected[9]=17;expected[10]=18;expected[11]=19;
repeat(10)@(negedge clk);rst_n=1;end
initial begin #3000000;$display("TEST FAILED: watchdog");$finish;end
endmodule
