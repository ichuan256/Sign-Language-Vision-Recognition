set moduleName kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4
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
set C_modelName {kp_hls_pw_core<2, 6, 6, 48, 64>_Pipeline_VITIS_LOOP_84_4}
set C_modelType { void 0 }
set ap_memory_interface_dict [dict create]
set C_modelArgList {
	{ sext_ln81 int 61 regular  }
	{ gmem int 64 regular {axi_master 2}  }
	{ w int 64 regular  }
	{ p_cast209_cast int 8 regular  }
	{ p_cast277_cast int 8 regular  }
	{ p_cast293_cast int 8 regular  }
	{ p_cast247_cast int 8 regular  }
	{ p_cast221_cast int 8 regular  }
	{ p_cast255_cast int 8 regular  }
	{ p_cast231_cast int 8 regular  }
	{ p_cast233_cast int 8 regular  }
	{ p_cast271_cast int 8 regular  }
	{ p_cast229_cast int 8 regular  }
	{ p_cast205_cast int 8 regular  }
	{ p_cast253_cast int 8 regular  }
	{ p_cast283_cast int 8 regular  }
	{ p_cast287_cast int 8 regular  }
	{ p_cast235_cast int 8 regular  }
	{ p_cast241_cast int 8 regular  }
	{ p_cast227_cast int 8 regular  }
	{ p_cast245_cast int 8 regular  }
	{ p_cast211_cast int 8 regular  }
	{ p_cast215_cast int 8 regular  }
	{ p_cast279_cast int 8 regular  }
	{ p_cast291_cast int 8 regular  }
	{ p_cast273_cast int 8 regular  }
	{ p_cast251_cast int 8 regular  }
	{ p_cast217_cast int 8 regular  }
	{ p_cast225_cast int 8 regular  }
	{ p_cast237_cast int 8 regular  }
	{ zext_ln84 int 8 regular  }
	{ p_cast213_cast int 8 regular  }
	{ p_cast201_cast int 8 regular  }
	{ p_cast219_cast int 8 regular  }
	{ p_cast249_cast int 8 regular  }
	{ p_cast275_cast int 8 regular  }
	{ p_cast223_cast int 8 regular  }
	{ p_cast243_cast int 8 regular  }
	{ p_cast263_cast int 8 regular  }
	{ p_cast285_cast int 8 regular  }
	{ p_cast265_cast int 8 regular  }
	{ p_cast261_cast int 8 regular  }
	{ p_cast281_cast int 8 regular  }
	{ p_cast289_cast int 8 regular  }
	{ p_cast203_cast int 8 regular  }
	{ p_cast267_cast int 8 regular  }
	{ p_cast259_cast int 8 regular  }
	{ p_cast239_cast int 8 regular  }
	{ p_cast207_cast int 8 regular  }
	{ p_cast257_cast int 8 regular  }
	{ p_cast269_cast int 8 regular  }
	{ M int 64 regular  }
	{ sh_prom_i int 32 regular  }
	{ sub2_i int 64 regular  }
	{ half int 64 regular  }
	{ empty int 11 regular  }
	{ p_cast302 int 9 regular  }
	{ mul_ln82 int 12 regular  }
	{ out_r int 64 regular  }
}
set hasAXIMCache 0
set hasAXIML2Cache 0
set AXIMCacheInstDict [dict create]
set C_modelArgMapList {[ 
	{ "Name" : "sext_ln81", "interface" : "wire", "bitwidth" : 61, "direction" : "READONLY"} , 
 	{ "Name" : "gmem", "interface" : "axi_master", "bitwidth" : 64, "direction" : "READWRITE", "bitSlice":[ {"cElement": [{"cName": "in_r","offset": { "type": "dynamic","port_name": "in_r","bundle": "ctrl"},"direction": "READONLY"},{"cName": "w","offset": { "type": "dynamic","port_name": "w","bundle": "ctrl"},"direction": "READONLY"},{"cName": "bias","offset": { "type": "dynamic","port_name": "bias","bundle": "ctrl"},"direction": "READONLY"},{"cName": "M","offset": { "type": "dynamic","port_name": "M","bundle": "ctrl"},"direction": "READONLY"},{"cName": "out_r","offset": { "type": "dynamic","port_name": "out_r","bundle": "ctrl"},"direction": "WRITEONLY"}]}]} , 
 	{ "Name" : "w", "interface" : "wire", "bitwidth" : 64, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast209_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast277_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast293_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast247_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast221_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast255_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast231_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast233_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast271_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast229_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast205_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast253_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast283_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast287_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast235_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast241_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast227_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast245_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast211_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast215_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast279_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast291_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast273_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast251_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast217_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast225_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast237_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "zext_ln84", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast213_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast201_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast219_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast249_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast275_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast223_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast243_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast263_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast285_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast265_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast261_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast281_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast289_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast203_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast267_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast259_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast239_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast207_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast257_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast269_cast", "interface" : "wire", "bitwidth" : 8, "direction" : "READONLY"} , 
 	{ "Name" : "M", "interface" : "wire", "bitwidth" : 64, "direction" : "READONLY"} , 
 	{ "Name" : "sh_prom_i", "interface" : "wire", "bitwidth" : 32, "direction" : "READONLY"} , 
 	{ "Name" : "sub2_i", "interface" : "wire", "bitwidth" : 64, "direction" : "READONLY"} , 
 	{ "Name" : "half", "interface" : "wire", "bitwidth" : 64, "direction" : "READONLY"} , 
 	{ "Name" : "empty", "interface" : "wire", "bitwidth" : 11, "direction" : "READONLY"} , 
 	{ "Name" : "p_cast302", "interface" : "wire", "bitwidth" : 9, "direction" : "READONLY"} , 
 	{ "Name" : "mul_ln82", "interface" : "wire", "bitwidth" : 12, "direction" : "READONLY"} , 
 	{ "Name" : "out_r", "interface" : "wire", "bitwidth" : 64, "direction" : "READONLY"} ]}
# RTL Port declarations: 
set portNum 110
set portList { 
	{ ap_clk sc_in sc_logic 1 clock -1 } 
	{ ap_rst sc_in sc_logic 1 reset -1 active_high_sync } 
	{ ap_start sc_in sc_logic 1 start -1 } 
	{ ap_done sc_out sc_logic 1 predone -1 } 
	{ ap_idle sc_out sc_logic 1 done -1 } 
	{ ap_ready sc_out sc_logic 1 ready -1 } 
	{ m_axi_gmem_AWVALID sc_out sc_logic 1 signal 1 } 
	{ m_axi_gmem_AWREADY sc_in sc_logic 1 signal 1 } 
	{ m_axi_gmem_AWADDR sc_out sc_lv 64 signal 1 } 
	{ m_axi_gmem_AWID sc_out sc_lv 1 signal 1 } 
	{ m_axi_gmem_AWLEN sc_out sc_lv 32 signal 1 } 
	{ m_axi_gmem_AWSIZE sc_out sc_lv 3 signal 1 } 
	{ m_axi_gmem_AWBURST sc_out sc_lv 2 signal 1 } 
	{ m_axi_gmem_AWLOCK sc_out sc_lv 2 signal 1 } 
	{ m_axi_gmem_AWCACHE sc_out sc_lv 4 signal 1 } 
	{ m_axi_gmem_AWPROT sc_out sc_lv 3 signal 1 } 
	{ m_axi_gmem_AWQOS sc_out sc_lv 4 signal 1 } 
	{ m_axi_gmem_AWREGION sc_out sc_lv 4 signal 1 } 
	{ m_axi_gmem_AWUSER sc_out sc_lv 1 signal 1 } 
	{ m_axi_gmem_WVALID sc_out sc_logic 1 signal 1 } 
	{ m_axi_gmem_WREADY sc_in sc_logic 1 signal 1 } 
	{ m_axi_gmem_WDATA sc_out sc_lv 64 signal 1 } 
	{ m_axi_gmem_WSTRB sc_out sc_lv 8 signal 1 } 
	{ m_axi_gmem_WLAST sc_out sc_logic 1 signal 1 } 
	{ m_axi_gmem_WID sc_out sc_lv 1 signal 1 } 
	{ m_axi_gmem_WUSER sc_out sc_lv 1 signal 1 } 
	{ m_axi_gmem_ARVALID sc_out sc_logic 1 signal 1 } 
	{ m_axi_gmem_ARREADY sc_in sc_logic 1 signal 1 } 
	{ m_axi_gmem_ARADDR sc_out sc_lv 64 signal 1 } 
	{ m_axi_gmem_ARID sc_out sc_lv 1 signal 1 } 
	{ m_axi_gmem_ARLEN sc_out sc_lv 32 signal 1 } 
	{ m_axi_gmem_ARSIZE sc_out sc_lv 3 signal 1 } 
	{ m_axi_gmem_ARBURST sc_out sc_lv 2 signal 1 } 
	{ m_axi_gmem_ARLOCK sc_out sc_lv 2 signal 1 } 
	{ m_axi_gmem_ARCACHE sc_out sc_lv 4 signal 1 } 
	{ m_axi_gmem_ARPROT sc_out sc_lv 3 signal 1 } 
	{ m_axi_gmem_ARQOS sc_out sc_lv 4 signal 1 } 
	{ m_axi_gmem_ARREGION sc_out sc_lv 4 signal 1 } 
	{ m_axi_gmem_ARUSER sc_out sc_lv 1 signal 1 } 
	{ m_axi_gmem_RVALID sc_in sc_logic 1 signal 1 } 
	{ m_axi_gmem_RREADY sc_out sc_logic 1 signal 1 } 
	{ m_axi_gmem_RDATA sc_in sc_lv 64 signal 1 } 
	{ m_axi_gmem_RLAST sc_in sc_logic 1 signal 1 } 
	{ m_axi_gmem_RID sc_in sc_lv 1 signal 1 } 
	{ m_axi_gmem_RFIFONUM sc_in sc_lv 9 signal 1 } 
	{ m_axi_gmem_RUSER sc_in sc_lv 1 signal 1 } 
	{ m_axi_gmem_RRESP sc_in sc_lv 2 signal 1 } 
	{ m_axi_gmem_BVALID sc_in sc_logic 1 signal 1 } 
	{ m_axi_gmem_BREADY sc_out sc_logic 1 signal 1 } 
	{ m_axi_gmem_BRESP sc_in sc_lv 2 signal 1 } 
	{ m_axi_gmem_BID sc_in sc_lv 1 signal 1 } 
	{ m_axi_gmem_BUSER sc_in sc_lv 1 signal 1 } 
	{ sext_ln81 sc_in sc_lv 61 signal 0 } 
	{ w sc_in sc_lv 64 signal 2 } 
	{ p_cast209_cast sc_in sc_lv 8 signal 3 } 
	{ p_cast277_cast sc_in sc_lv 8 signal 4 } 
	{ p_cast293_cast sc_in sc_lv 8 signal 5 } 
	{ p_cast247_cast sc_in sc_lv 8 signal 6 } 
	{ p_cast221_cast sc_in sc_lv 8 signal 7 } 
	{ p_cast255_cast sc_in sc_lv 8 signal 8 } 
	{ p_cast231_cast sc_in sc_lv 8 signal 9 } 
	{ p_cast233_cast sc_in sc_lv 8 signal 10 } 
	{ p_cast271_cast sc_in sc_lv 8 signal 11 } 
	{ p_cast229_cast sc_in sc_lv 8 signal 12 } 
	{ p_cast205_cast sc_in sc_lv 8 signal 13 } 
	{ p_cast253_cast sc_in sc_lv 8 signal 14 } 
	{ p_cast283_cast sc_in sc_lv 8 signal 15 } 
	{ p_cast287_cast sc_in sc_lv 8 signal 16 } 
	{ p_cast235_cast sc_in sc_lv 8 signal 17 } 
	{ p_cast241_cast sc_in sc_lv 8 signal 18 } 
	{ p_cast227_cast sc_in sc_lv 8 signal 19 } 
	{ p_cast245_cast sc_in sc_lv 8 signal 20 } 
	{ p_cast211_cast sc_in sc_lv 8 signal 21 } 
	{ p_cast215_cast sc_in sc_lv 8 signal 22 } 
	{ p_cast279_cast sc_in sc_lv 8 signal 23 } 
	{ p_cast291_cast sc_in sc_lv 8 signal 24 } 
	{ p_cast273_cast sc_in sc_lv 8 signal 25 } 
	{ p_cast251_cast sc_in sc_lv 8 signal 26 } 
	{ p_cast217_cast sc_in sc_lv 8 signal 27 } 
	{ p_cast225_cast sc_in sc_lv 8 signal 28 } 
	{ p_cast237_cast sc_in sc_lv 8 signal 29 } 
	{ zext_ln84 sc_in sc_lv 8 signal 30 } 
	{ p_cast213_cast sc_in sc_lv 8 signal 31 } 
	{ p_cast201_cast sc_in sc_lv 8 signal 32 } 
	{ p_cast219_cast sc_in sc_lv 8 signal 33 } 
	{ p_cast249_cast sc_in sc_lv 8 signal 34 } 
	{ p_cast275_cast sc_in sc_lv 8 signal 35 } 
	{ p_cast223_cast sc_in sc_lv 8 signal 36 } 
	{ p_cast243_cast sc_in sc_lv 8 signal 37 } 
	{ p_cast263_cast sc_in sc_lv 8 signal 38 } 
	{ p_cast285_cast sc_in sc_lv 8 signal 39 } 
	{ p_cast265_cast sc_in sc_lv 8 signal 40 } 
	{ p_cast261_cast sc_in sc_lv 8 signal 41 } 
	{ p_cast281_cast sc_in sc_lv 8 signal 42 } 
	{ p_cast289_cast sc_in sc_lv 8 signal 43 } 
	{ p_cast203_cast sc_in sc_lv 8 signal 44 } 
	{ p_cast267_cast sc_in sc_lv 8 signal 45 } 
	{ p_cast259_cast sc_in sc_lv 8 signal 46 } 
	{ p_cast239_cast sc_in sc_lv 8 signal 47 } 
	{ p_cast207_cast sc_in sc_lv 8 signal 48 } 
	{ p_cast257_cast sc_in sc_lv 8 signal 49 } 
	{ p_cast269_cast sc_in sc_lv 8 signal 50 } 
	{ M sc_in sc_lv 64 signal 51 } 
	{ sh_prom_i sc_in sc_lv 32 signal 52 } 
	{ sub2_i sc_in sc_lv 64 signal 53 } 
	{ half sc_in sc_lv 64 signal 54 } 
	{ empty sc_in sc_lv 11 signal 55 } 
	{ p_cast302 sc_in sc_lv 9 signal 56 } 
	{ mul_ln82 sc_in sc_lv 12 signal 57 } 
	{ out_r sc_in sc_lv 64 signal 58 } 
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
 	{ "name": "sext_ln81", "direction": "in", "datatype": "sc_lv", "bitwidth":61, "type": "signal", "bundle":{"name": "sext_ln81", "role": "default" }} , 
 	{ "name": "w", "direction": "in", "datatype": "sc_lv", "bitwidth":64, "type": "signal", "bundle":{"name": "w", "role": "default" }} , 
 	{ "name": "p_cast209_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast209_cast", "role": "default" }} , 
 	{ "name": "p_cast277_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast277_cast", "role": "default" }} , 
 	{ "name": "p_cast293_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast293_cast", "role": "default" }} , 
 	{ "name": "p_cast247_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast247_cast", "role": "default" }} , 
 	{ "name": "p_cast221_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast221_cast", "role": "default" }} , 
 	{ "name": "p_cast255_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast255_cast", "role": "default" }} , 
 	{ "name": "p_cast231_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast231_cast", "role": "default" }} , 
 	{ "name": "p_cast233_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast233_cast", "role": "default" }} , 
 	{ "name": "p_cast271_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast271_cast", "role": "default" }} , 
 	{ "name": "p_cast229_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast229_cast", "role": "default" }} , 
 	{ "name": "p_cast205_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast205_cast", "role": "default" }} , 
 	{ "name": "p_cast253_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast253_cast", "role": "default" }} , 
 	{ "name": "p_cast283_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast283_cast", "role": "default" }} , 
 	{ "name": "p_cast287_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast287_cast", "role": "default" }} , 
 	{ "name": "p_cast235_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast235_cast", "role": "default" }} , 
 	{ "name": "p_cast241_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast241_cast", "role": "default" }} , 
 	{ "name": "p_cast227_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast227_cast", "role": "default" }} , 
 	{ "name": "p_cast245_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast245_cast", "role": "default" }} , 
 	{ "name": "p_cast211_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast211_cast", "role": "default" }} , 
 	{ "name": "p_cast215_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast215_cast", "role": "default" }} , 
 	{ "name": "p_cast279_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast279_cast", "role": "default" }} , 
 	{ "name": "p_cast291_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast291_cast", "role": "default" }} , 
 	{ "name": "p_cast273_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast273_cast", "role": "default" }} , 
 	{ "name": "p_cast251_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast251_cast", "role": "default" }} , 
 	{ "name": "p_cast217_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast217_cast", "role": "default" }} , 
 	{ "name": "p_cast225_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast225_cast", "role": "default" }} , 
 	{ "name": "p_cast237_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast237_cast", "role": "default" }} , 
 	{ "name": "zext_ln84", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "zext_ln84", "role": "default" }} , 
 	{ "name": "p_cast213_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast213_cast", "role": "default" }} , 
 	{ "name": "p_cast201_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast201_cast", "role": "default" }} , 
 	{ "name": "p_cast219_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast219_cast", "role": "default" }} , 
 	{ "name": "p_cast249_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast249_cast", "role": "default" }} , 
 	{ "name": "p_cast275_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast275_cast", "role": "default" }} , 
 	{ "name": "p_cast223_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast223_cast", "role": "default" }} , 
 	{ "name": "p_cast243_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast243_cast", "role": "default" }} , 
 	{ "name": "p_cast263_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast263_cast", "role": "default" }} , 
 	{ "name": "p_cast285_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast285_cast", "role": "default" }} , 
 	{ "name": "p_cast265_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast265_cast", "role": "default" }} , 
 	{ "name": "p_cast261_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast261_cast", "role": "default" }} , 
 	{ "name": "p_cast281_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast281_cast", "role": "default" }} , 
 	{ "name": "p_cast289_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast289_cast", "role": "default" }} , 
 	{ "name": "p_cast203_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast203_cast", "role": "default" }} , 
 	{ "name": "p_cast267_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast267_cast", "role": "default" }} , 
 	{ "name": "p_cast259_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast259_cast", "role": "default" }} , 
 	{ "name": "p_cast239_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast239_cast", "role": "default" }} , 
 	{ "name": "p_cast207_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast207_cast", "role": "default" }} , 
 	{ "name": "p_cast257_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast257_cast", "role": "default" }} , 
 	{ "name": "p_cast269_cast", "direction": "in", "datatype": "sc_lv", "bitwidth":8, "type": "signal", "bundle":{"name": "p_cast269_cast", "role": "default" }} , 
 	{ "name": "M", "direction": "in", "datatype": "sc_lv", "bitwidth":64, "type": "signal", "bundle":{"name": "M", "role": "default" }} , 
 	{ "name": "sh_prom_i", "direction": "in", "datatype": "sc_lv", "bitwidth":32, "type": "signal", "bundle":{"name": "sh_prom_i", "role": "default" }} , 
 	{ "name": "sub2_i", "direction": "in", "datatype": "sc_lv", "bitwidth":64, "type": "signal", "bundle":{"name": "sub2_i", "role": "default" }} , 
 	{ "name": "half", "direction": "in", "datatype": "sc_lv", "bitwidth":64, "type": "signal", "bundle":{"name": "half", "role": "default" }} , 
 	{ "name": "empty", "direction": "in", "datatype": "sc_lv", "bitwidth":11, "type": "signal", "bundle":{"name": "empty", "role": "default" }} , 
 	{ "name": "p_cast302", "direction": "in", "datatype": "sc_lv", "bitwidth":9, "type": "signal", "bundle":{"name": "p_cast302", "role": "default" }} , 
 	{ "name": "mul_ln82", "direction": "in", "datatype": "sc_lv", "bitwidth":12, "type": "signal", "bundle":{"name": "mul_ln82", "role": "default" }} , 
 	{ "name": "out_r", "direction": "in", "datatype": "sc_lv", "bitwidth":64, "type": "signal", "bundle":{"name": "out_r", "role": "default" }}  ]}

