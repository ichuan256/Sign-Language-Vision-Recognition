set moduleName kp_hls_pw_core_2_6_6_48_64_s
set isTopModule 0
set isCombinational 0
set isDatapathOnly 0
set isPipelined 0
set pipeline_type none
set FunctionProtocol ap_ctrl_hs
set isOneStateSeq 0
set ProfileFlag 0
set StallSigGenFlag 0
set isEnableWaveformDebug 1
set hasInterrupt 0
set DLRegFirstOffset 0
set DLRegItemOffset 0
set C_modelName {kp_hls_pw_core<2, 6, 6, 48, 64>}
set C_modelType { void 0 }
set ap_memory_interface_dict [dict create]
set C_modelArgList {
	{ gmem int 64 regular {axi_master 2}  }
	{ in_r int 64 regular  }
	{ w int 64 regular  }
	{ bias int 64 regular  }
	{ M int 64 regular  }
	{ F int 32 regular  }
	{ out_r int 64 regular  }
}
set hasAXIMCache 0
set hasAXIML2Cache 0
set AXIMCacheInstDict [dict create]
set C_modelArgMapList {[ 
	{ "Name" : "gmem", "interface" : "axi_master", "bitwidth" : 64, "direction" : "READWRITE", "bitSlice":[ {"cElement": [{"cName": "in_r","offset": { "type": "dynamic","port_name": "in_r","bundle": "ctrl"},"direction": "READONLY"},{"cName": "w","offset": { "type": "dynamic","port_name": "w","bundle": "ctrl"},"direction": "READONLY"},{"cName": "bias","offset": { "type": "dynamic","port_name": "bias","bundle": "ctrl"},"direction": "READONLY"},{"cName": "M","offset": { "type": "dynamic","port_name": "M","bundle": "ctrl"},"direction": "READONLY"},{"cName": "out_r","offset": { "type": "dynamic","port_name": "out_r","bundle": "ctrl"},"direction": "WRITEONLY"}]}]} , 
 	{ "Name" : "in_r", "interface" : "wire", "bitwidth" : 64, "direction" : "READONLY"} , 
 	{ "Name" : "w", "interface" : "wire", "bitwidth" : 64, "direction" : "READONLY"} , 
 	{ "Name" : "bias", "interface" : "wire", "bitwidth" : 64, "direction" : "READONLY"} , 
 	{ "Name" : "M", "interface" : "wire", "bitwidth" : 64, "direction" : "READONLY"} , 
 	{ "Name" : "F", "interface" : "wire", "bitwidth" : 32, "direction" : "READONLY"} , 
 	{ "Name" : "out_r", "interface" : "wire", "bitwidth" : 64, "direction" : "READONLY"} ]}
