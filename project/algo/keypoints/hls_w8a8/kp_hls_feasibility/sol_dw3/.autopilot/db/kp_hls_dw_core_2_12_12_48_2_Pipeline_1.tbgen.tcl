set moduleName kp_hls_dw_core_2_12_12_48_2_Pipeline_1
set isTopModule 0
set isCombinational 0
set isDatapathOnly 0
set isPipelined 1
set pipeline_type none
set FunctionProtocol ap_ctrl_hs
set isOneStateSeq 0
set ProfileFlag 0
set StallSigGenFlag 0
set isEnableWaveformDebug 1
set hasInterrupt 0
set DLRegFirstOffset 0
set DLRegItemOffset 0
set C_modelName {kp_hls_dw_core<2, 12, 12, 48, 2>_Pipeline_1}
set C_modelType { void 0 }
set ap_memory_interface_dict [dict create]
dict set ap_memory_interface_dict xp_12 { MEM_WIDTH 1 MEM_SIZE 1248 MASTER_TYPE BRAM_CTRL MEM_ADDRESS_MODE WORD_ADDRESS PACKAGE_IO port READ_LATENCY 0 }
dict set ap_memory_interface_dict xp_11 { MEM_WIDTH 8 MEM_SIZE 1248 MASTER_TYPE BRAM_CTRL MEM_ADDRESS_MODE WORD_ADDRESS PACKAGE_IO port READ_LATENCY 0 }
dict set ap_memory_interface_dict xp_10 { MEM_WIDTH 8 MEM_SIZE 1248 MASTER_TYPE BRAM_CTRL MEM_ADDRESS_MODE WORD_ADDRESS PACKAGE_IO port READ_LATENCY 0 }
dict set ap_memory_interface_dict xp_9 { MEM_WIDTH 8 MEM_SIZE 1248 MASTER_TYPE BRAM_CTRL MEM_ADDRESS_MODE WORD_ADDRESS PACKAGE_IO port READ_LATENCY 0 }
dict set ap_memory_interface_dict xp_8 { MEM_WIDTH 8 MEM_SIZE 1248 MASTER_TYPE BRAM_CTRL MEM_ADDRESS_MODE WORD_ADDRESS PACKAGE_IO port READ_LATENCY 0 }
dict set ap_memory_interface_dict xp_7 { MEM_WIDTH 8 MEM_SIZE 1248 MASTER_TYPE BRAM_CTRL MEM_ADDRESS_MODE WORD_ADDRESS PACKAGE_IO port READ_LATENCY 0 }
dict set ap_memory_interface_dict xp_6 { MEM_WIDTH 8 MEM_SIZE 1248 MASTER_TYPE BRAM_CTRL MEM_ADDRESS_MODE WORD_ADDRESS PACKAGE_IO port READ_LATENCY 0 }
dict set ap_memory_interface_dict xp_5 { MEM_WIDTH 8 MEM_SIZE 1248 MASTER_TYPE BRAM_CTRL MEM_ADDRESS_MODE WORD_ADDRESS PACKAGE_IO port READ_LATENCY 0 }
dict set ap_memory_interface_dict xp_4 { MEM_WIDTH 8 MEM_SIZE 1248 MASTER_TYPE BRAM_CTRL MEM_ADDRESS_MODE WORD_ADDRESS PACKAGE_IO port READ_LATENCY 0 }
dict set ap_memory_interface_dict xp_3 { MEM_WIDTH 8 MEM_SIZE 1248 MASTER_TYPE BRAM_CTRL MEM_ADDRESS_MODE WORD_ADDRESS PACKAGE_IO port READ_LATENCY 0 }
dict set ap_memory_interface_dict xp_2 { MEM_WIDTH 8 MEM_SIZE 1248 MASTER_TYPE BRAM_CTRL MEM_ADDRESS_MODE WORD_ADDRESS PACKAGE_IO port READ_LATENCY 0 }
dict set ap_memory_interface_dict xp_1 { MEM_WIDTH 8 MEM_SIZE 1248 MASTER_TYPE BRAM_CTRL MEM_ADDRESS_MODE WORD_ADDRESS PACKAGE_IO port READ_LATENCY 0 }
dict set ap_memory_interface_dict xp { MEM_WIDTH 8 MEM_SIZE 1248 MASTER_TYPE BRAM_CTRL MEM_ADDRESS_MODE WORD_ADDRESS PACKAGE_IO port READ_LATENCY 0 }
set C_modelArgList {
	{ xp_12 int 1 regular {array 1248 { 0 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 } 0 1 }  }
	{ xp_11 int 8 regular {array 1248 { 0 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 } 0 1 }  }
	{ xp_10 int 8 regular {array 1248 { 0 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 } 0 1 }  }
	{ xp_9 int 8 regular {array 1248 { 0 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 } 0 1 }  }
	{ xp_8 int 8 regular {array 1248 { 0 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 } 0 1 }  }
	{ xp_7 int 8 regular {array 1248 { 0 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 } 0 1 }  }
	{ xp_6 int 8 regular {array 1248 { 0 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 } 0 1 }  }
	{ xp_5 int 8 regular {array 1248 { 0 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 } 0 1 }  }
	{ xp_4 int 8 regular {array 1248 { 0 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 } 0 1 }  }
	{ xp_3 int 8 regular {array 1248 { 0 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 } 0 1 }  }
	{ xp_2 int 8 regular {array 1248 { 0 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 } 0 1 }  }
	{ xp_1 int 8 regular {array 1248 { 0 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 } 0 1 }  }
	{ xp int 8 regular {array 1248 { 0 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 } 0 1 }  }
}
set hasAXIMCache 0
set hasAXIML2Cache 0
set AXIMCacheInstDict [dict create]
set C_modelArgMapList {[ 
	{ "Name" : "xp_12", "interface" : "memory", "bitwidth" : 1, "direction" : "WRITEONLY"} , 
 	{ "Name" : "xp_11", "interface" : "memory", "bitwidth" : 8, "direction" : "WRITEONLY"} , 
 	{ "Name" : "xp_10", "interface" : "memory", "bitwidth" : 8, "direction" : "WRITEONLY"} , 
 	{ "Name" : "xp_9", "interface" : "memory", "bitwidth" : 8, "direction" : "WRITEONLY"} , 
 	{ "Name" : "xp_8", "interface" : "memory", "bitwidth" : 8, "direction" : "WRITEONLY"} , 
 	{ "Name" : "xp_7", "interface" : "memory", "bitwidth" : 8, "direction" : "WRITEONLY"} , 
 	{ "Name" : "xp_6", "interface" : "memory", "bitwidth" : 8, "direction" : "WRITEONLY"} , 
 	{ "Name" : "xp_5", "interface" : "memory", "bitwidth" : 8, "direction" : "WRITEONLY"} , 
 	{ "Name" : "xp_4", "interface" : "memory", "bitwidth" : 8, "direction" : "WRITEONLY"} , 
 	{ "Name" : "xp_3", "interface" : "memory", "bitwidth" : 8, "direction" : "WRITEONLY"} , 
 	{ "Name" : "xp_2", "interface" : "memory", "bitwidth" : 8, "direction" : "WRITEONLY"} , 
 	{ "Name" : "xp_1", "interface" : "memory", "bitwidth" : 8, "direction" : "WRITEONLY"} , 
 	{ "Name" : "xp", "interface" : "memory", "bitwidth" : 8, "direction" : "WRITEONLY"} ]}
