`timescale 1ns/1ps

// Bus-level model, not an optical/analog sensor model. Faults change bytes on
// physical SDA reads; they do not force or bypass DUT internal signals.
module ov5640_startup_sensor_model #(
    parameter integer CAMERA=1
) (
    input wire scl, reset_n,
    inout wire sda,
    input wire [2:0] fault,
    output integer writes=0, reads=0, stream_writes=0,
    output reg [15:0] last_address=0,
    output reg [7:0] last_value=0
);
    reg [7:0] memory[0:65535];
    reg slave_low=0, active=0, read_pending=0, read_active=0, read_finished=0;
    reg [7:0] shift=0, read_byte=0;
    reg [15:0] address=0;
    integer bit_count=0, byte_count=0, tx_bit=7, i;
    assign sda=slave_low ? 1'b0 : 1'bz;
    task reset_registers;
        begin
            for(i=0;i<65536;i=i+1) memory[i]=0;
            memory[16'h300a]=8'h56; memory[16'h300b]=8'h40;
            memory[16'h4740]=(CAMERA==1) ? 8'h83 : 8'h56;
            memory[16'h3503]=(CAMERA==1) ? 8'hd7 : 8'h8a;
            memory[16'h3406]=(CAMERA==1) ? 8'hab : 8'h7c;
            memory[16'h3c01]=(CAMERA==1) ? 8'h12 : 8'h22;
            memory[16'h3a00]=(CAMERA==1) ? 8'h0d : 8'hda;
            memory[16'h3c00]=(CAMERA==1) ? 8'h31 : 8'h8a;
        end
    endtask
    initial reset_registers();
    always @(negedge reset_n) begin
        reset_registers();
        slave_low=0; active=0; read_active=0; read_finished=0;
    end
    always @(negedge sda) if(scl===1'b1 && reset_n) begin
        active=1; bit_count=0; byte_count=0; shift=0;
        read_pending=0; read_active=0; read_finished=0;
    end
    always @(posedge sda) if(scl===1'b1) active=0;
    always @(posedge scl) if(active) begin
        if(read_active) begin
            if(tx_bit==0) begin read_active=0; read_finished=1; end
            else tx_bit=tx_bit-1;
        end else if(!read_finished) begin
            if(bit_count<8) begin
                shift={shift[6:0],sda}; bit_count=bit_count+1;
                if(bit_count==8) begin
                    case(byte_count)
                        0: begin
                            if(shift!==8'h78 && shift!==8'h79)
                                $fatal(1,"sensor%0d invalid device byte %02x",CAMERA,shift);
                            read_pending=shift[0];
                        end
                        1: address[15:8]=shift;
                        2: address[7:0]=shift;
                        3: begin
                            if(address==16'h3008 && shift==8'h82) reset_registers();
                            memory[address]=shift;
                            last_address=address; last_value=shift; writes=writes+1;
                            if(address==16'h3008 && shift==8'h02) stream_writes=stream_writes+1;
                        end
                        default: $fatal(1,"sensor%0d extra SCCB byte",CAMERA);
                    endcase
                end
            end else begin
                bit_count=0; byte_count=byte_count+1;
                if(read_pending) begin
                    reads=reads+1; read_active=1; tx_bit=7;
                    read_byte=memory[address];
                    if(fault==1 && address==16'h300a) read_byte=8'h00;
                    if(fault==2 && address==16'h300b) read_byte=8'h00;
                    if(fault==3 && address==16'h3036) read_byte=8'h55;
                    if(fault==4 && address==16'h3008) read_byte=8'h42;
                    // Reserved stream-control bits must not cause rejection.
                    if(fault==0 && address==16'h3008) read_byte=read_byte | 8'h10;
                end
            end
        end
    end
    always @(negedge scl) begin
        if(active && read_active) slave_low=~read_byte[tx_bit];
        else slave_low=0;
    end
endmodule
