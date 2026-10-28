set ModuleHierarchy {[{
"Name" : "kp_hls_pw3_v3","ID" : "0","Type" : "sequential",
"SubInsts" : [
	{"Name" : "grp_kp_hls_pw_core_v3_6_6_48_64_16_s_fu_102","ID" : "1","Type" : "sequential",
		"SubInsts" : [
		{"Name" : "grp_kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_1_fu_345","ID" : "2","Type" : "sequential",
			"SubLoops" : [
			{"Name" : "Loop 1","ID" : "3","Type" : "pipeline"},]},
		{"Name" : "grp_kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_2_fu_385","ID" : "4","Type" : "sequential",
			"SubLoops" : [
			{"Name" : "Loop 1","ID" : "5","Type" : "pipeline"},]},],
		"SubLoops" : [
		{"Name" : "VITIS_LOOP_243_1","ID" : "6","Type" : "no",
		"SubLoops" : [
		{"Name" : "VITIS_LOOP_244_2","ID" : "7","Type" : "no",
			"SubInsts" : [
			{"Name" : "grp_kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_VITIS_LOOP_246_3_fu_409","ID" : "8","Type" : "sequential",
					"SubLoops" : [
					{"Name" : "VITIS_LOOP_246_3","ID" : "9","Type" : "pipeline"},]},]},]},]},]
}]}