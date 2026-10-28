# This script segment is generated automatically by AutoPilot

if {${::AESL::PGuard_rtl_comp_handler}} {
	::AP::rtl_comp_handler kp_hls_stem_mac_muladd_7ns_2ns_7ns_9_4_1 BINDTYPE {op} TYPE {all} IMPL {dsp_slice} LATENCY 3
}


# clear list
if {${::AESL::PGuard_autoexp_gen}} {
    cg_default_interface_gen_dc_begin
    cg_default_interface_gen_bundle_begin
    AESL_LIB_XILADAPTER::native_axis_begin
}

# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 110 \
    name xp \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp \
    op interface \
    ports { xp_address0 { O 10 vector } xp_ce0 { O 1 bit } xp_we0 { O 1 bit } xp_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 111 \
    name xp_1 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_1 \
    op interface \
    ports { xp_1_address0 { O 10 vector } xp_1_ce0 { O 1 bit } xp_1_we0 { O 1 bit } xp_1_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_1'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 112 \
    name xp_2 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_2 \
    op interface \
    ports { xp_2_address0 { O 10 vector } xp_2_ce0 { O 1 bit } xp_2_we0 { O 1 bit } xp_2_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_2'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 113 \
    name xp_3 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_3 \
    op interface \
    ports { xp_3_address0 { O 10 vector } xp_3_ce0 { O 1 bit } xp_3_we0 { O 1 bit } xp_3_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_3'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 114 \
    name xp_4 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_4 \
    op interface \
    ports { xp_4_address0 { O 10 vector } xp_4_ce0 { O 1 bit } xp_4_we0 { O 1 bit } xp_4_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_4'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 115 \
    name xp_5 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_5 \
    op interface \
    ports { xp_5_address0 { O 10 vector } xp_5_ce0 { O 1 bit } xp_5_we0 { O 1 bit } xp_5_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_5'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 116 \
    name xp_6 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_6 \
    op interface \
    ports { xp_6_address0 { O 10 vector } xp_6_ce0 { O 1 bit } xp_6_we0 { O 1 bit } xp_6_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_6'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 117 \
    name xp_7 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_7 \
    op interface \
    ports { xp_7_address0 { O 10 vector } xp_7_ce0 { O 1 bit } xp_7_we0 { O 1 bit } xp_7_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_7'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 118 \
    name xp_8 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_8 \
    op interface \
    ports { xp_8_address0 { O 10 vector } xp_8_ce0 { O 1 bit } xp_8_we0 { O 1 bit } xp_8_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_8'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 119 \
    name xp_9 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_9 \
    op interface \
    ports { xp_9_address0 { O 10 vector } xp_9_ce0 { O 1 bit } xp_9_we0 { O 1 bit } xp_9_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_9'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 120 \
    name xp_10 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_10 \
    op interface \
    ports { xp_10_address0 { O 10 vector } xp_10_ce0 { O 1 bit } xp_10_we0 { O 1 bit } xp_10_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_10'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 121 \
    name xp_11 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_11 \
    op interface \
    ports { xp_11_address0 { O 10 vector } xp_11_ce0 { O 1 bit } xp_11_we0 { O 1 bit } xp_11_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_11'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 122 \
    name xp_12 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_12 \
    op interface \
    ports { xp_12_address0 { O 10 vector } xp_12_ce0 { O 1 bit } xp_12_we0 { O 1 bit } xp_12_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_12'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 123 \
    name xp_13 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_13 \
    op interface \
    ports { xp_13_address0 { O 10 vector } xp_13_ce0 { O 1 bit } xp_13_we0 { O 1 bit } xp_13_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_13'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 124 \
    name xp_14 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_14 \
    op interface \
    ports { xp_14_address0 { O 10 vector } xp_14_ce0 { O 1 bit } xp_14_we0 { O 1 bit } xp_14_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_14'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 125 \
    name xp_15 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_15 \
    op interface \
    ports { xp_15_address0 { O 10 vector } xp_15_ce0 { O 1 bit } xp_15_we0 { O 1 bit } xp_15_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_15'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 126 \
    name xp_16 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_16 \
    op interface \
    ports { xp_16_address0 { O 10 vector } xp_16_ce0 { O 1 bit } xp_16_we0 { O 1 bit } xp_16_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_16'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 127 \
    name xp_17 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_17 \
    op interface \
    ports { xp_17_address0 { O 10 vector } xp_17_ce0 { O 1 bit } xp_17_we0 { O 1 bit } xp_17_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_17'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 128 \
    name xp_18 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_18 \
    op interface \
    ports { xp_18_address0 { O 10 vector } xp_18_ce0 { O 1 bit } xp_18_we0 { O 1 bit } xp_18_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_18'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 129 \
    name xp_19 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_19 \
    op interface \
    ports { xp_19_address0 { O 10 vector } xp_19_ce0 { O 1 bit } xp_19_we0 { O 1 bit } xp_19_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_19'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 130 \
    name xp_20 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_20 \
    op interface \
    ports { xp_20_address0 { O 10 vector } xp_20_ce0 { O 1 bit } xp_20_we0 { O 1 bit } xp_20_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_20'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 131 \
    name xp_21 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_21 \
    op interface \
    ports { xp_21_address0 { O 10 vector } xp_21_ce0 { O 1 bit } xp_21_we0 { O 1 bit } xp_21_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_21'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 132 \
    name xp_22 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_22 \
    op interface \
    ports { xp_22_address0 { O 10 vector } xp_22_ce0 { O 1 bit } xp_22_we0 { O 1 bit } xp_22_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_22'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 133 \
    name xp_23 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_23 \
    op interface \
    ports { xp_23_address0 { O 10 vector } xp_23_ce0 { O 1 bit } xp_23_we0 { O 1 bit } xp_23_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_23'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 134 \
    name xp_24 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_24 \
    op interface \
    ports { xp_24_address0 { O 10 vector } xp_24_ce0 { O 1 bit } xp_24_we0 { O 1 bit } xp_24_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_24'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 135 \
    name xp_25 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_25 \
    op interface \
    ports { xp_25_address0 { O 10 vector } xp_25_ce0 { O 1 bit } xp_25_we0 { O 1 bit } xp_25_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_25'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 136 \
    name xp_26 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_26 \
    op interface \
    ports { xp_26_address0 { O 10 vector } xp_26_ce0 { O 1 bit } xp_26_we0 { O 1 bit } xp_26_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_26'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 137 \
    name xp_27 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_27 \
    op interface \
    ports { xp_27_address0 { O 10 vector } xp_27_ce0 { O 1 bit } xp_27_we0 { O 1 bit } xp_27_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_27'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 138 \
    name xp_28 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_28 \
    op interface \
    ports { xp_28_address0 { O 10 vector } xp_28_ce0 { O 1 bit } xp_28_we0 { O 1 bit } xp_28_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_28'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 139 \
    name xp_29 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_29 \
    op interface \
    ports { xp_29_address0 { O 10 vector } xp_29_ce0 { O 1 bit } xp_29_we0 { O 1 bit } xp_29_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_29'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 140 \
    name xp_30 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_30 \
    op interface \
    ports { xp_30_address0 { O 10 vector } xp_30_ce0 { O 1 bit } xp_30_we0 { O 1 bit } xp_30_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_30'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 141 \
    name xp_31 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_31 \
    op interface \
    ports { xp_31_address0 { O 10 vector } xp_31_ce0 { O 1 bit } xp_31_we0 { O 1 bit } xp_31_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_31'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 142 \
    name xp_32 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_32 \
    op interface \
    ports { xp_32_address0 { O 10 vector } xp_32_ce0 { O 1 bit } xp_32_we0 { O 1 bit } xp_32_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_32'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 143 \
    name xp_33 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_33 \
    op interface \
    ports { xp_33_address0 { O 10 vector } xp_33_ce0 { O 1 bit } xp_33_we0 { O 1 bit } xp_33_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_33'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 144 \
    name xp_34 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_34 \
    op interface \
    ports { xp_34_address0 { O 10 vector } xp_34_ce0 { O 1 bit } xp_34_we0 { O 1 bit } xp_34_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_34'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 145 \
    name xp_35 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_35 \
    op interface \
    ports { xp_35_address0 { O 10 vector } xp_35_ce0 { O 1 bit } xp_35_we0 { O 1 bit } xp_35_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_35'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 146 \
    name xp_36 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_36 \
    op interface \
    ports { xp_36_address0 { O 10 vector } xp_36_ce0 { O 1 bit } xp_36_we0 { O 1 bit } xp_36_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_36'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 147 \
    name xp_37 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_37 \
    op interface \
    ports { xp_37_address0 { O 10 vector } xp_37_ce0 { O 1 bit } xp_37_we0 { O 1 bit } xp_37_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_37'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 148 \
    name xp_38 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_38 \
    op interface \
    ports { xp_38_address0 { O 10 vector } xp_38_ce0 { O 1 bit } xp_38_we0 { O 1 bit } xp_38_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_38'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 149 \
    name xp_39 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_39 \
    op interface \
    ports { xp_39_address0 { O 10 vector } xp_39_ce0 { O 1 bit } xp_39_we0 { O 1 bit } xp_39_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_39'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 150 \
    name xp_40 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_40 \
    op interface \
    ports { xp_40_address0 { O 10 vector } xp_40_ce0 { O 1 bit } xp_40_we0 { O 1 bit } xp_40_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_40'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 151 \
    name xp_41 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_41 \
    op interface \
    ports { xp_41_address0 { O 10 vector } xp_41_ce0 { O 1 bit } xp_41_we0 { O 1 bit } xp_41_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_41'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 152 \
    name xp_42 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_42 \
    op interface \
    ports { xp_42_address0 { O 10 vector } xp_42_ce0 { O 1 bit } xp_42_we0 { O 1 bit } xp_42_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_42'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 153 \
    name xp_43 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_43 \
    op interface \
    ports { xp_43_address0 { O 10 vector } xp_43_ce0 { O 1 bit } xp_43_we0 { O 1 bit } xp_43_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_43'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 154 \
    name xp_44 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_44 \
    op interface \
    ports { xp_44_address0 { O 10 vector } xp_44_ce0 { O 1 bit } xp_44_we0 { O 1 bit } xp_44_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_44'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 155 \
    name xp_45 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_45 \
    op interface \
    ports { xp_45_address0 { O 10 vector } xp_45_ce0 { O 1 bit } xp_45_we0 { O 1 bit } xp_45_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_45'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 156 \
    name xp_46 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_46 \
    op interface \
    ports { xp_46_address0 { O 10 vector } xp_46_ce0 { O 1 bit } xp_46_we0 { O 1 bit } xp_46_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_46'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 157 \
    name xp_47 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_47 \
    op interface \
    ports { xp_47_address0 { O 10 vector } xp_47_ce0 { O 1 bit } xp_47_we0 { O 1 bit } xp_47_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_47'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 158 \
    name xp_48 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_48 \
    op interface \
    ports { xp_48_address0 { O 10 vector } xp_48_ce0 { O 1 bit } xp_48_we0 { O 1 bit } xp_48_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_48'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 159 \
    name xp_49 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_49 \
    op interface \
    ports { xp_49_address0 { O 10 vector } xp_49_ce0 { O 1 bit } xp_49_we0 { O 1 bit } xp_49_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_49'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 160 \
    name xp_50 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_50 \
    op interface \
    ports { xp_50_address0 { O 10 vector } xp_50_ce0 { O 1 bit } xp_50_we0 { O 1 bit } xp_50_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_50'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 161 \
    name xp_51 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_51 \
    op interface \
    ports { xp_51_address0 { O 10 vector } xp_51_ce0 { O 1 bit } xp_51_we0 { O 1 bit } xp_51_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_51'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 162 \
    name xp_52 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_52 \
    op interface \
    ports { xp_52_address0 { O 10 vector } xp_52_ce0 { O 1 bit } xp_52_we0 { O 1 bit } xp_52_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_52'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 163 \
    name xp_53 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_53 \
    op interface \
    ports { xp_53_address0 { O 10 vector } xp_53_ce0 { O 1 bit } xp_53_we0 { O 1 bit } xp_53_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_53'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 164 \
    name xp_54 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_54 \
    op interface \
    ports { xp_54_address0 { O 10 vector } xp_54_ce0 { O 1 bit } xp_54_we0 { O 1 bit } xp_54_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_54'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 165 \
    name xp_55 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_55 \
    op interface \
    ports { xp_55_address0 { O 10 vector } xp_55_ce0 { O 1 bit } xp_55_we0 { O 1 bit } xp_55_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_55'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 166 \
    name xp_56 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_56 \
    op interface \
    ports { xp_56_address0 { O 10 vector } xp_56_ce0 { O 1 bit } xp_56_we0 { O 1 bit } xp_56_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_56'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 167 \
    name xp_57 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_57 \
    op interface \
    ports { xp_57_address0 { O 10 vector } xp_57_ce0 { O 1 bit } xp_57_we0 { O 1 bit } xp_57_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_57'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 168 \
    name xp_58 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_58 \
    op interface \
    ports { xp_58_address0 { O 10 vector } xp_58_ce0 { O 1 bit } xp_58_we0 { O 1 bit } xp_58_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_58'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 169 \
    name xp_59 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_59 \
    op interface \
    ports { xp_59_address0 { O 10 vector } xp_59_ce0 { O 1 bit } xp_59_we0 { O 1 bit } xp_59_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_59'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 170 \
    name xp_60 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_60 \
    op interface \
    ports { xp_60_address0 { O 10 vector } xp_60_ce0 { O 1 bit } xp_60_we0 { O 1 bit } xp_60_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_60'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 171 \
    name xp_61 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_61 \
    op interface \
    ports { xp_61_address0 { O 10 vector } xp_61_ce0 { O 1 bit } xp_61_we0 { O 1 bit } xp_61_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_61'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 172 \
    name xp_62 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_62 \
    op interface \
    ports { xp_62_address0 { O 10 vector } xp_62_ce0 { O 1 bit } xp_62_we0 { O 1 bit } xp_62_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_62'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 173 \
    name xp_63 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_63 \
    op interface \
    ports { xp_63_address0 { O 10 vector } xp_63_ce0 { O 1 bit } xp_63_we0 { O 1 bit } xp_63_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_63'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 174 \
    name xp_64 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_64 \
    op interface \
    ports { xp_64_address0 { O 10 vector } xp_64_ce0 { O 1 bit } xp_64_we0 { O 1 bit } xp_64_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_64'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 175 \
    name xp_65 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_65 \
    op interface \
    ports { xp_65_address0 { O 10 vector } xp_65_ce0 { O 1 bit } xp_65_we0 { O 1 bit } xp_65_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_65'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 176 \
    name xp_66 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_66 \
    op interface \
    ports { xp_66_address0 { O 10 vector } xp_66_ce0 { O 1 bit } xp_66_we0 { O 1 bit } xp_66_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_66'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 177 \
    name xp_67 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_67 \
    op interface \
    ports { xp_67_address0 { O 10 vector } xp_67_ce0 { O 1 bit } xp_67_we0 { O 1 bit } xp_67_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_67'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 178 \
    name xp_68 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_68 \
    op interface \
    ports { xp_68_address0 { O 10 vector } xp_68_ce0 { O 1 bit } xp_68_we0 { O 1 bit } xp_68_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_68'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 179 \
    name xp_69 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_69 \
    op interface \
    ports { xp_69_address0 { O 10 vector } xp_69_ce0 { O 1 bit } xp_69_we0 { O 1 bit } xp_69_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_69'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 180 \
    name xp_70 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_70 \
    op interface \
    ports { xp_70_address0 { O 10 vector } xp_70_ce0 { O 1 bit } xp_70_we0 { O 1 bit } xp_70_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_70'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 181 \
    name xp_71 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_71 \
    op interface \
    ports { xp_71_address0 { O 10 vector } xp_71_ce0 { O 1 bit } xp_71_we0 { O 1 bit } xp_71_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_71'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 182 \
    name xp_72 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_72 \
    op interface \
    ports { xp_72_address0 { O 10 vector } xp_72_ce0 { O 1 bit } xp_72_we0 { O 1 bit } xp_72_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_72'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 183 \
    name xp_73 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_73 \
    op interface \
    ports { xp_73_address0 { O 10 vector } xp_73_ce0 { O 1 bit } xp_73_we0 { O 1 bit } xp_73_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_73'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 184 \
    name xp_74 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_74 \
    op interface \
    ports { xp_74_address0 { O 10 vector } xp_74_ce0 { O 1 bit } xp_74_we0 { O 1 bit } xp_74_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_74'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 185 \
    name xp_75 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_75 \
    op interface \
    ports { xp_75_address0 { O 10 vector } xp_75_ce0 { O 1 bit } xp_75_we0 { O 1 bit } xp_75_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_75'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 186 \
    name xp_76 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_76 \
    op interface \
    ports { xp_76_address0 { O 10 vector } xp_76_ce0 { O 1 bit } xp_76_we0 { O 1 bit } xp_76_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_76'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 187 \
    name xp_77 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_77 \
    op interface \
    ports { xp_77_address0 { O 10 vector } xp_77_ce0 { O 1 bit } xp_77_we0 { O 1 bit } xp_77_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_77'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 188 \
    name xp_78 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_78 \
    op interface \
    ports { xp_78_address0 { O 10 vector } xp_78_ce0 { O 1 bit } xp_78_we0 { O 1 bit } xp_78_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_78'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 189 \
    name xp_79 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_79 \
    op interface \
    ports { xp_79_address0 { O 10 vector } xp_79_ce0 { O 1 bit } xp_79_we0 { O 1 bit } xp_79_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_79'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 190 \
    name xp_80 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_80 \
    op interface \
    ports { xp_80_address0 { O 10 vector } xp_80_ce0 { O 1 bit } xp_80_we0 { O 1 bit } xp_80_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_80'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 191 \
    name xp_81 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_81 \
    op interface \
    ports { xp_81_address0 { O 10 vector } xp_81_ce0 { O 1 bit } xp_81_we0 { O 1 bit } xp_81_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_81'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 192 \
    name xp_82 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_82 \
    op interface \
    ports { xp_82_address0 { O 10 vector } xp_82_ce0 { O 1 bit } xp_82_we0 { O 1 bit } xp_82_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_82'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 193 \
    name xp_83 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_83 \
    op interface \
    ports { xp_83_address0 { O 10 vector } xp_83_ce0 { O 1 bit } xp_83_we0 { O 1 bit } xp_83_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_83'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 194 \
    name xp_84 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_84 \
    op interface \
    ports { xp_84_address0 { O 10 vector } xp_84_ce0 { O 1 bit } xp_84_we0 { O 1 bit } xp_84_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_84'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 195 \
    name xp_85 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_85 \
    op interface \
    ports { xp_85_address0 { O 10 vector } xp_85_ce0 { O 1 bit } xp_85_we0 { O 1 bit } xp_85_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_85'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 196 \
    name xp_86 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_86 \
    op interface \
    ports { xp_86_address0 { O 10 vector } xp_86_ce0 { O 1 bit } xp_86_we0 { O 1 bit } xp_86_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_86'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 197 \
    name xp_87 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_87 \
    op interface \
    ports { xp_87_address0 { O 10 vector } xp_87_ce0 { O 1 bit } xp_87_we0 { O 1 bit } xp_87_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_87'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 198 \
    name xp_88 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_88 \
    op interface \
    ports { xp_88_address0 { O 10 vector } xp_88_ce0 { O 1 bit } xp_88_we0 { O 1 bit } xp_88_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_88'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 199 \
    name xp_89 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_89 \
    op interface \
    ports { xp_89_address0 { O 10 vector } xp_89_ce0 { O 1 bit } xp_89_we0 { O 1 bit } xp_89_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_89'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 200 \
    name xp_90 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_90 \
    op interface \
    ports { xp_90_address0 { O 10 vector } xp_90_ce0 { O 1 bit } xp_90_we0 { O 1 bit } xp_90_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_90'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 201 \
    name xp_91 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_91 \
    op interface \
    ports { xp_91_address0 { O 10 vector } xp_91_ce0 { O 1 bit } xp_91_we0 { O 1 bit } xp_91_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_91'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 202 \
    name xp_92 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_92 \
    op interface \
    ports { xp_92_address0 { O 10 vector } xp_92_ce0 { O 1 bit } xp_92_we0 { O 1 bit } xp_92_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_92'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 203 \
    name xp_93 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_93 \
    op interface \
    ports { xp_93_address0 { O 10 vector } xp_93_ce0 { O 1 bit } xp_93_we0 { O 1 bit } xp_93_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_93'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 204 \
    name xp_94 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_94 \
    op interface \
    ports { xp_94_address0 { O 10 vector } xp_94_ce0 { O 1 bit } xp_94_we0 { O 1 bit } xp_94_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_94'"
}
}


# XIL_BRAM:
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc ::AESL_LIB_XILADAPTER::xil_bram_gen] == "::AESL_LIB_XILADAPTER::xil_bram_gen"} {
eval "::AESL_LIB_XILADAPTER::xil_bram_gen { \
    id 205 \
    name xp_95 \
    reset_level 1 \
    sync_rst true \
    dir O \
    corename xp_95 \
    op interface \
    ports { xp_95_address0 { O 10 vector } xp_95_ce0 { O 1 bit } xp_95_we0 { O 1 bit } xp_95_d0 { O 8 vector } } \
} "
} else {
puts "@W \[IMPL-110\] Cannot find bus interface model in the library. Ignored generation of bus interface for 'xp_95'"
}
}


# Direct connection:
if {${::AESL::PGuard_autoexp_gen}} {
eval "cg_default_interface_gen_dc { \
    id 206 \
    name in_r \
    type other \
    dir I \
    reset_level 1 \
    sync_rst true \
    corename dc_in_r \
    op interface \
    ports { in_r { I 64 vector } } \
} "
}

# Direct connection:
if {${::AESL::PGuard_autoexp_gen}} {
eval "cg_default_interface_gen_dc { \
    id 207 \
    name gmem \
    type other \
    dir I \
    reset_level 1 \
    sync_rst true \
    corename dc_gmem \
    op interface \
    ports { m_axi_gmem_AWVALID { O 1 bit } m_axi_gmem_AWREADY { I 1 bit } m_axi_gmem_AWADDR { O 64 vector } m_axi_gmem_AWID { O 1 vector } m_axi_gmem_AWLEN { O 32 vector } m_axi_gmem_AWSIZE { O 3 vector } m_axi_gmem_AWBURST { O 2 vector } m_axi_gmem_AWLOCK { O 2 vector } m_axi_gmem_AWCACHE { O 4 vector } m_axi_gmem_AWPROT { O 3 vector } m_axi_gmem_AWQOS { O 4 vector } m_axi_gmem_AWREGION { O 4 vector } m_axi_gmem_AWUSER { O 1 vector } m_axi_gmem_WVALID { O 1 bit } m_axi_gmem_WREADY { I 1 bit } m_axi_gmem_WDATA { O 64 vector } m_axi_gmem_WSTRB { O 8 vector } m_axi_gmem_WLAST { O 1 bit } m_axi_gmem_WID { O 1 vector } m_axi_gmem_WUSER { O 1 vector } m_axi_gmem_ARVALID { O 1 bit } m_axi_gmem_ARREADY { I 1 bit } m_axi_gmem_ARADDR { O 64 vector } m_axi_gmem_ARID { O 1 vector } m_axi_gmem_ARLEN { O 32 vector } m_axi_gmem_ARSIZE { O 3 vector } m_axi_gmem_ARBURST { O 2 vector } m_axi_gmem_ARLOCK { O 2 vector } m_axi_gmem_ARCACHE { O 4 vector } m_axi_gmem_ARPROT { O 3 vector } m_axi_gmem_ARQOS { O 4 vector } m_axi_gmem_ARREGION { O 4 vector } m_axi_gmem_ARUSER { O 1 vector } m_axi_gmem_RVALID { I 1 bit } m_axi_gmem_RREADY { O 1 bit } m_axi_gmem_RDATA { I 64 vector } m_axi_gmem_RLAST { I 1 bit } m_axi_gmem_RID { I 1 vector } m_axi_gmem_RFIFONUM { I 9 vector } m_axi_gmem_RUSER { I 1 vector } m_axi_gmem_RRESP { I 2 vector } m_axi_gmem_BVALID { I 1 bit } m_axi_gmem_BREADY { O 1 bit } m_axi_gmem_BRESP { I 2 vector } m_axi_gmem_BID { I 1 vector } m_axi_gmem_BUSER { I 1 vector } } \
} "
}

# Direct connection:
if {${::AESL::PGuard_autoexp_gen}} {
eval "cg_default_interface_gen_dc { \
    id -1 \
    name ap_ctrl \
    type ap_ctrl \
    reset_level 1 \
    sync_rst true \
    corename ap_ctrl \
    op interface \
    ports { ap_start { I 1 bit } ap_ready { O 1 bit } ap_done { O 1 bit } ap_idle { O 1 bit } } \
} "
}


# Adapter definition:
set PortName ap_clk
set DataWd 1 
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc cg_default_interface_gen_clock] == "cg_default_interface_gen_clock"} {
eval "cg_default_interface_gen_clock { \
    id -2 \
    name ${PortName} \
    reset_level 1 \
    sync_rst true \
    corename apif_ap_clk \
    data_wd ${DataWd} \
    op interface \
}"
} else {
puts "@W \[IMPL-113\] Cannot find bus interface model in the library. Ignored generation of bus interface for '${PortName}'"
}
}


# Adapter definition:
set PortName ap_rst
set DataWd 1 
if {${::AESL::PGuard_autoexp_gen}} {
if {[info proc cg_default_interface_gen_reset] == "cg_default_interface_gen_reset"} {
eval "cg_default_interface_gen_reset { \
    id -3 \
    name ${PortName} \
    reset_level 1 \
    sync_rst true \
    corename apif_ap_rst \
    data_wd ${DataWd} \
    op interface \
}"
} else {
puts "@W \[IMPL-114\] Cannot find bus interface model in the library. Ignored generation of bus interface for '${PortName}'"
}
}



# merge
if {${::AESL::PGuard_autoexp_gen}} {
    cg_default_interface_gen_dc_end
    cg_default_interface_gen_bundle_end
    AESL_LIB_XILADAPTER::native_axis_end
}


# flow_control definition:
set InstName kp_hls_stem_flow_control_loop_pipe_sequential_init_U
set CompName kp_hls_stem_flow_control_loop_pipe_sequential_init
set name flow_control_loop_pipe_sequential_init
if {${::AESL::PGuard_autocg_gen} && ${::AESL::PGuard_autocg_ipmgen}} {
if {[info proc ::AESL_LIB_VIRTEX::xil_gen_UPC_flow_control] == "::AESL_LIB_VIRTEX::xil_gen_UPC_flow_control"} {
eval "::AESL_LIB_VIRTEX::xil_gen_UPC_flow_control { \
    name ${name} \
    prefix kp_hls_stem_ \
}"
} else {
puts "@W \[IMPL-107\] Cannot find ::AESL_LIB_VIRTEX::xil_gen_UPC_flow_control, check your platform lib"
}
}


if {${::AESL::PGuard_rtl_comp_handler}} {
	::AP::rtl_comp_handler $CompName BINDTYPE interface TYPE internal_upc_flow_control INSTNAME $InstName
}


