set moduleName kp_hls_stem
set isTopModule 1
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
set C_modelName {kp_hls_stem}
set C_modelType { void 0 }
set ap_memory_interface_dict [dict create]
set C_modelArgList {
	{ gmem int 64 regular {axi_master 2}  }
	{ in_r int 64 regular {axi_slave 0}  }
	{ w int 64 regular {axi_slave 0}  }
	{ bias int 64 regular {axi_slave 0}  }
	{ M int 64 regular {axi_slave 0}  }
	{ F int 32 regular {axi_slave 0}  }
	{ out_r int 64 regular {axi_slave 0}  }
}
set hasAXIMCache 0
set hasAXIML2Cache 0
set AXIMCacheInstDict [dict create]
set C_modelArgMapList {[ 
	{ "Name" : "gmem", "interface" : "axi_master", "bitwidth" : 64, "direction" : "READWRITE", "bitSlice":[ {"cElement": [{"cName": "in_r","offset": { "type": "dynamic","port_name": "in_r","bundle": "ctrl"},"direction": "READONLY"},{"cName": "w","offset": { "type": "dynamic","port_name": "w","bundle": "ctrl"},"direction": "READONLY"},{"cName": "bias","offset": { "type": "dynamic","port_name": "bias","bundle": "ctrl"},"direction": "READONLY"},{"cName": "M","offset": { "type": "dynamic","port_name": "M","bundle": "ctrl"},"direction": "READONLY"},{"cName": "out_r","offset": { "type": "dynamic","port_name": "out_r","bundle": "ctrl"},"direction": "WRITEONLY"}]}]} , 
 	{ "Name" : "in_r", "interface" : "axi_slave", "bundle":"ctrl","type":"ap_none","bitwidth" : 64, "direction" : "READONLY", "offset" : {"in":16}, "offset_end" : {"in":27}} , 
 	{ "Name" : "w", "interface" : "axi_slave", "bundle":"ctrl","type":"ap_none","bitwidth" : 64, "direction" : "READONLY", "offset" : {"in":28}, "offset_end" : {"in":39}} , 
 	{ "Name" : "bias", "interface" : "axi_slave", "bundle":"ctrl","type":"ap_none","bitwidth" : 64, "direction" : "READONLY", "offset" : {"in":40}, "offset_end" : {"in":51}} , 
 	{ "Name" : "M", "interface" : "axi_slave", "bundle":"ctrl","type":"ap_none","bitwidth" : 64, "direction" : "READONLY", "offset" : {"in":52}, "offset_end" : {"in":63}} , 
 	{ "Name" : "F", "interface" : "axi_slave", "bundle":"ctrl","type":"ap_none","bitwidth" : 32, "direction" : "READONLY", "offset" : {"in":64}, "offset_end" : {"in":71}} , 
 	{ "Name" : "out_r", "interface" : "axi_slave", "bundle":"ctrl","type":"ap_none","bitwidth" : 64, "direction" : "READONLY", "offset" : {"in":72}, "offset_end" : {"in":83}} ]}
# RTL Port declarations: 
set portNum 65
set portList { 
	{ ap_clk sc_in sc_logic 1 clock -1 } 
	{ ap_rst_n sc_in sc_logic 1 reset -1 active_low_sync } 
	{ m_axi_gmem_AWVALID sc_out sc_logic 1 signal 0 } 
	{ m_axi_gmem_AWREADY sc_in sc_logic 1 signal 0 } 
	{ m_axi_gmem_AWADDR sc_out sc_lv 64 signal 0 } 
	{ m_axi_gmem_AWID sc_out sc_lv 1 signal 0 } 
	{ m_axi_gmem_AWLEN sc_out sc_lv 8 signal 0 } 
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
	{ m_axi_gmem_ARLEN sc_out sc_lv 8 signal 0 } 
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
	{ m_axi_gmem_RUSER sc_in sc_lv 1 signal 0 } 
	{ m_axi_gmem_RRESP sc_in sc_lv 2 signal 0 } 
	{ m_axi_gmem_BVALID sc_in sc_logic 1 signal 0 } 
	{ m_axi_gmem_BREADY sc_out sc_logic 1 signal 0 } 
	{ m_axi_gmem_BRESP sc_in sc_lv 2 signal 0 } 
	{ m_axi_gmem_BID sc_in sc_lv 1 signal 0 } 
	{ m_axi_gmem_BUSER sc_in sc_lv 1 signal 0 } 
	{ s_axi_ctrl_AWVALID sc_in sc_logic 1 signal -1 } 
	{ s_axi_ctrl_AWREADY sc_out sc_logic 1 signal -1 } 
	{ s_axi_ctrl_AWADDR sc_in sc_lv 7 signal -1 } 
	{ s_axi_ctrl_WVALID sc_in sc_logic 1 signal -1 } 
	{ s_axi_ctrl_WREADY sc_out sc_logic 1 signal -1 } 
	{ s_axi_ctrl_WDATA sc_in sc_lv 32 signal -1 } 
	{ s_axi_ctrl_WSTRB sc_in sc_lv 4 signal -1 } 
	{ s_axi_ctrl_ARVALID sc_in sc_logic 1 signal -1 } 
	{ s_axi_ctrl_ARREADY sc_out sc_logic 1 signal -1 } 
	{ s_axi_ctrl_ARADDR sc_in sc_lv 7 signal -1 } 
	{ s_axi_ctrl_RVALID sc_out sc_logic 1 signal -1 } 
	{ s_axi_ctrl_RREADY sc_in sc_logic 1 signal -1 } 
	{ s_axi_ctrl_RDATA sc_out sc_lv 32 signal -1 } 
	{ s_axi_ctrl_RRESP sc_out sc_lv 2 signal -1 } 
	{ s_axi_ctrl_BVALID sc_out sc_logic 1 signal -1 } 
	{ s_axi_ctrl_BREADY sc_in sc_logic 1 signal -1 } 
	{ s_axi_ctrl_BRESP sc_out sc_lv 2 signal -1 } 
	{ interrupt sc_out sc_logic 1 signal -1 } 
}
set NewPortList {[ 
	{ "name": "s_axi_ctrl_AWADDR", "direction": "in", "datatype": "sc_lv", "bitwidth":7, "type": "signal", "bundle":{"name": "ctrl", "role": "AWADDR" },"address":[{"name":"kp_hls_stem","role":"start","value":"0","valid_bit":"0"},{"name":"kp_hls_stem","role":"continue","value":"0","valid_bit":"4"},{"name":"kp_hls_stem","role":"auto_start","value":"0","valid_bit":"7"},{"name":"in_r","role":"data","value":"16"},{"name":"w","role":"data","value":"28"},{"name":"bias","role":"data","value":"40"},{"name":"M","role":"data","value":"52"},{"name":"F","role":"data","value":"64"},{"name":"out_r","role":"data","value":"72"}] },
	{ "name": "s_axi_ctrl_AWVALID", "direction": "in", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "ctrl", "role": "AWVALID" } },
	{ "name": "s_axi_ctrl_AWREADY", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "ctrl", "role": "AWREADY" } },
	{ "name": "s_axi_ctrl_WVALID", "direction": "in", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "ctrl", "role": "WVALID" } },
	{ "name": "s_axi_ctrl_WREADY", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "ctrl", "role": "WREADY" } },
	{ "name": "s_axi_ctrl_WDATA", "direction": "in", "datatype": "sc_lv", "bitwidth":32, "type": "signal", "bundle":{"name": "ctrl", "role": "WDATA" } },
	{ "name": "s_axi_ctrl_WSTRB", "direction": "in", "datatype": "sc_lv", "bitwidth":4, "type": "signal", "bundle":{"name": "ctrl", "role": "WSTRB" } },
	{ "name": "s_axi_ctrl_ARADDR", "direction": "in", "datatype": "sc_lv", "bitwidth":7, "type": "signal", "bundle":{"name": "ctrl", "role": "ARADDR" },"address":[{"name":"kp_hls_stem","role":"start","value":"0","valid_bit":"0"},{"name":"kp_hls_stem","role":"done","value":"0","valid_bit":"1"},{"name":"kp_hls_stem","role":"idle","value":"0","valid_bit":"2"},{"name":"kp_hls_stem","role":"ready","value":"0","valid_bit":"3"},{"name":"kp_hls_stem","role":"auto_start","value":"0","valid_bit":"7"}] },
	{ "name": "s_axi_ctrl_ARVALID", "direction": "in", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "ctrl", "role": "ARVALID" } },
	{ "name": "s_axi_ctrl_ARREADY", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "ctrl", "role": "ARREADY" } },
	{ "name": "s_axi_ctrl_RVALID", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "ctrl", "role": "RVALID" } },
	{ "name": "s_axi_ctrl_RREADY", "direction": "in", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "ctrl", "role": "RREADY" } },
	{ "name": "s_axi_ctrl_RDATA", "direction": "out", "datatype": "sc_lv", "bitwidth":32, "type": "signal", "bundle":{"name": "ctrl", "role": "RDATA" } },
	{ "name": "s_axi_ctrl_RRESP", "direction": "out", "datatype": "sc_lv", "bitwidth":2, "type": "signal", "bundle":{"name": "ctrl", "role": "RRESP" } },
	{ "name": "s_axi_ctrl_BVALID", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "ctrl", "role": "BVALID" } },
	{ "name": "s_axi_ctrl_BREADY", "direction": "in", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "ctrl", "role": "BREADY" } },
	{ "name": "s_axi_ctrl_BRESP", "direction": "out", "datatype": "sc_lv", "bitwidth":2, "type": "signal", "bundle":{"name": "ctrl", "role": "BRESP" } },
	{ "name": "interrupt", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "ctrl", "role": "interrupt" } }, 
 	{ "name": "ap_clk", "direction": "in", "datatype": "sc_logic", "bitwidth":1, "type": "clock", "bundle":{"name": "ap_clk", "role": "default" }} , 
 	{ "name": "ap_rst_n", "direction": "in", "datatype": "sc_logic", "bitwidth":1, "type": "reset", "bundle":{"name": "ap_rst_n", "role": "default" }} , 
 	{ "name": "m_axi_gmem_AWVALID", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "gmem", "role": "AWVALID" }} , 
 	{ "name": "m_axi_gmem_AWREADY", "direction": "in", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "gmem", "role": "AWREADY" }} , 
 	{ "name": "m_axi_gmem_AWADDR", "direction": "out", "datatype": "sc_lv", "bitwidth":64, "type": "signal", "bundle":{"name": "gmem", "role": "AWADDR" }} , 
 	{ "name": "m_axi_gmem_AWID", "direction": "out", "datatype": "sc_lv", "bitwidth":1, "type": "signal", "bundle":{"name": "gmem", "role": "AWID" }} , 
 	{ "name": "m_axi_gmem_AWLEN", "direction": "out", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "gmem", "role": "AWLEN" }} , 
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
 	{ "name": "m_axi_gmem_ARLEN", "direction": "out", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "gmem", "role": "ARLEN" }} , 
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
 	{ "name": "m_axi_gmem_RUSER", "direction": "in", "datatype": "sc_lv", "bitwidth":1, "type": "signal", "bundle":{"name": "gmem", "role": "RUSER" }} , 
 	{ "name": "m_axi_gmem_RRESP", "direction": "in", "datatype": "sc_lv", "bitwidth":2, "type": "signal", "bundle":{"name": "gmem", "role": "RRESP" }} , 
 	{ "name": "m_axi_gmem_BVALID", "direction": "in", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "gmem", "role": "BVALID" }} , 
 	{ "name": "m_axi_gmem_BREADY", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "gmem", "role": "BREADY" }} , 
 	{ "name": "m_axi_gmem_BRESP", "direction": "in", "datatype": "sc_lv", "bitwidth":2, "type": "signal", "bundle":{"name": "gmem", "role": "BRESP" }} , 
 	{ "name": "m_axi_gmem_BID", "direction": "in", "datatype": "sc_lv", "bitwidth":1, "type": "signal", "bundle":{"name": "gmem", "role": "BID" }} , 
 	{ "name": "m_axi_gmem_BUSER", "direction": "in", "datatype": "sc_lv", "bitwidth":1, "type": "signal", "bundle":{"name": "gmem", "role": "BUSER" }}  ]}

