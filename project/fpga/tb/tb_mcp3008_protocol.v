// Independent MCP3008 model: observes only CS/SCLK/MOSI, never DUT internals.
// Microchip DS20001295E figures 5-1 and 6-1: B9 follows falling start+6.
// Run both SAMPLE_MASK=0x1F and 0xFF; values cover 0,1,255,256,512,768,1023.
`timescale 1ns/1ps
module tb_mcp3008_protocol;
`ifdef TB_ADC_ALL
parameter [7:0] SAMPLE_MASK = 8'hFF;
`else
parameter [7:0] SAMPLE_MASK = 8'h1F;
`endif
reg clk=0, rst_n=0, tick=0;
always #5 clk=~clk;
reg [31:0] timestamp=0;
wire sclk,mosi,busy,valid,last;
wire [2:0] cs_n;
wire [7:0] data;
wire [1:0] absent;
reg ready=0;
reg [15:0] lfsr=16'hACE1;
reg adc_miso=0;
sensor_if_spi #(.SCLK_FREQ_HZ(10_000_000), .GAP_CYCLES(10),
 .ADC_MASK(4'h3), .ADC_SAMPLE_MASK(SAMPLE_MASK), .WHO_RETRY_MAX(0)) dut
(.clk(clk),.rst_n(rst_n),.tick(tick),.timestamp(timestamp),
 .sclk(sclk),.mosi(mosi),.miso(adc_miso),.cs_n(cs_n),
 .m_axis_tdata(data),.m_axis_tvalid(valid),.m_axis_tlast(last),
 .m_axis_tready(ready),.imu_absent(absent),.busy(busy));

integer clocks=0,start_clock=0,channel=0,delta=0,transactions=0;
integer checked=0,n=0,errors=0,command=0;
reg [7:0] bytes[0:47];
reg [9:0] sample;
reg [7:0] channels_seen=0;
function [9:0] input_value(input integer c,input integer f);
 begin
  case ((c+f)%8)
   0: input_value=0; 1: input_value=256; 2: input_value=512;
   3: input_value=768; 4: input_value=100; 5: input_value=1023;
   6: input_value=1; default: input_value=255;
  endcase
 end
endfunction
always @(negedge clk) begin
 lfsr <= {lfsr[14:0],lfsr[15]^lfsr[13]^lfsr[12]^lfsr[10]};
 ready <= rst_n && (lfsr[0] || lfsr[3]);
end
always @(negedge cs_n[2]) begin
 clocks=0; start_clock=0; channel=0; command=0;
 transactions=transactions+1;
end
always @(posedge sclk) if(!cs_n[2]) begin
 clocks=clocks+1;
 command=((command<<1)|mosi)&255;
 if(start_clock==0 && mosi) start_clock=clocks;
 if(start_clock>0) case(clocks-start_clock)
  2: channel[2]=mosi;
  3: channel[1]=mosi;
  4: channel[0]=mosi;
 endcase
 if(clocks==8 && command!=1) begin
  $display("ERROR first command byte=%02x expected=01",command); errors=errors+1;
 end
 if(clocks==16) begin
  if(command!=(8'h80|(channel<<4))) begin
   $display("ERROR second command byte=%02x",command); errors=errors+1;
  end
  if(!SAMPLE_MASK[channel] || channels_seen[channel]) begin
   $display("ERROR unsampled or duplicate channel=%0d",channel); errors=errors+1;
  end
  channels_seen[channel]=1'b1;
 end
end
always @(negedge sclk or posedge cs_n[2]) begin
 if(cs_n[2]) adc_miso=0;
 else begin
  sample=input_value(channel,checked);
  delta=clocks-start_clock;
  if(start_clock>0 && delta>=6 && delta<=15) adc_miso=sample[15-delta];
  else if(start_clock>0 && delta>=16 && delta<=24) adc_miso=sample[delta-15];
  else adc_miso=0;
 end
end
always @(posedge cs_n[2]) if(rst_n && clocks!=0 && clocks!=24) begin
 $display("ERROR ADC clocks=%0d expected=24",clocks); errors=errors+1;
end
reg stalled=0, held_last=0;
reg [7:0] held_data=0;
always @(posedge clk) begin
 if(rst_n && stalled && (!valid || data!==held_data || last!==held_last)) begin
  $display("ERROR AXI output changed under backpressure"); errors=errors+1;
 end
 stalled<=valid&&!ready;
 held_data<=data; held_last<=last;
 if(valid && ready) begin
  if(n>=48) begin $display("TEST FAILED: frame overflow"); $finish; end
  bytes[n]=data; n=n+1;
  if(last) begin
   check_frame;
   checked=checked+1; n=0; channels_seen=0;
  end
 end
end
integer i,expected;
task check_frame;
 begin
  if(n!=48 || absent!=2'b11 || channels_seen!==SAMPLE_MASK) begin
   $display("ERROR frame structure n=%0d absent=%b channels=%02x",n,absent,channels_seen);
   errors=errors+1;
  end
  for(i=0;i<28;i=i+1) if(bytes[i]!==8'hEE) errors=errors+1;
  for(i=0;i<8;i=i+1) begin
   expected=SAMPLE_MASK[i]?input_value(i,checked):0;
   if({bytes[28+2*i],bytes[29+2*i]}!==expected[15:0]) begin
    $display("ERROR frame=%0d channel=%0d got=%0d expected=%0d",checked,i,
             {bytes[28+2*i],bytes[29+2*i]},expected);
    errors=errors+1;
   end
  end
  if({bytes[44],bytes[45],bytes[46],bytes[47]}!==timestamp) errors=errors+1;
 end
endtask
integer f;
initial begin
 repeat(10) @(negedge clk); rst_n=1;
 wait(!busy);
 for(f=0;f<8;f=f+1) begin
  @(negedge clk); timestamp=f+1; tick=1;
  @(negedge clk); tick=0;
  wait(checked==f+1); wait(!busy);
 end
 if(errors) begin
  $display("TEST FAILED: independent ADC errors=%0d",errors); $finish;
 end
 $display("TEST PASSED: independent ADC mask=%02x frames=%0d transactions=%0d",SAMPLE_MASK,checked,transactions);
 $finish;
end
initial begin #10_000_000; $display("TEST FAILED: independent ADC timeout"); $finish; end
endmodule
