# w6_hdmi_bd.tcl —— 合一 BD：HDMI 输出通路搬入手套工程（2026-10-15）
# 逐层复刻 PYNQ v3.0.1 base 的 video/hdmi_out/frontend 结构（只做输出，不含 hdmi_in），
# 层级名/实例名与 base 完全一致，pynq.lib.video 驱动零改动可用。
# 前提 1：algo/video_hls/run_video_hls.bat 已跑完（pixel_unpack、color_convert IP 已导出）
# 前提 2：fpga/ip_repo 下已有 rgb2dvi、axi_dynclk、color_swap_1.1（已在仓库内）
# 前提 3：Vivado 已打开 glove.xpr 且 BD（system）已打开；w6_audio_bd.tcl 已先跑过
# 用法：Tcl Console 里 source fpga/scripts/w6_hdmi_bd.tcl
# 配套约束：fpga/xdc/hdmi_w6.xdc

set w6h_script_dir [file dirname [file normalize [info script]]]
set w6h_repo_root [file normalize [file join $w6h_script_dir ../..]]

if {[catch {current_bd_design} curbd] || $curbd eq ""} {
    set bdfiles [get_files -quiet */system.bd]
    if {[llength $bdfiles] != 1} { error "Open the project with exactly one system.bd first." }
    open_bd_design [lindex $bdfiles 0]
    set curbd [current_bd_design]
}
puts "当前 BD：$curbd"

# ---- IP 仓库登记 ----
set ip_repos [list \
    [file join $w6h_repo_root fpga ip_repo] \
    [file join $w6h_repo_root algo video_hls pixel_unpack pixel_unpack solution1 impl ip] \
    [file join $w6h_repo_root algo video_hls color_convert color_convert solution1 impl ip] \
]
foreach r $ip_repos {
    if {[file isdir $r]} {
        set cur [get_property ip_repo_paths [current_project]]
        if {[lsearch $cur $r] < 0} { set_property ip_repo_paths [concat $cur $r] [current_project] }
    } else {
        puts "警告：仓库路径不存在 $r"
    }
}
update_ip_catalog -rebuild
# TMDS 接口定义检查（get_ipdefs 对 interface 类型查询不可靠，改用警告不拦截；
# 若真缺失，后面 create_bd_intf_pin 会报 BD 41-52 拦截）
if {![llength [get_ipdefs -quiet digilentinc.com:interface:tmds_rtl:*]]} {
    puts "提示：get_ipdefs 未列出 tmds_rtl（该命令对 interface 不可靠），继续尝试创建"
} else {
    puts "TMDS 接口定义已注册"
}
foreach pat {digilentinc.com:ip:rgb2dvi:* digilentinc.com:ip:axi_dynclk:* \
             xilinx.com:user:color_swap:* xilinx.com:hls:pixel_unpack:* xilinx.com:hls:color_convert:*} {
    if {![llength [get_ipdefs -quiet $pat]]} { error "缺 IP：$pat（先跑 run_video_hls.bat / 检查 ip_repo）" }
}
puts "全部 IP 已识别"

proc connect_if_free {src_pin sink_pin} {
    if {![llength [get_bd_pins -quiet $sink_pin]]} { puts "跳过（无此引脚）：$sink_pin"; return }
    if {[llength [get_bd_nets -quiet -of_objects [get_bd_pins $sink_pin]]]} {
        puts "跳过（已连接）：$sink_pin"; return
    }
    connect_bd_net [get_bd_pins $src_pin] [get_bd_pins $sink_pin]
}
proc latest_vlnv {pat} { return [lindex [get_ipdefs -quiet $pat] 0] }

