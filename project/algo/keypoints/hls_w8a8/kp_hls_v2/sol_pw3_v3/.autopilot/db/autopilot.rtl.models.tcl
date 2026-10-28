set SynModuleInfo {
  {SRCNAME {kp_hls_pw_core_v3<6, 6, 48, 64, 16>_Pipeline_1} MODELNAME kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_1 RTLNAME kp_hls_pw3_v3_kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_1
    SUBMODULES {
      {MODELNAME kp_hls_pw3_v3_flow_control_loop_pipe_sequential_init RTLNAME kp_hls_pw3_v3_flow_control_loop_pipe_sequential_init BINDTYPE interface TYPE internal_upc_flow_control INSTNAME kp_hls_pw3_v3_flow_control_loop_pipe_sequential_init_U}
    }
  }
  {SRCNAME {kp_hls_pw_core_v3<6, 6, 48, 64, 16>_Pipeline_2} MODELNAME kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_2 RTLNAME kp_hls_pw3_v3_kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_2}
  {SRCNAME {kp_hls_pw_core_v3<6, 6, 48, 64, 16>_Pipeline_VITIS_LOOP_246_3} MODELNAME kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_VITIS_LOOP_246_3 RTLNAME kp_hls_pw3_v3_kp_hls_pw_core_v3_6_6_48_64_16_Pipeline_VITIS_LOOP_246_3
    SUBMODULES {
      {MODELNAME kp_hls_pw3_v3_mul_8s_8ns_16_1_1 RTLNAME kp_hls_pw3_v3_mul_8s_8ns_16_1_1 BINDTYPE op TYPE mul IMPL auto LATENCY 0 ALLOW_PRAGMA 1}
      {MODELNAME kp_hls_pw3_v3_mac_muladd_8s_8ns_16s_17_4_1 RTLNAME kp_hls_pw3_v3_mac_muladd_8s_8ns_16s_17_4_1 BINDTYPE op TYPE all IMPL dsp_slice LATENCY 3}
    }
  }
  {SRCNAME {kp_hls_pw_core_v3<6, 6, 48, 64, 16>} MODELNAME kp_hls_pw_core_v3_6_6_48_64_16_s RTLNAME kp_hls_pw3_v3_kp_hls_pw_core_v3_6_6_48_64_16_s
    SUBMODULES {
      {MODELNAME kp_hls_pw3_v3_mul_32s_32s_64_2_1 RTLNAME kp_hls_pw3_v3_mul_32s_32s_64_2_1 BINDTYPE op TYPE mul IMPL auto LATENCY 1 ALLOW_PRAGMA 1}
      {MODELNAME kp_hls_pw3_v3_kp_hls_pw_core_v3_6_6_48_64_16_s_lin_RAM_AUTO_1R1W RTLNAME kp_hls_pw3_v3_kp_hls_pw_core_v3_6_6_48_64_16_s_lin_RAM_AUTO_1R1W BINDTYPE storage TYPE ram IMPL auto LATENCY 2 ALLOW_PRAGMA 1}
      {MODELNAME kp_hls_pw3_v3_kp_hls_pw_core_v3_6_6_48_64_16_s_lwt_RAM_AUTO_1R1W RTLNAME kp_hls_pw3_v3_kp_hls_pw_core_v3_6_6_48_64_16_s_lwt_RAM_AUTO_1R1W BINDTYPE storage TYPE ram IMPL auto LATENCY 2 ALLOW_PRAGMA 1}
    }
  }
  {SRCNAME kp_hls_pw3_v3 MODELNAME kp_hls_pw3_v3 RTLNAME kp_hls_pw3_v3 IS_TOP 1
    SUBMODULES {
      {MODELNAME kp_hls_pw3_v3_gmem_m_axi RTLNAME kp_hls_pw3_v3_gmem_m_axi BINDTYPE interface TYPE adapter IMPL m_axi}
      {MODELNAME kp_hls_pw3_v3_ctrl_s_axi RTLNAME kp_hls_pw3_v3_ctrl_s_axi BINDTYPE interface TYPE interface_s_axilite}
    }
  }
}