# RTL Port declarations: 
set portNum 58
set portList { 
	{ ap_clk sc_in sc_logic 1 clock -1 } 
	{ ap_rst sc_in sc_logic 1 reset -1 active_high_sync } 
	{ ap_start sc_in sc_logic 1 start -1 } 
	{ ap_done sc_out sc_logic 1 predone -1 } 
	{ ap_idle sc_out sc_logic 1 done -1 } 
	{ ap_ready sc_out sc_logic 1 ready -1 } 
	{ m_axi_gmem_AWVALID sc_out sc_logic 1 signal 0 } 
	{ m_axi_gmem_AWREADY sc_in sc_logic 1 signal 0 } 
	{ m_axi_gmem_AWADDR sc_out sc_lv 64 signal 0 } 
	{ m_axi_gmem_AWID sc_out sc_lv 1 signal 0 } 
	{ m_axi_gmem_AWLEN sc_out sc_lv 32 signal 0 } 
	{ m_axi_gmem_AWSIZE sc_out sc_lv 3 signal 0 } 
	{ m_axi_gmem_AWBURST sc_out sc_lv 2 signal 0 } 
	{ m_axi_gmem_AWLOCK sc_out sc_lv 2 signal 0 } 
	{ m_axi_gmem_AWCACHE sc_out sc_lv 4 signal 0 } 
	{ m_axi_gmem_AWPROT sc_out sc_lv 3 signal 0 } 
	{ m_axi_gmem_AWQOS sc_out sc_lv 4 signal 0 } 
	{ m_axi_gmem_AWREGION sc_out sc_lv 4 signal 0 } 
	{ m_axi_gmem_AWUSER sc_out sc_lv 1 signal 0 } 
	{ m_axi_gmem_WVALID sc_out sc_logic 1 signal 0 } 
	{ m_axi_gmem_WREADY sc_in sc_logic 1 signal 0 } 
	{ m_axi_gmem_WDATA sc_out sc_lv 64 signal 0 } 
	{ m_axi_gmem_WSTRB sc_out sc_lv 8 signal 0 } 
	{ m_axi_gmem_WLAST sc_out sc_logic 1 signal 0 } 
	{ m_axi_gmem_WID sc_out sc_lv 1 signal 0 } 
	{ m_axi_gmem_WUSER sc_out sc_lv 1 signal 0 } 
	{ m_axi_gmem_ARVALID sc_out sc_logic 1 signal 0 } 
	{ m_axi_gmem_ARREADY sc_in sc_logic 1 signal 0 } 
	{ m_axi_gmem_ARADDR sc_out sc_lv 64 signal 0 } 
	{ m_axi_gmem_ARID sc_out sc_lv 1 signal 0 } 
	{ m_axi_gmem_ARLEN sc_out sc_lv 32 signal 0 } 
	{ m_axi_gmem_ARSIZE sc_out sc_lv 3 signal 0 } 
	{ m_axi_gmem_ARBURST sc_out sc_lv 2 signal 0 } 
	{ m_axi_gmem_ARLOCK sc_out sc_lv 2 signal 0 } 
	{ m_axi_gmem_ARCACHE sc_out sc_lv 4 signal 0 } 
	{ m_axi_gmem_ARPROT sc_out sc_lv 3 signal 0 } 
	{ m_axi_gmem_ARQOS sc_out sc_lv 4 signal 0 } 
	{ m_axi_gmem_ARREGION sc_out sc_lv 4 signal 0 } 
	{ m_axi_gmem_ARUSER sc_out sc_lv 1 signal 0 } 
	{ m_axi_gmem_RVALID sc_in sc_logic 1 signal 0 } 
	{ m_axi_gmem_RREADY sc_out sc_logic 1 signal 0 } 
	{ m_axi_gmem_RDATA sc_in sc_lv 64 signal 0 } 
	{ m_axi_gmem_RLAST sc_in sc_logic 1 signal 0 } 
	{ m_axi_gmem_RID sc_in sc_lv 1 signal 0 } 
	{ m_axi_gmem_RFIFONUM sc_in sc_lv 9 signal 0 } 
	{ m_axi_gmem_RUSER sc_in sc_lv 1 signal 0 } 
	{ m_axi_gmem_RRESP sc_in sc_lv 2 signal 0 } 
	{ m_axi_gmem_BVALID sc_in sc_logic 1 signal 0 } 
	{ m_axi_gmem_BREADY sc_out sc_logic 1 signal 0 } 
	{ m_axi_gmem_BRESP sc_in sc_lv 2 signal 0 } 
	{ m_axi_gmem_BID sc_in sc_lv 1 signal 0 } 
	{ m_axi_gmem_BUSER sc_in sc_lv 1 signal 0 } 
	{ in_r sc_in sc_lv 64 signal 1 } 
	{ w sc_in sc_lv 64 signal 2 } 
	{ bias sc_in sc_lv 64 signal 3 } 
	{ M sc_in sc_lv 64 signal 4 } 
	{ F sc_in sc_lv 32 signal 5 } 
	{ out_r sc_in sc_lv 64 signal 6 } 
}
set NewPortList {[ 
	{ "name": "ap_clk", "direction": "in", "datatype": "sc_logic", "bitwidth":1, "type": "clock", "bundle":{"name": "ap_clk", "role": "default" }} , 
 	{ "name": "ap_rst", "direction": "in", "datatype": "sc_logic", "bitwidth":1, "type": "reset", "bundle":{"name": "ap_rst", "role": "default" }} , 
 	{ "name": "ap_start", "direction": "in", "datatype": "sc_logic", "bitwidth":1, "type": "start", "bundle":{"name": "ap_start", "role": "default" }} , 
 	{ "name": "ap_done", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "predone", "bundle":{"name": "ap_done", "role": "default" }} , 
 	{ "name": "ap_idle", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "done", "bundle":{"name": "ap_idle", "role": "default" }} , 
 	{ "name": "ap_ready", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "ready", "bundle":{"name": "ap_ready", "role": "default" }} , 
 	{ "name": "m_axi_gmem_AWVALID", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "gmem", "role": "AWVALID" }} , 
 	{ "name": "m_axi_gmem_AWREADY", "direction": "in", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "gmem", "role": "AWREADY" }} , 
 	{ "name": "m_axi_gmem_AWADDR", "direction": "out", "datatype": "sc_lv", "bitwidth":64, "type": "signal", "bundle":{"name": "gmem", "role": "AWADDR" }} , 
 	{ "name": "m_axi_gmem_AWID", "direction": "out", "datatype": "sc_lv", "bitwidth":1, "type": "signal", "bundle":{"name": "gmem", "role": "AWID" }} , 
 	{ "name": "m_axi_gmem_AWLEN", "direction": "out", "datatype": "sc_lv", "bitwidth":32, "type": "signal", "bundle":{"name": "gmem", "role": "AWLEN" }} , 
 	{ "name": "m_axi_gmem_AWSIZE", "direction": "out", "datatype": "sc_lv", "bitwidth":3, "type": "signal", "bundle":{"name": "gmem", "role": "AWSIZE" }} , 
 	{ "name": "m_axi_gmem_AWBURST", "direction": "out", "datatype": "sc_lv", "bitwidth":2, "type": "signal", "bundle":{"name": "gmem", "role": "AWBURST" }} , 
 	{ "name": "m_axi_gmem_AWLOCK", "direction": "out", "datatype": "sc_lv", "bitwidth":2, "type": "signal", "bundle":{"name": "gmem", "role": "AWLOCK" }} , 
 	{ "name": "m_axi_gmem_AWCACHE", "direction": "out", "datatype": "sc_lv", "bitwidth":4, "type": "signal", "bundle":{"name": "gmem", "role": "AWCACHE" }} , 
 	{ "name": "m_axi_gmem_AWPROT", "direction": "out", "datatype": "sc_lv", "bitwidth":3, "type": "signal", "bundle":{"name": "gmem", "role": "AWPROT" }} , 
 	{ "name": "m_axi_gmem_AWQOS", "direction": "out", "datatype": "sc_lv", "bitwidth":4, "type": "signal", "bundle":{"name": "gmem", "role": "AWQOS" }} , 
 	{ "name": "m_axi_gmem_AWREGION", "direction": "out", "datatype": "sc_lv", "bitwidth":4, "type": "signal", "bundle":{"name": "gmem", "role": "AWREGION" }} , 
 	{ "name": "m_axi_gmem_AWUSER", "direction": "out", "datatype": "sc_lv", "bitwidth":1, "type": "signal", "bundle":{"name": "gmem", "role": "AWUSER" }} , 
 	{ "name": "m_axi_gmem_WVALID", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "gmem", "role": "WVALID" }} , 
 	{ "name": "m_axi_gmem_WREADY", "direction": "in", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "gmem", "role": "WREADY" }} , 
 	{ "name": "m_axi_gmem_WDATA", "direction": "out", "datatype": "sc_lv", "bitwidth":64, "type": "signal", "bundle":{"name": "gmem", "role": "WDATA" }} , 
 	{ "name": "m_axi_gmem_WSTRB", "direction": "out", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "gmem", "role": "WSTRB" }} , 
 	{ "name": "m_axi_gmem_WLAST", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "gmem", "role": "WLAST" }} , 
 	{ "name": "m_axi_gmem_WID", "direction": "out", "datatype": "sc_lv", "bitwidth":1, "type": "signal", "bundle":{"name": "gmem", "role": "WID" }} , 
 	{ "name": "m_axi_gmem_WUSER", "direction": "out", "datatype": "sc_lv", "bitwidth":1, "type": "signal", "bundle":{"name": "gmem", "role": "WUSER" }} , 
 	{ "name": "m_axi_gmem_ARVALID", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "gmem", "role": "ARVALID" }} , 
 	{ "name": "m_axi_gmem_ARREADY", "direction": "in", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "gmem", "role": "ARREADY" }} , 
 	{ "name": "m_axi_gmem_ARADDR", "direction": "out", "datatype": "sc_lv", "bitwidth":64, "type": "signal", "bundle":{"name": "gmem", "role": "ARADDR" }} , 
 	{ "name": "m_axi_gmem_ARID", "direction": "out", "datatype": "sc_lv", "bitwidth":1, "type": "signal", "bundle":{"name": "gmem", "role": "ARID" }} , 
 	{ "name": "m_axi_gmem_ARLEN", "direction": "out", "datatype": "sc_lv", "bitwidth":32, "type": "signal", "bundle":{"name": "gmem", "role": "ARLEN" }} , 
 	{ "name": "m_axi_gmem_ARSIZE", "direction": "out", "datatype": "sc_lv", "bitwidth":3, "type": "signal", "bundle":{"name": "gmem", "role": "ARSIZE" }} , 
 	{ "name": "m_axi_gmem_ARBURST", "direction": "out", "datatype": "sc_lv", "bitwidth":2, "type": "signal", "bundle":{"name": "gmem", "role": "ARBURST" }} , 
 	{ "name": "m_axi_gmem_ARLOCK", "direction": "out", "datatype": "sc_lv", "bitwidth":2, "type": "signal", "bundle":{"name": "gmem", "role": "ARLOCK" }} , 
 	{ "name": "m_axi_gmem_ARCACHE", "direction": "out", "datatype": "sc_lv", "bitwidth":4, "type": "signal", "bundle":{"name": "gmem", "role": "ARCACHE" }} , 
 	{ "name": "m_axi_gmem_ARPROT", "direction": "out", "datatype": "sc_lv", "bitwidth":3, "type": "signal", "bundle":{"name": "gmem", "role": "ARPROT" }} , 
 	{ "name": "m_axi_gmem_ARQOS", "direction": "out", "datatype": "sc_lv", "bitwidth":4, "type": "signal", "bundle":{"name": "gmem", "role": "ARQOS" }} , 
 	{ "name": "m_axi_gmem_ARREGION", "direction": "out", "datatype": "sc_lv", "bitwidth":4, "type": "signal", "bundle":{"name": "gmem", "role": "ARREGION" }} , 
 	{ "name": "m_axi_gmem_ARUSER", "direction": "out", "datatype": "sc_lv", "bitwidth":1, "type": "signal", "bundle":{"name": "gmem", "role": "ARUSER" }} , 
 	{ "name": "m_axi_gmem_RVALID", "direction": "in", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "gmem", "role": "RVALID" }} , 
 	{ "name": "m_axi_gmem_RREADY", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "gmem", "role": "RREADY" }} , 
 	{ "name": "m_axi_gmem_RDATA", "direction": "in", "datatype": "sc_lv", "bitwidth":64, "type": "signal", "bundle":{"name": "gmem", "role": "RDATA" }} , 
 	{ "name": "m_axi_gmem_RLAST", "direction": "in", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "gmem", "role": "RLAST" }} , 
 	{ "name": "m_axi_gmem_RID", "direction": "in", "datatype": "sc_lv", "bitwidth":1, "type": "signal", "bundle":{"name": "gmem", "role": "RID" }} , 
 	{ "name": "m_axi_gmem_RFIFONUM", "direction": "in", "datatype": "sc_lv", "bitwidth":9, "type": "signal", "bundle":{"name": "gmem", "role": "RFIFONUM" }} , 
 	{ "name": "m_axi_gmem_RUSER", "direction": "in", "datatype": "sc_lv", "bitwidth":1, "type": "signal", "bundle":{"name": "gmem", "role": "RUSER" }} , 
 	{ "name": "m_axi_gmem_RRESP", "direction": "in", "datatype": "sc_lv", "bitwidth":2, "type": "signal", "bundle":{"name": "gmem", "role": "RRESP" }} , 
 	{ "name": "m_axi_gmem_BVALID", "direction": "in", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "gmem", "role": "BVALID" }} , 
 	{ "name": "m_axi_gmem_BREADY", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "gmem", "role": "BREADY" }} , 
 	{ "name": "m_axi_gmem_BRESP", "direction": "in", "datatype": "sc_lv", "bitwidth":2, "type": "signal", "bundle":{"name": "gmem", "role": "BRESP" }} , 
 	{ "name": "m_axi_gmem_BID", "direction": "in", "datatype": "sc_lv", "bitwidth":1, "type": "signal", "bundle":{"name": "gmem", "role": "BID" }} , 
 	{ "name": "m_axi_gmem_BUSER", "direction": "in", "datatype": "sc_lv", "bitwidth":1, "type": "signal", "bundle":{"name": "gmem", "role": "BUSER" }} , 
 	{ "name": "in_r", "direction": "in", "datatype": "sc_lv", "bitwidth":64, "type": "signal", "bundle":{"name": "in_r", "role": "default" }} , 
 	{ "name": "w", "direction": "in", "datatype": "sc_lv", "bitwidth":64, "type": "signal", "bundle":{"name": "w", "role": "default" }} , 
 	{ "name": "bias", "direction": "in", "datatype": "sc_lv", "bitwidth":64, "type": "signal", "bundle":{"name": "bias", "role": "default" }} , 
 	{ "name": "M", "direction": "in", "datatype": "sc_lv", "bitwidth":64, "type": "signal", "bundle":{"name": "M", "role": "default" }} , 
 	{ "name": "F", "direction": "in", "datatype": "sc_lv", "bitwidth":32, "type": "signal", "bundle":{"name": "F", "role": "default" }} , 
 	{ "name": "out_r", "direction": "in", "datatype": "sc_lv", "bitwidth":64, "type": "signal", "bundle":{"name": "out_r", "role": "default" }}  ]}

