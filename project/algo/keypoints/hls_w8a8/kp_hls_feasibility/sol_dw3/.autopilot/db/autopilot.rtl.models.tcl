set SynModuleInfo {
  {SRCNAME {kp_hls_dw_core<2, 12, 12, 48, 2>_Pipeline_1} MODELNAME kp_hls_dw_core_2_12_12_48_2_Pipeline_1 RTLNAME kp_hls_dw3_kp_hls_dw_core_2_12_12_48_2_Pipeline_1
    SUBMODULES {
      {MODELNAME kp_hls_dw3_mul_13ns_15ns_27_1_1 RTLNAME kp_hls_dw3_mul_13ns_15ns_27_1_1 BINDTYPE op TYPE mul IMPL auto LATENCY 0 ALLOW_PRAGMA 1}
      {MODELNAME kp_hls_dw3_urem_13ns_11ns_10_17_1 RTLNAME kp_hls_dw3_urem_13ns_11ns_10_17_1 BINDTYPE op TYPE urem IMPL auto LATENCY 16 ALLOW_PRAGMA 1}
      {MODELNAME kp_hls_dw3_urem_10ns_7ns_10_14_1 RTLNAME kp_hls_dw3_urem_10ns_7ns_10_14_1 BINDTYPE op TYPE urem IMPL auto LATENCY 13 ALLOW_PRAGMA 1}
      {MODELNAME kp_hls_dw3_mul_10ns_12ns_21_1_1 RTLNAME kp_hls_dw3_mul_10ns_12ns_21_1_1 BINDTYPE op TYPE mul IMPL auto LATENCY 0 ALLOW_PRAGMA 1}
      {MODELNAME kp_hls_dw3_mac_muladd_4ns_2ns_4ns_5_4_1 RTLNAME kp_hls_dw3_mac_muladd_4ns_2ns_4ns_5_4_1 BINDTYPE op TYPE all IMPL dsp_slice LATENCY 3}
      {MODELNAME kp_hls_dw3_flow_control_loop_pipe_sequential_init RTLNAME kp_hls_dw3_flow_control_loop_pipe_sequential_init BINDTYPE interface TYPE internal_upc_flow_control INSTNAME kp_hls_dw3_flow_control_loop_pipe_sequential_init_U}
    }
  }
  {SRCNAME kp_hls_dw_core_Pipeline_VITIS_LOOP_54_1_VITIS_LOOP_55_2_VITIS_LOOP_56_3_VITIS_LO MODELNAME kp_hls_dw_core_Pipeline_VITIS_LOOP_54_1_VITIS_LOOP_55_2_VITIS_LOOP_56_3_VITIS_LO RTLNAME kp_hls_dw3_kp_hls_dw_core_Pipeline_VITIS_LOOP_54_1_VITIS_LOOP_55_2_VITIS_LOOP_56_3_VITIS_LO
    SUBMODULES {
      {MODELNAME kp_hls_dw3_mac_muladd_4ns_2ns_4ns_6_4_1 RTLNAME kp_hls_dw3_mac_muladd_4ns_2ns_4ns_6_4_1 BINDTYPE op TYPE all IMPL dsp_slice LATENCY 3}
    }
  }
  {SRCNAME kp_hls_dw_core_Pipeline_VITIS_LOOP_60_5_VITIS_LOOP_61_6_VITIS_LOOP_62_7_VITIS_LO MODELNAME kp_hls_dw_core_Pipeline_VITIS_LOOP_60_5_VITIS_LOOP_61_6_VITIS_LOOP_62_7_VITIS_LO RTLNAME kp_hls_dw3_kp_hls_dw_core_Pipeline_VITIS_LOOP_60_5_VITIS_LOOP_61_6_VITIS_LOOP_62_7_VITIS_LO
    SUBMODULES {
      {MODELNAME kp_hls_dw3_mul_64s_32s_64_5_1 RTLNAME kp_hls_dw3_mul_64s_32s_64_5_1 BINDTYPE op TYPE mul IMPL auto LATENCY 4 ALLOW_PRAGMA 1}
      {MODELNAME kp_hls_dw3_mul_2ns_5ns_6_1_1 RTLNAME kp_hls_dw3_mul_2ns_5ns_6_1_1 BINDTYPE op TYPE mul IMPL auto LATENCY 0 ALLOW_PRAGMA 1}
      {MODELNAME kp_hls_dw3_sparsemux_13_3_8_1_1 RTLNAME kp_hls_dw3_sparsemux_13_3_8_1_1 BINDTYPE op TYPE sparsemux IMPL auto}
      {MODELNAME kp_hls_dw3_mul_8s_8ns_16_1_1 RTLNAME kp_hls_dw3_mul_8s_8ns_16_1_1 BINDTYPE op TYPE mul IMPL auto LATENCY 0 ALLOW_PRAGMA 1}
      {MODELNAME kp_hls_dw3_mac_muladd_8s_8ns_16s_17_4_1 RTLNAME kp_hls_dw3_mac_muladd_8s_8ns_16s_17_4_1 BINDTYPE op TYPE all IMPL dsp_slice LATENCY 3}
      {MODELNAME kp_hls_dw3_mac_muladd_8s_8ns_17s_18_4_1 RTLNAME kp_hls_dw3_mac_muladd_8s_8ns_17s_18_4_1 BINDTYPE op TYPE all IMPL dsp_slice LATENCY 3}
    }
  }
  {SRCNAME {kp_hls_dw_core<2, 12, 12, 48, 2>} MODELNAME kp_hls_dw_core_2_12_12_48_2_s RTLNAME kp_hls_dw3_kp_hls_dw_core_2_12_12_48_2_s
    SUBMODULES {
      {MODELNAME kp_hls_dw3_kp_hls_dw_core_2_12_12_48_2_s_xp_RAM_1WNR_AUTO_1R1W RTLNAME kp_hls_dw3_kp_hls_dw_core_2_12_12_48_2_s_xp_RAM_1WNR_AUTO_1R1W BINDTYPE storage TYPE ram_1wnr IMPL auto LATENCY 2 ALLOW_PRAGMA 1}
      {MODELNAME kp_hls_dw3_kp_hls_dw_core_2_12_12_48_2_s_xp_12_RAM_1WNR_AUTO_1R1W RTLNAME kp_hls_dw3_kp_hls_dw_core_2_12_12_48_2_s_xp_12_RAM_1WNR_AUTO_1R1W BINDTYPE storage TYPE ram_1wnr IMPL auto LATENCY 2 ALLOW_PRAGMA 1}
    }
  }
  {SRCNAME kp_hls_dw3 MODELNAME kp_hls_dw3 RTLNAME kp_hls_dw3 IS_TOP 1
    SUBMODULES {
      {MODELNAME kp_hls_dw3_gmem_m_axi RTLNAME kp_hls_dw3_gmem_m_axi BINDTYPE interface TYPE adapter IMPL m_axi}
      {MODELNAME kp_hls_dw3_ctrl_s_axi RTLNAME kp_hls_dw3_ctrl_s_axi BINDTYPE interface TYPE interface_s_axilite}
    }
  }
}