# ---- 层级 proc：frontend（复刻 base create_hier_cell_frontend_1，hdmi_out 用）----
proc w6h_create_frontend {parent name} {
    set hier [create_bd_cell -type hier $name]
    current_bd_instance $hier

    create_bd_intf_pin -mode Slave  -vlnv xilinx.com:interface:aximm_rtl:1.0 S00_AXILite
    create_bd_intf_pin -mode Slave  -vlnv xilinx.com:interface:aximm_rtl:1.0 S02_AXILite
    create_bd_intf_pin -mode Slave  -vlnv xilinx.com:interface:aximm_rtl:1.0 S04_AXILite
    create_bd_intf_pin -mode Master -vlnv digilentinc.com:interface:tmds_rtl:1.0 TMDS_out
    create_bd_intf_pin -mode Slave  -vlnv xilinx.com:interface:axis_rtl:1.0 video_in
    create_bd_pin -dir I -type clk clk_100M
    create_bd_pin -dir I -type clk clk_142M
    create_bd_pin -dir O -from 0 -to 0 hdmi_out_hpd
    create_bd_pin -dir O -type intr hdmi_out_hpd_irq
    create_bd_pin -dir I -from 0 -to 0 -type rst periph_resetn_clk100M
    create_bd_pin -dir O -type intr vtc_out_irq

    create_bd_cell -type ip -vlnv [latest_vlnv digilentinc.com:ip:axi_dynclk:*] axi_dynclk
    create_bd_cell -type ip -vlnv [latest_vlnv xilinx.com:user:color_swap:*] color_swap_0
    create_bd_cell -type ip -vlnv xilinx.com:ip:axi_gpio:2.0 hdmi_out_hpd_video
    set_property -dict [list CONFIG.C_ALL_OUTPUTS {1} CONFIG.C_GPIO_WIDTH {1} CONFIG.C_INTERRUPT_PRESENT {1}] \
        [get_bd_cells hdmi_out_hpd_video]
    create_bd_cell -type ip -vlnv [latest_vlnv digilentinc.com:ip:rgb2dvi:*] rgb2dvi_0
    set_property -dict [list CONFIG.kClkRange {2} CONFIG.kGenerateSerialClk {false} CONFIG.kRstActiveHigh {false}] \
        [get_bd_cells rgb2dvi_0]
    create_bd_cell -type ip -vlnv xilinx.com:ip:v_axi4s_vid_out:4.0 v_axi4s_vid_out_0
    set_property -dict [list CONFIG.C_ADDR_WIDTH {11} CONFIG.C_HAS_ASYNC_CLK {1} \
        CONFIG.C_HYSTERESIS_LEVEL {1024} CONFIG.C_VTG_MASTER_SLAVE {1}] [get_bd_cells v_axi4s_vid_out_0]
    create_bd_cell -type ip -vlnv xilinx.com:ip:v_tc:6.2 vtc_out
    set_property -dict [list CONFIG.enable_detection {false}] [get_bd_cells vtc_out]

    connect_bd_intf_net [get_bd_intf_pins TMDS_out] [get_bd_intf_pins rgb2dvi_0/TMDS]
    connect_bd_intf_net [get_bd_intf_pins S02_AXILite] [get_bd_intf_pins vtc_out/ctrl]
    connect_bd_intf_net [get_bd_intf_pins color_swap_0/pixel_output] [get_bd_intf_pins rgb2dvi_0/RGB]
    connect_bd_intf_net [get_bd_intf_pins S00_AXILite] [get_bd_intf_pins hdmi_out_hpd_video/S_AXI]
    connect_bd_intf_net [get_bd_intf_pins S04_AXILite] [get_bd_intf_pins axi_dynclk/s00_axi]
    connect_bd_intf_net [get_bd_intf_pins v_axi4s_vid_out_0/vid_io_out] [get_bd_intf_pins color_swap_0/pixel_input]
    connect_bd_intf_net [get_bd_intf_pins v_axi4s_vid_out_0/vtiming_in] [get_bd_intf_pins vtc_out/vtiming_out]
    connect_bd_intf_net [get_bd_intf_pins video_in] [get_bd_intf_pins v_axi4s_vid_out_0/video_in]

    connect_bd_net [get_bd_pins clk_100M] [get_bd_pins axi_dynclk/REF_CLK_I] \
        [get_bd_pins axi_dynclk/s00_axi_aclk] [get_bd_pins hdmi_out_hpd_video/s_axi_aclk] \
        [get_bd_pins vtc_out/s_axi_aclk]
    connect_bd_net [get_bd_pins periph_resetn_clk100M] [get_bd_pins axi_dynclk/s00_axi_aresetn] \
        [get_bd_pins hdmi_out_hpd_video/s_axi_aresetn] [get_bd_pins vtc_out/s_axi_aresetn]
    connect_bd_net [get_bd_pins clk_142M] [get_bd_pins v_axi4s_vid_out_0/aclk]
    connect_bd_net [get_bd_pins axi_dynclk/LOCKED_O] [get_bd_pins rgb2dvi_0/aRst_n]
    connect_bd_net [get_bd_pins axi_dynclk/PXL_CLK_5X_O] [get_bd_pins rgb2dvi_0/SerialClk]
    connect_bd_net [get_bd_pins axi_dynclk/PXL_CLK_O] [get_bd_pins rgb2dvi_0/PixelClk] \
        [get_bd_pins v_axi4s_vid_out_0/vid_io_out_clk] [get_bd_pins vtc_out/clk]
    connect_bd_net [get_bd_pins hdmi_out_hpd_video/gpio_io_o] [get_bd_pins hdmi_out_hpd]
    connect_bd_net [get_bd_pins hdmi_out_hpd_video/ip2intc_irpt] [get_bd_pins hdmi_out_hpd_irq]
    connect_bd_net [get_bd_pins vtc_out/irq] [get_bd_pins vtc_out_irq]

    current_bd_instance $parent
    return $hier
}

