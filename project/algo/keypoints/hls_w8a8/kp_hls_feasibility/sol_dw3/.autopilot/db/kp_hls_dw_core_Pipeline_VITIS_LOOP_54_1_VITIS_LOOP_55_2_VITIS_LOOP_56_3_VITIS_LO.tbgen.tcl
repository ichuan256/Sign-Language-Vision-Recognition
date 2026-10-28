set moduleName kp_hls_dw_core_Pipeline_VITIS_LOOP_54_1_VITIS_LOOP_55_2_VITIS_LOOP_56_3_VITIS_LO
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
set C_modelName {kp_hls_dw_core_Pipeline_VITIS_LOOP_54_1_VITIS_LOOP_55_2_VITIS_LOOP_56_3_VITIS_LO}
set C_modelType { void 0 }
set ap_memory_interface_dict [dict create]
dict set ap_memory_interface_dict xp { MEM_WIDTH 8 MEM_SIZE 1248 MASTER_TYPE BRAM_CTRL MEM_ADDRESS_MODE WORD_ADDRESS PACKAGE_IO port READ_LATENCY 0 }
dict set ap_memory_interface_dict xp_1 { MEM_WIDTH 8 MEM_SIZE 1248 MASTER_TYPE BRAM_CTRL MEM_ADDRESS_MODE WORD_ADDRESS PACKAGE_IO port READ_LATENCY 0 }
dict set ap_memory_interface_dict xp_2 { MEM_WIDTH 8 MEM_SIZE 1248 MASTER_TYPE BRAM_CTRL MEM_ADDRESS_MODE WORD_ADDRESS PACKAGE_IO port READ_LATENCY 0 }
dict set ap_memory_interface_dict xp_3 { MEM_WIDTH 8 MEM_SIZE 1248 MASTER_TYPE BRAM_CTRL MEM_ADDRESS_MODE WORD_ADDRESS PACKAGE_IO port READ_LATENCY 0 }
dict set ap_memory_interface_dict xp_4 { MEM_WIDTH 8 MEM_SIZE 1248 MASTER_TYPE BRAM_CTRL MEM_ADDRESS_MODE WORD_ADDRESS PACKAGE_IO port READ_LATENCY 0 }
dict set ap_memory_interface_dict xp_5 { MEM_WIDTH 8 MEM_SIZE 1248 MASTER_TYPE BRAM_CTRL MEM_ADDRESS_MODE WORD_ADDRESS PACKAGE_IO port READ_LATENCY 0 }
dict set ap_memory_interface_dict xp_6 { MEM_WIDTH 8 MEM_SIZE 1248 MASTER_TYPE BRAM_CTRL MEM_ADDRESS_MODE WORD_ADDRESS PACKAGE_IO port READ_LATENCY 0 }
dict set ap_memory_interface_dict xp_7 { MEM_WIDTH 8 MEM_SIZE 1248 MASTER_TYPE BRAM_CTRL MEM_ADDRESS_MODE WORD_ADDRESS PACKAGE_IO port READ_LATENCY 0 }
dict set ap_memory_interface_dict xp_8 { MEM_WIDTH 8 MEM_SIZE 1248 MASTER_TYPE BRAM_CTRL MEM_ADDRESS_MODE WORD_ADDRESS PACKAGE_IO port READ_LATENCY 0 }
dict set ap_memory_interface_dict xp_9 { MEM_WIDTH 8 MEM_SIZE 1248 MASTER_TYPE BRAM_CTRL MEM_ADDRESS_MODE WORD_ADDRESS PACKAGE_IO port READ_LATENCY 0 }
dict set ap_memory_interface_dict xp_10 { MEM_WIDTH 8 MEM_SIZE 1248 MASTER_TYPE BRAM_CTRL MEM_ADDRESS_MODE WORD_ADDRESS PACKAGE_IO port READ_LATENCY 0 }
dict set ap_memory_interface_dict xp_11 { MEM_WIDTH 8 MEM_SIZE 1248 MASTER_TYPE BRAM_CTRL MEM_ADDRESS_MODE WORD_ADDRESS PACKAGE_IO port READ_LATENCY 0 }
set C_modelArgList {
	{ xp int 8 regular {array 1248 { 0 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 } 0 1 }  }
	{ xp_1 int 8 regular {array 1248 { 0 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 } 0 1 }  }
	{ xp_2 int 8 regular {array 1248 { 0 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 } 0 1 }  }
	{ xp_3 int 8 regular {array 1248 { 0 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 } 0 1 }  }
	{ xp_4 int 8 regular {array 1248 { 0 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 } 0 1 }  }
	{ xp_5 int 8 regular {array 1248 { 0 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 } 0 1 }  }
	{ xp_6 int 8 regular {array 1248 { 0 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 } 0 1 }  }
	{ xp_7 int 8 regular {array 1248 { 0 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 } 0 1 }  }
	{ xp_8 int 8 regular {array 1248 { 0 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 } 0 1 }  }
	{ xp_9 int 8 regular {array 1248 { 0 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 } 0 1 }  }
	{ xp_10 int 8 regular {array 1248 { 0 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 } 0 1 }  }
	{ xp_11 int 8 regular {array 1248 { 0 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 3 } 0 1 }  }
	{ in_r int 64 regular  }
	{ gmem int 64 regular {axi_master 0}  }
}
set hasAXIMCache 0
set hasAXIML2Cache 0
set AXIMCacheInstDict [dict create]
set C_modelArgMapList {[ 
	{ "Name" : "xp", "interface" : "memory", "bitwidth" : 8, "direction" : "WRITEONLY"} , 
 	{ "Name" : "xp_1", "interface" : "memory", "bitwidth" : 8, "direction" : "WRITEONLY"} , 
 	{ "Name" : "xp_2", "interface" : "memory", "bitwidth" : 8, "direction" : "WRITEONLY"} , 
 	{ "Name" : "xp_3", "interface" : "memory", "bitwidth" : 8, "direction" : "WRITEONLY"} , 
 	{ "Name" : "xp_4", "interface" : "memory", "bitwidth" : 8, "direction" : "WRITEONLY"} , 
 	{ "Name" : "xp_5", "interface" : "memory", "bitwidth" : 8, "direction" : "WRITEONLY"} , 
 	{ "Name" : "xp_6", "interface" : "memory", "bitwidth" : 8, "direction" : "WRITEONLY"} , 
 	{ "Name" : "xp_7", "interface" : "memory", "bitwidth" : 8, "direction" : "WRITEONLY"} , 
 	{ "Name" : "xp_8", "interface" : "memory", "bitwidth" : 8, "direction" : "WRITEONLY"} , 
 	{ "Name" : "xp_9", "interface" : "memory", "bitwidth" : 8, "direction" : "WRITEONLY"} , 
 	{ "Name" : "xp_10", "interface" : "memory", "bitwidth" : 8, "direction" : "WRITEONLY"} , 
 	{ "Name" : "xp_11", "interface" : "memory", "bitwidth" : 8, "direction" : "WRITEONLY"} , 
 	{ "Name" : "in_r", "interface" : "wire", "bitwidth" : 64, "direction" : "READONLY"} , 
 	{ "Name" : "gmem", "interface" : "axi_master", "bitwidth" : 64, "direction" : "READONLY", "bitSlice":[ {"cElement": [{"cName": "in_r","offset": { "type": "dynamic","port_name": "in_r","bundle": "ctrl"},"direction": "READONLY"},{"cName": "w","offset": { "type": "dynamic","port_name": "w","bundle": "ctrl"},"direction": "READONLY"},{"cName": "bias","offset": { "type": "dynamic","port_name": "bias","bundle": "ctrl"},"direction": "READONLY"},{"cName": "M","offset": { "type": "dynamic","port_name": "M","bundle": "ctrl"},"direction": "READONLY"},{"cName": "out_r","offset": { "type": "dynamic","port_name": "out_r","bundle": "ctrl"},"direction": "WRITEONLY"}]}]} ]}
