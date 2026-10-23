# w6_audio_bd.tcl —— 合一 BD：把 ADAU1761 音频通路搬入手套工程（2026-10-15）
# 背景：本板替换 bitstream 会硬复位（2026-10-15 实测），录音与推理必须共存于同一 bit。
# 移植自 PYNQ v3.0.1 boards/Pynq-Z2/base：audio_codec_ctrl(1.0) + clk_wiz 10MHz + PS I2C1(EMIO)。
# IP 源码已拷入 fpga/ip_repo/audio_codec_ctrl_v1.0（来自 PYNQ 官方仓库，勿改）。
# 用法：Vivado 打开 glove.xpr 且 BD（system）已打开后，Tcl Console 里 source fpga/scripts/w6_audio_bd.tcl
# 效果：audio_codec_ctrl_0 @ 0x43C00000（与 base 一致，pynq.lib.audio 驱动零改动可用）
# 配套约束：fpga/xdc/audio_w6.xdc（8 条引脚，加入工程并启用）

set w6_script_dir [file dirname [file normalize [info script]]]
set w6_repo_root [file normalize [file join $w6_script_dir ../..]]

# ---- 前置：确保 BD 已打开 ----
if {[catch {current_bd_design} curbd] || $curbd eq ""} {
    set bdfiles [get_files -quiet */system.bd]
    if {[llength $bdfiles] != 1} {
        error "Open the target project with exactly one system.bd, then source w6_audio_bd.tcl."
    }
    open_bd_design [lindex $bdfiles 0]
    set curbd [current_bd_design]
}
puts "当前 BD：$curbd"

# ---- 前置 2：登记音频 IP 仓库 ----
set audio_repo [file join $w6_repo_root fpga ip_repo]
if {![file isfile [file join $audio_repo audio_codec_ctrl_v1.0 component.xml]]} {
    error "缺少 IP：$audio_repo/audio_codec_ctrl_v1.0/component.xml"
}
set cur_repos [get_property ip_repo_paths [current_project]]
if {[lsearch $cur_repos $audio_repo] < 0} {
    set_property ip_repo_paths [concat $cur_repos $audio_repo] [current_project]
}
update_ip_catalog -rebuild
if {![llength [get_ipdefs -quiet *audio_codec_ctrl*]]} {
    error "IP 目录中找不到 audio_codec_ctrl"
}
puts "IP 目录已识别：[get_ipdefs -quiet *audio_codec_ctrl*]"

proc connect_if_free {src_pin sink_pin} {
    if {![llength [get_bd_pins -quiet $sink_pin]]} { puts "跳过（无此引脚）：$sink_pin"; return }
    if {[llength [get_bd_nets -quiet -of_objects [get_bd_pins $sink_pin]]]} {
        puts "跳过（已连接）：$sink_pin"; return
    }
    connect_bd_net [get_bd_pins $src_pin] [get_bd_pins $sink_pin]
}

# ---- 1. ps7 开启 I2C1（EMIO 到 PL 引脚 U9/T9，codec 配置通道）----
# 与 base.tcl 一致：PCW_EN_I2C1=1 且 PCW_EN_EMIO_I2C1=1（codec I2C 走 PL 引脚，不是 MIO）
set_property -dict [list CONFIG.PCW_EN_I2C1 {1} CONFIG.PCW_EN_EMIO_I2C1 {1} CONFIG.PCW_I2C1_PERIPHERAL_ENABLE {1}] [get_bd_cells ps7]
if {![llength [get_bd_intf_ports -quiet IIC_1]]} {
    create_bd_intf_port -mode Master -vlnv xilinx.com:interface:iic_rtl:1.0 IIC_1
}
if {![llength [get_bd_nets -quiet -of_objects [get_bd_intf_pins ps7/IIC_1]]]} {
    connect_bd_intf_net [get_bd_intf_pins ps7/IIC_1] [get_bd_intf_ports IIC_1]
}
puts "ps7 I2C1(EMIO) 已开启并引出 IIC_1"