# ---- 层级 proc：hdmi_out（复刻 base create_hier_cell_hdmi_out）----
proc w6h_create_hdmi_out {parent name} {
    set hier [create_bd_cell -type hier $name]
    current_bd_instance $hier

    foreach p {S00_AXILite S01_AXILite S02_AXILite S03_AXILite S04_AXILite} {
        create_bd_intf_pin -mode Slave -vlnv xilinx.com:interface:aximm_rtl:1.0 $p
    }
    create_bd_intf_pin -mode Master -vlnv digilentinc.com:interface:tmds_rtl:1.0 TMDS_out
    create_bd_intf_pin -mode Slave  -vlnv xilinx.com:interface:axis_rtl:1.0 in_stream
    create_bd_pin -dir I -type clk clk_100M
    create_bd_pin -dir I -type clk clk_142M
    create_bd_pin -dir O -from 0 -to 0 hdmi_out_hpd
    create_bd_pin -dir O -type intr hdmi_out_hpd_irq
    create_bd_pin -dir I -from 0 -to 0 -type rst periph_resetn_clk100M
    create_bd_pin -dir I -from 0 -to 0 -type rst periph_resetn_clk142M
    create_bd_pin -dir O -type intr vtc_out_irq

    create_bd_cell -type ip -vlnv xilinx.com:ip:axis_register_slice:1.1 axis_register_slice_0
    create_bd_cell -type ip -vlnv [latest_vlnv xilinx.com:hls:color_convert:*] color_convert
    w6h_create_frontend $hier frontend
    create_bd_cell -type ip -vlnv [latest_vlnv xilinx.com:hls:pixel_unpack:*] pixel_unpack

    connect_bd_intf_net [get_bd_intf_pins TMDS_out] [get_bd_intf_pins frontend/TMDS_out]
    connect_bd_intf_net [get_bd_intf_pins S02_AXILite] [get_bd_intf_pins frontend/S02_AXILite]
    connect_bd_intf_net [get_bd_intf_pins S03_AXILite] [get_bd_intf_pins color_convert/s_axi_control]
    connect_bd_intf_net [get_bd_intf_pins S01_AXILite] [get_bd_intf_pins pixel_unpack/s_axi_control]
    connect_bd_intf_net [get_bd_intf_pins axis_register_slice_0/M_AXIS] [get_bd_intf_pins color_convert/stream_in_24]
    connect_bd_intf_net [get_bd_intf_pins color_convert/stream_out_24] [get_bd_intf_pins frontend/video_in]
    connect_bd_intf_net [get_bd_intf_pins in_stream] [get_bd_intf_pins pixel_unpack/stream_in_32]
    connect_bd_intf_net [get_bd_intf_pins pixel_unpack/stream_out_24] [get_bd_intf_pins axis_register_slice_0/S_AXIS]
    connect_bd_intf_net [get_bd_intf_pins S00_AXILite] [get_bd_intf_pins frontend/S00_AXILite]
    connect_bd_intf_net [get_bd_intf_pins S04_AXILite] [get_bd_intf_pins frontend/S04_AXILite]

    connect_bd_net [get_bd_pins clk_100M] [get_bd_pins frontend/clk_100M]
    connect_bd_net [get_bd_pins periph_resetn_clk100M] [get_bd_pins frontend/periph_resetn_clk100M]
    connect_bd_net [get_bd_pins clk_142M] [get_bd_pins axis_register_slice_0/aclk] \
        [get_bd_pins color_convert/ap_clk] [get_bd_pins frontend/clk_142M] [get_bd_pins pixel_unpack/ap_clk]
    connect_bd_net [get_bd_pins frontend/hdmi_out_hpd] [get_bd_pins hdmi_out_hpd]
    connect_bd_net [get_bd_pins frontend/hdmi_out_hpd_irq] [get_bd_pins hdmi_out_hpd_irq]
    connect_bd_net [get_bd_pins periph_resetn_clk142M] [get_bd_pins axis_register_slice_0/aresetn] \
        [get_bd_pins color_convert/ap_rst_n] [get_bd_pins pixel_unpack/ap_rst_n]
    connect_bd_net [get_bd_pins frontend/vtc_out_irq] [get_bd_pins vtc_out_irq]

    current_bd_instance $parent
    return $hier
}