set RtlHierarchyInfo {[
	{"ID" : "0", "Level" : "0", "Path" : "`AUTOTB_DUT_INST", "Parent" : "", "Child" : ["1"],
		"CDFG" : "kp_hls_pw_core_2_6_6_48_64_s",
		"Protocol" : "ap_ctrl_hs",
		"ControlExist" : "1", "ap_start" : "1", "ap_ready" : "1", "ap_done" : "1", "ap_continue" : "0", "ap_idle" : "1", "real_start" : "0",
		"Pipeline" : "None", "UnalignedPipeline" : "0", "RewindPipeline" : "0", "ProcessNetwork" : "0",
		"II" : "0",
		"VariableLatency" : "1", "ExactLatency" : "-1", "EstimateLatencyMin" : "236910", "EstimateLatencyMax" : "236910",
		"Combinational" : "0",
		"Datapath" : "0",
		"ClockEnable" : "0",
		"HasSubDataflow" : "0",
		"InDataflowNetwork" : "0",
		"HasNonBlockingOperation" : "0",
		"IsBlackBox" : "0",
		"Port" : [
			{"Name" : "gmem", "Type" : "MAXI", "Direction" : "IO",
				"BlockSignal" : [
					{"Name" : "gmem_blk_n_AR", "Type" : "RtlSignal"},
					{"Name" : "gmem_blk_n_R", "Type" : "RtlSignal"}],
				"SubConnect" : [
					{"ID" : "1", "SubInstance" : "grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874", "Port" : "gmem", "Inst_start_state" : "63", "Inst_end_state" : "64"}]},
			{"Name" : "in_r", "Type" : "None", "Direction" : "I"},
			{"Name" : "w", "Type" : "None", "Direction" : "I"},
			{"Name" : "bias", "Type" : "None", "Direction" : "I"},
			{"Name" : "M", "Type" : "None", "Direction" : "I"},
			{"Name" : "F", "Type" : "None", "Direction" : "I"},
			{"Name" : "out_r", "Type" : "None", "Direction" : "I"}],
		"Loop" : [
			{"Name" : "VITIS_LOOP_83_3", "PipelineType" : "no",
				"LoopDec" : {"FSMBitwidth" : "64", "FirstState" : "ap_ST_fsm_state5", "LastState" : ["ap_ST_fsm_state64"], "QuitState" : ["ap_ST_fsm_state5"], "PreState" : ["ap_ST_fsm_state4"], "PostState" : ["ap_ST_fsm_state4"], "OneDepthLoop" : "0", "OneStateBlock": ""}},
			{"Name" : "VITIS_LOOP_82_2", "PipelineType" : "no",
				"LoopDec" : {"FSMBitwidth" : "64", "FirstState" : "ap_ST_fsm_state4", "LastState" : ["ap_ST_fsm_state5"], "QuitState" : ["ap_ST_fsm_state4"], "PreState" : ["ap_ST_fsm_state3"], "PostState" : ["ap_ST_fsm_state3"], "OneDepthLoop" : "0", "OneStateBlock": ""}},
			{"Name" : "VITIS_LOOP_81_1", "PipelineType" : "no",
				"LoopDec" : {"FSMBitwidth" : "64", "FirstState" : "ap_ST_fsm_state3", "LastState" : ["ap_ST_fsm_state4"], "QuitState" : ["ap_ST_fsm_state3"], "PreState" : ["ap_ST_fsm_state2"], "PostState" : ["ap_ST_fsm_state1"], "OneDepthLoop" : "0", "OneStateBlock": ""}}]},
	{"ID" : "1", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874", "Parent" : "0", "Child" : ["2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46", "47", "48", "49", "50", "51"],
		"CDFG" : "kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4",
		"Protocol" : "ap_ctrl_hs",
		"ControlExist" : "1", "ap_start" : "1", "ap_ready" : "1", "ap_done" : "1", "ap_continue" : "0", "ap_idle" : "1", "real_start" : "0",
		"Pipeline" : "None", "UnalignedPipeline" : "0", "RewindPipeline" : "0", "ProcessNetwork" : "0",
		"II" : "0",
		"VariableLatency" : "1", "ExactLatency" : "-1", "EstimateLatencyMin" : "3230", "EstimateLatencyMax" : "3230",
		"Combinational" : "0",
		"Datapath" : "0",
		"ClockEnable" : "0",
		"HasSubDataflow" : "0",
		"InDataflowNetwork" : "0",
		"HasNonBlockingOperation" : "0",
		"IsBlackBox" : "0",
		"Port" : [
			{"Name" : "sext_ln81", "Type" : "None", "Direction" : "I"},
			{"Name" : "gmem", "Type" : "MAXI", "Direction" : "IO",
				"BlockSignal" : [
					{"Name" : "gmem_blk_n_AR", "Type" : "RtlSignal"},
					{"Name" : "gmem_blk_n_R", "Type" : "RtlSignal"},
					{"Name" : "gmem_blk_n_AW", "Type" : "RtlSignal"},
					{"Name" : "gmem_blk_n_W", "Type" : "RtlSignal"},
					{"Name" : "gmem_blk_n_B", "Type" : "RtlSignal"}]},
			{"Name" : "w", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast209_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast277_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast293_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast247_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast221_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast255_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast231_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast233_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast271_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast229_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast205_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast253_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast283_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast287_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast235_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast241_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast227_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast245_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast211_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast215_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast279_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast291_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast273_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast251_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast217_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast225_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast237_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "zext_ln84", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast213_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast201_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast219_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast249_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast275_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast223_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast243_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast263_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast285_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast265_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast261_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast281_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast289_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast203_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast267_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast259_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast239_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast207_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast257_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast269_cast", "Type" : "None", "Direction" : "I"},
			{"Name" : "M", "Type" : "None", "Direction" : "I"},
			{"Name" : "sh_prom_i", "Type" : "None", "Direction" : "I"},
			{"Name" : "sub2_i", "Type" : "None", "Direction" : "I"},
			{"Name" : "half", "Type" : "None", "Direction" : "I"},
			{"Name" : "empty", "Type" : "None", "Direction" : "I"},
			{"Name" : "p_cast302", "Type" : "None", "Direction" : "I"},
			{"Name" : "mul_ln82", "Type" : "None", "Direction" : "I"},
			{"Name" : "out_r", "Type" : "None", "Direction" : "I"}],
		"Loop" : [
			{"Name" : "VITIS_LOOP_84_4", "PipelineType" : "UPC",
				"LoopDec" : {"FSMBitwidth" : "50", "FirstState" : "ap_ST_fsm_pp0_stage0", "FirstStateIter" : "ap_enable_reg_pp0_iter0", "FirstStateBlock" : "ap_block_pp0_stage0_subdone", "LastState" : "ap_ST_fsm_pp0_stage28", "LastStateIter" : "ap_enable_reg_pp0_iter1", "LastStateBlock" : "ap_block_pp0_stage28_subdone", "QuitState" : "ap_ST_fsm_pp0_stage28", "QuitStateIter" : "ap_enable_reg_pp0_iter1", "QuitStateBlock" : "ap_block_pp0_stage28_subdone", "OneDepthLoop" : "0", "has_ap_ctrl" : "1", "has_continue" : "0"}}]},
	{"ID" : "2", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mul_64s_32s_64_5_1_U1", "Parent" : "1"},
	{"ID" : "3", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mul_8s_8ns_16_1_1_U2", "Parent" : "1"},
	{"ID" : "4", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mul_8s_8ns_16_1_1_U3", "Parent" : "1"},
	{"ID" : "5", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mul_8s_8ns_16_1_1_U4", "Parent" : "1"},
	{"ID" : "6", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mul_8s_8ns_16_1_1_U5", "Parent" : "1"},
	{"ID" : "7", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mul_8s_8ns_16_1_1_U6", "Parent" : "1"},
	{"ID" : "8", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mul_8s_8ns_16_1_1_U7", "Parent" : "1"},
	{"ID" : "9", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mul_8s_8ns_16_1_1_U8", "Parent" : "1"},
	{"ID" : "10", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mul_8s_8ns_16_1_1_U9", "Parent" : "1"},
	{"ID" : "11", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mul_8s_8ns_16_1_1_U10", "Parent" : "1"},
	{"ID" : "12", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mul_8s_8ns_16_1_1_U11", "Parent" : "1"},
	{"ID" : "13", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mul_8s_8ns_16_1_1_U12", "Parent" : "1"},
	{"ID" : "14", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mul_8s_8ns_16_1_1_U13", "Parent" : "1"},
	{"ID" : "15", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mul_8s_8ns_16_1_1_U14", "Parent" : "1"},
	{"ID" : "16", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mul_8s_8ns_16_1_1_U15", "Parent" : "1"},
	{"ID" : "17", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mul_8s_8ns_16_1_1_U16", "Parent" : "1"},
	{"ID" : "18", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mul_8s_8ns_16_1_1_U17", "Parent" : "1"},
	{"ID" : "19", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mul_8s_8ns_16_1_1_U18", "Parent" : "1"},
	{"ID" : "20", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_16s_17_4_1_U19", "Parent" : "1"},
	{"ID" : "21", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_16s_17_4_1_U20", "Parent" : "1"},
	{"ID" : "22", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_17s_18_4_1_U21", "Parent" : "1"},
	{"ID" : "23", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_16s_17_4_1_U22", "Parent" : "1"},
	{"ID" : "24", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_17s_18_4_1_U23", "Parent" : "1"},
	{"ID" : "25", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_16s_17_4_1_U24", "Parent" : "1"},
	{"ID" : "26", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_17s_18_4_1_U25", "Parent" : "1"},
	{"ID" : "27", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_16s_17_4_1_U26", "Parent" : "1"},
	{"ID" : "28", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_17s_18_4_1_U27", "Parent" : "1"},
	{"ID" : "29", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_16s_17_4_1_U28", "Parent" : "1"},
	{"ID" : "30", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_17s_18_4_1_U29", "Parent" : "1"},
	{"ID" : "31", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_16s_17_4_1_U30", "Parent" : "1"},
	{"ID" : "32", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_17s_18_4_1_U31", "Parent" : "1"},
	{"ID" : "33", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_16s_17_4_1_U32", "Parent" : "1"},
	{"ID" : "34", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_17s_18_4_1_U33", "Parent" : "1"},
	{"ID" : "35", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_16s_17_4_1_U34", "Parent" : "1"},
	{"ID" : "36", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_17s_18_4_1_U35", "Parent" : "1"},
	{"ID" : "37", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_16s_17_4_1_U36", "Parent" : "1"},
	{"ID" : "38", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_17s_18_4_1_U37", "Parent" : "1"},
	{"ID" : "39", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_16s_17_4_1_U38", "Parent" : "1"},
	{"ID" : "40", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_17s_18_4_1_U39", "Parent" : "1"},
	{"ID" : "41", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_16s_17_4_1_U40", "Parent" : "1"},
	{"ID" : "42", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_17s_18_4_1_U41", "Parent" : "1"},
	{"ID" : "43", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_16s_17_4_1_U42", "Parent" : "1"},
	{"ID" : "44", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_17s_18_4_1_U43", "Parent" : "1"},
	{"ID" : "45", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_16s_17_4_1_U44", "Parent" : "1"},
	{"ID" : "46", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_17s_18_4_1_U45", "Parent" : "1"},
	{"ID" : "47", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_16s_17_4_1_U46", "Parent" : "1"},
	{"ID" : "48", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_17s_18_4_1_U47", "Parent" : "1"},
	{"ID" : "49", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_16s_17_4_1_U48", "Parent" : "1"},
	{"ID" : "50", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.mac_muladd_8s_8ns_16s_17_4_1_U49", "Parent" : "1"},
	{"ID" : "51", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4_fu_874.flow_control_loop_pipe_sequential_init_U", "Parent" : "1"}]}


set ArgLastReadFirstWriteLatency {
	kp_hls_pw_core_2_6_6_48_64_s {
		gmem {Type IO LastRead 74 FirstWrite 73}
		in_r {Type I LastRead 1 FirstWrite -1}
		w {Type I LastRead 1 FirstWrite -1}
		bias {Type I LastRead 1 FirstWrite -1}
		M {Type I LastRead 1 FirstWrite -1}
		F {Type I LastRead 0 FirstWrite -1}
		out_r {Type I LastRead 1 FirstWrite -1}}
	kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4 {
		sext_ln81 {Type I LastRead 0 FirstWrite -1}
		gmem {Type IO LastRead 74 FirstWrite 73}
		w {Type I LastRead 0 FirstWrite -1}
		p_cast209_cast {Type I LastRead 0 FirstWrite -1}
		p_cast277_cast {Type I LastRead 0 FirstWrite -1}
		p_cast293_cast {Type I LastRead 0 FirstWrite -1}
		p_cast247_cast {Type I LastRead 0 FirstWrite -1}
		p_cast221_cast {Type I LastRead 0 FirstWrite -1}
		p_cast255_cast {Type I LastRead 0 FirstWrite -1}
		p_cast231_cast {Type I LastRead 0 FirstWrite -1}
		p_cast233_cast {Type I LastRead 0 FirstWrite -1}
		p_cast271_cast {Type I LastRead 0 FirstWrite -1}
		p_cast229_cast {Type I LastRead 0 FirstWrite -1}
		p_cast205_cast {Type I LastRead 0 FirstWrite -1}
		p_cast253_cast {Type I LastRead 0 FirstWrite -1}
		p_cast283_cast {Type I LastRead 0 FirstWrite -1}
		p_cast287_cast {Type I LastRead 0 FirstWrite -1}
		p_cast235_cast {Type I LastRead 0 FirstWrite -1}
		p_cast241_cast {Type I LastRead 0 FirstWrite -1}
		p_cast227_cast {Type I LastRead 0 FirstWrite -1}
		p_cast245_cast {Type I LastRead 0 FirstWrite -1}
		p_cast211_cast {Type I LastRead 0 FirstWrite -1}
		p_cast215_cast {Type I LastRead 0 FirstWrite -1}
		p_cast279_cast {Type I LastRead 0 FirstWrite -1}
		p_cast291_cast {Type I LastRead 0 FirstWrite -1}
		p_cast273_cast {Type I LastRead 0 FirstWrite -1}
		p_cast251_cast {Type I LastRead 0 FirstWrite -1}
		p_cast217_cast {Type I LastRead 0 FirstWrite -1}
		p_cast225_cast {Type I LastRead 0 FirstWrite -1}
		p_cast237_cast {Type I LastRead 0 FirstWrite -1}
		zext_ln84 {Type I LastRead 0 FirstWrite -1}
		p_cast213_cast {Type I LastRead 0 FirstWrite -1}
		p_cast201_cast {Type I LastRead 0 FirstWrite -1}
		p_cast219_cast {Type I LastRead 0 FirstWrite -1}
		p_cast249_cast {Type I LastRead 0 FirstWrite -1}
		p_cast275_cast {Type I LastRead 0 FirstWrite -1}
		p_cast223_cast {Type I LastRead 0 FirstWrite -1}
		p_cast243_cast {Type I LastRead 0 FirstWrite -1}
		p_cast263_cast {Type I LastRead 0 FirstWrite -1}
		p_cast285_cast {Type I LastRead 0 FirstWrite -1}
		p_cast265_cast {Type I LastRead 0 FirstWrite -1}
		p_cast261_cast {Type I LastRead 0 FirstWrite -1}
		p_cast281_cast {Type I LastRead 0 FirstWrite -1}
		p_cast289_cast {Type I LastRead 0 FirstWrite -1}
		p_cast203_cast {Type I LastRead 0 FirstWrite -1}
		p_cast267_cast {Type I LastRead 0 FirstWrite -1}
		p_cast259_cast {Type I LastRead 0 FirstWrite -1}
		p_cast239_cast {Type I LastRead 0 FirstWrite -1}
		p_cast207_cast {Type I LastRead 0 FirstWrite -1}
		p_cast257_cast {Type I LastRead 0 FirstWrite -1}
		p_cast269_cast {Type I LastRead 0 FirstWrite -1}
		M {Type I LastRead 0 FirstWrite -1}
		sh_prom_i {Type I LastRead 0 FirstWrite -1}
		sub2_i {Type I LastRead 0 FirstWrite -1}
		half {Type I LastRead 0 FirstWrite -1}
		empty {Type I LastRead 0 FirstWrite -1}
		p_cast302 {Type I LastRead 0 FirstWrite -1}
		mul_ln82 {Type I LastRead 0 FirstWrite -1}
		out_r {Type I LastRead 0 FirstWrite -1}}}

set hasDtUnsupportedChannel 0

set PerformanceInfo {[
	{"Name" : "Latency", "Min" : "236910", "Max" : "236910"}
	, {"Name" : "Interval", "Min" : "236910", "Max" : "236910"}
]}

set PipelineEnableSignalInfo {[
]}

set Spec2ImplPortList { 
	 { m_axi {  { m_axi_gmem_AWVALID VALID 1 1 }  { m_axi_gmem_AWREADY READY 0 1 }  { m_axi_gmem_AWADDR ADDR 1 64 }  { m_axi_gmem_AWID ID 1 1 }  { m_axi_gmem_AWLEN SIZE 1 32 }  { m_axi_gmem_AWSIZE BURST 1 3 }  { m_axi_gmem_AWBURST LOCK 1 2 }  { m_axi_gmem_AWLOCK CACHE 1 2 }  { m_axi_gmem_AWCACHE PROT 1 4 }  { m_axi_gmem_AWPROT QOS 1 3 }  { m_axi_gmem_AWQOS REGION 1 4 }  { m_axi_gmem_AWREGION USER 1 4 }  { m_axi_gmem_AWUSER DATA 1 1 }  { m_axi_gmem_WVALID VALID 1 1 }  { m_axi_gmem_WREADY READY 0 1 }  { m_axi_gmem_WDATA FIFONUM 1 64 }  { m_axi_gmem_WSTRB STRB 1 8 }  { m_axi_gmem_WLAST LAST 1 1 }  { m_axi_gmem_WID ID 1 1 }  { m_axi_gmem_WUSER DATA 1 1 }  { m_axi_gmem_ARVALID VALID 1 1 }  { m_axi_gmem_ARREADY READY 0 1 }  { m_axi_gmem_ARADDR ADDR 1 64 }  { m_axi_gmem_ARID ID 1 1 }  { m_axi_gmem_ARLEN SIZE 1 32 }  { m_axi_gmem_ARSIZE BURST 1 3 }  { m_axi_gmem_ARBURST LOCK 1 2 }  { m_axi_gmem_ARLOCK CACHE 1 2 }  { m_axi_gmem_ARCACHE PROT 1 4 }  { m_axi_gmem_ARPROT QOS 1 3 }  { m_axi_gmem_ARQOS REGION 1 4 }  { m_axi_gmem_ARREGION USER 1 4 }  { m_axi_gmem_ARUSER DATA 1 1 }  { m_axi_gmem_RVALID VALID 0 1 }  { m_axi_gmem_RREADY READY 1 1 }  { m_axi_gmem_RDATA FIFONUM 0 64 }  { m_axi_gmem_RLAST LAST 0 1 }  { m_axi_gmem_RID ID 0 1 }  { m_axi_gmem_RFIFONUM LEN 0 9 }  { m_axi_gmem_RUSER DATA 0 1 }  { m_axi_gmem_RRESP RESP 0 2 }  { m_axi_gmem_BVALID VALID 0 1 }  { m_axi_gmem_BREADY READY 1 1 }  { m_axi_gmem_BRESP RESP 0 2 }  { m_axi_gmem_BID ID 0 1 }  { m_axi_gmem_BUSER DATA 0 1 } } }
	in_r { ap_none {  { in_r in_data 0 64 } } }
	w { ap_none {  { w in_data 0 64 } } }
	bias { ap_none {  { bias in_data 0 64 } } }
	M { ap_none {  { M in_data 0 64 } } }
	F { ap_none {  { F in_data 0 32 } } }
	out_r { ap_none {  { out_r in_data 0 64 } } }
}