# RTL Port declarations: 
set portNum 58
set portList { 
	{ ap_clk sc_in sc_logic 1 clock -1 } 
	{ ap_rst sc_in sc_logic 1 reset -1 active_high_sync } 
	{ ap_start sc_in sc_logic 1 start -1 } 
	{ ap_done sc_out sc_logic 1 predone -1 } 
	{ ap_idle sc_out sc_logic 1 done -1 } 
	{ ap_ready sc_out sc_logic 1 ready -1 } 
	{ xp_12_address0 sc_out sc_lv 11 signal 0 } 
	{ xp_12_ce0 sc_out sc_logic 1 signal 0 } 
	{ xp_12_we0 sc_out sc_logic 1 signal 0 } 
	{ xp_12_d0 sc_out sc_lv 1 signal 0 } 
	{ xp_11_address0 sc_out sc_lv 11 signal 1 } 
	{ xp_11_ce0 sc_out sc_logic 1 signal 1 } 
	{ xp_11_we0 sc_out sc_logic 1 signal 1 } 
	{ xp_11_d0 sc_out sc_lv 8 signal 1 } 
	{ xp_10_address0 sc_out sc_lv 11 signal 2 } 
	{ xp_10_ce0 sc_out sc_logic 1 signal 2 } 
	{ xp_10_we0 sc_out sc_logic 1 signal 2 } 
	{ xp_10_d0 sc_out sc_lv 8 signal 2 } 
	{ xp_9_address0 sc_out sc_lv 11 signal 3 } 
	{ xp_9_ce0 sc_out sc_logic 1 signal 3 } 
	{ xp_9_we0 sc_out sc_logic 1 signal 3 } 
	{ xp_9_d0 sc_out sc_lv 8 signal 3 } 
	{ xp_8_address0 sc_out sc_lv 11 signal 4 } 
	{ xp_8_ce0 sc_out sc_logic 1 signal 4 } 
	{ xp_8_we0 sc_out sc_logic 1 signal 4 } 
	{ xp_8_d0 sc_out sc_lv 8 signal 4 } 
	{ xp_7_address0 sc_out sc_lv 11 signal 5 } 
	{ xp_7_ce0 sc_out sc_logic 1 signal 5 } 
	{ xp_7_we0 sc_out sc_logic 1 signal 5 } 
	{ xp_7_d0 sc_out sc_lv 8 signal 5 } 
	{ xp_6_address0 sc_out sc_lv 11 signal 6 } 
	{ xp_6_ce0 sc_out sc_logic 1 signal 6 } 
	{ xp_6_we0 sc_out sc_logic 1 signal 6 } 
	{ xp_6_d0 sc_out sc_lv 8 signal 6 } 
	{ xp_5_address0 sc_out sc_lv 11 signal 7 } 
	{ xp_5_ce0 sc_out sc_logic 1 signal 7 } 
	{ xp_5_we0 sc_out sc_logic 1 signal 7 } 
	{ xp_5_d0 sc_out sc_lv 8 signal 7 } 
	{ xp_4_address0 sc_out sc_lv 11 signal 8 } 
	{ xp_4_ce0 sc_out sc_logic 1 signal 8 } 
	{ xp_4_we0 sc_out sc_logic 1 signal 8 } 
	{ xp_4_d0 sc_out sc_lv 8 signal 8 } 
	{ xp_3_address0 sc_out sc_lv 11 signal 9 } 
	{ xp_3_ce0 sc_out sc_logic 1 signal 9 } 
	{ xp_3_we0 sc_out sc_logic 1 signal 9 } 
	{ xp_3_d0 sc_out sc_lv 8 signal 9 } 
	{ xp_2_address0 sc_out sc_lv 11 signal 10 } 
	{ xp_2_ce0 sc_out sc_logic 1 signal 10 } 
	{ xp_2_we0 sc_out sc_logic 1 signal 10 } 
	{ xp_2_d0 sc_out sc_lv 8 signal 10 } 
	{ xp_1_address0 sc_out sc_lv 11 signal 11 } 
	{ xp_1_ce0 sc_out sc_logic 1 signal 11 } 
	{ xp_1_we0 sc_out sc_logic 1 signal 11 } 
	{ xp_1_d0 sc_out sc_lv 8 signal 11 } 
	{ xp_address0 sc_out sc_lv 11 signal 12 } 
	{ xp_ce0 sc_out sc_logic 1 signal 12 } 
	{ xp_we0 sc_out sc_logic 1 signal 12 } 
	{ xp_d0 sc_out sc_lv 8 signal 12 } 
}
set NewPortList {[ 
	{ "name": "ap_clk", "direction": "in", "datatype": "sc_logic", "bitwidth":1, "type": "clock", "bundle":{"name": "ap_clk", "role": "default" }} , 
 	{ "name": "ap_rst", "direction": "in", "datatype": "sc_logic", "bitwidth":1, "type": "reset", "bundle":{"name": "ap_rst", "role": "default" }} , 
 	{ "name": "ap_start", "direction": "in", "datatype": "sc_logic", "bitwidth":1, "type": "start", "bundle":{"name": "ap_start", "role": "default" }} , 
 	{ "name": "ap_done", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "predone", "bundle":{"name": "ap_done", "role": "default" }} , 
 	{ "name": "ap_idle", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "done", "bundle":{"name": "ap_idle", "role": "default" }} , 
 	{ "name": "ap_ready", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "ready", "bundle":{"name": "ap_ready", "role": "default" }} , 
 	{ "name": "xp_12_address0", "direction": "out", "datatype": "sc_lv", "bitwidth":11, "type": "signal", "bundle":{"name": "xp_12", "role": "address0" }} , 
 	{ "name": "xp_12_ce0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_12", "role": "ce0" }} , 
 	{ "name": "xp_12_we0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_12", "role": "we0" }} , 
 	{ "name": "xp_12_d0", "direction": "out", "datatype": "sc_lv", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_12", "role": "d0" }} , 
 	{ "name": "xp_11_address0", "direction": "out", "datatype": "sc_lv", "bitwidth":11, "type": "signal", "bundle":{"name": "xp_11", "role": "address0" }} , 
 	{ "name": "xp_11_ce0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_11", "role": "ce0" }} , 
 	{ "name": "xp_11_we0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_11", "role": "we0" }} , 
 	{ "name": "xp_11_d0", "direction": "out", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "xp_11", "role": "d0" }} , 
 	{ "name": "xp_10_address0", "direction": "out", "datatype": "sc_lv", "bitwidth":11, "type": "signal", "bundle":{"name": "xp_10", "role": "address0" }} , 
 	{ "name": "xp_10_ce0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_10", "role": "ce0" }} , 
 	{ "name": "xp_10_we0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_10", "role": "we0" }} , 
 	{ "name": "xp_10_d0", "direction": "out", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "xp_10", "role": "d0" }} , 
 	{ "name": "xp_9_address0", "direction": "out", "datatype": "sc_lv", "bitwidth":11, "type": "signal", "bundle":{"name": "xp_9", "role": "address0" }} , 
 	{ "name": "xp_9_ce0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_9", "role": "ce0" }} , 
 	{ "name": "xp_9_we0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_9", "role": "we0" }} , 
 	{ "name": "xp_9_d0", "direction": "out", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "xp_9", "role": "d0" }} , 
 	{ "name": "xp_8_address0", "direction": "out", "datatype": "sc_lv", "bitwidth":11, "type": "signal", "bundle":{"name": "xp_8", "role": "address0" }} , 
 	{ "name": "xp_8_ce0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_8", "role": "ce0" }} , 
 	{ "name": "xp_8_we0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_8", "role": "we0" }} , 
 	{ "name": "xp_8_d0", "direction": "out", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "xp_8", "role": "d0" }} , 
 	{ "name": "xp_7_address0", "direction": "out", "datatype": "sc_lv", "bitwidth":11, "type": "signal", "bundle":{"name": "xp_7", "role": "address0" }} , 
 	{ "name": "xp_7_ce0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_7", "role": "ce0" }} , 
 	{ "name": "xp_7_we0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_7", "role": "we0" }} , 
 	{ "name": "xp_7_d0", "direction": "out", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "xp_7", "role": "d0" }} , 
 	{ "name": "xp_6_address0", "direction": "out", "datatype": "sc_lv", "bitwidth":11, "type": "signal", "bundle":{"name": "xp_6", "role": "address0" }} , 
 	{ "name": "xp_6_ce0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_6", "role": "ce0" }} , 
 	{ "name": "xp_6_we0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_6", "role": "we0" }} , 
 	{ "name": "xp_6_d0", "direction": "out", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "xp_6", "role": "d0" }} , 
 	{ "name": "xp_5_address0", "direction": "out", "datatype": "sc_lv", "bitwidth":11, "type": "signal", "bundle":{"name": "xp_5", "role": "address0" }} , 
 	{ "name": "xp_5_ce0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_5", "role": "ce0" }} , 
 	{ "name": "xp_5_we0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_5", "role": "we0" }} , 
 	{ "name": "xp_5_d0", "direction": "out", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "xp_5", "role": "d0" }} , 
 	{ "name": "xp_4_address0", "direction": "out", "datatype": "sc_lv", "bitwidth":11, "type": "signal", "bundle":{"name": "xp_4", "role": "address0" }} , 
 	{ "name": "xp_4_ce0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_4", "role": "ce0" }} , 
 	{ "name": "xp_4_we0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_4", "role": "we0" }} , 
 	{ "name": "xp_4_d0", "direction": "out", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "xp_4", "role": "d0" }} , 
 	{ "name": "xp_3_address0", "direction": "out", "datatype": "sc_lv", "bitwidth":11, "type": "signal", "bundle":{"name": "xp_3", "role": "address0" }} , 
 	{ "name": "xp_3_ce0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_3", "role": "ce0" }} , 
 	{ "name": "xp_3_we0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_3", "role": "we0" }} , 
 	{ "name": "xp_3_d0", "direction": "out", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "xp_3", "role": "d0" }} , 
 	{ "name": "xp_2_address0", "direction": "out", "datatype": "sc_lv", "bitwidth":11, "type": "signal", "bundle":{"name": "xp_2", "role": "address0" }} , 
 	{ "name": "xp_2_ce0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_2", "role": "ce0" }} , 
 	{ "name": "xp_2_we0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_2", "role": "we0" }} , 
 	{ "name": "xp_2_d0", "direction": "out", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "xp_2", "role": "d0" }} , 
 	{ "name": "xp_1_address0", "direction": "out", "datatype": "sc_lv", "bitwidth":11, "type": "signal", "bundle":{"name": "xp_1", "role": "address0" }} , 
 	{ "name": "xp_1_ce0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_1", "role": "ce0" }} , 
 	{ "name": "xp_1_we0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_1", "role": "we0" }} , 
 	{ "name": "xp_1_d0", "direction": "out", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "xp_1", "role": "d0" }} , 
 	{ "name": "xp_address0", "direction": "out", "datatype": "sc_lv", "bitwidth":11, "type": "signal", "bundle":{"name": "xp", "role": "address0" }} , 
 	{ "name": "xp_ce0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp", "role": "ce0" }} , 
 	{ "name": "xp_we0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp", "role": "we0" }} , 
 	{ "name": "xp_d0", "direction": "out", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "xp", "role": "d0" }}  ]}