# ---- 层级 proc：video（复刻 base create_hier_cell_video，只保留输出链路）----
proc w6h_create_video {parent name} {
    set hier [create_bd_cell -type hier $name]
    current_bd_instance $hier

    create_bd_intf_pin -mode Master -vlnv xilinx.com:interface:aximm_rtl:1.0 M_AXI
    create_bd_intf_pin -mode Slave  -vlnv xilinx.com:interface:aximm_rtl:1.0 S_AXI
    create_bd_intf_pin -mode Master -vlnv digilentinc.com:interface:tmds_rtl:1.0 TMDS_out
    create_bd_pin -dir I -type clk clk_100M
    create_bd_pin -dir I -type clk clk_142M
    create_bd_pin -dir I -from 0 -to 0 -type rst periph_resetn_clk100M
    create_bd_pin -dir I -from 0 -to 0 -type rst ic_resetn_clk100M
    create_bd_pin -dir I -from 0 -to 0 -type rst ic_resetn_clk142M
    create_bd_pin -dir O -from 2 -to 0 -type intr video_irq
    create_bd_pin -dir O -from 0 -to 0 hdmi_out_hpd

    # VDMA：只开 MM2S（读帧缓冲），配置与 base 一致
    create_bd_cell -type ip -vlnv xilinx.com:ip:axi_vdma:6.3 axi_vdma
    set_property -dict [list \
        CONFIG.c_include_s2mm {0} \
        CONFIG.c_m_axi_mm2s_data_width {32} \
        CONFIG.c_m_axis_mm2s_tdata_width {32} \
        CONFIG.c_mm2s_genlock_mode {1} \
        CONFIG.c_mm2s_linebuffer_depth {512} \
        CONFIG.c_mm2s_max_burst_length {32} \
        CONFIG.c_num_fstores {4} \
    ] [get_bd_cells axi_vdma]

    create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1 axi_interconnect_0
    set_property -dict [list CONFIG.NUM_SI {1} CONFIG.NUM_MI {6}] [get_bd_cells axi_interconnect_0]
    create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1 axi_mem_intercon
    set_property -dict [list CONFIG.NUM_SI {1} CONFIG.NUM_MI {1}] [get_bd_cells axi_mem_intercon]
    create_bd_cell -type ip -vlnv xilinx.com:ip:xlconcat:2.1 xlconcat_0
    set_property -dict [list CONFIG.NUM_PORTS {3}] [get_bd_cells xlconcat_0]

    w6h_create_hdmi_out $hier hdmi_out

    connect_bd_intf_net [get_bd_intf_pins TMDS_out] [get_bd_intf_pins hdmi_out/TMDS_out]
    connect_bd_intf_net [get_bd_intf_pins S_AXI] [get_bd_intf_pins axi_interconnect_0/S00_AXI]
    connect_bd_intf_net [get_bd_intf_pins axi_interconnect_0/M00_AXI] [get_bd_intf_pins axi_vdma/S_AXI_LITE]
    connect_bd_intf_net [get_bd_intf_pins axi_interconnect_0/M01_AXI] [get_bd_intf_pins hdmi_out/S01_AXILite]
    connect_bd_intf_net [get_bd_intf_pins axi_interconnect_0/M02_AXI] [get_bd_intf_pins hdmi_out/S03_AXILite]
    connect_bd_intf_net [get_bd_intf_pins axi_interconnect_0/M03_AXI] [get_bd_intf_pins hdmi_out/S04_AXILite]
    connect_bd_intf_net [get_bd_intf_pins axi_interconnect_0/M04_AXI] [get_bd_intf_pins hdmi_out/S02_AXILite]
    connect_bd_intf_net [get_bd_intf_pins axi_interconnect_0/M05_AXI] [get_bd_intf_pins hdmi_out/S00_AXILite]
    connect_bd_intf_net [get_bd_intf_pins axi_vdma/M_AXIS_MM2S] [get_bd_intf_pins hdmi_out/in_stream]
    connect_bd_intf_net [get_bd_intf_pins axi_vdma/M_AXI_MM2S] [get_bd_intf_pins axi_mem_intercon/S00_AXI]
    connect_bd_intf_net [get_bd_intf_pins axi_mem_intercon/M00_AXI] [get_bd_intf_pins M_AXI]

    connect_bd_net [get_bd_pins clk_100M] \
        [get_bd_pins axi_interconnect_0/ACLK] [get_bd_pins axi_interconnect_0/S00_ACLK] \
        [get_bd_pins axi_interconnect_0/M00_ACLK] \
        [get_bd_pins axi_interconnect_0/M03_ACLK] \
        [get_bd_pins axi_interconnect_0/M04_ACLK] [get_bd_pins axi_interconnect_0/M05_ACLK] \
        [get_bd_pins axi_vdma/s_axi_lite_aclk] [get_bd_pins hdmi_out/clk_100M]
    connect_bd_net [get_bd_pins clk_142M] \
        [get_bd_pins axi_interconnect_0/M01_ACLK] [get_bd_pins axi_interconnect_0/M02_ACLK] \
        [get_bd_pins axi_mem_intercon/ACLK] [get_bd_pins axi_mem_intercon/S00_ACLK] \
        [get_bd_pins axi_mem_intercon/M00_ACLK] [get_bd_pins axi_vdma/m_axi_mm2s_aclk] \
        [get_bd_pins axi_vdma/m_axis_mm2s_aclk] [get_bd_pins hdmi_out/clk_142M]
    connect_bd_net [get_bd_pins periph_resetn_clk100M] \
        [get_bd_pins axi_interconnect_0/ARESETN] [get_bd_pins axi_interconnect_0/S00_ARESETN] \
        [get_bd_pins axi_interconnect_0/M00_ARESETN] \
        [get_bd_pins axi_interconnect_0/M03_ARESETN] \
        [get_bd_pins axi_interconnect_0/M04_ARESETN] [get_bd_pins axi_interconnect_0/M05_ARESETN] \
        [get_bd_pins axi_vdma/axi_resetn] [get_bd_pins hdmi_out/periph_resetn_clk100M]
    connect_bd_net [get_bd_pins periph_resetn_clk142M] \
        [get_bd_pins axi_interconnect_0/M01_ARESETN] [get_bd_pins axi_interconnect_0/M02_ARESETN] \
        [get_bd_pins hdmi_out/periph_resetn_clk142M]
    connect_bd_net [get_bd_pins ic_resetn_clk142M] \
        [get_bd_pins axi_mem_intercon/ARESETN] [get_bd_pins axi_mem_intercon/S00_ARESETN] \
        [get_bd_pins axi_mem_intercon/M00_ARESETN]

    connect_bd_net [get_bd_pins axi_vdma/mm2s_introut] [get_bd_pins xlconcat_0/In0]
    connect_bd_net [get_bd_pins hdmi_out/vtc_out_irq] [get_bd_pins xlconcat_0/In1]
    connect_bd_net [get_bd_pins hdmi_out/hdmi_out_hpd_irq] [get_bd_pins xlconcat_0/In2]
    connect_bd_net [get_bd_pins xlconcat_0/dout] [get_bd_pins video_irq]
    connect_bd_net [get_bd_pins hdmi_out/hdmi_out_hpd] [get_bd_pins hdmi_out_hpd]

    current_bd_instance /
    return $hier
}