# RTL Port declarations: 
set portNum 101
set portList { 
	{ ap_clk sc_in sc_logic 1 clock -1 } 
	{ ap_rst sc_in sc_logic 1 reset -1 active_high_sync } 
	{ ap_start sc_in sc_logic 1 start -1 } 
	{ ap_done sc_out sc_logic 1 predone -1 } 
	{ ap_idle sc_out sc_logic 1 done -1 } 
	{ ap_ready sc_out sc_logic 1 ready -1 } 
	{ m_axi_gmem_AWVALID sc_out sc_logic 1 signal 13 } 
	{ m_axi_gmem_AWREADY sc_in sc_logic 1 signal 13 } 
	{ m_axi_gmem_AWADDR sc_out sc_lv 64 signal 13 } 
	{ m_axi_gmem_AWID sc_out sc_lv 1 signal 13 } 
	{ m_axi_gmem_AWLEN sc_out sc_lv 32 signal 13 } 
	{ m_axi_gmem_AWSIZE sc_out sc_lv 3 signal 13 } 
	{ m_axi_gmem_AWBURST sc_out sc_lv 2 signal 13 } 
	{ m_axi_gmem_AWLOCK sc_out sc_lv 2 signal 13 } 
	{ m_axi_gmem_AWCACHE sc_out sc_lv 4 signal 13 } 
	{ m_axi_gmem_AWPROT sc_out sc_lv 3 signal 13 } 
	{ m_axi_gmem_AWQOS sc_out sc_lv 4 signal 13 } 
	{ m_axi_gmem_AWREGION sc_out sc_lv 4 signal 13 } 
	{ m_axi_gmem_AWUSER sc_out sc_lv 1 signal 13 } 
	{ m_axi_gmem_WVALID sc_out sc_logic 1 signal 13 } 
	{ m_axi_gmem_WREADY sc_in sc_logic 1 signal 13 } 
	{ m_axi_gmem_WDATA sc_out sc_lv 64 signal 13 } 
	{ m_axi_gmem_WSTRB sc_out sc_lv 8 signal 13 } 
	{ m_axi_gmem_WLAST sc_out sc_logic 1 signal 13 } 
	{ m_axi_gmem_WID sc_out sc_lv 1 signal 13 } 
	{ m_axi_gmem_WUSER sc_out sc_lv 1 signal 13 } 
	{ m_axi_gmem_ARVALID sc_out sc_logic 1 signal 13 } 
	{ m_axi_gmem_ARREADY sc_in sc_logic 1 signal 13 } 
	{ m_axi_gmem_ARADDR sc_out sc_lv 64 signal 13 } 
	{ m_axi_gmem_ARID sc_out sc_lv 1 signal 13 } 
	{ m_axi_gmem_ARLEN sc_out sc_lv 32 signal 13 } 
	{ m_axi_gmem_ARSIZE sc_out sc_lv 3 signal 13 } 
	{ m_axi_gmem_ARBURST sc_out sc_lv 2 signal 13 } 
	{ m_axi_gmem_ARLOCK sc_out sc_lv 2 signal 13 } 
	{ m_axi_gmem_ARCACHE sc_out sc_lv 4 signal 13 } 
	{ m_axi_gmem_ARPROT sc_out sc_lv 3 signal 13 } 
	{ m_axi_gmem_ARQOS sc_out sc_lv 4 signal 13 } 
	{ m_axi_gmem_ARREGION sc_out sc_lv 4 signal 13 } 
	{ m_axi_gmem_ARUSER sc_out sc_lv 1 signal 13 } 
	{ m_axi_gmem_RVALID sc_in sc_logic 1 signal 13 } 
	{ m_axi_gmem_RREADY sc_out sc_logic 1 signal 13 } 
	{ m_axi_gmem_RDATA sc_in sc_lv 64 signal 13 } 
	{ m_axi_gmem_RLAST sc_in sc_logic 1 signal 13 } 
	{ m_axi_gmem_RID sc_in sc_lv 1 signal 13 } 
	{ m_axi_gmem_RFIFONUM sc_in sc_lv 9 signal 13 } 
	{ m_axi_gmem_RUSER sc_in sc_lv 1 signal 13 } 
	{ m_axi_gmem_RRESP sc_in sc_lv 2 signal 13 } 
	{ m_axi_gmem_BVALID sc_in sc_logic 1 signal 13 } 
	{ m_axi_gmem_BREADY sc_out sc_logic 1 signal 13 } 
	{ m_axi_gmem_BRESP sc_in sc_lv 2 signal 13 } 
	{ m_axi_gmem_BID sc_in sc_lv 1 signal 13 } 
	{ m_axi_gmem_BUSER sc_in sc_lv 1 signal 13 } 
	{ xp_address0 sc_out sc_lv 11 signal 0 } 
	{ xp_ce0 sc_out sc_logic 1 signal 0 } 
	{ xp_we0 sc_out sc_logic 1 signal 0 } 
	{ xp_d0 sc_out sc_lv 8 signal 0 } 
	{ xp_1_address0 sc_out sc_lv 11 signal 1 } 
	{ xp_1_ce0 sc_out sc_logic 1 signal 1 } 
	{ xp_1_we0 sc_out sc_logic 1 signal 1 } 
	{ xp_1_d0 sc_out sc_lv 8 signal 1 } 
	{ xp_2_address0 sc_out sc_lv 11 signal 2 } 
	{ xp_2_ce0 sc_out sc_logic 1 signal 2 } 
	{ xp_2_we0 sc_out sc_logic 1 signal 2 } 
	{ xp_2_d0 sc_out sc_lv 8 signal 2 } 
	{ xp_3_address0 sc_out sc_lv 11 signal 3 } 
	{ xp_3_ce0 sc_out sc_logic 1 signal 3 } 
	{ xp_3_we0 sc_out sc_logic 1 signal 3 } 
	{ xp_3_d0 sc_out sc_lv 8 signal 3 } 
	{ xp_4_address0 sc_out sc_lv 11 signal 4 } 
	{ xp_4_ce0 sc_out sc_logic 1 signal 4 } 
	{ xp_4_we0 sc_out sc_logic 1 signal 4 } 
	{ xp_4_d0 sc_out sc_lv 8 signal 4 } 
	{ xp_5_address0 sc_out sc_lv 11 signal 5 } 
	{ xp_5_ce0 sc_out sc_logic 1 signal 5 } 
	{ xp_5_we0 sc_out sc_logic 1 signal 5 } 
	{ xp_5_d0 sc_out sc_lv 8 signal 5 } 
	{ xp_6_address0 sc_out sc_lv 11 signal 6 } 
	{ xp_6_ce0 sc_out sc_logic 1 signal 6 } 
	{ xp_6_we0 sc_out sc_logic 1 signal 6 } 
	{ xp_6_d0 sc_out sc_lv 8 signal 6 } 
	{ xp_7_address0 sc_out sc_lv 11 signal 7 } 
	{ xp_7_ce0 sc_out sc_logic 1 signal 7 } 
	{ xp_7_we0 sc_out sc_logic 1 signal 7 } 
	{ xp_7_d0 sc_out sc_lv 8 signal 7 } 
	{ xp_8_address0 sc_out sc_lv 11 signal 8 } 
	{ xp_8_ce0 sc_out sc_logic 1 signal 8 } 
	{ xp_8_we0 sc_out sc_logic 1 signal 8 } 
	{ xp_8_d0 sc_out sc_lv 8 signal 8 } 
	{ xp_9_address0 sc_out sc_lv 11 signal 9 } 
	{ xp_9_ce0 sc_out sc_logic 1 signal 9 } 
	{ xp_9_we0 sc_out sc_logic 1 signal 9 } 
	{ xp_9_d0 sc_out sc_lv 8 signal 9 } 
	{ xp_10_address0 sc_out sc_lv 11 signal 10 } 
	{ xp_10_ce0 sc_out sc_logic 1 signal 10 } 
	{ xp_10_we0 sc_out sc_logic 1 signal 10 } 
	{ xp_10_d0 sc_out sc_lv 8 signal 10 } 
	{ xp_11_address0 sc_out sc_lv 11 signal 11 } 
	{ xp_11_ce0 sc_out sc_logic 1 signal 11 } 
	{ xp_11_we0 sc_out sc_logic 1 signal 11 } 
	{ xp_11_d0 sc_out sc_lv 8 signal 11 } 
	{ in_r sc_in sc_lv 64 signal 12 } 
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
 	{ "name": "xp_address0", "direction": "out", "datatype": "sc_lv", "bitwidth":11, "type": "signal", "bundle":{"name": "xp", "role": "address0" }} , 
 	{ "name": "xp_ce0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp", "role": "ce0" }} , 
 	{ "name": "xp_we0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp", "role": "we0" }} , 
 	{ "name": "xp_d0", "direction": "out", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "xp", "role": "d0" }} , 
 	{ "name": "xp_1_address0", "direction": "out", "datatype": "sc_lv", "bitwidth":11, "type": "signal", "bundle":{"name": "xp_1", "role": "address0" }} , 
 	{ "name": "xp_1_ce0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_1", "role": "ce0" }} , 
 	{ "name": "xp_1_we0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_1", "role": "we0" }} , 
 	{ "name": "xp_1_d0", "direction": "out", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "xp_1", "role": "d0" }} , 
 	{ "name": "xp_2_address0", "direction": "out", "datatype": "sc_lv", "bitwidth":11, "type": "signal", "bundle":{"name": "xp_2", "role": "address0" }} , 
 	{ "name": "xp_2_ce0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_2", "role": "ce0" }} , 
 	{ "name": "xp_2_we0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_2", "role": "we0" }} , 
 	{ "name": "xp_2_d0", "direction": "out", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "xp_2", "role": "d0" }} , 
 	{ "name": "xp_3_address0", "direction": "out", "datatype": "sc_lv", "bitwidth":11, "type": "signal", "bundle":{"name": "xp_3", "role": "address0" }} , 
 	{ "name": "xp_3_ce0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_3", "role": "ce0" }} , 
 	{ "name": "xp_3_we0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_3", "role": "we0" }} , 
 	{ "name": "xp_3_d0", "direction": "out", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "xp_3", "role": "d0" }} , 
 	{ "name": "xp_4_address0", "direction": "out", "datatype": "sc_lv", "bitwidth":11, "type": "signal", "bundle":{"name": "xp_4", "role": "address0" }} , 
 	{ "name": "xp_4_ce0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_4", "role": "ce0" }} , 
 	{ "name": "xp_4_we0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_4", "role": "we0" }} , 
 	{ "name": "xp_4_d0", "direction": "out", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "xp_4", "role": "d0" }} , 
 	{ "name": "xp_5_address0", "direction": "out", "datatype": "sc_lv", "bitwidth":11, "type": "signal", "bundle":{"name": "xp_5", "role": "address0" }} , 
 	{ "name": "xp_5_ce0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_5", "role": "ce0" }} , 
 	{ "name": "xp_5_we0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_5", "role": "we0" }} , 
 	{ "name": "xp_5_d0", "direction": "out", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "xp_5", "role": "d0" }} , 
 	{ "name": "xp_6_address0", "direction": "out", "datatype": "sc_lv", "bitwidth":11, "type": "signal", "bundle":{"name": "xp_6", "role": "address0" }} , 
 	{ "name": "xp_6_ce0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_6", "role": "ce0" }} , 
 	{ "name": "xp_6_we0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_6", "role": "we0" }} , 
 	{ "name": "xp_6_d0", "direction": "out", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "xp_6", "role": "d0" }} , 
 	{ "name": "xp_7_address0", "direction": "out", "datatype": "sc_lv", "bitwidth":11, "type": "signal", "bundle":{"name": "xp_7", "role": "address0" }} , 
 	{ "name": "xp_7_ce0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_7", "role": "ce0" }} , 
 	{ "name": "xp_7_we0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_7", "role": "we0" }} , 
 	{ "name": "xp_7_d0", "direction": "out", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "xp_7", "role": "d0" }} , 
 	{ "name": "xp_8_address0", "direction": "out", "datatype": "sc_lv", "bitwidth":11, "type": "signal", "bundle":{"name": "xp_8", "role": "address0" }} , 
 	{ "name": "xp_8_ce0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_8", "role": "ce0" }} , 
 	{ "name": "xp_8_we0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_8", "role": "we0" }} , 
 	{ "name": "xp_8_d0", "direction": "out", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "xp_8", "role": "d0" }} , 
 	{ "name": "xp_9_address0", "direction": "out", "datatype": "sc_lv", "bitwidth":11, "type": "signal", "bundle":{"name": "xp_9", "role": "address0" }} , 
 	{ "name": "xp_9_ce0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_9", "role": "ce0" }} , 
 	{ "name": "xp_9_we0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_9", "role": "we0" }} , 
 	{ "name": "xp_9_d0", "direction": "out", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "xp_9", "role": "d0" }} , 
 	{ "name": "xp_10_address0", "direction": "out", "datatype": "sc_lv", "bitwidth":11, "type": "signal", "bundle":{"name": "xp_10", "role": "address0" }} , 
 	{ "name": "xp_10_ce0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_10", "role": "ce0" }} , 
 	{ "name": "xp_10_we0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_10", "role": "we0" }} , 
 	{ "name": "xp_10_d0", "direction": "out", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "xp_10", "role": "d0" }} , 
 	{ "name": "xp_11_address0", "direction": "out", "datatype": "sc_lv", "bitwidth":11, "type": "signal", "bundle":{"name": "xp_11", "role": "address0" }} , 
 	{ "name": "xp_11_ce0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_11", "role": "ce0" }} , 
 	{ "name": "xp_11_we0", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "xp_11", "role": "we0" }} , 
 	{ "name": "xp_11_d0", "direction": "out", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "xp_11", "role": "d0" }} , 
 	{ "name": "in_r", "direction": "in", "datatype": "sc_lv", "bitwidth":64, "type": "signal", "bundle":{"name": "in_r", "role": "default" }}  ]}