set RtlHierarchyInfo {[
	{"ID" : "0", "Level" : "0", "Path" : "`AUTOTB_DUT_INST", "Parent" : "", "Child" : ["1", "167", "168"],
		"CDFG" : "kp_hls_stem",
		"Protocol" : "ap_ctrl_hs",
		"ControlExist" : "1", "ap_start" : "1", "ap_ready" : "1", "ap_done" : "1", "ap_continue" : "0", "ap_idle" : "1", "real_start" : "0",
		"Pipeline" : "None", "UnalignedPipeline" : "0", "RewindPipeline" : "0", "ProcessNetwork" : "0",
		"II" : "0",
		"VariableLatency" : "1", "ExactLatency" : "-1", "EstimateLatencyMin" : "2249951", "EstimateLatencyMax" : "2249951",
		"Combinational" : "0",
		"Datapath" : "0",
		"ClockEnable" : "0",
		"HasSubDataflow" : "0",
		"InDataflowNetwork" : "0",
		"HasNonBlockingOperation" : "0",
		"IsBlackBox" : "0",
		"Port" : [
			{"Name" : "gmem", "Type" : "MAXI", "Direction" : "IO",
				"SubConnect" : [
					{"ID" : "1", "SubInstance" : "grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102", "Port" : "gmem", "Inst_start_state" : "2", "Inst_end_state" : "3"}]},
			{"Name" : "in_r", "Type" : "None", "Direction" : "I"},
			{"Name" : "w", "Type" : "None", "Direction" : "I"},
			{"Name" : "bias", "Type" : "None", "Direction" : "I"},
			{"Name" : "M", "Type" : "None", "Direction" : "I"},
			{"Name" : "F", "Type" : "None", "Direction" : "I"},
			{"Name" : "out_r", "Type" : "None", "Direction" : "I"}]},
	{"ID" : "1", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102", "Parent" : "0", "Child" : ["2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46", "47", "48", "49", "50", "51", "52", "53", "54", "55", "56", "57", "58", "59", "60", "61", "62", "63", "64", "65", "66", "67", "68", "69", "70", "71", "72", "73", "74", "75", "76", "77", "78", "79", "80", "81", "82", "83", "84", "85", "86", "87", "88", "89", "90", "91", "92", "93", "94", "95", "96", "97", "98", "99", "106", "109"],
		"CDFG" : "kp_hls_conv_core_2_96_96_3_2_16_s",
		"Protocol" : "ap_ctrl_hs",
		"ControlExist" : "1", "ap_start" : "1", "ap_ready" : "1", "ap_done" : "1", "ap_continue" : "0", "ap_idle" : "1", "real_start" : "0",
		"Pipeline" : "None", "UnalignedPipeline" : "0", "RewindPipeline" : "0", "ProcessNetwork" : "0",
		"II" : "0",
		"VariableLatency" : "1", "ExactLatency" : "-1", "EstimateLatencyMin" : "2249949", "EstimateLatencyMax" : "2249949",
		"Combinational" : "0",
		"Datapath" : "0",
		"ClockEnable" : "0",
		"HasSubDataflow" : "0",
		"InDataflowNetwork" : "0",
		"HasNonBlockingOperation" : "0",
		"IsBlackBox" : "0",
		"Port" : [
			{"Name" : "gmem", "Type" : "MAXI", "Direction" : "IO",
				"SubConnect" : [
					{"ID" : "106", "SubInstance" : "grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_112_1_VITIS_LOOP_113_2_VITIS_LOOP_114_3_VIT_fu_674", "Port" : "gmem", "Inst_start_state" : "3", "Inst_end_state" : "4"},
					{"ID" : "109", "SubInstance" : "grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778", "Port" : "gmem", "Inst_start_state" : "5", "Inst_end_state" : "6"}]},
			{"Name" : "in_r", "Type" : "None", "Direction" : "I"},
			{"Name" : "w", "Type" : "None", "Direction" : "I"},
			{"Name" : "bias", "Type" : "None", "Direction" : "I"},
			{"Name" : "M", "Type" : "None", "Direction" : "I"},
			{"Name" : "F", "Type" : "None", "Direction" : "I"},
			{"Name" : "out_r", "Type" : "None", "Direction" : "I"}]},
	{"ID" : "2", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_U", "Parent" : "1"},
	{"ID" : "3", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_1_U", "Parent" : "1"},
	{"ID" : "4", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_2_U", "Parent" : "1"},
	{"ID" : "5", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_3_U", "Parent" : "1"},
	{"ID" : "6", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_4_U", "Parent" : "1"},
	{"ID" : "7", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_5_U", "Parent" : "1"},
	{"ID" : "8", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_6_U", "Parent" : "1"},
	{"ID" : "9", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_7_U", "Parent" : "1"},
	{"ID" : "10", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_8_U", "Parent" : "1"},
	{"ID" : "11", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_9_U", "Parent" : "1"},
	{"ID" : "12", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_10_U", "Parent" : "1"},
	{"ID" : "13", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_11_U", "Parent" : "1"},
	{"ID" : "14", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_12_U", "Parent" : "1"},
	{"ID" : "15", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_13_U", "Parent" : "1"},
	{"ID" : "16", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_14_U", "Parent" : "1"},
	{"ID" : "17", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_15_U", "Parent" : "1"},
	{"ID" : "18", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_16_U", "Parent" : "1"},
	{"ID" : "19", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_17_U", "Parent" : "1"},
	{"ID" : "20", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_18_U", "Parent" : "1"},
	{"ID" : "21", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_19_U", "Parent" : "1"},
	{"ID" : "22", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_20_U", "Parent" : "1"},
	{"ID" : "23", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_21_U", "Parent" : "1"},
	{"ID" : "24", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_22_U", "Parent" : "1"},
	{"ID" : "25", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_23_U", "Parent" : "1"},
	{"ID" : "26", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_24_U", "Parent" : "1"},
	{"ID" : "27", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_25_U", "Parent" : "1"},
	{"ID" : "28", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_26_U", "Parent" : "1"},
	{"ID" : "29", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_27_U", "Parent" : "1"},
	{"ID" : "30", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_28_U", "Parent" : "1"},
	{"ID" : "31", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_29_U", "Parent" : "1"},
	{"ID" : "32", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_30_U", "Parent" : "1"},
	{"ID" : "33", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_31_U", "Parent" : "1"},
	{"ID" : "34", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_32_U", "Parent" : "1"},
	{"ID" : "35", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_33_U", "Parent" : "1"},
	{"ID" : "36", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_34_U", "Parent" : "1"},
	{"ID" : "37", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_35_U", "Parent" : "1"},
	{"ID" : "38", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_36_U", "Parent" : "1"},
	{"ID" : "39", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_37_U", "Parent" : "1"},
	{"ID" : "40", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_38_U", "Parent" : "1"},
	{"ID" : "41", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_39_U", "Parent" : "1"},
	{"ID" : "42", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_40_U", "Parent" : "1"},
	{"ID" : "43", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_41_U", "Parent" : "1"},
	{"ID" : "44", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_42_U", "Parent" : "1"},
	{"ID" : "45", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_43_U", "Parent" : "1"},
	{"ID" : "46", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_44_U", "Parent" : "1"},
	{"ID" : "47", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_45_U", "Parent" : "1"},
	{"ID" : "48", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_46_U", "Parent" : "1"},
	{"ID" : "49", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_47_U", "Parent" : "1"},
	{"ID" : "50", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_48_U", "Parent" : "1"},
	{"ID" : "51", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_49_U", "Parent" : "1"},
	{"ID" : "52", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_50_U", "Parent" : "1"},
	{"ID" : "53", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_51_U", "Parent" : "1"},
	{"ID" : "54", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_52_U", "Parent" : "1"},
	{"ID" : "55", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_53_U", "Parent" : "1"},
	{"ID" : "56", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_54_U", "Parent" : "1"},
	{"ID" : "57", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_55_U", "Parent" : "1"},
	{"ID" : "58", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_56_U", "Parent" : "1"},
	{"ID" : "59", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_57_U", "Parent" : "1"},
	{"ID" : "60", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_58_U", "Parent" : "1"},
	{"ID" : "61", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_59_U", "Parent" : "1"},
	{"ID" : "62", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_60_U", "Parent" : "1"},
	{"ID" : "63", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_61_U", "Parent" : "1"},
	{"ID" : "64", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_62_U", "Parent" : "1"},
	{"ID" : "65", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_63_U", "Parent" : "1"},
	{"ID" : "66", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_64_U", "Parent" : "1"},
	{"ID" : "67", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_65_U", "Parent" : "1"},
	{"ID" : "68", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_66_U", "Parent" : "1"},
	{"ID" : "69", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_67_U", "Parent" : "1"},
	{"ID" : "70", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_68_U", "Parent" : "1"},
	{"ID" : "71", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_69_U", "Parent" : "1"},
	{"ID" : "72", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_70_U", "Parent" : "1"},
	{"ID" : "73", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_71_U", "Parent" : "1"},
	{"ID" : "74", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_72_U", "Parent" : "1"},
	{"ID" : "75", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_73_U", "Parent" : "1"},
	{"ID" : "76", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_74_U", "Parent" : "1"},
	{"ID" : "77", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_75_U", "Parent" : "1"},
	{"ID" : "78", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_76_U", "Parent" : "1"},
	{"ID" : "79", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_77_U", "Parent" : "1"},
	{"ID" : "80", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_78_U", "Parent" : "1"},
	{"ID" : "81", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_79_U", "Parent" : "1"},
	{"ID" : "82", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_80_U", "Parent" : "1"},
	{"ID" : "83", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_81_U", "Parent" : "1"},
	{"ID" : "84", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_82_U", "Parent" : "1"},
	{"ID" : "85", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_83_U", "Parent" : "1"},
	{"ID" : "86", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_84_U", "Parent" : "1"},
	{"ID" : "87", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_85_U", "Parent" : "1"},
	{"ID" : "88", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_86_U", "Parent" : "1"},
	{"ID" : "89", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_87_U", "Parent" : "1"},
	{"ID" : "90", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_88_U", "Parent" : "1"},
	{"ID" : "91", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_89_U", "Parent" : "1"},
	{"ID" : "92", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_90_U", "Parent" : "1"},
	{"ID" : "93", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_91_U", "Parent" : "1"},
	{"ID" : "94", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_92_U", "Parent" : "1"},
	{"ID" : "95", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_93_U", "Parent" : "1"},
	{"ID" : "96", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_94_U", "Parent" : "1"},
	{"ID" : "97", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_95_U", "Parent" : "1"},
	{"ID" : "98", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.xp_96_U", "Parent" : "1"},
	{"ID" : "99", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_2_96_96_3_2_16_Pipeline_1_fu_476", "Parent" : "1", "Child" : ["100", "101", "102", "103", "104", "105"],
		"CDFG" : "kp_hls_conv_core_2_96_96_3_2_16_Pipeline_1",
		"Protocol" : "ap_ctrl_hs",
		"ControlExist" : "1", "ap_start" : "1", "ap_ready" : "1", "ap_done" : "1", "ap_continue" : "0", "ap_idle" : "1", "real_start" : "0",
		"Pipeline" : "None", "UnalignedPipeline" : "0", "RewindPipeline" : "0", "ProcessNetwork" : "0",
		"II" : "0",
		"VariableLatency" : "1", "ExactLatency" : "-1", "EstimateLatencyMin" : "56488", "EstimateLatencyMax" : "56488",
		"Combinational" : "0",
		"Datapath" : "0",
		"ClockEnable" : "0",
		"HasSubDataflow" : "0",
		"InDataflowNetwork" : "0",
		"HasNonBlockingOperation" : "0",
		"IsBlackBox" : "0",
		"Port" : [
			{"Name" : "xp_96", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_95", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_94", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_93", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_92", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_91", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_90", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_89", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_88", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_87", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_86", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_85", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_84", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_83", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_82", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_81", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_80", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_79", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_78", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_77", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_76", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_75", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_74", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_73", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_72", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_71", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_70", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_69", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_68", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_67", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_66", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_65", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_64", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_63", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_62", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_61", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_60", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_59", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_58", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_57", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_56", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_55", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_54", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_53", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_52", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_51", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_50", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_49", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_48", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_47", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_46", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_45", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_44", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_43", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_42", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_41", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_40", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_39", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_38", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_37", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_36", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_35", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_34", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_33", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_32", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_31", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_30", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_29", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_28", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_27", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_26", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_25", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_24", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_23", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_22", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_21", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_20", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_19", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_18", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_17", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_16", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_15", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_14", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_13", "Type" : "Memory", "Direction" : "O"},
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
				"LoopDec" : {"FSMBitwidth" : "1", "FirstState" : "ap_ST_fsm_pp0_stage0", "FirstStateIter" : "ap_enable_reg_pp0_iter0", "FirstStateBlock" : "ap_block_pp0_stage0_subdone", "LastState" : "ap_ST_fsm_pp0_stage0", "LastStateIter" : "ap_enable_reg_pp0_iter33", "LastStateBlock" : "ap_block_pp0_stage0_subdone", "QuitState" : "ap_ST_fsm_pp0_stage0", "QuitStateIter" : "ap_enable_reg_pp0_iter33", "QuitStateBlock" : "ap_block_pp0_stage0_subdone", "OneDepthLoop" : "0", "has_ap_ctrl" : "1", "has_continue" : "0"}}]},
	{"ID" : "100", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_2_96_96_3_2_16_Pipeline_1_fu_476.mul_15ns_17ns_31_1_1_U1", "Parent" : "99"},
	{"ID" : "101", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_2_96_96_3_2_16_Pipeline_1_fu_476.urem_15ns_10ns_9_19_1_U2", "Parent" : "99"},
	{"ID" : "102", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_2_96_96_3_2_16_Pipeline_1_fu_476.mul_9ns_11ns_19_1_1_U3", "Parent" : "99"},
	{"ID" : "103", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_2_96_96_3_2_16_Pipeline_1_fu_476.urem_9ns_3ns_9_13_1_U4", "Parent" : "99"},
	{"ID" : "104", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_2_96_96_3_2_16_Pipeline_1_fu_476.mac_muladd_7ns_2ns_7ns_8_4_1_U5", "Parent" : "99"},
	{"ID" : "105", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_2_96_96_3_2_16_Pipeline_1_fu_476.flow_control_loop_pipe_sequential_init_U", "Parent" : "99"},
	{"ID" : "106", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_112_1_VITIS_LOOP_113_2_VITIS_LOOP_114_3_VIT_fu_674", "Parent" : "1", "Child" : ["107", "108"],
		"CDFG" : "kp_hls_conv_core_Pipeline_VITIS_LOOP_112_1_VITIS_LOOP_113_2_VITIS_LOOP_114_3_VIT",
		"Protocol" : "ap_ctrl_hs",
		"ControlExist" : "1", "ap_start" : "1", "ap_ready" : "1", "ap_done" : "1", "ap_continue" : "0", "ap_idle" : "1", "real_start" : "0",
		"Pipeline" : "None", "UnalignedPipeline" : "0", "RewindPipeline" : "0", "ProcessNetwork" : "0",
		"II" : "0",
		"VariableLatency" : "1", "ExactLatency" : "-1", "EstimateLatencyMin" : "55312", "EstimateLatencyMax" : "55312",
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
			{"Name" : "xp_12", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_13", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_14", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_15", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_16", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_17", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_18", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_19", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_20", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_21", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_22", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_23", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_24", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_25", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_26", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_27", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_28", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_29", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_30", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_31", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_32", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_33", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_34", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_35", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_36", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_37", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_38", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_39", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_40", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_41", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_42", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_43", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_44", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_45", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_46", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_47", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_48", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_49", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_50", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_51", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_52", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_53", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_54", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_55", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_56", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_57", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_58", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_59", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_60", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_61", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_62", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_63", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_64", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_65", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_66", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_67", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_68", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_69", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_70", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_71", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_72", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_73", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_74", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_75", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_76", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_77", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_78", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_79", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_80", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_81", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_82", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_83", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_84", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_85", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_86", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_87", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_88", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_89", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_90", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_91", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_92", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_93", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_94", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "xp_95", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "in_r", "Type" : "None", "Direction" : "I"},
			{"Name" : "gmem", "Type" : "MAXI", "Direction" : "I",
				"BlockSignal" : [
					{"Name" : "gmem_blk_n_AR", "Type" : "RtlSignal"},
					{"Name" : "gmem_blk_n_R", "Type" : "RtlSignal"}]}],
		"Loop" : [
			{"Name" : "VITIS_LOOP_112_1_VITIS_LOOP_113_2_VITIS_LOOP_114_3_VITIS_LOOP_115_4", "PipelineType" : "UPC",
				"LoopDec" : {"FSMBitwidth" : "1", "FirstState" : "ap_ST_fsm_pp0_stage0", "FirstStateIter" : "ap_enable_reg_pp0_iter0", "FirstStateBlock" : "ap_block_pp0_stage0_subdone", "LastState" : "ap_ST_fsm_pp0_stage0", "LastStateIter" : "ap_enable_reg_pp0_iter15", "LastStateBlock" : "ap_block_pp0_stage0_subdone", "QuitState" : "ap_ST_fsm_pp0_stage0", "QuitStateIter" : "ap_enable_reg_pp0_iter15", "QuitStateBlock" : "ap_block_pp0_stage0_subdone", "OneDepthLoop" : "0", "has_ap_ctrl" : "1", "has_continue" : "0"}}]},
	{"ID" : "107", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_112_1_VITIS_LOOP_113_2_VITIS_LOOP_114_3_VIT_fu_674.mac_muladd_7ns_2ns_7ns_9_4_1_U108", "Parent" : "106"},
	{"ID" : "108", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_112_1_VITIS_LOOP_113_2_VITIS_LOOP_114_3_VIT_fu_674.flow_control_loop_pipe_sequential_init_U", "Parent" : "106"},
	{"ID" : "109", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778", "Parent" : "1", "Child" : ["110", "111", "112", "113", "114", "115", "116", "117", "118", "119", "120", "121", "122", "123", "124", "125", "126", "127", "128", "129", "130", "131", "132", "133", "134", "135", "136", "137", "138", "139", "140", "141", "142", "143", "144", "145", "146", "147", "148", "149", "150", "151", "152", "153", "154", "155", "156", "157", "158", "159", "160", "161", "162", "163", "164", "165", "166"],
		"CDFG" : "kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT",
		"Protocol" : "ap_ctrl_hs",
		"ControlExist" : "1", "ap_start" : "1", "ap_ready" : "1", "ap_done" : "1", "ap_continue" : "0", "ap_idle" : "1", "real_start" : "0",
		"Pipeline" : "None", "UnalignedPipeline" : "0", "RewindPipeline" : "0", "ProcessNetwork" : "0",
		"II" : "0",
		"VariableLatency" : "1", "ExactLatency" : "-1", "EstimateLatencyMin" : "2138144", "EstimateLatencyMax" : "2138144",
		"Combinational" : "0",
		"Datapath" : "0",
		"ClockEnable" : "0",
		"HasSubDataflow" : "0",
		"InDataflowNetwork" : "0",
		"HasNonBlockingOperation" : "0",
		"IsBlackBox" : "0",
		"Port" : [
			{"Name" : "sext_ln118", "Type" : "None", "Direction" : "I"},
			{"Name" : "gmem", "Type" : "MAXI", "Direction" : "IO",
				"BlockSignal" : [
					{"Name" : "gmem_blk_n_AR", "Type" : "RtlSignal"},
					{"Name" : "gmem_blk_n_R", "Type" : "RtlSignal"},
					{"Name" : "gmem_blk_n_AW", "Type" : "RtlSignal"},
					{"Name" : "gmem_blk_n_W", "Type" : "RtlSignal"},
					{"Name" : "gmem_blk_n_B", "Type" : "RtlSignal"}]},
			{"Name" : "w", "Type" : "None", "Direction" : "I"},
			{"Name" : "M", "Type" : "None", "Direction" : "I"},
			{"Name" : "sh_prom_i", "Type" : "None", "Direction" : "I"},
			{"Name" : "sub2_i", "Type" : "None", "Direction" : "I"},
			{"Name" : "half", "Type" : "None", "Direction" : "I"},
			{"Name" : "out_r", "Type" : "None", "Direction" : "I"},
			{"Name" : "xp", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_1", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_2", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_3", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_4", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_5", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_6", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_7", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_8", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_9", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_10", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_11", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_12", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_13", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_14", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_15", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_16", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_17", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_18", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_19", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_20", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_21", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_22", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_23", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_24", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_25", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_26", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_27", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_28", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_29", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_30", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_31", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_32", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_33", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_34", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_35", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_36", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_37", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_38", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_39", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_40", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_41", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_42", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_43", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_44", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_45", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_46", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_47", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_48", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_49", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_50", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_51", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_52", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_53", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_54", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_55", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_56", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_57", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_58", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_59", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_60", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_61", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_62", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_63", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_64", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_65", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_66", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_67", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_68", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_69", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_70", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_71", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_72", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_73", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_74", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_75", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_76", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_77", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_78", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_79", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_80", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_81", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_82", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_83", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_84", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_85", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_86", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_87", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_88", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_89", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_90", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_91", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_92", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_93", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_94", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_95", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "xp_96", "Type" : "Memory", "Direction" : "I"}],
		"Loop" : [
			{"Name" : "VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VITIS_LOOP_121_8", "PipelineType" : "UPC",
				"LoopDec" : {"FSMBitwidth" : "29", "FirstState" : "ap_ST_fsm_pp0_stage0", "FirstStateIter" : "ap_enable_reg_pp0_iter0", "FirstStateBlock" : "ap_block_pp0_stage0_subdone", "LastState" : "ap_ST_fsm_pp0_stage2", "LastStateIter" : "ap_enable_reg_pp0_iter2", "LastStateBlock" : "ap_block_pp0_stage2_subdone", "QuitState" : "ap_ST_fsm_pp0_stage2", "QuitStateIter" : "ap_enable_reg_pp0_iter2", "QuitStateBlock" : "ap_block_pp0_stage2_subdone", "OneDepthLoop" : "0", "has_ap_ctrl" : "1", "has_continue" : "0"}}]},
	{"ID" : "110", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mul_64s_32s_64_5_1_U208", "Parent" : "109"},
	{"ID" : "111", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.sparsemux_97_6_8_1_1_U209", "Parent" : "109"},
	{"ID" : "112", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.sparsemux_97_6_8_1_1_U210", "Parent" : "109"},
	{"ID" : "113", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mul_2ns_8ns_9_1_1_U211", "Parent" : "109"},
	{"ID" : "114", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mul_2ns_8ns_9_1_1_U212", "Parent" : "109"},
	{"ID" : "115", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mul_2ns_10ns_10_1_1_U213", "Parent" : "109"},
	{"ID" : "116", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.sparsemux_97_6_8_1_1_U214", "Parent" : "109"},
	{"ID" : "117", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.sparsemux_97_6_8_1_1_U215", "Parent" : "109"},
	{"ID" : "118", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.sparsemux_97_6_8_1_1_U216", "Parent" : "109"},
	{"ID" : "119", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.sparsemux_97_6_8_1_1_U217", "Parent" : "109"},
	{"ID" : "120", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.sparsemux_97_6_8_1_1_U218", "Parent" : "109"},
	{"ID" : "121", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.sparsemux_97_6_8_1_1_U219", "Parent" : "109"},
	{"ID" : "122", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.sparsemux_97_6_8_1_1_U220", "Parent" : "109"},
	{"ID" : "123", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.sparsemux_97_6_8_1_1_U221", "Parent" : "109"},
	{"ID" : "124", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.sparsemux_97_6_8_1_1_U222", "Parent" : "109"},
	{"ID" : "125", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mul_8s_8ns_16_1_1_U223", "Parent" : "109"},
	{"ID" : "126", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mul_8s_8ns_16_1_1_U224", "Parent" : "109"},
	{"ID" : "127", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mul_8s_8ns_16_1_1_U225", "Parent" : "109"},
	{"ID" : "128", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mul_8s_8ns_16_1_1_U226", "Parent" : "109"},
	{"ID" : "129", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mul_8s_8ns_16_1_1_U227", "Parent" : "109"},
	{"ID" : "130", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.sparsemux_97_6_8_1_1_U228", "Parent" : "109"},
	{"ID" : "131", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.sparsemux_97_6_8_1_1_U229", "Parent" : "109"},
	{"ID" : "132", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mul_8s_8ns_16_1_1_U230", "Parent" : "109"},
	{"ID" : "133", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.sparsemux_97_6_8_1_1_U231", "Parent" : "109"},
	{"ID" : "134", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mul_8s_8ns_16_1_1_U232", "Parent" : "109"},
	{"ID" : "135", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.sparsemux_97_6_8_1_1_U233", "Parent" : "109"},
	{"ID" : "136", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.sparsemux_97_6_8_1_1_U234", "Parent" : "109"},
	{"ID" : "137", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.sparsemux_97_6_8_1_1_U235", "Parent" : "109"},
	{"ID" : "138", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.sparsemux_97_6_8_1_1_U236", "Parent" : "109"},
	{"ID" : "139", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.sparsemux_97_6_8_1_1_U237", "Parent" : "109"},
	{"ID" : "140", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.sparsemux_97_6_8_1_1_U238", "Parent" : "109"},
	{"ID" : "141", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mul_8s_8ns_16_1_1_U239", "Parent" : "109"},
	{"ID" : "142", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.sparsemux_97_6_8_1_1_U240", "Parent" : "109"},
	{"ID" : "143", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.sparsemux_97_6_8_1_1_U241", "Parent" : "109"},
	{"ID" : "144", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mul_8s_8ns_16_1_1_U242", "Parent" : "109"},
	{"ID" : "145", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.sparsemux_97_6_8_1_1_U243", "Parent" : "109"},
	{"ID" : "146", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.sparsemux_97_6_8_1_1_U244", "Parent" : "109"},
	{"ID" : "147", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mul_8s_8ns_16_1_1_U245", "Parent" : "109"},
	{"ID" : "148", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.sparsemux_97_6_8_1_1_U246", "Parent" : "109"},
	{"ID" : "149", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mul_8s_8ns_16_1_1_U247", "Parent" : "109"},
	{"ID" : "150", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mul_8s_8ns_16_1_1_U248", "Parent" : "109"},
	{"ID" : "151", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mac_muladd_8s_8ns_16s_17_4_1_U249", "Parent" : "109"},
	{"ID" : "152", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mac_muladd_8s_8ns_16s_17_4_1_U250", "Parent" : "109"},
	{"ID" : "153", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mac_muladd_8s_8ns_16s_17_4_1_U251", "Parent" : "109"},
	{"ID" : "154", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mac_muladd_8s_8ns_16s_17_4_1_U252", "Parent" : "109"},
	{"ID" : "155", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mac_muladd_8s_8ns_17s_18_4_1_U253", "Parent" : "109"},
	{"ID" : "156", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mac_muladd_8s_8ns_16s_17_4_1_U254", "Parent" : "109"},
	{"ID" : "157", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mac_muladd_8s_8ns_16s_17_4_1_U255", "Parent" : "109"},
	{"ID" : "158", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mac_muladd_8s_8ns_16s_17_4_1_U256", "Parent" : "109"},
	{"ID" : "159", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mac_muladd_8s_8ns_17s_18_4_1_U257", "Parent" : "109"},
	{"ID" : "160", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mac_muladd_8s_8ns_16s_17_4_1_U258", "Parent" : "109"},
	{"ID" : "161", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mac_muladd_8s_8ns_16s_17_4_1_U259", "Parent" : "109"},
	{"ID" : "162", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mac_muladd_8s_8ns_16s_17_4_1_U260", "Parent" : "109"},
	{"ID" : "163", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mac_muladd_8s_8ns_17s_18_4_1_U261", "Parent" : "109"},
	{"ID" : "164", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mac_muladd_8s_8ns_16s_17_4_1_U262", "Parent" : "109"},
	{"ID" : "165", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.mac_muladd_8s_8ns_16s_17_4_1_U263", "Parent" : "109"},
	{"ID" : "166", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102.grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778.flow_control_loop_pipe_sequential_init_U", "Parent" : "109"},
	{"ID" : "167", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.ctrl_s_axi_U", "Parent" : "0"},
	{"ID" : "168", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.gmem_m_axi_U", "Parent" : "0"}]}


set ArgLastReadFirstWriteLatency {
	kp_hls_stem {
		gmem {Type IO LastRead 56 FirstWrite -1}
		in_r {Type I LastRead 0 FirstWrite -1}
		w {Type I LastRead 0 FirstWrite -1}
		bias {Type I LastRead 0 FirstWrite -1}
		M {Type I LastRead 0 FirstWrite -1}
		F {Type I LastRead 0 FirstWrite -1}
		out_r {Type I LastRead 0 FirstWrite -1}}
	kp_hls_conv_core_2_96_96_3_2_16_s {
		gmem {Type IO LastRead 56 FirstWrite -1}
		in_r {Type I LastRead 2 FirstWrite -1}
		w {Type I LastRead 4 FirstWrite -1}
		bias {Type I LastRead 4 FirstWrite -1}
		M {Type I LastRead 4 FirstWrite -1}
		F {Type I LastRead 3 FirstWrite -1}
		out_r {Type I LastRead 4 FirstWrite -1}}
	kp_hls_conv_core_2_96_96_3_2_16_Pipeline_1 {
		xp_96 {Type O LastRead -1 FirstWrite 33}
		xp_95 {Type O LastRead -1 FirstWrite 33}
		xp_94 {Type O LastRead -1 FirstWrite 33}
		xp_93 {Type O LastRead -1 FirstWrite 33}
		xp_92 {Type O LastRead -1 FirstWrite 33}
		xp_91 {Type O LastRead -1 FirstWrite 33}
		xp_90 {Type O LastRead -1 FirstWrite 33}
		xp_89 {Type O LastRead -1 FirstWrite 33}
		xp_88 {Type O LastRead -1 FirstWrite 33}
		xp_87 {Type O LastRead -1 FirstWrite 33}
		xp_86 {Type O LastRead -1 FirstWrite 33}
		xp_85 {Type O LastRead -1 FirstWrite 33}
		xp_84 {Type O LastRead -1 FirstWrite 33}
		xp_83 {Type O LastRead -1 FirstWrite 33}
		xp_82 {Type O LastRead -1 FirstWrite 33}
		xp_81 {Type O LastRead -1 FirstWrite 33}
		xp_80 {Type O LastRead -1 FirstWrite 33}
		xp_79 {Type O LastRead -1 FirstWrite 33}
		xp_78 {Type O LastRead -1 FirstWrite 33}
		xp_77 {Type O LastRead -1 FirstWrite 33}
		xp_76 {Type O LastRead -1 FirstWrite 33}
		xp_75 {Type O LastRead -1 FirstWrite 33}
		xp_74 {Type O LastRead -1 FirstWrite 33}
		xp_73 {Type O LastRead -1 FirstWrite 33}
		xp_72 {Type O LastRead -1 FirstWrite 33}
		xp_71 {Type O LastRead -1 FirstWrite 33}
		xp_70 {Type O LastRead -1 FirstWrite 33}
		xp_69 {Type O LastRead -1 FirstWrite 33}
		xp_68 {Type O LastRead -1 FirstWrite 33}
		xp_67 {Type O LastRead -1 FirstWrite 33}
		xp_66 {Type O LastRead -1 FirstWrite 33}
		xp_65 {Type O LastRead -1 FirstWrite 33}
		xp_64 {Type O LastRead -1 FirstWrite 33}
		xp_63 {Type O LastRead -1 FirstWrite 33}
		xp_62 {Type O LastRead -1 FirstWrite 33}
		xp_61 {Type O LastRead -1 FirstWrite 33}
		xp_60 {Type O LastRead -1 FirstWrite 33}
		xp_59 {Type O LastRead -1 FirstWrite 33}
		xp_58 {Type O LastRead -1 FirstWrite 33}
		xp_57 {Type O LastRead -1 FirstWrite 33}
		xp_56 {Type O LastRead -1 FirstWrite 33}
		xp_55 {Type O LastRead -1 FirstWrite 33}
		xp_54 {Type O LastRead -1 FirstWrite 33}
		xp_53 {Type O LastRead -1 FirstWrite 33}
		xp_52 {Type O LastRead -1 FirstWrite 33}
		xp_51 {Type O LastRead -1 FirstWrite 33}
		xp_50 {Type O LastRead -1 FirstWrite 33}
		xp_49 {Type O LastRead -1 FirstWrite 33}
		xp_48 {Type O LastRead -1 FirstWrite 33}
		xp_47 {Type O LastRead -1 FirstWrite 33}
		xp_46 {Type O LastRead -1 FirstWrite 33}
		xp_45 {Type O LastRead -1 FirstWrite 33}
		xp_44 {Type O LastRead -1 FirstWrite 33}
		xp_43 {Type O LastRead -1 FirstWrite 33}
		xp_42 {Type O LastRead -1 FirstWrite 33}
		xp_41 {Type O LastRead -1 FirstWrite 33}
		xp_40 {Type O LastRead -1 FirstWrite 33}
		xp_39 {Type O LastRead -1 FirstWrite 33}
		xp_38 {Type O LastRead -1 FirstWrite 33}
		xp_37 {Type O LastRead -1 FirstWrite 33}
		xp_36 {Type O LastRead -1 FirstWrite 33}
		xp_35 {Type O LastRead -1 FirstWrite 33}
		xp_34 {Type O LastRead -1 FirstWrite 33}
		xp_33 {Type O LastRead -1 FirstWrite 33}
		xp_32 {Type O LastRead -1 FirstWrite 33}
		xp_31 {Type O LastRead -1 FirstWrite 33}
		xp_30 {Type O LastRead -1 FirstWrite 33}
		xp_29 {Type O LastRead -1 FirstWrite 33}
		xp_28 {Type O LastRead -1 FirstWrite 33}
		xp_27 {Type O LastRead -1 FirstWrite 33}
		xp_26 {Type O LastRead -1 FirstWrite 33}
		xp_25 {Type O LastRead -1 FirstWrite 33}
		xp_24 {Type O LastRead -1 FirstWrite 33}
		xp_23 {Type O LastRead -1 FirstWrite 33}
		xp_22 {Type O LastRead -1 FirstWrite 33}
		xp_21 {Type O LastRead -1 FirstWrite 33}
		xp_20 {Type O LastRead -1 FirstWrite 33}
		xp_19 {Type O LastRead -1 FirstWrite 33}
		xp_18 {Type O LastRead -1 FirstWrite 33}
		xp_17 {Type O LastRead -1 FirstWrite 33}
		xp_16 {Type O LastRead -1 FirstWrite 33}
		xp_15 {Type O LastRead -1 FirstWrite 33}
		xp_14 {Type O LastRead -1 FirstWrite 33}
		xp_13 {Type O LastRead -1 FirstWrite 33}
		xp_12 {Type O LastRead -1 FirstWrite 33}
		xp_11 {Type O LastRead -1 FirstWrite 33}
		xp_10 {Type O LastRead -1 FirstWrite 33}
		xp_9 {Type O LastRead -1 FirstWrite 33}
		xp_8 {Type O LastRead -1 FirstWrite 33}
		xp_7 {Type O LastRead -1 FirstWrite 33}
		xp_6 {Type O LastRead -1 FirstWrite 33}
		xp_5 {Type O LastRead -1 FirstWrite 33}
		xp_4 {Type O LastRead -1 FirstWrite 33}
		xp_3 {Type O LastRead -1 FirstWrite 33}
		xp_2 {Type O LastRead -1 FirstWrite 33}
		xp_1 {Type O LastRead -1 FirstWrite 33}
		xp {Type O LastRead -1 FirstWrite 33}}
	kp_hls_conv_core_Pipeline_VITIS_LOOP_112_1_VITIS_LOOP_113_2_VITIS_LOOP_114_3_VIT {
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
		xp_12 {Type O LastRead -1 FirstWrite 15}
		xp_13 {Type O LastRead -1 FirstWrite 15}
		xp_14 {Type O LastRead -1 FirstWrite 15}
		xp_15 {Type O LastRead -1 FirstWrite 15}
		xp_16 {Type O LastRead -1 FirstWrite 15}
		xp_17 {Type O LastRead -1 FirstWrite 15}
		xp_18 {Type O LastRead -1 FirstWrite 15}
		xp_19 {Type O LastRead -1 FirstWrite 15}
		xp_20 {Type O LastRead -1 FirstWrite 15}
		xp_21 {Type O LastRead -1 FirstWrite 15}
		xp_22 {Type O LastRead -1 FirstWrite 15}
		xp_23 {Type O LastRead -1 FirstWrite 15}
		xp_24 {Type O LastRead -1 FirstWrite 15}
		xp_25 {Type O LastRead -1 FirstWrite 15}
		xp_26 {Type O LastRead -1 FirstWrite 15}
		xp_27 {Type O LastRead -1 FirstWrite 15}
		xp_28 {Type O LastRead -1 FirstWrite 15}
		xp_29 {Type O LastRead -1 FirstWrite 15}
		xp_30 {Type O LastRead -1 FirstWrite 15}
		xp_31 {Type O LastRead -1 FirstWrite 15}
		xp_32 {Type O LastRead -1 FirstWrite 15}
		xp_33 {Type O LastRead -1 FirstWrite 15}
		xp_34 {Type O LastRead -1 FirstWrite 15}
		xp_35 {Type O LastRead -1 FirstWrite 15}
		xp_36 {Type O LastRead -1 FirstWrite 15}
		xp_37 {Type O LastRead -1 FirstWrite 15}
		xp_38 {Type O LastRead -1 FirstWrite 15}
		xp_39 {Type O LastRead -1 FirstWrite 15}
		xp_40 {Type O LastRead -1 FirstWrite 15}
		xp_41 {Type O LastRead -1 FirstWrite 15}
		xp_42 {Type O LastRead -1 FirstWrite 15}
		xp_43 {Type O LastRead -1 FirstWrite 15}
		xp_44 {Type O LastRead -1 FirstWrite 15}
		xp_45 {Type O LastRead -1 FirstWrite 15}
		xp_46 {Type O LastRead -1 FirstWrite 15}
		xp_47 {Type O LastRead -1 FirstWrite 15}
		xp_48 {Type O LastRead -1 FirstWrite 15}
		xp_49 {Type O LastRead -1 FirstWrite 15}
		xp_50 {Type O LastRead -1 FirstWrite 15}
		xp_51 {Type O LastRead -1 FirstWrite 15}
		xp_52 {Type O LastRead -1 FirstWrite 15}
		xp_53 {Type O LastRead -1 FirstWrite 15}
		xp_54 {Type O LastRead -1 FirstWrite 15}
		xp_55 {Type O LastRead -1 FirstWrite 15}
		xp_56 {Type O LastRead -1 FirstWrite 15}
		xp_57 {Type O LastRead -1 FirstWrite 15}
		xp_58 {Type O LastRead -1 FirstWrite 15}
		xp_59 {Type O LastRead -1 FirstWrite 15}
		xp_60 {Type O LastRead -1 FirstWrite 15}
		xp_61 {Type O LastRead -1 FirstWrite 15}
		xp_62 {Type O LastRead -1 FirstWrite 15}
		xp_63 {Type O LastRead -1 FirstWrite 15}
		xp_64 {Type O LastRead -1 FirstWrite 15}
		xp_65 {Type O LastRead -1 FirstWrite 15}
		xp_66 {Type O LastRead -1 FirstWrite 15}
		xp_67 {Type O LastRead -1 FirstWrite 15}
		xp_68 {Type O LastRead -1 FirstWrite 15}
		xp_69 {Type O LastRead -1 FirstWrite 15}
		xp_70 {Type O LastRead -1 FirstWrite 15}
		xp_71 {Type O LastRead -1 FirstWrite 15}
		xp_72 {Type O LastRead -1 FirstWrite 15}
		xp_73 {Type O LastRead -1 FirstWrite 15}
		xp_74 {Type O LastRead -1 FirstWrite 15}
		xp_75 {Type O LastRead -1 FirstWrite 15}
		xp_76 {Type O LastRead -1 FirstWrite 15}
		xp_77 {Type O LastRead -1 FirstWrite 15}
		xp_78 {Type O LastRead -1 FirstWrite 15}
		xp_79 {Type O LastRead -1 FirstWrite 15}
		xp_80 {Type O LastRead -1 FirstWrite 15}
		xp_81 {Type O LastRead -1 FirstWrite 15}
		xp_82 {Type O LastRead -1 FirstWrite 15}
		xp_83 {Type O LastRead -1 FirstWrite 15}
		xp_84 {Type O LastRead -1 FirstWrite 15}
		xp_85 {Type O LastRead -1 FirstWrite 15}
		xp_86 {Type O LastRead -1 FirstWrite 15}
		xp_87 {Type O LastRead -1 FirstWrite 15}
		xp_88 {Type O LastRead -1 FirstWrite 15}
		xp_89 {Type O LastRead -1 FirstWrite 15}
		xp_90 {Type O LastRead -1 FirstWrite 15}
		xp_91 {Type O LastRead -1 FirstWrite 15}
		xp_92 {Type O LastRead -1 FirstWrite 15}
		xp_93 {Type O LastRead -1 FirstWrite 15}
		xp_94 {Type O LastRead -1 FirstWrite 15}
		xp_95 {Type O LastRead -1 FirstWrite 15}
		in_r {Type I LastRead 0 FirstWrite -1}
		gmem {Type I LastRead 13 FirstWrite -1}}
	kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT {
		sext_ln118 {Type I LastRead 0 FirstWrite -1}
		gmem {Type IO LastRead 56 FirstWrite 55}
		w {Type I LastRead 0 FirstWrite -1}
		M {Type I LastRead 0 FirstWrite -1}
		sh_prom_i {Type I LastRead 0 FirstWrite -1}
		sub2_i {Type I LastRead 0 FirstWrite -1}
		half {Type I LastRead 0 FirstWrite -1}
		out_r {Type I LastRead 0 FirstWrite -1}
		xp {Type I LastRead 8 FirstWrite -1}
		xp_1 {Type I LastRead 7 FirstWrite -1}
		xp_2 {Type I LastRead 8 FirstWrite -1}
		xp_3 {Type I LastRead 7 FirstWrite -1}
		xp_4 {Type I LastRead 8 FirstWrite -1}
		xp_5 {Type I LastRead 7 FirstWrite -1}
		xp_6 {Type I LastRead 8 FirstWrite -1}
		xp_7 {Type I LastRead 7 FirstWrite -1}
		xp_8 {Type I LastRead 8 FirstWrite -1}
		xp_9 {Type I LastRead 7 FirstWrite -1}
		xp_10 {Type I LastRead 8 FirstWrite -1}
		xp_11 {Type I LastRead 7 FirstWrite -1}
		xp_12 {Type I LastRead 8 FirstWrite -1}
		xp_13 {Type I LastRead 7 FirstWrite -1}
		xp_14 {Type I LastRead 8 FirstWrite -1}
		xp_15 {Type I LastRead 7 FirstWrite -1}
		xp_16 {Type I LastRead 8 FirstWrite -1}
		xp_17 {Type I LastRead 7 FirstWrite -1}
		xp_18 {Type I LastRead 8 FirstWrite -1}
		xp_19 {Type I LastRead 7 FirstWrite -1}
		xp_20 {Type I LastRead 8 FirstWrite -1}
		xp_21 {Type I LastRead 7 FirstWrite -1}
		xp_22 {Type I LastRead 8 FirstWrite -1}
		xp_23 {Type I LastRead 7 FirstWrite -1}
		xp_24 {Type I LastRead 8 FirstWrite -1}
		xp_25 {Type I LastRead 7 FirstWrite -1}
		xp_26 {Type I LastRead 8 FirstWrite -1}
		xp_27 {Type I LastRead 7 FirstWrite -1}
		xp_28 {Type I LastRead 8 FirstWrite -1}
		xp_29 {Type I LastRead 7 FirstWrite -1}
		xp_30 {Type I LastRead 8 FirstWrite -1}
		xp_31 {Type I LastRead 7 FirstWrite -1}
		xp_32 {Type I LastRead 8 FirstWrite -1}
		xp_33 {Type I LastRead 7 FirstWrite -1}
		xp_34 {Type I LastRead 8 FirstWrite -1}
		xp_35 {Type I LastRead 7 FirstWrite -1}
		xp_36 {Type I LastRead 8 FirstWrite -1}
		xp_37 {Type I LastRead 7 FirstWrite -1}
		xp_38 {Type I LastRead 8 FirstWrite -1}
		xp_39 {Type I LastRead 7 FirstWrite -1}
		xp_40 {Type I LastRead 8 FirstWrite -1}
		xp_41 {Type I LastRead 7 FirstWrite -1}
		xp_42 {Type I LastRead 8 FirstWrite -1}
		xp_43 {Type I LastRead 7 FirstWrite -1}
		xp_44 {Type I LastRead 8 FirstWrite -1}
		xp_45 {Type I LastRead 7 FirstWrite -1}
		xp_46 {Type I LastRead 8 FirstWrite -1}
		xp_47 {Type I LastRead 7 FirstWrite -1}
		xp_48 {Type I LastRead 8 FirstWrite -1}
		xp_49 {Type I LastRead 7 FirstWrite -1}
		xp_50 {Type I LastRead 8 FirstWrite -1}
		xp_51 {Type I LastRead 7 FirstWrite -1}
		xp_52 {Type I LastRead 8 FirstWrite -1}
		xp_53 {Type I LastRead 7 FirstWrite -1}
		xp_54 {Type I LastRead 7 FirstWrite -1}
		xp_55 {Type I LastRead 7 FirstWrite -1}
		xp_56 {Type I LastRead 7 FirstWrite -1}
		xp_57 {Type I LastRead 7 FirstWrite -1}
		xp_58 {Type I LastRead 7 FirstWrite -1}
		xp_59 {Type I LastRead 7 FirstWrite -1}
		xp_60 {Type I LastRead 7 FirstWrite -1}
		xp_61 {Type I LastRead 7 FirstWrite -1}
		xp_62 {Type I LastRead 7 FirstWrite -1}
		xp_63 {Type I LastRead 7 FirstWrite -1}
		xp_64 {Type I LastRead 7 FirstWrite -1}
		xp_65 {Type I LastRead 7 FirstWrite -1}
		xp_66 {Type I LastRead 7 FirstWrite -1}
		xp_67 {Type I LastRead 7 FirstWrite -1}
		xp_68 {Type I LastRead 7 FirstWrite -1}
		xp_69 {Type I LastRead 7 FirstWrite -1}
		xp_70 {Type I LastRead 7 FirstWrite -1}
		xp_71 {Type I LastRead 7 FirstWrite -1}
		xp_72 {Type I LastRead 7 FirstWrite -1}
		xp_73 {Type I LastRead 7 FirstWrite -1}
		xp_74 {Type I LastRead 7 FirstWrite -1}
		xp_75 {Type I LastRead 7 FirstWrite -1}
		xp_76 {Type I LastRead 7 FirstWrite -1}
		xp_77 {Type I LastRead 7 FirstWrite -1}
		xp_78 {Type I LastRead 7 FirstWrite -1}
		xp_79 {Type I LastRead 7 FirstWrite -1}
		xp_80 {Type I LastRead 7 FirstWrite -1}
		xp_81 {Type I LastRead 7 FirstWrite -1}
		xp_82 {Type I LastRead 7 FirstWrite -1}
		xp_83 {Type I LastRead 7 FirstWrite -1}
		xp_84 {Type I LastRead 7 FirstWrite -1}
		xp_85 {Type I LastRead 7 FirstWrite -1}
		xp_86 {Type I LastRead 7 FirstWrite -1}
		xp_87 {Type I LastRead 7 FirstWrite -1}
		xp_88 {Type I LastRead 7 FirstWrite -1}
		xp_89 {Type I LastRead 7 FirstWrite -1}
		xp_90 {Type I LastRead 7 FirstWrite -1}
		xp_91 {Type I LastRead 7 FirstWrite -1}
		xp_92 {Type I LastRead 7 FirstWrite -1}
		xp_93 {Type I LastRead 7 FirstWrite -1}
		xp_94 {Type I LastRead 7 FirstWrite -1}
		xp_95 {Type I LastRead 7 FirstWrite -1}
		xp_96 {Type I LastRead 7 FirstWrite -1}}}

set hasDtUnsupportedChannel 0

set PerformanceInfo {[
	{"Name" : "Latency", "Min" : "2249951", "Max" : "2249951"}
	, {"Name" : "Interval", "Min" : "2249952", "Max" : "2249952"}
]}

set PipelineEnableSignalInfo {[
]}

set Spec2ImplPortList { 
	gmem { m_axi {  { m_axi_gmem_AWVALID VALID 1 1 }  { m_axi_gmem_AWREADY READY 0 1 }  { m_axi_gmem_AWADDR ADDR 1 64 }  { m_axi_gmem_AWID ID 1 1 }  { m_axi_gmem_AWLEN SIZE 1 8 }  { m_axi_gmem_AWSIZE BURST 1 3 }  { m_axi_gmem_AWBURST LOCK 1 2 }  { m_axi_gmem_AWLOCK CACHE 1 2 }  { m_axi_gmem_AWCACHE PROT 1 4 }  { m_axi_gmem_AWPROT QOS 1 3 }  { m_axi_gmem_AWQOS REGION 1 4 }  { m_axi_gmem_AWREGION USER 1 4 }  { m_axi_gmem_AWUSER DATA 1 1 }  { m_axi_gmem_WVALID VALID 1 1 }  { m_axi_gmem_WREADY READY 0 1 }  { m_axi_gmem_WDATA FIFONUM 1 64 }  { m_axi_gmem_WSTRB STRB 1 8 }  { m_axi_gmem_WLAST LAST 1 1 }  { m_axi_gmem_WID ID 1 1 }  { m_axi_gmem_WUSER DATA 1 1 }  { m_axi_gmem_ARVALID VALID 1 1 }  { m_axi_gmem_ARREADY READY 0 1 }  { m_axi_gmem_ARADDR ADDR 1 64 }  { m_axi_gmem_ARID ID 1 1 }  { m_axi_gmem_ARLEN SIZE 1 8 }  { m_axi_gmem_ARSIZE BURST 1 3 }  { m_axi_gmem_ARBURST LOCK 1 2 }  { m_axi_gmem_ARLOCK CACHE 1 2 }  { m_axi_gmem_ARCACHE PROT 1 4 }  { m_axi_gmem_ARPROT QOS 1 3 }  { m_axi_gmem_ARQOS REGION 1 4 }  { m_axi_gmem_ARREGION USER 1 4 }  { m_axi_gmem_ARUSER DATA 1 1 }  { m_axi_gmem_RVALID VALID 0 1 }  { m_axi_gmem_RREADY READY 1 1 }  { m_axi_gmem_RDATA FIFONUM 0 64 }  { m_axi_gmem_RLAST LAST 0 1 }  { m_axi_gmem_RID ID 0 1 }  { m_axi_gmem_RUSER DATA 0 1 }  { m_axi_gmem_RRESP RESP 0 2 }  { m_axi_gmem_BVALID VALID 0 1 }  { m_axi_gmem_BREADY READY 1 1 }  { m_axi_gmem_BRESP RESP 0 2 }  { m_axi_gmem_BID ID 0 1 }  { m_axi_gmem_BUSER DATA 0 1 } } }
}

set maxi_interface_dict [dict create]
dict set maxi_interface_dict gmem { CHANNEL_NUM 0 BUNDLE gmem NUM_READ_OUTSTANDING 16 NUM_WRITE_OUTSTANDING 16 MAX_READ_BURST_LENGTH 16 MAX_WRITE_BURST_LENGTH 16 READ_WRITE_MODE READ_WRITE}

# RTL port scheduling information:
set fifoSchedulingInfoList { 
}

# RTL bus port read request latency information:
set busReadReqLatencyList { 
	{ gmem 1 }
}

# RTL bus port write response latency information:
set busWriteResLatencyList { 
	{ gmem 1 }
}

# RTL array port load latency information:
set memoryLoadLatencyList { 
}
