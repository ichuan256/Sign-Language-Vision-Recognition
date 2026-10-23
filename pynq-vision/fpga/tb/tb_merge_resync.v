`timescale 1ns/1ps
// Independent counter scoreboard: stale, future, partial late, wrap and stalls.
module tb_merge_resync;
reg clk=0, rst_n=0;
always #5 clk=~clk;
reg [7:0] ld=0, rd=0;
reg lv=0,ll=0,rv=0,rl=0,ready=1;
wire lr,rr,mv,ml;
wire [7:0] md;
wire [15:0] missing;
merge_stream #(.TIMEOUT_CYCLES(120)) dut(
 .clk(clk),.rst_n(rst_n),
 .s_axis_l_tdata(ld),.s_axis_l_tvalid(lv),.s_axis_l_tlast(ll),.s_axis_l_tready(lr),
 .s_axis_r_tdata(rd),.s_axis_r_tvalid(rv),.s_axis_r_tlast(rl),.s_axis_r_tready(rr),
 .m_axis_tdata(md),.m_axis_tvalid(mv),.m_axis_tlast(ml),.m_axis_tready(ready),
 .stat_r_timeout(missing),.busy());
task automatic send_hand;
 input left; input [31:0] ts; input pause_cycles;
 integer i; reg [7:0] d;
 begin
  for(i=0;i<48;i=i+1) begin
   if(pause_cycles && i==12) begin
    @(negedge clk); rv=0; repeat(160) @(negedge clk);
   end
   d=left ? 8'h11 : 8'h22;
   if(i>=44) d=ts >> ((47-i)*8);
   @(negedge clk);
   if(left) begin ld=d;lv=1;ll=(i==47);end
   else begin rd=d;rv=1;rl=(i==47);end
   @(posedge clk);
   while(left ? !lr : !rr) @(posedge clk);
  end
  @(negedge clk);
  if(left) begin lv=0;ll=0;end else begin rv=0;rl=0;end
 end
endtask
integer n=0,k=0,i,errors=0;
reg [7:0] frame[0:99];
reg [31:0] expected[0:9];
reg paired[0:9];
reg stalled=0,held_last; reg [7:0] held_data;
always @(posedge clk) if(rst_n) begin
 if(stalled && (!mv || md!==held_data || ml!==held_last)) begin
  $display("ERROR output changed under backpressure");errors=errors+1;
 end
 stalled=mv && !ready; held_data=md;held_last=ml;
 if(mv && ready) begin
  frame[k]=md;
  if(ml) begin
   if(k!=99 || n>=10) begin $display("ERROR frame size/count");errors=errors+1;end
   if(frame[0]!==8'hAA || frame[98]!==8'h55 || frame[99]!==8'h5A
       || frame[1]!==expected[n][7:0]
       || {frame[46],frame[47],frame[48],frame[49]}!==expected[n]) begin
    $display("ERROR left counter/markers frame=%0d",n);errors=errors+1;
   end
   for(i=0;i<44;i=i+1) if(frame[i+2]!==8'h11) begin
    $display("ERROR left data");errors=errors+1;
   end
   if(paired[n]) begin
    if({frame[94],frame[95],frame[96],frame[97]}!==expected[n]) begin
     $display("ERROR cross-tick pairing frame=%0d",n);errors=errors+1;
    end
    for(i=0;i<44;i=i+1) if(frame[i+50]!==8'h22) begin
     $display("ERROR right data");errors=errors+1;
    end
   end else for(i=50;i<98;i=i+1) if(frame[i]!==8'hEE) begin
    $display("ERROR missing right changed mid-frame");errors=errors+1;
   end
   n=n+1;k=0;
  end else k=k+1;
 end
end
initial begin
 expected[0]=1;paired[0]=0;expected[1]=2;paired[1]=1;
 expected[2]=3;paired[2]=0;expected[3]=4;paired[3]=1;
 expected[4]=5;paired[4]=0;expected[5]=6;paired[5]=1;
 expected[6]=32'hFFFFFFFF;paired[6]=1;expected[7]=0;paired[7]=1;
 expected[8]=1;paired[8]=0;expected[9]=2;paired[9]=1;
 repeat(5) @(negedge clk);rst_n=1;
 send_hand(1,1,0);wait(n==1);
 send_hand(0,1,0);
 fork send_hand(1,2,0);send_hand(0,2,0);join
 wait(n==2);repeat(2) @(negedge clk);ready=0;
 fork send_hand(0,4,0);send_hand(1,3,0);join
 wait(mv);repeat(250) @(negedge clk);ready=1;wait(n==3);
 send_hand(1,4,0);wait(n==4);
 send_hand(1,5,0);wait(mv);
 send_hand(0,5,1);wait(n==5);
 fork send_hand(1,6,0);send_hand(0,6,0);join
 wait(n==6);
 fork send_hand(1,32'hFFFFFFFF,0);send_hand(0,32'hFFFFFFFF,0);join
 wait(n==7);
 fork send_hand(1,0,0);send_hand(0,0,0);join
 wait(n==8);
 fork send_hand(1,1,0);send_hand(0,2,0);join
 wait(n==9);send_hand(1,2,0);wait(n==10);
 repeat(5) @(negedge clk);
 if(missing!=4) begin $display("ERROR missing count %0d",missing);errors=errors+1;end
 if(errors==0) $display("TEST PASSED: 10 frames, stale/future/partial/wrap/stall");
 else $display("TEST FAILED: %0d errors",errors);
 $finish;
end
initial begin #1000000;$display("TEST FAILED: watchdog frames=%0d",n);$finish;end
endmodule