set RtlHierarchyInfo {[
	{"ID" : "0", "Level" : "0", "Path" : "`AUTOTB_DUT_INST", "Parent" : "", "Child" : ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46", "47", "48", "49", "50"],
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
	{"ID" : "1", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mul_64s_32s_64_5_1_U1", "Parent" : "0"},
	{"ID" : "2", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mul_8s_8ns_16_1_1_U2", "Parent" : "0"},
	{"ID" : "3", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mul_8s_8ns_16_1_1_U3", "Parent" : "0"},
	{"ID" : "4", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mul_8s_8ns_16_1_1_U4", "Parent" : "0"},
	{"ID" : "5", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mul_8s_8ns_16_1_1_U5", "Parent" : "0"},
	{"ID" : "6", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mul_8s_8ns_16_1_1_U6", "Parent" : "0"},
	{"ID" : "7", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mul_8s_8ns_16_1_1_U7", "Parent" : "0"},
	{"ID" : "8", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mul_8s_8ns_16_1_1_U8", "Parent" : "0"},
	{"ID" : "9", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mul_8s_8ns_16_1_1_U9", "Parent" : "0"},
	{"ID" : "10", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mul_8s_8ns_16_1_1_U10", "Parent" : "0"},
	{"ID" : "11", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mul_8s_8ns_16_1_1_U11", "Parent" : "0"},
	{"ID" : "12", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mul_8s_8ns_16_1_1_U12", "Parent" : "0"},
	{"ID" : "13", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mul_8s_8ns_16_1_1_U13", "Parent" : "0"},
	{"ID" : "14", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mul_8s_8ns_16_1_1_U14", "Parent" : "0"},
	{"ID" : "15", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mul_8s_8ns_16_1_1_U15", "Parent" : "0"},
	{"ID" : "16", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mul_8s_8ns_16_1_1_U16", "Parent" : "0"},
	{"ID" : "17", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mul_8s_8ns_16_1_1_U17", "Parent" : "0"},
	{"ID" : "18", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mul_8s_8ns_16_1_1_U18", "Parent" : "0"},
	{"ID" : "19", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_16s_17_4_1_U19", "Parent" : "0"},
	{"ID" : "20", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_16s_17_4_1_U20", "Parent" : "0"},
	{"ID" : "21", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_17s_18_4_1_U21", "Parent" : "0"},
	{"ID" : "22", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_16s_17_4_1_U22", "Parent" : "0"},
	{"ID" : "23", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_17s_18_4_1_U23", "Parent" : "0"},
	{"ID" : "24", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_16s_17_4_1_U24", "Parent" : "0"},
	{"ID" : "25", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_17s_18_4_1_U25", "Parent" : "0"},
	{"ID" : "26", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_16s_17_4_1_U26", "Parent" : "0"},
	{"ID" : "27", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_17s_18_4_1_U27", "Parent" : "0"},
	{"ID" : "28", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_16s_17_4_1_U28", "Parent" : "0"},
	{"ID" : "29", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_17s_18_4_1_U29", "Parent" : "0"},
	{"ID" : "30", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_16s_17_4_1_U30", "Parent" : "0"},
	{"ID" : "31", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_17s_18_4_1_U31", "Parent" : "0"},
	{"ID" : "32", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_16s_17_4_1_U32", "Parent" : "0"},
	{"ID" : "33", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_17s_18_4_1_U33", "Parent" : "0"},
	{"ID" : "34", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_16s_17_4_1_U34", "Parent" : "0"},
	{"ID" : "35", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_17s_18_4_1_U35", "Parent" : "0"},
	{"ID" : "36", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_16s_17_4_1_U36", "Parent" : "0"},
	{"ID" : "37", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_17s_18_4_1_U37", "Parent" : "0"},
	{"ID" : "38", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_16s_17_4_1_U38", "Parent" : "0"},
	{"ID" : "39", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_17s_18_4_1_U39", "Parent" : "0"},
	{"ID" : "40", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_16s_17_4_1_U40", "Parent" : "0"},
	{"ID" : "41", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_17s_18_4_1_U41", "Parent" : "0"},
	{"ID" : "42", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_16s_17_4_1_U42", "Parent" : "0"},
	{"ID" : "43", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_17s_18_4_1_U43", "Parent" : "0"},
	{"ID" : "44", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_16s_17_4_1_U44", "Parent" : "0"},
	{"ID" : "45", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_17s_18_4_1_U45", "Parent" : "0"},
	{"ID" : "46", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_16s_17_4_1_U46", "Parent" : "0"},
	{"ID" : "47", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_17s_18_4_1_U47", "Parent" : "0"},
	{"ID" : "48", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_16s_17_4_1_U48", "Parent" : "0"},
	{"ID" : "49", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.mac_muladd_8s_8ns_16s_17_4_1_U49", "Parent" : "0"},
	{"ID" : "50", "Level" : "1", "Path" : "`AUTOTB_DUT_INST.flow_control_loop_pipe_sequential_init_U", "Parent" : "0"}]}


set ArgLastReadFirstWriteLatency {
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
	{"Name" : "Latency", "Min" : "3230", "Max" : "3230"}
	, {"Name" : "Interval", "Min" : "3230", "Max" : "3230"}
]}

set PipelineEnableSignalInfo {[
	{"Pipeline" : "0", "EnableSignal" : "ap_enable_pp0"}
]}

set Spec2ImplPortList { 
	sext_ln81 { ap_none {  { sext_ln81 in_data 0 61 } } }
	 { m_axi {  { m_axi_gmem_AWVALID VALID 1 1 }  { m_axi_gmem_AWREADY READY 0 1 }  { m_axi_gmem_AWADDR ADDR 1 64 }  { m_axi_gmem_AWID ID 1 1 }  { m_axi_gmem_AWLEN SIZE 1 32 }  { m_axi_gmem_AWSIZE BURST 1 3 }  { m_axi_gmem_AWBURST LOCK 1 2 }  { m_axi_gmem_AWLOCK CACHE 1 2 }  { m_axi_gmem_AWCACHE PROT 1 4 }  { m_axi_gmem_AWPROT QOS 1 3 }  { m_axi_gmem_AWQOS REGION 1 4 }  { m_axi_gmem_AWREGION USER 1 4 }  { m_axi_gmem_AWUSER DATA 1 1 }  { m_axi_gmem_WVALID VALID 1 1 }  { m_axi_gmem_WREADY READY 0 1 }  { m_axi_gmem_WDATA FIFONUM 1 64 }  { m_axi_gmem_WSTRB STRB 1 8 }  { m_axi_gmem_WLAST LAST 1 1 }  { m_axi_gmem_WID ID 1 1 }  { m_axi_gmem_WUSER DATA 1 1 }  { m_axi_gmem_ARVALID VALID 1 1 }  { m_axi_gmem_ARREADY READY 0 1 }  { m_axi_gmem_ARADDR ADDR 1 64 }  { m_axi_gmem_ARID ID 1 1 }  { m_axi_gmem_ARLEN SIZE 1 32 }  { m_axi_gmem_ARSIZE BURST 1 3 }  { m_axi_gmem_ARBURST LOCK 1 2 }  { m_axi_gmem_ARLOCK CACHE 1 2 }  { m_axi_gmem_ARCACHE PROT 1 4 }  { m_axi_gmem_ARPROT QOS 1 3 }  { m_axi_gmem_ARQOS REGION 1 4 }  { m_axi_gmem_ARREGION USER 1 4 }  { m_axi_gmem_ARUSER DATA 1 1 }  { m_axi_gmem_RVALID VALID 0 1 }  { m_axi_gmem_RREADY READY 1 1 }  { m_axi_gmem_RDATA FIFONUM 0 64 }  { m_axi_gmem_RLAST LAST 0 1 }  { m_axi_gmem_RID ID 0 1 }  { m_axi_gmem_RFIFONUM LEN 0 9 }  { m_axi_gmem_RUSER DATA 0 1 }  { m_axi_gmem_RRESP RESP 0 2 }  { m_axi_gmem_BVALID VALID 0 1 }  { m_axi_gmem_BREADY READY 1 1 }  { m_axi_gmem_BRESP RESP 0 2 }  { m_axi_gmem_BID ID 0 1 }  { m_axi_gmem_BUSER DATA 0 1 } } }
	w { ap_none {  { w in_data 0 64 } } }
	p_cast209_cast { ap_none {  { p_cast209_cast in_data 0 8 } } }
	p_cast277_cast { ap_none {  { p_cast277_cast in_data 0 8 } } }
	p_cast293_cast { ap_none {  { p_cast293_cast in_data 0 8 } } }
	p_cast247_cast { ap_none {  { p_cast247_cast in_data 0 8 } } }
	p_cast221_cast { ap_none {  { p_cast221_cast in_data 0 8 } } }
	p_cast255_cast { ap_none {  { p_cast255_cast in_data 0 8 } } }
	p_cast231_cast { ap_none {  { p_cast231_cast in_data 0 8 } } }
	p_cast233_cast { ap_none {  { p_cast233_cast in_data 0 8 } } }
	p_cast271_cast { ap_none {  { p_cast271_cast in_data 0 8 } } }
	p_cast229_cast { ap_none {  { p_cast229_cast in_data 0 8 } } }
	p_cast205_cast { ap_none {  { p_cast205_cast in_data 0 8 } } }
	p_cast253_cast { ap_none {  { p_cast253_cast in_data 0 8 } } }
	p_cast283_cast { ap_none {  { p_cast283_cast in_data 0 8 } } }
	p_cast287_cast { ap_none {  { p_cast287_cast in_data 0 8 } } }
	p_cast235_cast { ap_none {  { p_cast235_cast in_data 0 8 } } }
	p_cast241_cast { ap_none {  { p_cast241_cast in_data 0 8 } } }
	p_cast227_cast { ap_none {  { p_cast227_cast in_data 0 8 } } }
	p_cast245_cast { ap_none {  { p_cast245_cast in_data 0 8 } } }
	p_cast211_cast { ap_none {  { p_cast211_cast in_data 0 8 } } }
	p_cast215_cast { ap_none {  { p_cast215_cast in_data 0 8 } } }
	p_cast279_cast { ap_none {  { p_cast279_cast in_data 0 8 } } }
	p_cast291_cast { ap_none {  { p_cast291_cast in_data 0 8 } } }
	p_cast273_cast { ap_none {  { p_cast273_cast in_data 0 8 } } }
	p_cast251_cast { ap_none {  { p_cast251_cast in_data 0 8 } } }
	p_cast217_cast { ap_none {  { p_cast217_cast in_data 0 8 } } }
	p_cast225_cast { ap_none {  { p_cast225_cast in_data 0 8 } } }
	p_cast237_cast { ap_none {  { p_cast237_cast in_data 0 8 } } }
	zext_ln84 { ap_none {  { zext_ln84 in_data 0 8 } } }
	p_cast213_cast { ap_none {  { p_cast213_cast in_data 0 8 } } }
	p_cast201_cast { ap_none {  { p_cast201_cast in_data 0 8 } } }
	p_cast219_cast { ap_none {  { p_cast219_cast in_data 0 8 } } }
	p_cast249_cast { ap_none {  { p_cast249_cast in_data 0 8 } } }
	p_cast275_cast { ap_none {  { p_cast275_cast in_data 0 8 } } }
	p_cast223_cast { ap_none {  { p_cast223_cast in_data 0 8 } } }
	p_cast243_cast { ap_none {  { p_cast243_cast in_data 0 8 } } }
	p_cast263_cast { ap_none {  { p_cast263_cast in_data 0 8 } } }
	p_cast285_cast { ap_none {  { p_cast285_cast in_data 0 8 } } }
	p_cast265_cast { ap_none {  { p_cast265_cast in_data 0 8 } } }
	p_cast261_cast { ap_none {  { p_cast261_cast in_data 0 8 } } }
	p_cast281_cast { ap_none {  { p_cast281_cast in_data 0 8 } } }
	p_cast289_cast { ap_none {  { p_cast289_cast in_data 0 8 } } }
	p_cast203_cast { ap_none {  { p_cast203_cast in_data 0 8 } } }
	p_cast267_cast { ap_none {  { p_cast267_cast in_data 0 8 } } }
	p_cast259_cast { ap_none {  { p_cast259_cast in_data 0 8 } } }
	p_cast239_cast { ap_none {  { p_cast239_cast in_data 0 8 } } }
	p_cast207_cast { ap_none {  { p_cast207_cast in_data 0 8 } } }
	p_cast257_cast { ap_none {  { p_cast257_cast in_data 0 8 } } }
	p_cast269_cast { ap_none {  { p_cast269_cast in_data 0 8 } } }
	M { ap_none {  { M in_data 0 64 } } }
	sh_prom_i { ap_none {  { sh_prom_i in_data 0 32 } } }
	sub2_i { ap_none {  { sub2_i in_data 0 64 } } }
	half { ap_none {  { half in_data 0 64 } } }
	empty { ap_none {  { empty in_data 0 11 } } }
	p_cast302 { ap_none {  { p_cast302 in_data 0 9 } } }
	mul_ln82 { ap_none {  { mul_ln82 in_data 0 12 } } }
	out_r { ap_none {  { out_r in_data 0 64 } } }
}
