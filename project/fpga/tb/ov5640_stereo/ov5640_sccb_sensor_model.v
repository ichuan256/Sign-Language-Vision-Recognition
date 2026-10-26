`timescale 1ns/1ps

// Simulation-only SCCB register model. Decodes physical START/repeated START,
// register addresses and write data; drives only low or Z during sensor reads.
// Ninth bits are don't-care. Each instance has independent register storage.
module ov5640_sccb_sensor_model #(
    parameter integer CAMERA = 1
) (
    input wire scl,
    inout wire sda,
    output integer writes = 0,
    output integer reads = 0,
    output integer starts = 0,
    output integer stops = 0,
    output reg [15:0] last_address = 0,
    output reg [7:0] last_value = 0
);
    reg [7:0] memory [0:65535];
    reg slave_low = 0, active = 0, read_pending = 0;
    reg read_active = 0, read_finished = 0;
    reg [7:0] shift = 0;
    reg [15:0] address = 0;
    integer bit_count = 0, byte_count = 0, tx_bit = 7, i;
    assign sda = slave_low ? 1'b0 : 1'bz;
    initial begin
        for (i=0; i<65536; i=i+1) memory[i] = 0;
        memory[16'h4740] = (CAMERA==1) ? 8'h83 : 8'h56;
        memory[16'h3503] = (CAMERA==1) ? 8'hd7 : 8'h8a;
        memory[16'h3406] = (CAMERA==1) ? 8'hab : 8'h7c;
        memory[16'h3c01] = (CAMERA==1) ? 8'h12 : 8'h22;
        memory[16'h3a00] = (CAMERA==1) ? 8'h0d : 8'hda;
        memory[16'h3c00] = (CAMERA==1) ? 8'h31 : 8'h8a;
    end
    always @(negedge sda) if (scl === 1'b1) begin
        starts = starts + 1;
        active = 1;
        bit_count = 0;
        byte_count = 0;
        shift = 0;
        read_pending = 0;
        read_active = 0;
        read_finished = 0;
    end
    always @(posedge sda) if (scl === 1'b1) begin
        if (active) stops = stops + 1;
        active = 0;
    end
    always @(posedge scl) if (active) begin
        if (read_active) begin
            if (tx_bit == 0) begin
                read_active = 0;
                read_finished = 1;
            end else tx_bit = tx_bit - 1;
        end else if (!read_finished) begin
            if (bit_count < 8) begin
                shift = {shift[6:0], sda};
                bit_count = bit_count + 1;
                if (bit_count == 8) begin
                    case (byte_count)
                        0: begin
                            if (shift !== 8'h78 && shift !== 8'h79)
                                $fatal(1, "camera%0d bad SCCB address %02x", CAMERA, shift);
                            read_pending = shift[0];
                        end
                        1: address[15:8] = shift;
                        2: address[7:0] = shift;
                        3: begin
                            memory[address] = shift;
                            writes = writes + 1;
                            last_address = address;
                            last_value = shift;
                        end
                        default: $fatal(1, "camera%0d extra transmitted byte", CAMERA);
                    endcase
                end
            end else begin
                bit_count = 0;
                byte_count = byte_count + 1;
                if (read_pending) begin
                    read_active = 1;
                    reads = reads + 1;
                    tx_bit = 7;
                end
            end
        end
    end
    always @(negedge scl) begin
        if (active && read_active) slave_low = ~memory[address][tx_bit];
        else slave_low = 0;
    end
endmodule
