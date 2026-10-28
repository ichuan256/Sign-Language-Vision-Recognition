set ModuleHierarchy {[{
"Name" : "kp_hls_stem","ID" : "0","Type" : "sequential",
"SubInsts" : [
	{"Name" : "grp_kp_hls_conv_core_2_96_96_3_2_16_s_fu_102","ID" : "1","Type" : "sequential",
		"SubInsts" : [
		{"Name" : "grp_kp_hls_conv_core_2_96_96_3_2_16_Pipeline_1_fu_476","ID" : "2","Type" : "sequential",
			"SubLoops" : [
			{"Name" : "Loop 1","ID" : "3","Type" : "pipeline"},]},
		{"Name" : "grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_112_1_VITIS_LOOP_113_2_VITIS_LOOP_114_3_VIT_fu_674","ID" : "4","Type" : "sequential",
			"SubLoops" : [
			{"Name" : "VITIS_LOOP_112_1_VITIS_LOOP_113_2_VITIS_LOOP_114_3_VITIS_LOOP_115_4","ID" : "5","Type" : "pipeline"},]},
		{"Name" : "grp_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT_fu_778","ID" : "6","Type" : "sequential",
			"SubLoops" : [
			{"Name" : "VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VITIS_LOOP_121_8","ID" : "7","Type" : "pipeline"},]},]},]
}]}