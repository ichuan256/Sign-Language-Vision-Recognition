// End-to-end two SPI schedulers -> merge_stream, with independent pin models.
`timescale 1ns/1ps
module w3_spi_devices #(parameter HAND=0)(
 input sclk,mosi, input [2:0] cs_n, output reg miso
);
integer clocks[0:2];
integer command[0:2];
integer channel=0, bit_index, dev, value, k;
initial begin
 miso=0;
 for(k=0;k<3;k=k+1) begin clocks[k]=0; command[k]=0; end
end
always @(negedge cs_n[0]) begin clocks[0]=0; command[0]=0; end
always @(negedge cs_n[1]) begin clocks[1]=0; command[1]=0; end
always @(negedge cs_n[2]) begin clocks[2]=0; command[2]=0; channel=0; end
always @(posedge sclk) begin
 for(k=0;k<3;k=k+1) if(!cs_n[k]) begin
  clocks[k]=clocks[k]+1;
  if(clocks[k]<=8) command[k]=((command[k]<<1)|mosi)&255;
 end
 if(!cs_n[2]) case(clocks[2])
  10: channel[2]=mosi; 11: channel[1]=mosi; 12: channel[0]=mosi;
 endcase
end
always @(negedge sclk or posedge cs_n[0] or posedge cs_n[1] or posedge cs_n[2]) begin
 miso=0;
 if(!cs_n[2]) begin
  value=channel*100+HAND*50+7;
  // start at clock 8, B9 becomes available after falling clock 14.
  if(clocks[2]>=14 && clocks[2]<=23) miso=(value>>(23-clocks[2]))&1;
 end else begin
  for(dev=0;dev<2;dev=dev+1) if(!cs_n[dev] && clocks[dev]>=8) begin
   bit_index=7-((clocks[dev]-8)%8);
   value=(command[dev]==8'hF5)?8'h70:
         ((command[dev]==8'h9B)?8'h18:
          ((command[dev]==8'h9C)?8'h10:(8'h10+HAND*32+dev*16)));
   miso=(value>>bit_index)&1;
  end
 end
end
endmodule

module tb_w3_dual_hand;
reg clk=0,rst_n=0,tick=0;
always #5 clk=~clk;
reg [31:0] timestamp=0;
wire [1:0] busy;
wire [1:0] sclk,mosi,miso,valid,last,ready;
wire [2:0] cs_l,cs_r;
wire [7:0] dl,dr,out_data;
wire out_valid,out_last;
wire [15:0] timeouts;
reg out_ready=0;
reg [15:0] rng=16'hAA21;
wire [1:0] absent_l,absent_r;
sensor_if_spi #(.SCLK_FREQ_HZ(10_000_000),.GAP_CYCLES(10),.WHO_RETRY_MAX(1)) left(
 .clk(clk),.rst_n(rst_n),.tick(tick),.timestamp(timestamp),
 .sclk(sclk[0]),.mosi(mosi[0]),.miso(miso[0]),.cs_n(cs_l),
 .m_axis_tdata(dl),.m_axis_tvalid(valid[0]),.m_axis_tlast(last[0]),
 .m_axis_tready(ready[0]),.busy(busy[0]),.imu_absent(absent_l));
sensor_if_spi #(.SCLK_FREQ_HZ(5_000_000),.GAP_CYCLES(10),.WHO_RETRY_MAX(1)) right(
 .clk(clk),.rst_n(rst_n),.tick(tick),.timestamp(timestamp),
 .sclk(sclk[1]),.mosi(mosi[1]),.miso(miso[1]),.cs_n(cs_r),
 .m_axis_tdata(dr),.m_axis_tvalid(valid[1]),.m_axis_tlast(last[1]),
 .m_axis_tready(ready[1]),.busy(busy[1]),.imu_absent(absent_r));
w3_spi_devices #(.HAND(0)) model_l(sclk[0],mosi[0],cs_l,miso[0]);
w3_spi_devices #(.HAND(1)) model_r(sclk[1],mosi[1],cs_r,miso[1]);
merge_stream mrg(.clk(clk),.rst_n(rst_n),
 .s_axis_l_tdata(dl),.s_axis_l_tvalid(valid[0]),.s_axis_l_tlast(last[0]),.s_axis_l_tready(ready[0]),
 .s_axis_r_tdata(dr),.s_axis_r_tvalid(valid[1]),.s_axis_r_tlast(last[1]),.s_axis_r_tready(ready[1]),
 .m_axis_tdata(out_data),.m_axis_tvalid(out_valid),.m_axis_tlast(out_last),
 .m_axis_tready(out_ready),.stat_r_timeout(timeouts),.busy());
always @(negedge clk) begin
 rng<={rng[14:0],rng[15]^rng[13]^rng[12]^rng[10]};
 out_ready<=rst_n&&(rng[0]||rng[3]);
end
integer n=0,checked=0,errors=0,h,c,i,base,expected,f;
reg [7:0] bytes[0:99];
reg stalled=0,held_last=0;
reg [7:0] held_data=0;
always @(posedge clk) begin
 if(rst_n&&stalled&&(!out_valid||out_data!==held_data||out_last!==held_last)) errors=errors+1;
 stalled<=out_valid&&!out_ready; held_data<=out_data; held_last<=out_last;
 if(out_valid&&out_ready) begin
  bytes[n]=out_data; n=n+1;
  if(out_last) begin
   if(n!=100||bytes[0]!==8'hAA||bytes[1]!==timestamp[7:0]||
      bytes[98]!==8'h55||bytes[99]!==8'h5A) errors=errors+1;
   for(h=0;h<2;h=h+1) begin
    base=2+h*48;
    for(i=0;i<28;i=i+1) begin
     expected=16+h*32+(i/14)*16;
     if(bytes[base+i]!==expected[7:0]) begin
      $display("ERROR IMU h=%0d byte=%0d got=%02x expected=%02x",h,i,bytes[base+i],expected);
      errors=errors+1;
     end
    end
    for(c=0;c<8;c=c+1) begin
     expected=(c<5)?c*100+h*50+7:0;
     if({bytes[base+28+2*c],bytes[base+29+2*c]}!==expected[15:0]) begin
      $display("ERROR ADC h=%0d ch=%0d",h,c); errors=errors+1;
     end
    end
    if({bytes[base+44],bytes[base+45],bytes[base+46],bytes[base+47]}!==timestamp) errors=errors+1;
   end
   checked=checked+1; n=0;
  end
 end
end
initial begin
 repeat(10) @(negedge clk); rst_n=1; wait(busy==0);
 for(f=0;f<8;f=f+1) begin
  @(negedge clk); timestamp=32'hFFFFFFFC+f; tick=1;
  @(negedge clk); tick=0;
  wait(checked==f+1); wait(busy==0);
 end
 if(errors||timeouts||absent_l||absent_r) $display("TEST FAILED dual-hand errors=%0d timeout=%0d",errors,timeouts);
 else $display("TEST PASSED: dual-hand 8 frames, ten distinct ADC inputs, four IMUs, rollover, skew and backpressure");
 $finish;
end
initial begin #20_000_000; $display("TEST FAILED: dual-hand timeout"); $finish; end
endmodule
