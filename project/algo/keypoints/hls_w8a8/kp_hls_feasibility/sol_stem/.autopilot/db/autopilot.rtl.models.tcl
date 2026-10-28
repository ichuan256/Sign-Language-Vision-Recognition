set SynModuleInfo {
  {SRCNAME {kp_hls_conv_core<2, 96, 96, 3, 2, 16>_Pipeline_1} MODELNAME kp_hls_conv_core_2_96_96_3_2_16_Pipeline_1 RTLNAME kp_hls_stem_kp_hls_conv_core_2_96_96_3_2_16_Pipeline_1
    SUBMODULES {
      {MODELNAME kp_hls_stem_mul_15ns_17ns_31_1_1 RTLNAME kp_hls_stem_mul_15ns_17ns_31_1_1 BINDTYPE op TYPE mul IMPL auto LATENCY 0 ALLOW_PRAGMA 1}
      {MODELNAME kp_hls_stem_urem_15ns_10ns_9_19_1 RTLNAME kp_hls_stem_urem_15ns_10ns_9_19_1 BINDTYPE op TYPE urem IMPL auto LATENCY 18 ALLOW_PRAGMA 1}
      {MODELNAME kp_hls_stem_mul_9ns_11ns_19_1_1 RTLNAME kp_hls_stem_mul_9ns_11ns_19_1_1 BINDTYPE op TYPE mul IMPL auto LATENCY 0 ALLOW_PRAGMA 1}
      {MODELNAME kp_hls_stem_urem_9ns_3ns_9_13_1 RTLNAME kp_hls_stem_urem_9ns_3ns_9_13_1 BINDTYPE op TYPE urem IMPL auto LATENCY 12 ALLOW_PRAGMA 1}
      {MODELNAME kp_hls_stem_mac_muladd_7ns_2ns_7ns_8_4_1 RTLNAME kp_hls_stem_mac_muladd_7ns_2ns_7ns_8_4_1 BINDTYPE op TYPE all IMPL dsp_slice LATENCY 3}
      {MODELNAME kp_hls_stem_flow_control_loop_pipe_sequential_init RTLNAME kp_hls_stem_flow_control_loop_pipe_sequential_init BINDTYPE interface TYPE internal_upc_flow_control INSTNAME kp_hls_stem_flow_control_loop_pipe_sequential_init_U}
    }
  }
  {SRCNAME kp_hls_conv_core_Pipeline_VITIS_LOOP_112_1_VITIS_LOOP_113_2_VITIS_LOOP_114_3_VIT MODELNAME kp_hls_conv_core_Pipeline_VITIS_LOOP_112_1_VITIS_LOOP_113_2_VITIS_LOOP_114_3_VIT RTLNAME kp_hls_stem_kp_hls_conv_core_Pipeline_VITIS_LOOP_112_1_VITIS_LOOP_113_2_VITIS_LOOP_114_3_VIT
    SUBMODULES {
      {MODELNAME kp_hls_stem_mac_muladd_7ns_2ns_7ns_9_4_1 RTLNAME kp_hls_stem_mac_muladd_7ns_2ns_7ns_9_4_1 BINDTYPE op TYPE all IMPL dsp_slice LATENCY 3}
    }
  }
  {SRCNAME kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT MODELNAME kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT RTLNAME kp_hls_stem_kp_hls_conv_core_Pipeline_VITIS_LOOP_118_5_VITIS_LOOP_119_6_VITIS_LOOP_120_7_VIT
    SUBMODULES {
      {MODELNAME kp_hls_stem_mul_64s_32s_64_5_1 RTLNAME kp_hls_stem_mul_64s_32s_64_5_1 BINDTYPE op TYPE mul IMPL auto LATENCY 4 ALLOW_PRAGMA 1}
      {MODELNAME kp_hls_stem_sparsemux_97_6_8_1_1 RTLNAME kp_hls_stem_sparsemux_97_6_8_1_1 BINDTYPE op TYPE sparsemux IMPL auto}
      {MODELNAME kp_hls_stem_mul_2ns_8ns_9_1_1 RTLNAME kp_hls_stem_mul_2ns_8ns_9_1_1 BINDTYPE op TYPE mul IMPL auto LATENCY 0 ALLOW_PRAGMA 1}
      {MODELNAME kp_hls_stem_mul_2ns_10ns_10_1_1 RTLNAME kp_hls_stem_mul_2ns_10ns_10_1_1 BINDTYPE op TYPE mul IMPL auto LATENCY 0 ALLOW_PRAGMA 1}
      {MODELNAME kp_hls_stem_mul_8s_8ns_16_1_1 RTLNAME kp_hls_stem_mul_8s_8ns_16_1_1 BINDTYPE op TYPE mul IMPL auto LATENCY 0 ALLOW_PRAGMA 1}
      {MODELNAME kp_hls_stem_mac_muladd_8s_8ns_16s_17_4_1 RTLNAME kp_hls_stem_mac_muladd_8s_8ns_16s_17_4_1 BINDTYPE op TYPE all IMPL dsp_slice LATENCY 3}
      {MODELNAME kp_hls_stem_mac_muladd_8s_8ns_17s_18_4_1 RTLNAME kp_hls_stem_mac_muladd_8s_8ns_17s_18_4_1 BINDTYPE op TYPE all IMPL dsp_slice LATENCY 3}
    }
  }
  {SRCNAME {kp_hls_conv_core<2, 96, 96, 3, 2, 16>} MODELNAME kp_hls_conv_core_2_96_96_3_2_16_s RTLNAME kp_hls_stem_kp_hls_conv_core_2_96_96_3_2_16_s
    SUBMODULES {
      {MODELNAME kp_hls_stem_kp_hls_conv_core_2_96_96_3_2_16_s_xp_RAM_1WNR_AUTO_1R1W RTLNAME kp_hls_stem_kp_hls_conv_core_2_96_96_3_2_16_s_xp_RAM_1WNR_AUTO_1R1W BINDTYPE storage TYPE ram_1wnr IMPL auto LATENCY 2 ALLOW_PRAGMA 1}
      {MODELNAME kp_hls_stem_kp_hls_conv_core_2_96_96_3_2_16_s_xp_96_RAM_1WNR_AUTO_1R1W RTLNAME kp_hls_stem_kp_hls_conv_core_2_96_96_3_2_16_s_xp_96_RAM_1WNR_AUTO_1R1W BINDTYPE storage TYPE ram_1wnr IMPL auto LATENCY 2 ALLOW_PRAGMA 1}
    }
  }
  {SRCNAME kp_hls_stem MODELNAME kp_hls_stem RTLNAME kp_hls_stem IS_TOP 1
    SUBMODULES {
      {MODELNAME kp_hls_stem_gmem_m_axi RTLNAME kp_hls_stem_gmem_m_axi BINDTYPE interface TYPE adapter IMPL m_axi}
      {MODELNAME kp_hls_stem_ctrl_s_axi RTLNAME kp_hls_stem_ctrl_s_axi BINDTYPE interface TYPE interface_s_axilite}
    }
  }
}