# ================= 顶层实例化 =================
# 上次失败可能留下残缺 video 层级：以 hdmi_out/TMDS_out 是否已连线作为完成度标记
if {[llength [get_bd_cells -quiet video]]} {
    set done 0
    if {[llength [get_bd_cells -quiet video/hdmi_out]]} {
        set p [get_bd_intf_pins -quiet video/hdmi_out/TMDS_out]
        # fix 2026-10-17: intf pin must be queried with get_bd_intf_nets;
        # get_bd_nets always returns empty here and false-triggers rebuild
        if {[llength $p] && [llength [get_bd_intf_nets -quiet -of_objects $p]]} { set done 1 }
    }
    if {$done} {
        puts "video 层级完整，跳过创建"
    } else {
        puts "检测到残缺 video 层级（上次报错中断所致），删除重建"
        delete_bd_objs [get_bd_cells video]
    }
}
if {![llength [get_bd_cells -quiet video]]} {
    # 1. ps7：开 FCLK_CLK1=142.857MHz（视频像素域）+ S_AXI_HP2（VDMA 读帧缓冲）
    set_property -dict [list \
        CONFIG.PCW_EN_CLK1_PORT {1} \
        CONFIG.PCW_CLK1_FREQ {142857132} \
        CONFIG.PCW_FPGA1_PERIPHERAL_FREQMHZ {142} \
        CONFIG.PCW_USE_S_AXI_HP2 {1} \
        CONFIG.PCW_S_AXI_HP2_DATA_WIDTH {64} \
    ] [get_bd_cells ps7]
    # 显式标注 FCLK_CLK1 频率，保证 VDMA 时钟规则校验能看到真实值
    set_property CONFIG.FREQ_HZ 142857132 [get_bd_pins ps7/FCLK_CLK1]

    # 142M 域独立复位模块（复刻 base 的 rst_ps7_0_fclk1）
    if {![llength [get_bd_cells -quiet proc_sys_reset_142M]]} {
        create_bd_cell -type ip -vlnv xilinx.com:ip:proc_sys_reset:5.0 proc_sys_reset_142M
        connect_bd_net [get_bd_pins ps7/FCLK_CLK1] [get_bd_pins proc_sys_reset_142M/slowest_sync_clk]
        connect_bd_net [get_bd_pins ps7/FCLK_RESET0_N] [get_bd_pins proc_sys_reset_142M/ext_reset_in]
    }

    # 2. 创建 video 层级
    w6h_create_video / video

    # 3. 控制口：video/S_AXI → 现有 ps7_axi_periph 扩展一个新 M 口（复刻 base 做法）
    set periph ps7_axi_periph
    set num [get_property CONFIG.NUM_MI [get_bd_cells $periph]]
    set miname [format "M%02d" $num]
    set_property CONFIG.NUM_MI [expr {$num + 1}] [get_bd_cells $periph]
    connect_bd_intf_net [get_bd_intf_pins $periph/${miname}_AXI] [get_bd_intf_pins video/S_AXI]
    connect_if_free ps7/FCLK_CLK0 $periph/${miname}_ACLK
    connect_if_free proc_sys_reset_0/peripheral_aresetn $periph/${miname}_ARESETN

    # 4. 数据口：video/M_AXI → HP2 直连（复刻 base：HP 64bit + 层级内 axi_mem_intercon 自动转宽）
    connect_bd_intf_net [get_bd_intf_pins video/M_AXI] [get_bd_intf_pins ps7/S_AXI_HP2]
    connect_if_free ps7/FCLK_CLK1 ps7/S_AXI_HP2_ACLK

    # 5. 时钟复位
    connect_if_free ps7/FCLK_CLK0 video/clk_100M
    connect_if_free ps7/FCLK_CLK1 video/clk_142M
    connect_if_free proc_sys_reset_0/peripheral_aresetn      video/periph_resetn_clk100M
    connect_if_free proc_sys_reset_0/interconnect_aresetn    video/ic_resetn_clk100M
    connect_if_free proc_sys_reset_142M/peripheral_aresetn   video/periph_resetn_clk142M
    connect_if_free proc_sys_reset_142M/interconnect_aresetn video/ic_resetn_clk142M

    # 6. 中断：把现有 IRQ_F2P 的直连中断源与 video/video_irq 合并进新的 xlconcat
    set irq_pin [get_bd_pins ps7/IRQ_F2P]
    set old_net [get_bd_nets -quiet -of_objects $irq_pin]
    if {![llength [get_bd_cells -quiet xlconcat_irq]]} {
        create_bd_cell -type ip -vlnv xilinx.com:ip:xlconcat:2.1 xlconcat_irq
    }
    if {[llength $old_net]} {
        set old_src [get_bd_pins -quiet -of_objects $old_net -filter {DIR == O}]
        delete_bd_objs $old_net
        set_property CONFIG.NUM_PORTS {2} [get_bd_cells xlconcat_irq]
        if {[llength $old_src]} { connect_bd_net $old_src [get_bd_pins xlconcat_irq/In0] }
        connect_bd_net [get_bd_pins video/video_irq] [get_bd_pins xlconcat_irq/In1]
    } else {
        set_property CONFIG.NUM_PORTS {1} [get_bd_cells xlconcat_irq]
        connect_bd_net [get_bd_pins video/video_irq] [get_bd_pins xlconcat_irq/In0]
    }
    connect_bd_net [get_bd_pins xlconcat_irq/dout] $irq_pin

    # 7. 外部端口
    if {![llength [get_bd_intf_ports -quiet hdmi_out]]} {
        create_bd_intf_port -mode Master -vlnv digilentinc.com:interface:tmds_rtl:1.0 hdmi_out
    }
    connect_bd_intf_net [get_bd_intf_ports hdmi_out] [get_bd_intf_pins video/TMDS_out]
    if {![llength [get_bd_ports -quiet hdmi_out_hpd]]} {
        create_bd_port -dir O -from 0 -to 0 hdmi_out_hpd
    }
    connect_bd_net [get_bd_ports hdmi_out_hpd] [get_bd_pins video/hdmi_out_hpd]
}

