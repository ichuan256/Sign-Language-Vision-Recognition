`timescale 1ns/1ps

module tb_kws_mlp_accel;
    localparam integer VECTOR_COUNT = 8;
    localparam integer WORDS_PER_VECTOR = 30; // 26 Q12 inputs, class, 3 scores
    reg clk = 0;
    reg resetn = 0;
    always #5 clk = ~clk;

    reg [7:0] awaddr = 0;
    reg awvalid = 0;
    wire awready;
    reg [31:0] wdata = 0;
    reg [3:0] wstrb = 4'hf;
    reg wvalid = 0;
    wire wready;
    wire [1:0] bresp;
    wire bvalid;
    reg bready = 0;
    reg [7:0] araddr = 0;
    reg arvalid = 0;
    wire arready;
    wire [31:0] rdata;
    wire [1:0] rresp;
    wire rvalid;
    reg rready = 0;

    reg [31:0] vectors [0:VECTOR_COUNT*WORDS_PER_VECTOR-1];
    integer vector_id, feature_id, cycles, errors, accepted;
    reg [31:0] value;

    kws_mlp_accel dut (
        .s_axi_aclk(clk), .s_axi_aresetn(resetn),
        .s_axi_awaddr(awaddr), .s_axi_awvalid(awvalid), .s_axi_awready(awready),
        .s_axi_wdata(wdata), .s_axi_wstrb(wstrb), .s_axi_wvalid(wvalid), .s_axi_wready(wready),
        .s_axi_bresp(bresp), .s_axi_bvalid(bvalid), .s_axi_bready(bready),
        .s_axi_araddr(araddr), .s_axi_arvalid(arvalid), .s_axi_arready(arready),
        .s_axi_rdata(rdata), .s_axi_rresp(rresp), .s_axi_rvalid(rvalid), .s_axi_rready(rready)
    );

    task axi_write;
        input [7:0] address;
        input [31:0] data;
        input order; // 0: AW then W; 1: W then AW
        begin
            if (order == 0) begin
                @(negedge clk); awaddr = address; awvalid = 1;
                while (!awready) @(posedge clk);
                @(negedge clk); awvalid = 0; wdata = data; wstrb = 4'hf; wvalid = 1;
                while (!wready) @(posedge clk);
            end else begin
                @(negedge clk); wdata = data; wstrb = 4'hf; wvalid = 1;
                while (!wready) @(posedge clk);
                @(negedge clk); wvalid = 0; awaddr = address; awvalid = 1;
                while (!awready) @(posedge clk);
            end
            @(negedge clk); awvalid = 0; wvalid = 0; bready = 1;
            while (!bvalid) @(posedge clk);
            if (bresp != 2'b00) begin
                $display("ERROR AXI write SLVERR addr=%02x data=%08x", address, data);
                errors = errors + 1;
            end
            @(posedge clk);
            @(negedge clk); bready = 0;
        end
    endtask

    task axi_write_expect_error;
        input [7:0] address;
        input [31:0] data;
        begin
            @(negedge clk); awaddr = address; awvalid = 1; wdata = data; wstrb = 4'hf; wvalid = 1;
            while (!(awready && wready)) @(posedge clk);
            @(negedge clk); awvalid = 0; wvalid = 0; bready = 1;
            while (!bvalid) @(posedge clk);
            if (bresp != 2'b10) begin
                $display("ERROR expected SLVERR addr=%02x got=%b", address, bresp);
                errors = errors + 1;
            end
            @(posedge clk);
            @(negedge clk); bready = 0;
        end
    endtask

    task axi_read;
        input [7:0] address;
        output [31:0] data;
        begin
            @(negedge clk); araddr = address; arvalid = 1;
            while (!arready) @(posedge clk);
            @(negedge clk); arvalid = 0; rready = 1;
            while (!rvalid) @(posedge clk);
            data = rdata;
            if (rresp != 2'b00) begin
                $display("ERROR AXI read SLVERR addr=%02x", address);
                errors = errors + 1;
            end
            @(posedge clk);
            @(negedge clk); rready = 0;
        end
    endtask

    initial begin
        errors = 0;
        accepted = 0;
        $readmemh("kws_mlp_vectors.mem", vectors);
        repeat (8) @(posedge clk);
        @(negedge clk); resetn = 1;
        axi_read(8'h04, value);
        if (value != 32'h4b575301) begin
            $display("ERROR magic=%08x", value); errors = errors + 1;
        end

        // A start without all 26 features must be rejected and reported.
        axi_write_expect_error(8'h00, 32'h00000001);
        axi_read(8'h00, value);
        if ((value & 8) == 0) begin
            $display("ERROR incomplete-input status bit was not set"); errors = errors + 1;
        end
        axi_write(8'h00, 32'h00000008, 0); // clear sticky error

        for (vector_id = 0; vector_id < VECTOR_COUNT; vector_id = vector_id + 1) begin
            for (feature_id = 0; feature_id < 26; feature_id = feature_id + 1)
                axi_write(8'h10 + 4 * feature_id,
                          vectors[vector_id * WORDS_PER_VECTOR + feature_id],
                          feature_id[0]);

            axi_read(8'h0c, value);
            if (value[25:0] != 26'h3ffffff) begin
                $display("ERROR vector=%0d valid mask=%08x", vector_id, value);
                errors = errors + 1;
            end
            axi_write(8'h00, 32'h00000001, vector_id[0]);

            accepted = 0;
            for (cycles = 0; cycles < 200; cycles = cycles + 1) begin
                axi_read(8'h00, value);
                if (value[1]) begin accepted = 1; cycles = 200; end
            end
            if (!accepted) begin
                $display("ERROR vector=%0d inference did not finish", vector_id);
                errors = errors + 1;
            end else begin
                axi_read(8'h08, value);
                if (value != 273) begin
                    $display("ERROR vector=%0d cycle count=%0d expected 273", vector_id, value);
                    errors = errors + 1;
                end
                axi_read(8'h8c, value);
                if (value !== vectors[vector_id * WORDS_PER_VECTOR + 26]) begin
                    $display("ERROR vector=%0d class=%0d expected=%0d", vector_id, value,
                             vectors[vector_id * WORDS_PER_VECTOR + 26]);
                    errors = errors + 1;
                end
                axi_read(8'h80, value);
                if (value !== vectors[vector_id * WORDS_PER_VECTOR + 27]) begin
                    $display("ERROR vector=%0d score0=%08x expected=%08x", vector_id, value,
                             vectors[vector_id * WORDS_PER_VECTOR + 27]);
                    errors = errors + 1;
                end
                axi_read(8'h84, value);
                if (value !== vectors[vector_id * WORDS_PER_VECTOR + 28]) begin
                    $display("ERROR vector=%0d score1=%08x expected=%08x", vector_id, value,
                             vectors[vector_id * WORDS_PER_VECTOR + 28]);
                    errors = errors + 1;
                end
                axi_read(8'h88, value);
                if (value !== vectors[vector_id * WORDS_PER_VECTOR + 29]) begin
                    $display("ERROR vector=%0d score2=%08x expected=%08x", vector_id, value,
                             vectors[vector_id * WORDS_PER_VECTOR + 29]);
                    errors = errors + 1;
                end
                $display("PASS vector=%0d class=%0d scores=[%0d,%0d,%0d] cycles=273",
                         vector_id, vectors[vector_id * WORDS_PER_VECTOR + 26],
                         $signed(vectors[vector_id * WORDS_PER_VECTOR + 27]),
                         $signed(vectors[vector_id * WORDS_PER_VECTOR + 28]),
                         $signed(vectors[vector_id * WORDS_PER_VECTOR + 29]));
            end
        end

        if (errors == 0)
            $display("==== TEST PASSED: %0d MLP vectors plus AXI protocol/error checks ====", VECTOR_COUNT);
        else
            $display("==== TEST FAILED: %0d errors ====", errors);
        $finish;
    end

    initial begin
        #2_000_000;
        $display("==== TEST FAILED: watchdog timeout ====");
        $finish;
    end
endmodule
