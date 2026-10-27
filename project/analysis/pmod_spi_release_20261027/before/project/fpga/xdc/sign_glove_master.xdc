# =============================================================================
# 妙手通言 · PYNQ-Z2 Master XDC（W1 冻结稿 v0.1）
# 依据：方案 v2.1 §3.4 接口与引脚规划
# 引脚号来源：TUL 官方板卡文件 part0_pins.xml（PYNQ-Z2 A.0），已逐一核对
# 规则：W2 冻结后禁止临时改线（方案 §10 风险表 "高" 级）
#
# 命名约定（与 Block Design 外部端口名一致）：
#   左手 SPI 总线 A：spia_sclk / spia_mosi / spia_miso / spia_cs[2:0]
#   右手 SPI 总线 B：spib_*（同构）
#   TTS 播报：     uart_tts_txd   → SYN6288（AXI UART Lite #1）
#   无线推送：     uart_esp_txd / uart_esp_rxd → ESP32（AXI UART Lite #2）
#   备用链路：     Arduino D0/D1 保留给 PS UART1（EMIO），本文件不约束
# =============================================================================

# ----------------------------------------------------------------------------
# Pmod A = 左手 SPI 总线 A（2×MPU6500 + 1×MCP3208，SCLK 1MHz，100Hz 节拍）
# 连接器丝印 → FPGA 引脚（part0_pins.xml index 11-18）
# ----------------------------------------------------------------------------
# JA1  = SCLK
set_property -dict {PACKAGE_PIN Y18 IOSTANDARD LVCMOS33} [get_ports spia_sclk]
# JA2  = MOSI
set_property -dict {PACKAGE_PIN Y19 IOSTANDARD LVCMOS33} [get_ports spia_mosi]
# JA3  = MISO
set_property -dict {PACKAGE_PIN Y16 IOSTANDARD LVCMOS33} [get_ports spia_miso]
# JA4  = CS0 → MPU6500 #0（手背）
set_property -dict {PACKAGE_PIN Y17 IOSTANDARD LVCMOS33} [get_ports {spia_cs[0]}]
# JA7  = CS1 → MPU6500 #1（前臂）
set_property -dict {PACKAGE_PIN U18 IOSTANDARD LVCMOS33} [get_ports {spia_cs[1]}]
# JA8  = CS2 → MCP3208 #1（左手 5 路弯曲 + 3 路预留）
set_property -dict {PACKAGE_PIN U19 IOSTANDARD LVCMOS33} [get_ports {spia_cs[2]}]
# JA9/JA10（W18/W19）留作调试触发/逻辑分析仪挂钩

# ----------------------------------------------------------------------------
# Pmod B = 右手 SPI 总线 B（同构）
# 连接器丝印 → FPGA 引脚（part0_pins.xml index 19-26）
# ----------------------------------------------------------------------------
# JB1  = SCLK
set_property -dict {PACKAGE_PIN W14 IOSTANDARD LVCMOS33} [get_ports spib_sclk]
# JB2  = MOSI
set_property -dict {PACKAGE_PIN Y14 IOSTANDARD LVCMOS33} [get_ports spib_mosi]
# JB3  = MISO
set_property -dict {PACKAGE_PIN T11 IOSTANDARD LVCMOS33} [get_ports spib_miso]
# JB4  = CS0 → MPU6500 #2（手背）
set_property -dict {PACKAGE_PIN T10 IOSTANDARD LVCMOS33} [get_ports {spib_cs[0]}]
# JB7  = CS1 → MPU6500 #3（前臂）
set_property -dict {PACKAGE_PIN V16 IOSTANDARD LVCMOS33} [get_ports {spib_cs[1]}]
# JB8  = CS2 → MCP3208 #2（右手 5 路弯曲 + 3 路预留）
set_property -dict {PACKAGE_PIN W16 IOSTANDARD LVCMOS33} [get_ports {spib_cs[2]}]

# ----------------------------------------------------------------------------
# Arduino 数字 IO（D0-D13 在 part0_pins.xml 中名为 arduino_a0_a13_tri_i_*）
# D0=T14  D1=U12  D2=U13  D3=V13  D4=V15  D5=T15  D6=R16
# D7=U17  D8=V17  D9=V18  D10=T16 D11=R17 D12=P18 D13=N17
# ----------------------------------------------------------------------------

# AXI UART Lite #1 → SYN6288 TTS（D2=TX，单向即可；D3 留作 SYN6288 BUSY 检测输入）
set_property -dict {PACKAGE_PIN U13 IOSTANDARD LVCMOS33} [get_ports uart_tts_txd]
set_property -dict {PACKAGE_PIN V13 IOSTANDARD LVCMOS33} [get_ports tts_busy]

# AXI UART Lite #2 → ESP32 软 AP（D4=TX，D5=RX 全双工）
set_property -dict {PACKAGE_PIN V15 IOSTANDARD LVCMOS33} [get_ports uart_esp_txd]
set_property -dict {PACKAGE_PIN T15 IOSTANDARD LVCMOS33} [get_ports uart_esp_rxd]

# D0(T14)/D1(U12)：PS UART1 备用链路，走 EMIO 约束另附，W2 冻结时补充
# D6-D13：调试与扩展预留，暂不约束

# ----------------------------------------------------------------------------
# 板载按键 / LED / RGB（采集打标状态机，方案 §3.4）
# 若在 BD 中用板卡接口自动化（btns_4bits/leds_4bits/rgb_leds）则以下不生效，
# 此处作为手写约束备份，两者取其一，勿重复约束。
# ----------------------------------------------------------------------------
# BTN0=D19 BTN1=D20 BTN2=L20 BTN3=L19
# set_property -dict {PACKAGE_PIN D19 IOSTANDARD LVCMOS33} [get_ports {btn[0]}]
# set_property -dict {PACKAGE_PIN D20 IOSTANDARD LVCMOS33} [get_ports {btn[1]}]
# LD0-LD3 = R14 P14 N16 M14
# RGB0 = L15/G17/N15  RGB1 = G14/L14/M15

# ----------------------------------------------------------------------------
# 时序约束：PL 100MHz 主时钟（由 PS FCLK_CLK0 供给，BD 内自动衍生）
# SPI 为源同步低速接口（SCLK 1MHz），输入延迟约束在 W2 板级调通时按实测补充
# ----------------------------------------------------------------------------
# W2 TODO: set_input_delay on spia_miso/spib_miso relative to spia_sclk/spib_sclk