# 2026-10-17 fix (always run, idempotent): proc_sys_reset_142M tie-offs.
# BD ties unconnected inputs to 0; dcm_locked=0 holds the whole 142M domain in
# permanent reset -> color_convert/v_axi4s_vid_out AXI access hard-hangs the PS.
# Mirror w3's proc_sys_reset_0: dcm_locked<-const_one, aux_reset_in<-const_zero.
if {[llength [get_bd_cells -quiet proc_sys_reset_142M]]} {
    set cone [get_bd_cells -quiet const_one]
    if {![llength $cone]} {
        set cone [create_bd_cell -type ip -vlnv xilinx.com:ip:xlconstant:1.1 const_one]
        set_property CONFIG.CONST_VAL {1} [get_bd_cells $cone]
    }
    set czero [get_bd_cells -quiet const_zero]
    if {![llength $czero]} {
        set czero [create_bd_cell -type ip -vlnv xilinx.com:ip:xlconstant:1.1 const_zero]
        set_property CONFIG.CONST_VAL {0} [get_bd_cells $czero]
    }
    foreach {pin src} [list dcm_locked $cone aux_reset_in $czero] {
        set pp [get_bd_pins -quiet proc_sys_reset_142M/$pin]
        if {[llength $pp] && ![llength [get_bd_nets -quiet -of_objects $pp]]} {
            connect_bd_net [get_bd_pins $src/dout] $pp
            puts "PATCH: proc_sys_reset_142M/$pin tied via $src"
        }
    }
    # fix 2026-10-18: net video/M01_ARESETN_1 (axi_interconnect_0 M01/M02 ARESETN
    # + hdmi_out/periph_resetn_clk142M -> color_convert/pixel_unpack/axis_register_slice)
    # has NO driver -> held in reset forever -> any AXI read hard-hangs the PS.
    # Drive it with proc_sys_reset_142M/peripheral_aresetn (pin-to-pin form:
    # -net form fails across hierarchy levels, BD 41-1255)
    set hp [get_bd_pins -quiet video/axi_interconnect_0/M01_ARESETN]
    set psrc [get_bd_pins -quiet proc_sys_reset_142M/peripheral_aresetn]
    if {[llength $hp] && [llength $psrc] && ![llength [get_bd_nets -quiet -of_objects $psrc]]} {
        if {[catch {connect_bd_net $psrc $hp} msg]} {
            puts "PATCH skip (M01_ARESETN already driven): [string trim $msg]"
        } else {
            puts "PATCH: proc_sys_reset_142M/peripheral_aresetn -> video/axi_interconnect_0/M01_ARESETN net"
        }
    }
}

