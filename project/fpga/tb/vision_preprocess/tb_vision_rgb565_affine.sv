`timescale 1ns/1ps
module tb_vision_rgb565_affine;
    reg clk=0; always #5 clk=~clk;
    reg reset_n=0, start=0;
    wire busy, done;
    wire [7:0] error_code;
    reg [31:0] cfg_src_base=0, cfg_src_stride=0;
    reg [15:0] cfg_src_width=0, cfg_src_height=0, cfg_dst_width=0, cfg_dst_height=0;
    reg signed [31:0] cfg_a=0, cfg_b=0, cfg_c=0, cfg_d=0, cfg_e=0, cfg_f=0;
    wire rd_req_valid, rd_rsp_ready;
    wire [31:0] rd_req_addr;
    reg rd_req_ready=0, rd_rsp_valid=0, rd_rsp_error=0;
    reg [31:0] rd_rsp_data=0;
    wire [23:0] m_axis_tdata;
    wire m_axis_tvalid, m_axis_tuser, m_axis_tlast;
    reg m_axis_tready=0;
    vision_rgb565_affine dut(.*);
    localparam MAX_WORDS=1048576, MAX_PIXELS=1048576;
    reg [31:0] input_mem [0:MAX_WORDS-1];
    reg [23:0] expected_mem [0:MAX_PIXELS-1];
    reg [31:0] cfg_mem [0:11];
    reg [31:0] case_count_mem [0:0];
    string vectors, file_path;
    integer case_count, case_index, input_words, total_pixels, output_pixels=0;
    integer read_requests=0, checked_cases=0, checked_invalid=0, stalled_cycles=0;
    integer response_delay=0, frame_cycles=0, global_cycles=0;
    integer fault_request=0, mem_index, fd, j, override_count;
    reg [31:0] model_base=0, model_stride=0, model_height=0;
    reg [31:0] held_addr=0, rng=32'h6d2b79f5;
    reg pending=0, active=0, reject_reads=0, fault_enable=0, error_seen=0;
    reg output_stalled=0, request_stalled=0;
    reg [26:0] held_output;
    reg [32:0] held_request;
    reg [23:0] expected_pixel;
    reg [15:0] p565;

    always @(posedge clk) begin
        global_cycles=global_cycles+1;
        if (global_cycles>50000000) $fatal(1,"sampler global watchdog case=%0d time=%0t",case_index,$time);
        if (!reset_n) begin
            rd_req_ready<=0; rd_rsp_valid<=0; rd_rsp_error<=0;
            pending<=0; response_delay<=0; m_axis_tready<=0;
            rng<=32'h6d2b79f5; output_stalled<=0; request_stalled<=0;
        end else begin
            rng<={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};
            rd_req_ready<=!pending && !rd_rsp_valid && (rng[1] || rng[8]);
            m_axis_tready<=rng[0] && rng[6:4]!=0;
            if (output_stalled && {m_axis_tvalid,m_axis_tlast,m_axis_tuser,m_axis_tdata}!==held_output)
                $fatal(1,"sampler RGB output changed under backpressure case=%0d",case_index);
            if (request_stalled && {rd_req_valid,rd_req_addr}!==held_request)
                $fatal(1,"sampler read request changed under backpressure case=%0d",case_index);
            output_stalled<=m_axis_tvalid && !m_axis_tready;
            request_stalled<=rd_req_valid && !rd_req_ready;
            held_output<={m_axis_tvalid,m_axis_tlast,m_axis_tuser,m_axis_tdata};
            held_request<={rd_req_valid,rd_req_addr};
            if (m_axis_tvalid && !m_axis_tready) stalled_cycles=stalled_cycles+1;
            if (rd_rsp_valid && rd_rsp_ready) rd_rsp_valid<=0;
            if (rd_req_valid && rd_req_ready) begin
                if (!active || reject_reads || error_seen)
                    $fatal(1,"sampler unexpected memory read case=%0d addr=%h",case_index,rd_req_addr);
                if (pending || rd_rsp_valid) $fatal(1,"more than one abstract read outstanding");
                if (rd_req_addr[1:0]!=0 || {32'd0,rd_req_addr}<{32'd0,model_base}
                    || ({32'd0,rd_req_addr}+64'd4)>({32'd0,model_base}+{32'd0,model_stride}*{32'd0,model_height}))
                    $fatal(1,"out-of-frame or unaligned read addr=%h base=%h",rd_req_addr,model_base);
                held_addr<=rd_req_addr; pending<=1;
                response_delay<=rng[11:8]; read_requests=read_requests+1;
            end
            if (pending) begin
                if (response_delay==0) begin
                    mem_index=(held_addr-model_base)>>2;
                    if (mem_index<0 || mem_index>=input_words) $fatal(1,"memory model index out of range");
                    rd_rsp_data<=input_mem[mem_index];
                    rd_rsp_error<=fault_enable && read_requests==fault_request;
                    rd_rsp_valid<=1; pending<=0;
                end else response_delay<=response_delay-1;
            end
            if (rd_rsp_valid && rd_rsp_ready && rd_rsp_error) error_seen=1;
            if (m_axis_tvalid && m_axis_tready) begin
                if (!active || reject_reads || output_pixels>=total_pixels)
                    $fatal(1,"sampler unexpected output case=%0d pixel=%0d",case_index,output_pixels);
                expected_pixel=error_seen ? 24'd0 : expected_mem[output_pixels];
                if (m_axis_tdata!==expected_pixel)
                    $fatal(1,"sampler mismatch case=%0d pixel=%0d got=%h expected=%h",case_index,output_pixels,m_axis_tdata,expected_pixel);
                if (m_axis_tuser!==(output_pixels==0) || m_axis_tlast!==(output_pixels==total_pixels-1))
                    $fatal(1,"sampler packet metadata case=%0d pixel=%0d user=%b last=%b",case_index,output_pixels,m_axis_tuser,m_axis_tlast);
                output_pixels=output_pixels+1;
            end
        end
    end
    task set_config;
        begin
            cfg_src_base=cfg_mem[0]; cfg_src_stride=cfg_mem[1];
            cfg_src_width=cfg_mem[2]; cfg_src_height=cfg_mem[3];
            cfg_dst_width=cfg_mem[4]; cfg_dst_height=cfg_mem[5];
            cfg_a=cfg_mem[6]; cfg_b=cfg_mem[7]; cfg_c=cfg_mem[8];
            cfg_d=cfg_mem[9]; cfg_e=cfg_mem[10]; cfg_f=cfg_mem[11];
        end
    endtask
    task start_and_wait;
        input integer expected_error;
        input integer invalid_task;
        begin
            @(negedge clk);
            set_config();
            model_base=cfg_mem[0]; model_stride=cfg_mem[1]; model_height=cfg_mem[3];
            output_pixels=0; read_requests=0; error_seen=0;
            reject_reads=invalid_task; active=1; start=1;
            @(negedge clk); start=0;
            if (!invalid_task) begin
                if (!busy || done) $fatal(1,"legal task did not become busy");
                // Busy START and configuration edits must not alter the snapshot.
                cfg_src_base=32'hdeadbeef; cfg_src_stride=0;
                cfg_src_width=0; cfg_src_height=0; cfg_dst_width=0; cfg_dst_height=0;
                cfg_a=32'h7fffffff; cfg_b=32'h80000000; cfg_c=32'h12345678;
                cfg_d=32'h80000000; cfg_e=32'h7fffffff; cfg_f=32'h87654321;
                start=1;
                repeat(2) @(negedge clk);
                start=0;
            end
            frame_cycles=0;
            while (!done) begin
                @(negedge clk); frame_cycles=frame_cycles+1;
                if (frame_cycles>10000000) $fatal(1,"sampler task timeout case=%0d outputs=%0d",case_index,output_pixels);
            end
            if (busy || error_code!==expected_error)
                $fatal(1,"sampler completion case=%0d busy=%b error=%0d expected=%0d",case_index,busy,error_code,expected_error);
            if (invalid_task) begin
                if (read_requests!=0 || output_pixels!=0) $fatal(1,"illegal config caused IO");
                checked_invalid=checked_invalid+1;
            end else begin
                if (output_pixels!=total_pixels) $fatal(1,"sampler output count %0d expected %0d",output_pixels,total_pixels);
                if (pending || rd_rsp_valid) $fatal(1,"sampler done with outstanding read");
                checked_cases=checked_cases+1;
            end
            active=0;
            repeat(3) @(negedge clk);
            if (done || busy || m_axis_tvalid || rd_req_valid || error_code!==expected_error)
                $fatal(1,"sampler did not remain idle/status stable after done");
        end
    endtask
    task basic_config;
        begin
            cfg_mem[0]=32'h00001000; cfg_mem[1]=16;
            cfg_mem[2]=8; cfg_mem[3]=2; cfg_mem[4]=8; cfg_mem[5]=2;
            cfg_mem[6]=65536; cfg_mem[7]=0; cfg_mem[8]=0;
            cfg_mem[9]=0; cfg_mem[10]=65536; cfg_mem[11]=0;
        end
    endtask
    initial begin
        $display("SAMPLER deterministic seed=6d2b79f5");
        if (!$value$plusargs("VECTORS=%s",vectors))
            vectors="project/_tmp/vision_preprocess_vectors_20261028";
        file_path={vectors,"/case_count.mem"};
        fd=$fopen(file_path,"r");
        if (fd==0) $fatal(1,"missing fixtures %s; pass +VECTORS=<directory>",file_path);
        $fclose(fd); $readmemh(file_path,case_count_mem);
        case_count=case_count_mem[0];
        if ($value$plusargs("CASE_COUNT=%d",override_count)) case_count=override_count;
        if (case_count<1 || case_count>1000) $fatal(1,"invalid fixture count %0d",case_count);
        repeat(5) @(negedge clk); reset_n=1;
        for (case_index=0;case_index<case_count;case_index=case_index+1) begin
            file_path=$sformatf("%s/case_%0d_cfg.mem",vectors,case_index); $readmemh(file_path,cfg_mem);
            input_words=(cfg_mem[1]*cfg_mem[3])/4;
            total_pixels=cfg_mem[4]*cfg_mem[5];
            if (input_words<1 || input_words>MAX_WORDS || total_pixels<1 || total_pixels>MAX_PIXELS)
                $fatal(1,"fixture memory capacity exceeded case=%0d",case_index);
            file_path=$sformatf("%s/case_%0d_input.mem",vectors,case_index); $readmemh(file_path,input_mem,0,input_words-1);
            file_path=$sformatf("%s/case_%0d_expected.mem",vectors,case_index); $readmemh(file_path,expected_mem,0,total_pixels-1);
            fault_enable=0; start_and_wait(0,0);
            $display("CASE_PASS %0d pixels=%0d reads=%0d cycles=%0d",case_index,total_pixels,read_requests,frame_cycles);
        end
        // Inject an error on a later cache miss. Previously completed pixels
        // retain their values; all not-yet-emitted pixels must drain as black.
        basic_config(); input_words=8; total_pixels=16;
        for (j=0;j<16;j=j+1) begin
            p565=(j*13+32'h4210)&16'hffff;
            if (j[0]) input_mem[j/2][31:16]=p565;
            else input_mem[j/2][15:0]=p565;
            expected_mem[j]={{p565[4:0],p565[4:2]}, {p565[10:5],p565[10:9]}, {p565[15:11],p565[15:13]}};
        end
        fault_enable=1; fault_request=3; start_and_wait(4,0);
        if (read_requests!=fault_request || !error_seen) $fatal(1,"read-error stop not exercised");
        fault_enable=0;
        // A new task reuses the same physical addresses with changed content.
        // No stale cache entries or sticky read-error state may leak across it.
        for (j=0;j<16;j=j+1) begin
            p565=(32'h9ce7+j*29)&16'hffff;
            if (j[0]) input_mem[j/2][31:16]=p565;
            else input_mem[j/2][15:0]=p565;
            expected_mem[j]={{p565[4:0],p565[4:2]}, {p565[10:5],p565[10:9]}, {p565[15:11],p565[15:13]}};
        end
        start_and_wait(0,0);
        // Validate dimensions, stride, alignment, full-frame 32-bit extent,
        // error priority, and post-error recovery without global reset.
        basic_config(); cfg_mem[2]=0; start_and_wait(1,1);
        basic_config(); cfg_mem[2]=4097; start_and_wait(1,1);
        basic_config(); cfg_mem[3]=0; start_and_wait(1,1);
        basic_config(); cfg_mem[3]=4097; start_and_wait(1,1);
        basic_config(); cfg_mem[4]=0; start_and_wait(1,1);
        basic_config(); cfg_mem[4]=2049; start_and_wait(1,1);
        basic_config(); cfg_mem[5]=0; start_and_wait(1,1);
        basic_config(); cfg_mem[5]=2049; start_and_wait(1,1);
        basic_config(); cfg_mem[1]=12; start_and_wait(1,1);
        basic_config(); cfg_mem[1]=0; start_and_wait(1,1);
        basic_config(); cfg_mem[1]=6; start_and_wait(1,1);
        basic_config(); cfg_mem[0]=32'h1002; start_and_wait(2,1);
        basic_config(); cfg_mem[1]=18; start_and_wait(2,1);
        basic_config(); cfg_mem[0]=32'hfffffff0; start_and_wait(3,1);
        basic_config(); cfg_mem[1]=32'hfffffffc; start_and_wait(3,1);
        // Exact address-space endpoint is legal; only its single first source
        // pixel is needed and the full aligned word must remain in range.
        basic_config(); cfg_mem[0]=32'hfffffffc; cfg_mem[1]=4;
        cfg_mem[2]=1; cfg_mem[3]=1; cfg_mem[4]=1; cfg_mem[5]=1;
        input_words=1; total_pixels=1; input_mem[0]=32'h0000ffff; expected_mem[0]=24'hffffff;
        start_and_wait(0,0);
        if (stalled_cycles==0) $fatal(1,"sampler backpressure not exercised");
        $display("TEST_PASS tb_vision_rgb565_affine frames=%0d invalid=%0d stalled_cycles=%0d",checked_cases,checked_invalid,stalled_cycles);
        $finish;
    end
endmodule
