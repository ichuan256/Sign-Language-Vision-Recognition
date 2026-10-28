set moduleName kp_hls_pw3_v3
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
set C_modelName {kp_hls_pw3_v3}
set C_modelType { void 0 }
set ap_memory_interface_dict [dict create]
set C_modelArgList {
	{ gmem int 32 regular {axi_master 2}  }
	{ in_r int 64 regular {axi_slave 0}  }
	{ wt int 64 regular {axi_slave 0}  }
	{ bias int 64 regular {axi_slave 0}  }
	{ M int 64 regular {axi_slave 0}  }
	{ F int 32 regular {axi_slave 0}  }
	{ out_r int 64 regular {axi_slave 0}  }
}
set hasAXIMCache 0
set hasAXIML2Cache 0
set AXIMCacheInstDict [dict create]
set C_modelArgMapList {[ 
	{ "Name" : "gmem", "interface" : "axi_master", "bitwidth" : 32, "direction" : "READWRITE", "bitSlice":[ {"cElement": [{"cName": "in_r","offset": { "type": "dynamic","port_name": "in_r","bundle": "ctrl"},"direction": "READONLY"},{"cName": "wt","offset": { "type": "dynamic","port_name": "wt","bundle": "ctrl"},"direction": "READONLY"},{"cName": "bias","offset": { "type": "dynamic","port_name": "bias","bundle": "ctrl"},"direction": "READONLY"},{"cName": "M","offset": { "type": "dynamic","port_name": "M","bundle": "ctrl"},"direction": "READONLY"},{"cName": "out_r","offset": { "type": "dynamic","port_name": "out_r","bundle": "ctrl"},"direction": "WRITEONLY"}]}]} , 
 	{ "Name" : "in_r", "interface" : "axi_slave", "bundle":"ctrl","type":"ap_none","bitwidth" : 64, "direction" : "READONLY", "offset" : {"in":16}, "offset_end" : {"in":27}} , 
 	{ "Name" : "wt", "interface" : "axi_slave", "bundle":"ctrl","type":"ap_none","bitwidth" : 64, "direction" : "READONLY", "offset" : {"in":28}, "offset_end" : {"in":39}} , 
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
	{ m_axi_gmem_WDATA sc_out sc_lv 32 signal 0 } 
	{ m_axi_gmem_WSTRB sc_out sc_lv 4 signal 0 } 
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
	{ m_axi_gmem_RDATA sc_in sc_lv 32 signal 0 } 
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
	{ "name": "s_axi_ctrl_AWADDR", "direction": "in", "datatype": "sc_lv", "bitwidth":7, "type": "signal", "bundle":{"name": "ctrl", "role": "AWADDR" },"address":[{"name":"kp_hls_pw3_v3","role":"start","value":"0","valid_bit":"0"},{"name":"kp_hls_pw3_v3","role":"continue","value":"0","valid_bit":"4"},{"name":"kp_hls_pw3_v3","role":"auto_start","value":"0","valid_bit":"7"},{"name":"in_r","role":"data","value":"16"},{"name":"wt","role":"data","value":"28"},{"name":"bias","role":"data","value":"40"},{"name":"M","role":"data","value":"52"},{"name":"F","role":"data","value":"64"},{"name":"out_r","role":"data","value":"72"}] },
	{ "name": "s_axi_ctrl_AWVALID", "direction": "in", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "ctrl", "role": "AWVALID" } },
	{ "name": "s_axi_ctrl_AWREADY", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "ctrl", "role": "AWREADY" } },
	{ "name": "s_axi_ctrl_WVALID", "direction": "in", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "ctrl", "role": "WVALID" } },
	{ "name": "s_axi_ctrl_WREADY", "direction": "out", "datatype": "sc_logic", "bitwidth":1, "type": "signal", "bundle":{"name": "ctrl", "role": "WREADY" } },
	{ "name": "s_axi_ctrl_WDATA", "direction": "in", "datatype": "sc_lv", "bitwidth":32, "type": "signal", "bundle":{"name": "ctrl", "role": "WDATA" } },
	{ "name": "s_axi_ctrl_WSTRB", "direction": "in", "datatype": "sc_lv", "bitwidth":4, "type": "signal", "bundle":{"name": "ctrl", "role": "WSTRB" } },
	{ "name": "s_axi_ctrl_ARADDR", "direction": "in", "datatype": "sc_lv", "bitwidth":7, "type": "signal", "bundle":{"name": "ctrl", "role": "ARADDR" },"address":[{"name":"kp_hls_pw3_v3","role":"start","value":"0","valid_bit":"0"},{"name":"kp_hls_pw3_v3","role":"done","value":"0","valid_bit":"1"},{"name":"kp_hls_pw3_v3","role":"idle","value":"0","valid_bit":"2"},{"name":"kp_hls_pw3_v3","role":"ready","value":"0","valid_bit":"3"},{"name":"kp_hls_pw3_v3","role":"auto_start","value":"0","valid_bit":"7"}] },
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
 	{ "name": "m_axi_gmem_WDATA", "direction": "out", "datatype": "sc_lv", "bitwidth":32, "type": "signal", "bundle":{"name": "gmem", "role": "WDATA" }} , 
 	{ "name": "m_axi_gmem_WSTRB", "direction": "out", "datatype": "sc_lv", "bitwidth":4, "type": "signal", "bundle":{"name": "gmem", "role": "WSTRB" }} , 
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
 	{ "name": "m_axi_gmem_RDATA", "direction": "in", "datatype": "sc_lv", "bitwidth":32, "type": "signal", "bundle":{"name": "gmem", "role": "RDATA" }} , 
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
	{"ID" : "0", "Level" : "0", "Path" : "`AUTOTB_DUT_INST", "Parent" : "", "Child" : ["1", "57", "58"],
		"CDFG" : "kp_hls_pw3_v3",
		"Protocol" : "ap_ctrl_hs",
		"ControlExist" : "1", "ap_start" : "1", "ap_ready" : "1", "ap_done" : "1", "ap_continue" : "0", "ap_idle" : "1", "real_start" : "0",
		"Pipeline" : "None", "UnalignedPipeline" : "0", "RewindPipeline" : "0", "ProcessNetwork" : "0",
		"II" : "0",
		"VariableLatency" : "1", "ExactLatency" : "-1", "EstimateLatencyMin" : "80932", "EstimateLatencyMax" : "80932",
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
					{"ID" : "1", "SubInstance" : "grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102", "Port" : "gmem", "Inst_start_state" : "1", "Inst_end_state" : "2"}]},
			{"Name" : "in_r", "Type" : "None", "Direction" : "I"},
			{"Name" : "wt", "Type" : "None", "Direction" : "I"},
			{"Name" : "bias", "Type" : "None", "Direction" : "I"},
			{"Name" : "M", "Type" : "None", "Direction" : "I"},
			{"Name" : "F", "Type" : "None", "Direction" : "I"},
			{"Name" : "out_r", "Type" : "None", "Direction" : "I"}]},
	{"ID" : "1", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102", "Parent" : "0", "Child" : ["2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "36", "38", "56"],
		"CDFG" : "kp_hls_pw_core_v3_6_6_48_64_16_s",
		"Protocol" : "ap_ctrl_hs",
		"ControlExist" : "1", "ap_start" : "1", "ap_ready" : "1", "ap_done" : "1", "ap_continue" : "0", "ap_idle" : "1", "real_start" : "0",
		"Pipeline" : "None", "UnalignedPipeline" : "0", "RewindPipeline" : "0", "ProcessNetwork" : "0",
		"II" : "0",
		"VariableLatency" : "1", "ExactLatency" : "-1", "EstimateLatencyMin" : "80931", "EstimateLatencyMax" : "80931",
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
					{"Name" : "gmem_blk_n_R", "Type" : "RtlSignal"},
					{"Name" : "gmem_blk_n_AW", "Type" : "RtlSignal"},
					{"Name" : "gmem_blk_n_W", "Type" : "RtlSignal"},
					{"Name" : "gmem_blk_n_B", "Type" : "RtlSignal"}],
				"SubConnect" : [
					{"ID" : "34", "SubInstance" : "grp_kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_1_fu_345", "Port" : "gmem", "Inst_start_state" : "1", "Inst_end_state" : "2"},
					{"ID" : "36", "SubInstance" : "grp_kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_2_fu_385", "Port" : "gmem", "Inst_start_state" : "3", "Inst_end_state" : "4"}]},
			{"Name" : "in_r", "Type" : "None", "Direction" : "I"},
			{"Name" : "wt", "Type" : "None", "Direction" : "I"},
			{"Name" : "bias", "Type" : "None", "Direction" : "I"},
			{"Name" : "M", "Type" : "None", "Direction" : "I"},
			{"Name" : "F", "Type" : "None", "Direction" : "I"},
			{"Name" : "out_r", "Type" : "None", "Direction" : "I"}],
		"Loop" : [
			{"Name" : "VITIS_LOOP_244_2", "PipelineType" : "no",
				"LoopDec" : {"FSMBitwidth" : "29", "FirstState" : "ap_ST_fsm_state6", "LastState" : ["ap_ST_fsm_state29"], "QuitState" : ["ap_ST_fsm_state6"], "PreState" : ["ap_ST_fsm_state5"], "PostState" : ["ap_ST_fsm_state5"], "OneDepthLoop" : "0", "OneStateBlock": ""}},
			{"Name" : "VITIS_LOOP_243_1", "PipelineType" : "no",
				"LoopDec" : {"FSMBitwidth" : "29", "FirstState" : "ap_ST_fsm_state5", "LastState" : ["ap_ST_fsm_state6"], "QuitState" : ["ap_ST_fsm_state5"], "PreState" : ["ap_ST_fsm_state4"], "PostState" : ["ap_ST_fsm_state1"], "OneDepthLoop" : "0", "OneStateBlock": ""}}]},
	{"ID" : "2", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lin_U", "Parent" : "1"},
	{"ID" : "3", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lin_1_U", "Parent" : "1"},
	{"ID" : "4", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lin_2_U", "Parent" : "1"},
	{"ID" : "5", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lin_3_U", "Parent" : "1"},
	{"ID" : "6", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lin_4_U", "Parent" : "1"},
	{"ID" : "7", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lin_5_U", "Parent" : "1"},
	{"ID" : "8", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lin_6_U", "Parent" : "1"},
	{"ID" : "9", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lin_7_U", "Parent" : "1"},
	{"ID" : "10", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lin_8_U", "Parent" : "1"},
	{"ID" : "11", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lin_9_U", "Parent" : "1"},
	{"ID" : "12", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lin_10_U", "Parent" : "1"},
	{"ID" : "13", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lin_11_U", "Parent" : "1"},
	{"ID" : "14", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lin_12_U", "Parent" : "1"},
	{"ID" : "15", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lin_13_U", "Parent" : "1"},
	{"ID" : "16", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lin_14_U", "Parent" : "1"},
	{"ID" : "17", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lin_15_U", "Parent" : "1"},
	{"ID" : "18", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lwt_U", "Parent" : "1"},
	{"ID" : "19", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lwt_1_U", "Parent" : "1"},
	{"ID" : "20", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lwt_2_U", "Parent" : "1"},
	{"ID" : "21", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lwt_3_U", "Parent" : "1"},
	{"ID" : "22", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lwt_4_U", "Parent" : "1"},
	{"ID" : "23", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lwt_5_U", "Parent" : "1"},
	{"ID" : "24", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lwt_6_U", "Parent" : "1"},
	{"ID" : "25", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lwt_7_U", "Parent" : "1"},
	{"ID" : "26", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lwt_8_U", "Parent" : "1"},
	{"ID" : "27", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lwt_9_U", "Parent" : "1"},
	{"ID" : "28", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lwt_10_U", "Parent" : "1"},
	{"ID" : "29", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lwt_11_U", "Parent" : "1"},
	{"ID" : "30", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lwt_12_U", "Parent" : "1"},
	{"ID" : "31", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lwt_13_U", "Parent" : "1"},
	{"ID" : "32", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lwt_14_U", "Parent" : "1"},
	{"ID" : "33", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.lwt_15_U", "Parent" : "1"},
	{"ID" : "34", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.grp_kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_1_fu_345", "Parent" : "1", "Child" : ["35"],
		"CDFG" : "kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_1",
		"Protocol" : "ap_ctrl_hs",
		"ControlExist" : "1", "ap_start" : "1", "ap_ready" : "1", "ap_done" : "1", "ap_continue" : "0", "ap_idle" : "1", "real_start" : "0",
		"Pipeline" : "None", "UnalignedPipeline" : "0", "RewindPipeline" : "0", "ProcessNetwork" : "0",
		"II" : "0",
		"VariableLatency" : "1", "ExactLatency" : "-1", "EstimateLatencyMin" : "1739", "EstimateLatencyMax" : "1739",
		"Combinational" : "0",
		"Datapath" : "0",
		"ClockEnable" : "0",
		"HasSubDataflow" : "0",
		"InDataflowNetwork" : "0",
		"HasNonBlockingOperation" : "0",
		"IsBlackBox" : "0",
		"Port" : [
			{"Name" : "lin_15", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "lin_14", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "lin_13", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "lin_12", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "lin_11", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "lin_10", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "lin_9", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "lin_8", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "lin_7", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "lin_6", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "lin_5", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "lin_4", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "lin_3", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "lin_2", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "lin_1", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "lin", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "in_r", "Type" : "None", "Direction" : "I"},
			{"Name" : "gmem", "Type" : "MAXI", "Direction" : "I",
				"BlockSignal" : [
					{"Name" : "gmem_blk_n_AR", "Type" : "RtlSignal"},
					{"Name" : "gmem_blk_n_R", "Type" : "RtlSignal"}]}],
		"Loop" : [
			{"Name" : "Loop 1", "PipelineType" : "UPC",
				"LoopDec" : {"FSMBitwidth" : "1", "FirstState" : "ap_ST_fsm_pp0_stage0", "FirstStateIter" : "ap_enable_reg_pp0_iter0", "FirstStateBlock" : "ap_block_pp0_stage0_subdone", "LastState" : "ap_ST_fsm_pp0_stage0", "LastStateIter" : "ap_enable_reg_pp0_iter10", "LastStateBlock" : "ap_block_pp0_stage0_subdone", "QuitState" : "ap_ST_fsm_pp0_stage0", "QuitStateIter" : "ap_enable_reg_pp0_iter10", "QuitStateBlock" : "ap_block_pp0_stage0_subdone", "OneDepthLoop" : "0", "has_ap_ctrl" : "1", "has_continue" : "0"}}]},
	{"ID" : "35", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.grp_kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_1_fu_345.flow_control_loop_pipe_sequential_init_U", "Parent" : "34"},
	{"ID" : "36", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.grp_kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_2_fu_385", "Parent" : "1", "Child" : ["37"],
		"CDFG" : "kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_2",
		"Protocol" : "ap_ctrl_hs",
		"ControlExist" : "1", "ap_start" : "1", "ap_ready" : "1", "ap_done" : "1", "ap_continue" : "0", "ap_idle" : "1", "real_start" : "0",
		"Pipeline" : "None", "UnalignedPipeline" : "0", "RewindPipeline" : "0", "ProcessNetwork" : "0",
		"II" : "0",
		"VariableLatency" : "1", "ExactLatency" : "-1", "EstimateLatencyMin" : "3084", "EstimateLatencyMax" : "3084",
		"Combinational" : "0",
		"Datapath" : "0",
		"ClockEnable" : "0",
		"HasSubDataflow" : "0",
		"InDataflowNetwork" : "0",
		"HasNonBlockingOperation" : "0",
		"IsBlackBox" : "0",
		"Port" : [
			{"Name" : "lwt_15", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "lwt_14", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "lwt_13", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "lwt_12", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "lwt_11", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "lwt_10", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "lwt_9", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "lwt_8", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "lwt_7", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "lwt_6", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "lwt_5", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "lwt_4", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "lwt_3", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "lwt_2", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "lwt_1", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "lwt", "Type" : "Memory", "Direction" : "O"},
			{"Name" : "wt", "Type" : "None", "Direction" : "I"},
			{"Name" : "gmem", "Type" : "MAXI", "Direction" : "I",
				"BlockSignal" : [
					{"Name" : "gmem_blk_n_AR", "Type" : "RtlSignal"},
					{"Name" : "gmem_blk_n_R", "Type" : "RtlSignal"}]}],
		"Loop" : [
			{"Name" : "Loop 1", "PipelineType" : "UPC",
				"LoopDec" : {"FSMBitwidth" : "1", "FirstState" : "ap_ST_fsm_pp0_stage0", "FirstStateIter" : "ap_enable_reg_pp0_iter0", "FirstStateBlock" : "ap_block_pp0_stage0_subdone", "LastState" : "ap_ST_fsm_pp0_stage0", "LastStateIter" : "ap_enable_reg_pp0_iter11", "LastStateBlock" : "ap_block_pp0_stage0_subdone", "QuitState" : "ap_ST_fsm_pp0_stage0", "QuitStateIter" : "ap_enable_reg_pp0_iter11", "QuitStateBlock" : "ap_block_pp0_stage0_subdone", "OneDepthLoop" : "0", "has_ap_ctrl" : "1", "has_continue" : "0"}}]},
	{"ID" : "37", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.grp_kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_2_fu_385.flow_control_loop_pipe_sequential_init_U", "Parent" : "36"},
	{"ID" : "38", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.grp_kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_VITIS_LOOP_246_3_fu_409", "Parent" : "1", "Child" : ["39", "40", "41", "42", "43", "44", "45", "46", "47", "48", "49", "50", "51", "52", "53", "54", "55"],
		"CDFG" : "kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_VITIS_LOOP_246_3",
		"Protocol" : "ap_ctrl_hs",
		"ControlExist" : "1", "ap_start" : "1", "ap_ready" : "1", "ap_done" : "1", "ap_continue" : "0", "ap_idle" : "1", "real_start" : "0",
		"Pipeline" : "None", "UnalignedPipeline" : "0", "RewindPipeline" : "0", "ProcessNetwork" : "0",
		"II" : "0",
		"VariableLatency" : "1", "ExactLatency" : "-1", "EstimateLatencyMin" : "9", "EstimateLatencyMax" : "9",
		"Combinational" : "0",
		"Datapath" : "0",
		"ClockEnable" : "0",
		"HasSubDataflow" : "0",
		"InDataflowNetwork" : "0",
		"HasNonBlockingOperation" : "0",
		"IsBlackBox" : "0",
		"Port" : [
			{"Name" : "acc", "Type" : "None", "Direction" : "I"},
			{"Name" : "mul_ln244", "Type" : "None", "Direction" : "I"},
			{"Name" : "mul_ln246", "Type" : "None", "Direction" : "I"},
			{"Name" : "lin", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lwt", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lin_1", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lwt_1", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lin_2", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lwt_2", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lin_3", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lwt_3", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lin_4", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lwt_4", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lin_5", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lwt_5", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lin_6", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lwt_6", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lin_7", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lwt_7", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lin_8", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lwt_8", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lin_9", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lwt_9", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lin_10", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lwt_10", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lin_11", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lwt_11", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lin_12", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lwt_12", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lin_13", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lwt_13", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lin_14", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lwt_14", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lin_15", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "lwt_15", "Type" : "Memory", "Direction" : "I"},
			{"Name" : "acc_1_out", "Type" : "Vld", "Direction" : "O"}],
		"Loop" : [
			{"Name" : "VITIS_LOOP_246_3", "PipelineType" : "UPC",
				"LoopDec" : {"FSMBitwidth" : "1", "FirstState" : "ap_ST_fsm_pp0_stage0", "FirstStateIter" : "ap_enable_reg_pp0_iter0", "FirstStateBlock" : "ap_block_pp0_stage0_subdone", "LastState" : "ap_ST_fsm_pp0_stage0", "LastStateIter" : "ap_enable_reg_pp0_iter5", "LastStateBlock" : "ap_block_pp0_stage0_subdone", "QuitState" : "ap_ST_fsm_pp0_stage0", "QuitStateIter" : "ap_enable_reg_pp0_iter5", "QuitStateBlock" : "ap_block_pp0_stage0_subdone", "OneDepthLoop" : "0", "has_ap_ctrl" : "1", "has_continue" : "0"}}]},
	{"ID" : "39", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.grp_kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_VITIS_LOOP_246_3_fu_409.mul_8s_8ns_16_1_1_U37", "Parent" : "38"},
	{"ID" : "40", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.grp_kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_VITIS_LOOP_246_3_fu_409.mul_8s_8ns_16_1_1_U38", "Parent" : "38"},
	{"ID" : "41", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.grp_kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_VITIS_LOOP_246_3_fu_409.mul_8s_8ns_16_1_1_U39", "Parent" : "38"},
	{"ID" : "42", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.grp_kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_VITIS_LOOP_246_3_fu_409.mul_8s_8ns_16_1_1_U40", "Parent" : "38"},
	{"ID" : "43", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.grp_kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_VITIS_LOOP_246_3_fu_409.mul_8s_8ns_16_1_1_U41", "Parent" : "38"},
	{"ID" : "44", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.grp_kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_VITIS_LOOP_246_3_fu_409.mul_8s_8ns_16_1_1_U42", "Parent" : "38"},
	{"ID" : "45", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.grp_kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_VITIS_LOOP_246_3_fu_409.mul_8s_8ns_16_1_1_U43", "Parent" : "38"},
	{"ID" : "46", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.grp_kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_VITIS_LOOP_246_3_fu_409.mul_8s_8ns_16_1_1_U44", "Parent" : "38"},
	{"ID" : "47", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.grp_kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_VITIS_LOOP_246_3_fu_409.mac_muladd_8s_8ns_16s_17_4_1_U45", "Parent" : "38"},
	{"ID" : "48", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.grp_kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_VITIS_LOOP_246_3_fu_409.mac_muladd_8s_8ns_16s_17_4_1_U46", "Parent" : "38"},
	{"ID" : "49", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.grp_kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_VITIS_LOOP_246_3_fu_409.mac_muladd_8s_8ns_16s_17_4_1_U47", "Parent" : "38"},
	{"ID" : "50", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.grp_kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_VITIS_LOOP_246_3_fu_409.mac_muladd_8s_8ns_16s_17_4_1_U48", "Parent" : "38"},
	{"ID" : "51", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.grp_kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_VITIS_LOOP_246_3_fu_409.mac_muladd_8s_8ns_16s_17_4_1_U49", "Parent" : "38"},
	{"ID" : "52", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.grp_kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_VITIS_LOOP_246_3_fu_409.mac_muladd_8s_8ns_16s_17_4_1_U50", "Parent" : "38"},
	{"ID" : "53", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.grp_kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_VITIS_LOOP_246_3_fu_409.mac_muladd_8s_8ns_16s_17_4_1_U51", "Parent" : "38"},
	{"ID" : "54", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.grp_kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_VITIS_LOOP_246_3_fu_409.mac_muladd_8s_8ns_16s_17_4_1_U52", "Parent" : "38"},
	{"ID" : "55", "Level" : "3", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.grp_kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_VITIS_LOOP_246_3_fu_409.flow_control_loop_pipe_sequential_init_U", "Parent" : "38"},
	{"ID" : "56", "Level" : "2", "Path" : "`AUTOTB_DUT_INST.grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102.mul_32s_32s_64_2_1_U91", "Parent" : "1"},
	{"ID" : "57", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.ctrl_s_axi_U", "Parent" : "0"},
	{"ID" : "58", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.gmem_m_axi_U", "Parent" : "0"}]}


set ArgLastReadFirstWriteLatency {
	kp_hls_pw3_v3 {
		gmem {Type IO LastRead 24 FirstWrite -1}
		in_r {Type I LastRead 0 FirstWrite -1}
		wt {Type I LastRead 0 FirstWrite -1}
		bias {Type I LastRead 0 FirstWrite -1}
		M {Type I LastRead 0 FirstWrite -1}
		F {Type I LastRead 0 FirstWrite -1}
		out_r {Type I LastRead 0 FirstWrite -1}}
	kp_hls_pw_core_v3_6_6_48_64_16_s {
		gmem {Type IO LastRead 24 FirstWrite -1}
		in_r {Type I LastRead 0 FirstWrite -1}
		wt {Type I LastRead 2 FirstWrite -1}
		bias {Type I LastRead 3 FirstWrite -1}
		M {Type I LastRead 3 FirstWrite -1}
		F {Type I LastRead 2 FirstWrite -1}
		out_r {Type I LastRead 3 FirstWrite -1}}
	kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_1 {
		lin_15 {Type O LastRead -1 FirstWrite 10}
		lin_14 {Type O LastRead -1 FirstWrite 10}
		lin_13 {Type O LastRead -1 FirstWrite 10}
		lin_12 {Type O LastRead -1 FirstWrite 10}
		lin_11 {Type O LastRead -1 FirstWrite 10}
		lin_10 {Type O LastRead -1 FirstWrite 10}
		lin_9 {Type O LastRead -1 FirstWrite 10}
		lin_8 {Type O LastRead -1 FirstWrite 10}
		lin_7 {Type O LastRead -1 FirstWrite 10}
		lin_6 {Type O LastRead -1 FirstWrite 10}
		lin_5 {Type O LastRead -1 FirstWrite 10}
		lin_4 {Type O LastRead -1 FirstWrite 10}
		lin_3 {Type O LastRead -1 FirstWrite 10}
		lin_2 {Type O LastRead -1 FirstWrite 10}
		lin_1 {Type O LastRead -1 FirstWrite 10}
		lin {Type O LastRead -1 FirstWrite 10}
		in_r {Type I LastRead 0 FirstWrite -1}
		gmem {Type I LastRead 9 FirstWrite -1}}
	kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_2 {
		lwt_15 {Type O LastRead -1 FirstWrite 11}
		lwt_14 {Type O LastRead -1 FirstWrite 11}
		lwt_13 {Type O LastRead -1 FirstWrite 11}
		lwt_12 {Type O LastRead -1 FirstWrite 11}
		lwt_11 {Type O LastRead -1 FirstWrite 11}
		lwt_10 {Type O LastRead -1 FirstWrite 11}
		lwt_9 {Type O LastRead -1 FirstWrite 11}
		lwt_8 {Type O LastRead -1 FirstWrite 11}
		lwt_7 {Type O LastRead -1 FirstWrite 11}
		lwt_6 {Type O LastRead -1 FirstWrite 11}
		lwt_5 {Type O LastRead -1 FirstWrite 11}
		lwt_4 {Type O LastRead -1 FirstWrite 11}
		lwt_3 {Type O LastRead -1 FirstWrite 11}
		lwt_2 {Type O LastRead -1 FirstWrite 11}
		lwt_1 {Type O LastRead -1 FirstWrite 11}
		lwt {Type O LastRead -1 FirstWrite 11}
		wt {Type I LastRead 0 FirstWrite -1}
		gmem {Type I LastRead 9 FirstWrite -1}}
	kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_VITIS_LOOP_246_3 {
		acc {Type I LastRead 0 FirstWrite -1}
		mul_ln244 {Type I LastRead 0 FirstWrite -1}
		mul_ln246 {Type I LastRead 0 FirstWrite -1}
		lin {Type I LastRead 1 FirstWrite -1}
		lwt {Type I LastRead 1 FirstWrite -1}
		lin_1 {Type I LastRead 0 FirstWrite -1}
		lwt_1 {Type I LastRead 0 FirstWrite -1}
		lin_2 {Type I LastRead 1 FirstWrite -1}
		lwt_2 {Type I LastRead 1 FirstWrite -1}
		lin_3 {Type I LastRead 0 FirstWrite -1}
		lwt_3 {Type I LastRead 0 FirstWrite -1}
		lin_4 {Type I LastRead 1 FirstWrite -1}
		lwt_4 {Type I LastRead 1 FirstWrite -1}
		lin_5 {Type I LastRead 0 FirstWrite -1}
		lwt_5 {Type I LastRead 0 FirstWrite -1}
		lin_6 {Type I LastRead 1 FirstWrite -1}
		lwt_6 {Type I LastRead 1 FirstWrite -1}
		lin_7 {Type I LastRead 0 FirstWrite -1}
		lwt_7 {Type I LastRead 0 FirstWrite -1}
		lin_8 {Type I LastRead 1 FirstWrite -1}
		lwt_8 {Type I LastRead 1 FirstWrite -1}
		lin_9 {Type I LastRead 0 FirstWrite -1}
		lwt_9 {Type I LastRead 0 FirstWrite -1}
		lin_10 {Type I LastRead 1 FirstWrite -1}
		lwt_10 {Type I LastRead 1 FirstWrite -1}
		lin_11 {Type I LastRead 0 FirstWrite -1}
		lwt_11 {Type I LastRead 0 FirstWrite -1}
		lin_12 {Type I LastRead 1 FirstWrite -1}
		lwt_12 {Type I LastRead 1 FirstWrite -1}
		lin_13 {Type I LastRead 0 FirstWrite -1}
		lwt_13 {Type I LastRead 0 FirstWrite -1}
		lin_14 {Type I LastRead 1 FirstWrite -1}
		lwt_14 {Type I LastRead 1 FirstWrite -1}
		lin_15 {Type I LastRead 0 FirstWrite -1}
		lwt_15 {Type I LastRead 0 FirstWrite -1}
		acc_1_out {Type O LastRead -1 FirstWrite 4}}}

set hasDtUnsupportedChannel 0

set PerformanceInfo {[
	{"Name" : "Latency", "Min" : "80932", "Max" : "80932"}
	, {"Name" : "Interval", "Min" : "80933", "Max" : "80933"}
]}

set PipelineEnableSignalInfo {[
]}

set Spec2ImplPortList { 
	gmem { m_axi {  { m_axi_gmem_AWVALID VALID 1 1 }  { m_axi_gmem_AWREADY READY 0 1 }  { m_axi_gmem_AWADDR ADDR 1 64 }  { m_axi_gmem_AWID ID 1 1 }  { m_axi_gmem_AWLEN SIZE 1 8 }  { m_axi_gmem_AWSIZE BURST 1 3 }  { m_axi_gmem_AWBURST LOCK 1 2 }  { m_axi_gmem_AWLOCK CACHE 1 2 }  { m_axi_gmem_AWCACHE PROT 1 4 }  { m_axi_gmem_AWPROT QOS 1 3 }  { m_axi_gmem_AWQOS REGION 1 4 }  { m_axi_gmem_AWREGION USER 1 4 }  { m_axi_gmem_AWUSER DATA 1 1 }  { m_axi_gmem_WVALID VALID 1 1 }  { m_axi_gmem_WREADY READY 0 1 }  { m_axi_gmem_WDATA FIFONUM 1 32 }  { m_axi_gmem_WSTRB STRB 1 4 }  { m_axi_gmem_WLAST LAST 1 1 }  { m_axi_gmem_WID ID 1 1 }  { m_axi_gmem_WUSER DATA 1 1 }  { m_axi_gmem_ARVALID VALID 1 1 }  { m_axi_gmem_ARREADY READY 0 1 }  { m_axi_gmem_ARADDR ADDR 1 64 }  { m_axi_gmem_ARID ID 1 1 }  { m_axi_gmem_ARLEN SIZE 1 8 }  { m_axi_gmem_ARSIZE BURST 1 3 }  { m_axi_gmem_ARBURST LOCK 1 2 }  { m_axi_gmem_ARLOCK CACHE 1 2 }  { m_axi_gmem_ARCACHE PROT 1 4 }  { m_axi_gmem_ARPROT QOS 1 3 }  { m_axi_gmem_ARQOS REGION 1 4 }  { m_axi_gmem_ARREGION USER 1 4 }  { m_axi_gmem_ARUSER DATA 1 1 }  { m_axi_gmem_RVALID VALID 0 1 }  { m_axi_gmem_RREADY READY 1 1 }  { m_axi_gmem_RDATA FIFONUM 0 32 }  { m_axi_gmem_RLAST LAST 0 1 }  { m_axi_gmem_RID ID 0 1 }  { m_axi_gmem_RUSER DATA 0 1 }  { m_axi_gmem_RRESP RESP 0 2 }  { m_axi_gmem_BVALID VALID 0 1 }  { m_axi_gmem_BREADY READY 1 1 }  { m_axi_gmem_BRESP RESP 0 2 }  { m_axi_gmem_BID ID 0 1 }  { m_axi_gmem_BUSER DATA 0 1 } } }
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