# ---- 2. clk_wiz：FCLK_CLK0(100M) → 10MHz 音频主时钟 ----
if {[llength [get_bd_cells -quiet clk_wiz_audio]]} {
    puts "clk_wiz_audio 已存在，跳过创建"
} else {
    create_bd_cell -type ip -vlnv xilinx.com:ip:clk_wiz:6.0 clk_wiz_audio
    set_property -dict [list \
        CONFIG.CLKOUT1_REQUESTED_OUT_FREQ {10.000} \
        CONFIG.PRIM_SOURCE {No_buffer} \
        CONFIG.RESET_PORT {resetn} \
        CONFIG.RESET_TYPE {ACTIVE_LOW} \
    ] [get_bd_cells clk_wiz_audio]
    connect_bd_net [get_bd_pins ps7/FCLK_CLK0] [get_bd_pins clk_wiz_audio/clk_in1]
    connect_if_free proc_sys_reset_0/peripheral_aresetn clk_wiz_audio/resetn
}
if {![llength [get_bd_ports -quiet audio_clk_10MHz]]} {
    create_bd_port -dir O -type clk audio_clk_10MHz
}
if {![llength [get_bd_nets -quiet -of_objects [get_bd_pins clk_wiz_audio/clk_out1]]]} {
    connect_bd_net [get_bd_pins clk_wiz_audio/clk_out1] [get_bd_ports audio_clk_10MHz]
}
puts "10MHz 音频主时钟就绪"

# ---- 3. audio_codec_ctrl_0 实例 ----
if {[llength [get_bd_cells -quiet audio_codec_ctrl_0]]} {
    puts "audio_codec_ctrl_0 已存在，跳过创建"
} else {
    create_bd_cell -type ip -vlnv xilinx.com:user:audio_codec_ctrl:1.0 audio_codec_ctrl_0

    # 时钟与复位（FCLK_CLK0 域，与 base 一致）
    connect_if_free ps7/FCLK_CLK0 audio_codec_ctrl_0/s_axi_aclk
    connect_if_free proc_sys_reset_0/peripheral_aresetn audio_codec_ctrl_0/s_axi_aresetn

    # S_AXI → M_AXI_GP0 互连（自动化分配 M 口与地址，稍后强制 0x43C00000）
    apply_bd_automation -rule xilinx.com:bd_rule:axi4 \
        -config {Master "/ps7/M_AXI_GP0" Clk "Auto" } \
        [get_bd_intf_pins audio_codec_ctrl_0/S_AXI]

    # 外部引脚
    foreach {port dir} {bclk O lrclk O sdata_o O sdata_i I} {
        if {![llength [get_bd_ports -quiet $port]]} { create_bd_port -dir $dir $port }
    }
    if {![llength [get_bd_ports -quiet codec_addr]]} {
        create_bd_port -dir O -from 1 -to 0 codec_addr
    }
    connect_bd_net [get_bd_ports bclk]     [get_bd_pins audio_codec_ctrl_0/bclk]
    connect_bd_net [get_bd_ports lrclk]    [get_bd_pins audio_codec_ctrl_0/lrclk]
    connect_bd_net [get_bd_ports sdata_o]  [get_bd_pins audio_codec_ctrl_0/sdata_o]
    connect_bd_net [get_bd_ports sdata_i]  [get_bd_pins audio_codec_ctrl_0/sdata_i]
    connect_bd_net [get_bd_ports codec_addr] [get_bd_pins audio_codec_ctrl_0/codec_address]
    puts "audio_codec_ctrl_0 已创建并接线"
}

# ---- 4. 固定地址与 base 对齐：0x43C00000，64K ----
assign_bd_address
assign_bd_address -offset 0x43C00000 -range 0x00010000 \
    -target_address_space [get_bd_addr_spaces ps7/Data] \
    [get_bd_addr_segs audio_codec_ctrl_0/S_AXI/reg0] -force

validate_bd_design
save_bd_design
puts "==== 音频通路挂载完成 ===="
puts "下一步：把 fpga/xdc/audio_w6.xdc 加入工程并启用 → Regenerate Layout → Generate Bitstream"
puts "产物命名建议：kws_final.bit/.hwh（替代 kws_w4，只加载一次）"