set RtlHierarchyInfo {[
	{"ID" : "0", "Level" : "0", "Path" : "`AUTOTB_DUT_INST", "Parent" : "", "Child" : ["1", "2"],
		"CDFG" : "kp_hls_dw_core_Pipeline_VITIS_LOOP_54_1_VITIS_LOOP_55_2_VITIS_LOOP_56_3_VITIS_LO",
		"Protocol" : "ap_ctrl_hs",
		"ControlExist" : "1", "ap_start" : "1", "ap_ready" : "1", "ap_done" : "1", "ap_continue" : "0", "ap_idle" : "1", "real_start" : "0",
		"Pipeline" : "None", "UnalignedPipeline" : "0", "RewindPipeline" : "0", "ProcessNetwork" : "0",
		"II" : "0",
		"VariableLatency" : "1", "ExactLatency" : "-1", "EstimateLatencyMin" : "13840", "EstimateLatencyMax" : "13840",
		"Combinational" : "0",
		"Datapath" : "0",
		"ClockEnable" : "0",
		"HasSubDataflow" : "0",
		"InDataflowNetwork" : "0",
		"HasNonBlockingOperation" : "0",
		"IsBlackBox" : "0",
		"Port" : [
			{"Name" : "xp", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_1", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_2", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_3", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_4", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_5", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_6", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_7", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_8", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_9", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_10", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_11", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "in_r", "Type" : "None", "Direction" : "I"},
			{"Name" : "gmem", "Type" : "MAXI", "Direction" : "I",
				"BlockSignal" : [
					{"Name" : "gmem_blk_n_AR", "Type" : "RtlSignal"},
					{"Name" : "gmem_blk_n_R", "Type" : "RtlSignal"}]}],
		"Loop" : [
			{"Name" : "VITIS_LOOP_54_1_VITIS_LOOP_55_2_VITIS_LOOP_56_3_VITIS_LOOP_57_4", "PipelineType" : "UPC",
				"LoopDec" : {"FSMBitwidth" : "1", "FirstState" : "ap_ST_fsm_pp0_stage0", "FirstStateIter" : "ap_enable_reg_pp0_iter0", "FirstStateBlock" : "ap_block_pp0_stage0_subdone", "LastState" : "ap_ST_fsm_pp0_stage0", "LastStateIter" : "ap_enable_reg_pp0_iter15", "LastStateBlock" : "ap_block_pp0_stage0_subdone", "QuitState" : "ap_ST_fsm_pp0_stage0", "QuitStateIter" : "ap_enable_reg_pp0_iter15", "QuitStateBlock" : "ap_block_pp0_stage0_subdone", "OneDepthLoop" : "0", "has_ap_ctrl" : "1", "has_continue" : "0"}}]},
	{"ID" : "1", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_4ns_2ns_4ns_6_4_1_U24", "Parent" : "0"},
	{"ID" : "2", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.flow_control_loop_pipe_sequential_init_U", "Parent" : "0"}]}


set ArgLastReadFirstWriteLatency {
	kp_hls_dw_core_Pipeline_VITIS_LOOP_54_1_VITIS_LOOP_55_2_VITIS_LOOP_56_3_VITIS_LO {
		xp {Type O LastRead -1 FirstWrite 15}
		xp_1 {Type O LastRead -1 FirstWrite 15}
		xp_2 {Type O LastRead -1 FirstWrite 15}
		xp_3 {Type O LastRead -1 FirstWrite 15}
		xp_4 {Type O LastRead -1 FirstWrite 15}
		xp_5 {Type O LastRead -1 FirstWrite 15}
		xp_6 {Type O LastRead -1 FirstWrite 15}
		xp_7 {Type O LastRead -1 FirstWrite 15}
		xp_8 {Type O LastRead -1 FirstWrite 15}
		xp_9 {Type O LastRead -1 FirstWrite 15}
		xp_10 {Type O LastRead -1 FirstWrite 15}
		xp_11 {Type O LastRead -1 FirstWrite 15}
		in_r {Type I LastRead 0 FirstWrite -1}
		gmem {Type I LastRead 13 FirstWrite -1}}}

set hasDtUnsupportedChannel 0

set PerformanceInfo {[
	{"Name" : "Latency", "Min" : "13840", "Max" : "13840"}
	, {"Name" : "Interval", "Min" : "13840", "Max" : "13840"}
]}

set PipelineEnableSignalInfo {[
	{"Pipeline" : "0", "EnableSignal" : "ap_enable_pp0"}
]}

set Spec2ImplPortList { 
	xp { ap_memory {  { xp_address0 mem_address 1 11 }  { xp_ce0 mem_ce 1 1 }  { xp_we0 mem_we 1 1 }  { xp_d0 mem_din 1 8 } } }
	xp_1 { ap_memory {  { xp_1_address0 mem_address 1 11 }  { xp_1_ce0 mem_ce 1 1 }  { xp_1_we0 mem_we 1 1 }  { xp_1_d0 mem_din 1 8 } } }
	xp_2 { ap_memory {  { xp_2_address0 mem_address 1 11 }  { xp_2_ce0 mem_ce 1 1 }  { xp_2_we0 mem_we 1 1 }  { xp_2_d0 mem_din 1 8 } } }
	xp_3 { ap_memory {  { xp_3_address0 mem_address 1 11 }  { xp_3_ce0 mem_ce 1 1 }  { xp_3_we0 mem_we 1 1 }  { xp_3_d0 mem_din 1 8 } } }
	xp_4 { ap_memory {  { xp_4_address0 mem_address 1 11 }  { xp_4_ce0 mem_ce 1 1 }  { xp_4_we0 mem_we 1 1 }  { xp_4_d0 mem_din 1 8 } } }
	xp_5 { ap_memory {  { xp_5_address0 mem_address 1 11 }  { xp_5_ce0 mem_ce 1 1 }  { xp_5_we0 mem_we 1 1 }  { xp_5_d0 mem_din 1 8 } } }
	xp_6 { ap_memory {  { xp_6_address0 mem_address 1 11 }  { xp_6_ce0 mem_ce 1 1 }  { xp_6_we0 mem_we 1 1 }  { xp_6_d0 mem_din 1 8 } } }
	xp_7 { ap_memory {  { xp_7_address0 mem_address 1 11 }  { xp_7_ce0 mem_ce 1 1 }  { xp_7_we0 mem_we 1 1 }  { xp_7_d0 mem_din 1 8 } } }
	xp_8 { ap_memory {  { xp_8_address0 mem_address 1 11 }  { xp_8_ce0 mem_ce 1 1 }  { xp_8_we0 mem_we 1 1 }  { xp_8_d0 mem_din 1 8 } } }
	xp_9 { ap_memory {  { xp_9_address0 mem_address 1 11 }  { xp_9_ce0 mem_ce 1 1 }  { xp_9_we0 mem_we 1 1 }  { xp_9_d0 mem_din 1 8 } } }
	xp_10 { ap_memory {  { xp_10_address0 mem_address 1 11 }  { xp_10_ce0 mem_ce 1 1 }  { xp_10_we0 mem_we 1 1 }  { xp_10_d0 mem_din 1 8 } } }
	xp_11 { ap_memory {  { xp_11_address0 mem_address 1 11 }  { xp_11_ce0 mem_ce 1 1 }  { xp_11_we0 mem_we 1 1 }  { xp_11_d0 mem_din 1 8 } } }
	in_r { ap_none {  { in_r in_data 0 64 } } }
	 { m_axi {  { m_axi_gmem_AWVALID VALID 1 1 }  { m_axi_gmem_AWREADY READY 0 1 }  { m_axi_gmem_AWADDR ADDR 1 64 }  { m_axi_gmem_AWID ID 1 1 }  { m_axi_gmem_AWLEN SIZE 1 32 }  { m_axi_gmem_AWSIZE BURST 1 3 }  { m_axi_gmem_AWBURST LOCK 1 2 }  { m_axi_gmem_AWLOCK CACHE 1 2 }  { m_axi_gmem_AWCACHE PROT 1 4 }  { m_axi_gmem_AWPROT QOS 1 3 }  { m_axi_gmem_AWQOS REGION 1 4 }  { m_axi_gmem_AWREGION USER 1 4 }  { m_axi_gmem_AWUSER DATA 1 1 }  { m_axi_gmem_WVALID VALID 1 1 }  { m_axi_gmem_WREADY READY 0 1 }  { m_axi_gmem_WDATA FIFONUM 1 64 }  { m_axi_gmem_WSTRB STRB 1 8 }  { m_axi_gmem_WLAST LAST 1 1 }  { m_axi_gmem_WID ID 1 1 }  { m_axi_gmem_WUSER DATA 1 1 }  { m_axi_gmem_ARVALID VALID 1 1 }  { m_axi_gmem_ARREADY READY 0 1 }  { m_axi_gmem_ARADDR ADDR 1 64 }  { m_axi_gmem_ARID ID 1 1 }  { m_axi_gmem_ARLEN SIZE 1 32 }  { m_axi_gmem_ARSIZE BURST 1 3 }  { m_axi_gmem_ARBURST LOCK 1 2 }  { m_axi_gmem_ARLOCK CACHE 1 2 }  { m_axi_gmem_ARCACHE PROT 1 4 }  { m_axi_gmem_ARPROT QOS 1 3 }  { m_axi_gmem_ARQOS REGION 1 4 }  { m_axi_gmem_ARREGION USER 1 4 }  { m_axi_gmem_ARUSER DATA 1 1 }  { m_axi_gmem_RVALID VALID 0 1 }  { m_axi_gmem_RREADY READY 1 1 }  { m_axi_gmem_RDATA FIFONUM 0 64 }  { m_axi_gmem_RLAST LAST 0 1 }  { m_axi_gmem_RID ID 0 1 }  { m_axi_gmem_RFIFONUM LEN 0 9 }  { m_axi_gmem_RUSER DATA 0 1 }  { m_axi_gmem_RRESP RESP 0 2 }  { m_axi_gmem_BVALID VALID 0 1 }  { m_axi_gmem_BREADY READY 1 1 }  { m_axi_gmem_BRESP RESP 0 2 }  { m_axi_gmem_BID ID 0 1 }  { m_axi_gmem_BUSER DATA 0 1 } } }
}
