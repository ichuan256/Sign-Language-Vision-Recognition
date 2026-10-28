set SynModuleInfo {
  {SRCNAME {kp_hls_pw_core<2, 6, 6, 48, 64>_Pipeline_VITIS_LOOP_84_4} MODELNAME kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4 RTLNAME kp_hls_pw3_kp_hls_pw_core_2_6_6_48_64_Pipeline_VITIS_LOOP_84_4
    SUBMODULES {
      {MODELNAME kp_hls_pw3_mul_64s_32s_64_5_1 RTLNAME kp_hls_pw3_mul_64s_32s_64_5_1 BINDTYPE op TYPE mul IMPL auto LATENCY 4 ALLOW_PRAGMA 1}
      {MODELNAME kp_hls_pw3_mul_8s_8ns_16_1_1 RTLNAME kp_hls_pw3_mul_8s_8ns_16_1_1 BINDTYPE op TYPE mul IMPL auto LATENCY 0 ALLOW_PRAGMA 1}
      {MODELNAME kp_hls_pw3_mac_muladd_8s_8ns_16s_17_4_1 RTLNAME kp_hls_pw3_mac_muladd_8s_8ns_16s_17_4_1 BINDTYPE op TYPE all IMPL dsp_slice LATENCY 3}
      {MODELNAME kp_hls_pw3_mac_muladd_8s_8ns_17s_18_4_1 RTLNAME kp_hls_pw3_mac_muladd_8s_8ns_17s_18_4_1 BINDTYPE op TYPE all IMPL dsp_slice LATENCY 3}
      {MODELNAME kp_hls_pw3_flow_control_loop_pipe_sequential_init RTLNAME kp_hls_pw3_flow_control_loop_pipe_sequential_init BINDTYPE interface TYPE internal_upc_flow_control INSTNAME kp_hls_pw3_flow_control_loop_pipe_sequential_init_U}
    }
  }
  {SRCNAME {kp_hls_pw_core<2, 6, 6, 48, 64>} MODELNAME kp_hls_pw_core_2_6_6_48_64_s RTLNAME kp_hls_pw3_kp_hls_pw_core_2_6_6_48_64_s}
  {SRCNAME kp_hls_pw3 MODELNAME kp_hls_pw3 RTLNAME kp_hls_pw3 IS_TOP 1
    SUBMODULES {
      {MODELNAME kp_hls_pw3_gmem_m_axi RTLNAME kp_hls_pw3_gmem_m_axi BINDTYPE interface TYPE adapter IMPL m_axi}
      {MODELNAME kp_hls_pw3_ctrl_s_axi RTLNAME kp_hls_pw3_ctrl_s_axi BINDTYPE interface TYPE interface_s_axilite}
    }
  }
}