set RtlHierarchyInfo {[
	{"ID" : "0", "Level" : "0", "Path" : "`AUTOTB_DUT_INST", "Parent" : "", "Child" : ["1", "2", "3", "4", "5", "6"],
		"CDFG" : "kp_hls_dw_core_2_12_12_48_2_Pipeline_1",
		"Protocol" : "ap_ctrl_hs",
		"ControlExist" : "1", "ap_start" : "1", "ap_ready" : "1", "ap_done" : "1", "ap_continue" : "0", "ap_idle" : "1", "real_start" : "0",
		"Pipeline" : "None", "UnalignedPipeline" : "0", "RewindPipeline" : "0", "ProcessNetwork" : "0",
		"II" : "0",
		"VariableLatency" : "1", "ExactLatency" : "-1", "EstimateLatencyMin" : "16256", "EstimateLatencyMax" : "16256",
		"Combinational" : "0",
		"Datapath" : "0",
		"ClockEnable" : "0",
		"HasSubDataflow" : "0",
		"InDataflowNetwork" : "0",
		"HasNonBlockingOperation" : "0",
		"IsBlackBox" : "0",
		"Port" : [
			{"Name" : "xp_12", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_11", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_10", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_9", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_8", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_7", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_6", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_5", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_4", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_3", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_2", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_1", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp", "Type" : "Memory", "Direction" : "O"}],
		"Loop" : [
			{"Name" : "Loop 1", "PipelineType" : "UPC",
				"LoopDec" : {"FSMBitwidth" : "1", "FirstState" : "ap_ST_fsm_pp0_stage0", "FirstStateIter" : "ap_enable_reg_pp0_iter0", "FirstStateBlock" : "ap_block_pp0_stage0_subdone", "LastState" : "ap_ST_fsm_pp0_stage0", "LastStateIter" : "ap_enable_reg_pp0_iter31", "LastStateBlock" : "ap_block_pp0_stage0_subdone", "QuitState" : "ap_ST_fsm_pp0_stage0", "QuitStateIter" : "ap_enable_reg_pp0_iter31", "QuitStateBlock" : "ap_block_pp0_stage0_subdone", "OneDepthLoop" : "0", "has_ap_ctrl" : "1", "has_continue" : "0"}}]},
	{"ID" : "1", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mul_13ns_15ns_27_1_1_U1", "Parent" : "0"},
	{"ID" : "2", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.urem_13ns_11ns_10_17_1_U2", "Parent" : "0"},
	{"ID" : "3", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.urem_10ns_7ns_10_14_1_U3", "Parent" : "0"},
	{"ID" : "4", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mul_10ns_12ns_21_1_1_U4", "Parent" : "0"},
	{"ID" : "5", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_4ns_2ns_4ns_5_4_1_U5", "Parent" : "0"},
	{"ID" : "6", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.flow_control_loop_pipe_sequential_init_U", "Parent" : "0"}]}


set ArgLastReadFirstWriteLatency {
	kp_hls_dw_core_2_12_12_48_2_Pipeline_1 {
		xp_12 {Type O LastRead -1 FirstWrite 31}
		xp_11 {Type O LastRead -1 FirstWrite 31}
		xp_10 {Type O LastRead -1 FirstWrite 31}
		xp_9 {Type O LastRead -1 FirstWrite 31}
		xp_8 {Type O LastRead -1 FirstWrite 31}
		xp_7 {Type O LastRead -1 FirstWrite 31}
		xp_6 {Type O LastRead -1 FirstWrite 31}
		xp_5 {Type O LastRead -1 FirstWrite 31}
		xp_4 {Type O LastRead -1 FirstWrite 31}
		xp_3 {Type O LastRead -1 FirstWrite 31}
		xp_2 {Type O LastRead -1 FirstWrite 31}
		xp_1 {Type O LastRead -1 FirstWrite 31}
		xp {Type O LastRead -1 FirstWrite 31}}}

set hasDtUnsupportedChannel 0

set PerformanceInfo {[
	{"Name" : "Latency", "Min" : "16256", "Max" : "16256"}
	, {"Name" : "Interval", "Min" : "16256", "Max" : "16256"}
]}

set PipelineEnableSignalInfo {[
	{"Pipeline" : "0", "EnableSignal" : "ap_enable_pp0"}
]}

set Spec2ImplPortList { 
	xp_12 { ap_memory {  { xp_12_address0 mem_address 1 11 }  { xp_12_ce0 mem_ce 1 1 }  { xp_12_we0 mem_we 1 1 }  { xp_12_d0 mem_din 1 1 } } }
	xp_11 { ap_memory {  { xp_11_address0 mem_address 1 11 }  { xp_11_ce0 mem_ce 1 1 }  { xp_11_we0 mem_we 1 1 }  { xp_11_d0 mem_din 1 8 } } }
	xp_10 { ap_memory {  { xp_10_address0 mem_address 1 11 }  { xp_10_ce0 mem_ce 1 1 }  { xp_10_we0 mem_we 1 1 }  { xp_10_d0 mem_din 1 8 } } }
	xp_9 { ap_memory {  { xp_9_address0 mem_address 1 11 }  { xp_9_ce0 mem_ce 1 1 }  { xp_9_we0 mem_we 1 1 }  { xp_9_d0 mem_din 1 8 } } }
	xp_8 { ap_memory {  { xp_8_address0 mem_address 1 11 }  { xp_8_ce0 mem_ce 1 1 }  { xp_8_we0 mem_we 1 1 }  { xp_8_d0 mem_din 1 8 } } }
	xp_7 { ap_memory {  { xp_7_address0 mem_address 1 11 }  { xp_7_ce0 mem_ce 1 1 }  { xp_7_we0 mem_we 1 1 }  { xp_7_d0 mem_din 1 8 } } }
	xp_6 { ap_memory {  { xp_6_address0 mem_address 1 11 }  { xp_6_ce0 mem_ce 1 1 }  { xp_6_we0 mem_we 1 1 }  { xp_6_d0 mem_din 1 8 } } }
	xp_5 { ap_memory {  { xp_5_address0 mem_address 1 11 }  { xp_5_ce0 mem_ce 1 1 }  { xp_5_we0 mem_we 1 1 }  { xp_5_d0 mem_din 1 8 } } }
	xp_4 { ap_memory {  { xp_4_address0 mem_address 1 11 }  { xp_4_ce0 mem_ce 1 1 }  { xp_4_we0 mem_we 1 1 }  { xp_4_d0 mem_din 1 8 } } }
	xp_3 { ap_memory {  { xp_3_address0 mem_address 1 11 }  { xp_3_ce0 mem_ce 1 1 }  { xp_3_we0 mem_we 1 1 }  { xp_3_d0 mem_din 1 8 } } }
	xp_2 { ap_memory {  { xp_2_address0 mem_address 1 11 }  { xp_2_ce0 mem_ce 1 1 }  { xp_2_we0 mem_we 1 1 }  { xp_2_d0 mem_din 1 8 } } }
	xp_1 { ap_memory {  { xp_1_address0 mem_address 1 11 }  { xp_1_ce0 mem_ce 1 1 }  { xp_1_we0 mem_we 1 1 }  { xp_1_d0 mem_din 1 8 } } }
	xp { ap_memory {  { xp_address0 mem_address 1 11 }  { xp_ce0 mem_ce 1 1 }  { xp_we0 mem_we 1 1 }  { xp_d0 mem_din 1 8 } } }
}