# 2026-10-18 experiment (always run, idempotent): reclock the 142M video domain
# onto FCLK_CLK0 (100M). All 142M wiring verified correct in the netlist, yet
# AXI reads of color_convert/pixel_unpack hard-hang the PS, while the 100M
# cascade (incl. video-internal gpio) works. Suspect the FCLK1 fabric path.
# 720p60 (74.25MHz pixel) fits under a 100MHz stream clock, so the domain is
# not strictly required. Move clock + both resets to the 100M domain.
if {[llength [get_bd_cells -quiet video]]} {
    set vclk [get_bd_pins -quiet video/clk_142M]
    set f0   [get_bd_pins -quiet ps7/FCLK_CLK0]
    if {[llength $vclk] && [llength $f0]} {
        set old [get_bd_nets -quiet -of_objects $vclk]
        set drv [get_bd_pins -quiet -of_objects $old -filter {DIR == O}]
        if {[llength $drv] && [string match *FCLK_CLK1* $drv]} {
            disconnect_bd_net $old $vclk
            connect_bd_net $f0 $vclk
            puts "PATCH: video/clk_142M reclocked to FCLK_CLK0 (100M)"
        }
    }
    # HP2 ACLK also follows the data interconnect to FCLK_CLK0
    set hp2 [get_bd_pins -quiet ps7/S_AXI_HP2_ACLK]
    if {[llength $hp2] && [llength $f0]} {
        set nhp [get_bd_nets -quiet -of_objects $hp2]
        if {[llength $nhp]} {
            disconnect_bd_net $nhp $hp2
            connect_bd_net $f0 $hp2
            puts "PATCH: ps7/S_AXI_HP2_ACLK moved to FCLK_CLK0"
        }
    }
    # move the two 142M resets onto the 100M reset generator
    set rp [get_bd_pins -quiet video/M01_ARESETN]
    set r0 [get_bd_pins -quiet proc_sys_reset_0/peripheral_aresetn]
    set r142 [get_bd_pins -quiet proc_sys_reset_142M/peripheral_aresetn]
    if {[llength $rp] && [llength $r0] && [llength $r142]} {
        set n142 [get_bd_nets -quiet -of_objects $r142]
        if {[llength $n142]} {
            disconnect_bd_net $n142 $r142
            connect_bd_net $r0 $rp
            puts "PATCH: video 142M periph reset moved to proc_sys_reset_0"
        }
    }
    set icpin [get_bd_pins -quiet video/ic_resetn_clk142M]
    set ic0  [get_bd_pins -quiet proc_sys_reset_0/interconnect_aresetn]
    set ic142 [get_bd_pins -quiet proc_sys_reset_142M/interconnect_aresetn]
    if {[llength $icpin] && [llength $ic0] && [llength $ic142]} {
        set nic [get_bd_nets -quiet -of_objects $ic142]
        if {[llength $nic]} {
            disconnect_bd_net $nic $ic142
            connect_bd_net $ic0 $icpin
            puts "PATCH: video ic_resetn_clk142M moved to proc_sys_reset_0"
        }
    }
}

# fix 2026-10-18b (always run, idempotent): axis_register_slice_0 keeps its
# default TUSER_WIDTH=0, severing the AXIS start-of-frame sideband:
# color_convert/stream_in_24_TUSER ends up tied to 1'b0, v_axi4s_vid_out never
# sees a frame start and outputs nothing (black screen with all clocks,
# resets, VTC timing and VDMA transfers verified healthy)
if {[llength [get_bd_cells -quiet video]]} {
    set slc [get_bd_cells -quiet video/hdmi_out/axis_register_slice_0]
    if {[llength $slc] && [get_property CONFIG.TUSER_WIDTH $slc] != 1} {
        set_property CONFIG.TUSER_WIDTH {1} $slc
        puts "PATCH: axis_register_slice_0 TUSER_WIDTH=1 (restore SOF path)"
    }
}

assign_bd_address
# DEBUG: 打印 VDMA 时钟频率
foreach p {s_axi_lite_aclk m_axi_mm2s_aclk m_axis_mm2s_aclk} {
    set pin [get_bd_pins -quiet video/axi_vdma/$p]
    if {[llength $pin]} {
        puts "VDMACLK $p freq=[get_property CONFIG.FREQ_HZ $pin]"
    }
}
puts "FCLK1 freq=[get_property CONFIG.FREQ_HZ [get_bd_pins ps7/FCLK_CLK1]]"
validate_bd_design
save_bd_design
puts "==== HDMI 输出挂载完成 ===="
puts "下一步：加入 fpga/xdc/hdmi_w6.xdc → Regenerate Layout → Generate Bitstream → kws_hdmi.bit/.hwh"
