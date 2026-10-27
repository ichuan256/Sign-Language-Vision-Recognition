# ATK-OV5640 双目模块物理接口核对

2026-10-27 更新：Pmod A/B 的外部 SPI 端口、12 根管脚约束及两组 SPI 时序约束已从工程源码移除；内部保留的两路 MISO 接 const_zero。Vivado 2024.1 BD 校验和新 wrapper 生成通过。旧传感器/DMA/KWS 内部链路仍保留，完整 M0b 裁剪未完成。已发布及板上 bit/HWH 未重建或替换，实物引脚须在新固件成对构建、部署并冷启动后才按新接口生效。记录：project/analysis/pmod_spi_release_20261027/README.md。

创建日期：2026-10-26；状态更新：2026-10-27。  
状态：OV5640 的 720p30 RGB565 配置、完整冷启动 RTL 和软件/RTL 验证已完成；按用户指定物理分区，左相机 OV1 使用 Raspberry Pi 23～40 脚区域的 14 个 IO，右相机 OV2 使用 1～22 脚区域的 14 个 IO，两路 PWDN 分别使用 Arduino D6/D7，30 根信号分配已落表。剩余工作是电气/引脚占用复核、完整 XDC、整板采集链路集成和真实相机验收。配置与验证证据见 [完整冷启动记录](startup_sequence.md) 和 [720p30 验证记录](mode_720p30_validation/README.md)。

## 结论

ATK-OV5640 双目模块不是 USB 或 MIPI 模块，而是两路独立的 8 位 DVP。模块通过一个 P1、2×20、2.54 mm 间距的双排弯排母与外部连接。两颗 OV5640 各自有独立的 PCLK、VSYNC、HREF、D[7:0] 和 SCCB；两路不能共用像素时钟，也不能把两路数据总线直接拼接后当成一个同步视频口。

模块只要求外部提供 3.3 V。板上有两颗 24 MHz 有源晶振，分别给 OV2/OV1 产生 XCLK；板上 LDO 产生传感器所需的 2.8 V 和 1.5 V，因此 FPGA 不需要另接 XCLK、2.8 V 或 1.5 V。资料给出的模块功耗为 270 mA，3.3 V 供电和地线必须按此留出余量。

模块标注的 IO 电平为 2.8 V LVTTL、可兼容 3.3 V。原理图中两路 SCCB 的 SCL/SDA 都通过 4.7 kΩ 电阻上拉到各自的 OVx_VCC2.8；FPGA 侧的 SCL/SDA 应实现为开漏/三态方式，不能用 3.3 V 推挽输出强行拉高。PYNQ-Z2 侧的具体 bank、VCCO、管脚和连接器仍须根据板卡原理图、当前 W6 约束和实际转接板复核。

## P1 逐针定义

以下编号按原理图 P1 的 2×20 排列读取：奇数脚在左列，偶数脚在右列。方向是相对于摄像头模块而言。
实际插接时仍应以模块 PCB 上的 Pin 1 标记和排线方向为准，不要只凭此表的左右列方向判断插头朝向。

| P1 脚号 | 网络 | 方向 | 说明 |
|---:|---|---|---|
| 1 | NC | — | 原理图标记未连接 |
| 2 | NC | — | 原理图标记未连接 |
| 3 | NC | — | 原理图标记未连接 |
| 4 | NC | — | 原理图标记未连接 |
| 5 | OV1_VSYNC | 模块 → FPGA | OV1 帧同步输出 |
| 6 | OV1_SCL | FPGA → 模块 | OV1 SCCB 时钟；原理图上拉至 OV1_VCC2.8 |
| 7 | OV1_HREF | 模块 → FPGA | OV1 行同步/行有效输出 |
| 8 | OV1_SDA | 双向 | OV1 SCCB 数据；原理图上拉至 OV1_VCC2.8 |
| 9 | OV1_RESET | FPGA → 模块 | OV1 复位，低有效 |
| 10 | OV1_D0 | 模块 → FPGA | OV1 DVP 数据 |
| 11 | OV1_D1 | 模块 → FPGA | OV1 DVP 数据 |
| 12 | OV1_D2 | 模块 → FPGA | OV1 DVP 数据 |
| 13 | OV1_D3 | 模块 → FPGA | OV1 DVP 数据 |
| 14 | OV1_D4 | 模块 → FPGA | OV1 DVP 数据 |
| 15 | OV1_D5 | 模块 → FPGA | OV1 DVP 数据 |
| 16 | OV1_D6 | 模块 → FPGA | OV1 DVP 数据 |
| 17 | OV1_D7 | 模块 → FPGA | OV1 DVP 数据 |
| 18 | OV1_PCLK | 模块 → FPGA | OV1 像素时钟输出 |
| 19 | OV1_PWDN | FPGA → 模块 | OV1 掉电控制，高有效；正常工作应保持低 |
| 20 | OV2_PWDN | FPGA → 模块 | OV2 掉电控制，高有效；正常工作应保持低 |
| 21 | OV2_VSYNC | 模块 → FPGA | OV2 帧同步输出 |
| 22 | OV2_SCL | FPGA → 模块 | OV2 SCCB 时钟；原理图上拉至 OV2_VCC2.8 |
| 23 | OV2_HREF | 模块 → FPGA | OV2 行同步/行有效输出 |
| 24 | OV2_SDA | 双向 | OV2 SCCB 数据；原理图上拉至 OV2_VCC2.8 |
| 25 | OV2_RESET | FPGA → 模块 | OV2 复位，低有效 |
| 26 | OV2_D0 | 模块 → FPGA | OV2 DVP 数据 |
| 27 | OV2_D1 | 模块 → FPGA | OV2 DVP 数据 |
| 28 | OV2_D2 | 模块 → FPGA | OV2 DVP 数据 |
| 29 | OV2_D3 | 模块 → FPGA | OV2 DVP 数据 |
| 30 | OV2_D4 | 模块 → FPGA | OV2 DVP 数据 |
| 31 | OV2_D5 | 模块 → FPGA | OV2 DVP 数据 |
| 32 | OV2_D6 | 模块 → FPGA | OV2 DVP 数据 |
| 33 | OV2_D7 | 模块 → FPGA | OV2 DVP 数据 |
| 34 | OV2_PCLK | 模块 → FPGA | OV2 像素时钟输出 |
| 35 | NC | — | 原理图未标注信号，按未连接处理 |
| 36 | NC | — | 原理图未标注信号，按未连接处理 |
| 37 | GND | — | 模块地 |
| 38 | VCC3.3 | 外部 → 模块 | 模块实际供电脚，接 3.3 V |
| 39 | GND | — | 模块地 |
| 40 | VCC5 | 外部 → 模块 | 手册注明模块没有使用；不要把它当作摄像头供电脚 |

## DVP 与 SCCB 的有效信息

- 模块采用 OV5640 的默认 8 位 DVP 接法；资料图示为传感器 Y9..Y2 映射到外部 D7..D0，Y1/Y0 不接。
- 在 RGB565 模式下，每个 PCLK 输出一个字节，每个像素由两个字节组成，资料明确说明低字节先输出、高字节后输出。RTL 不能直接照抄旧例程的拼接顺序，必须用色条或寄存器读回结果确认最终 RGB565 字节序。
- HREF 为高时输出有效数据；每个 PCLK 对应一个 8 位数据字节。VSYNC 标记帧边界。资料中的时序图足以确定数据/行/帧的关系，但具体采样边沿、VSYNC 有效极性和寄存器配置仍应在 RTL 仿真及示波器/逻辑分析仪实测中冻结。
- 两路 SCCB 是物理上独立的总线，不应假定靠不同地址共用一条总线。SCCB 与 I2C 相似，但确认位规则不同；初始化控制器应按 OV5640 SCCB 时序实现。
- JPEG 模式仍复用 DVP 引脚，但数据不连续，帧以 JPEG 标记结束；首轮 FPGA 采集建议使用固定分辨率 RGB565，先不要把 JPEG 与连续帧 DMA 混在同一验收中。

## 已完成配置与待实测边界（2026-10-27 更新）

720p30 RGB565 的配置实现及软件/RTL 验证已经完成：27 项配置子表、308 项完整冷启动 ROM、RESET/PWDN 时序、双路芯片 ID/关键寄存器检查和受检查结果控制的 stream-on 均已实现。ROM/JSON 一致性、模式合同与 XSim 回归已有通过记录；真实相机输出和板级电气时序尚待接线后实测。各项状态如下：

| 项目 | 冻结值/状态 | 依据与边界 |
|---|---|---|
| 相机数量与接口 | 两路独立 8-bit DVP；每路独立 SCCB、PCLK、VSYNC、HREF、D[7:0] | 模块手册 p.2、p.4；两路相机不能共用 PCLK |
| 外部输入时钟 | 两路各 24 MHz XCLK，由模块板载晶振提供 | 模块手册 p.4、双目板原理图；传感器内部仍需配置 PLL/分频以得到目标时序 |
| 目标尺寸与帧率 | **1280×720、标称30fps** | 2026-10-26用户决定；HTS1892/VTS740、SCLK42MHz计算约29.998286fps，尚未实测 |
| 目标像素格式 | RGB565，8-bit DVP；每像素两字节，低字节先出 | 模块手册 p.6-7；FPGA 合并字节顺序按此目标实现 |
| VSYNC 有效极性 | **冻结 FPGA 接收契约为高有效**，匹配现有 RTL 默认值；相机位值仍须板上核验 | DVP 指南 p.27 和芯片数据手册将 `0x4740[0]=1` 解释为高有效；Linux 上游 `ov5640_set_power_dvp()` 却明确注明实物该位为 0 时高有效、1 时低有效。不能据资料中的一个位值断言实际极性；HREF 位说明也有差异，详见 `configuration_choices.md` |
| PCLK 采样边沿 | **FPGA 上升沿采样的配置已实现并通过仿真**；物理输入时序待实测 | 采集器使用 `posedge cam_pclk`。27 项子表对 `0x4740` 的掩码为 `0x20`；完整冷启动入口使用 `DVP_POLARITY_VALUE=0x22`、掩码 `0x2f`，均已实现。实际相机读回和波形测量仍待完成，详见 startup_sequence.md |
| 720p30 RGB565 初始化表 | **27 项子表、308 项完整 ROM 及一致性/模式合同验证已完成** | 已实现基础 ISP、subsampling/binning、窗口、曝光、防闪烁、ID/所选寄存器读回及受控 stream-on，并通过软件检查与 XSim 验证；PCLK 84MHz 为计算值，真实相机验收待完成，见 mode_720p30_validation/README.md |
| 双目帧同步 | 未冻结 | 两路同设分辨率和帧率不等同于帧起点同步；需读回/波形测量帧相位，或另行实现传感器同步方案 |

参考资料核验记录：`2，OV5640参考资料/OV5640_自动对焦照相模组应用指南(DVP_接口)__R2.13C.pdf` p.14-15 的初始化示例将 `0x4300=0x30`、`0x501f=0x00` 配成 YUV422，不是 RGB565；p.19-24 的模式示例包含 VGA30、854x48030、720p15/30，未给出 1080p30 完整表。p.27 定义 `0x4740` 的 VSYNC、HREF 与 PCLK 极性位。`OV5640_CSP3_DS_2.01_Ruisipusheng.pdf` p.25、p.35-36 描述格式/VSYNC/极性寄存器，但没有给出可直接用于本双目模块的完整目标配置。正点原子模块手册 p.2 的 1080p30、RGB565 是规格能力，不是寄存器初始化序列。

配置实现与软件/RTL 验证已完成，不再列为待补齐项。当前 19 项 XSim 回归全部通过，覆盖完整 720p RGB565 帧、坏帧恢复、独立 PCLK、SCCB 事务、完整启动及错误/超时处理，记录见 [720p30 验证记录](mode_720p30_validation/README.md)。接线后仍需在真实相机上验证两路 SCCB 读回、帧尺寸/FPS、VSYNC/HREF/PCLK 波形及 RGB565 字节序；这些硬件验收未完成前，不将计算帧率或仿真通过表述为实物达到 720p30。

## 接线时可直接采用的安全边界

1. 只给 P1-38 提供 3.3 V，并将 P1-37/P1-39 接同一系统地；P1-40 不作为摄像头供电。3.3 V 电源按至少 270 mA 模块功耗并留启动余量，实际能否由 PYNQ-Z2 3.3 V 轨直接承担要查板卡资料后决定。
2. OV1/OV2 的 D[7:0]、PCLK、VSYNC、HREF 必须分别进入两个 FPGA 输入组；PCLK1/PCLK2 分别作为各自采集域时钟，不能在模块外短接。
3. OV1/OV2 的 SCL/SDA 保持独立。SCL/SDA 上拉已经在模块上，并且上拉电压是约 2.8 V；FPGA 端使用开漏/三态 I/O，不能用推挽高电平驱动 SDA。
4. RESET/PWDN 上电时序已在完整冷启动 RTL 中实现并通过仿真：RESET 低有效，PWDN 高有效。四根控制线须接到相应顶层端口，不能悬空；实际管脚电平及相机响应在上板时核验，具体等待顺序见 [完整冷启动记录](startup_sequence.md)。
5. P1 有 30 根信号线、4 根电源/地线和 6 根 NC，不能把它简化为“一个 Pmod 只接 D[7:0]”。PYNQ-Z2 的连接器和当前 W6 已占用管脚需要先做完整的 30 信号预算；仓库里旧的 `Pmod JA=左目、Pmod JB=右目` 注释不是经过该模块 P1 针脚核对后的结论。

## 补充两个独立数字 IO（2026-10-27）

每路相机有 15 根信号，两路共 30 根。两路 PWDN 分到 Arduino D6/D7，其余 28 根已按下节左右物理分区逐脚分配；电源另接并与 PYNQ-Z2 共地。分配是待整板集成/实测的接线方案，尚未成为已部署约束。

| 摄像头信号 | 摄像头 P1 脚 | PYNQ-Z2 数字口 | Arduino 排针位置 | FPGA 封装脚 | 候选 IO 标准 |
|---|---:|---|---|---|---|
| OV1_PWDN / ov1_pwdn | 19 | D6 / AR6 | J4 第 7 脚 | R16 | LVCMOS33 |
| OV2_PWDN / ov2_pwdn | 20 | D7 / AR7 | J4 第 8 脚 | U17 | LVCMOS33 |

依据：本地 TUL PYNQ-Z2 Reference Manual v1.0 第 17 节表 17（PDF 第 26 页），以及 backup/pynq-z2/PYNQ-Z2 v1.0.xdc 第 100–101 行。两脚为普通 PL 数字 IO，适合慢速 PWDN 控制；PWDN 高有效，正常工作拉低，两路保持独立。

静态检索当前工程 XDC/Tcl/BD/HDL，未发现 R16/U17 的有效 PACKAGE_PIN/LOC 分配；sign_glove_master.xdc 第 65 行将 D6–D13 标为调试与扩展预留。此处仅记录候选接线，不代表综合网表或板端验证。后续须在候选顶层引出 ov1_pwdn/ov2_pwdn 并绑定 R16/U17，生成并验收配套 bit/HWH。

共享与占用：Raspberry Pi 排针中有 8 个 IO 与 Pmod A 共用 FPGA 引脚，不能重复计数。2026-10-27 已在源码移除 sign_glove_master.xdc 的两路 SPI 管脚、时序和 BD 外部端口，共享组 Y18/Y19/Y16/Y17/U18/U19 不再预留给 SPI；当前板上旧固件尚未随此变更重建部署。D6/D7 不属于该共享组。下节已选定两路 PCLK 的时钟能力 P 侧引脚，其布线资源与时序仍待实现阶段核验。

## 按物理距离分配左右相机（2026-10-27）

按用户给出的排针区域划分：图中物理 23～40 脚一端负责左摄像头，其余物理 1～22 脚一端负责右摄像头；每端扣除电源/GND 后恰好 14 个信号 IO。左右是用户指定的安装方向，不依据镜头正反面自行交换。约定左摄像头为 OV1、右摄像头为 OV2，实际模块 OV1/OV2 镜头位置须按丝印核对；如果模块装反，应交换安装方向或整组映射，不只交换数据线。

重要勘误：用户截图对应 TUL v1.0 的旧表 22。TUL v1.1 修订记录明确修正 Raspberry Pi 到 Zynq 的引脚映射；本表保留截图中的物理分区，但 FPGA 封装脚统一采用 v1.1（PDF 第 30 页、正文第 27 页表 22），并用 Xilinx/PYNQ v3.0.1 的 base.xdc 核对。旧图中例如 26 脚 F20 应为 U19、29 脚 Y6 应为 Y19、31 脚 Y7 应为 U18；右半区也有更正，不能沿用旧图字母生成 XDC。

### 左摄像头 OV1：Raspberry Pi 23～40 脚区域

| 相机信号 | 摄像头 P1 物理脚 | PYNQ-Z2 接头 | 接头物理脚/丝印 | FPGA 封装脚 |
|---|---:|---|---|---|
| OV1_VSYNC | 5 | Raspberry Pi | 26 | U19 |
| OV1_SCL | 6 | Raspberry Pi | 23 | W10 |
| OV1_HREF | 7 | Raspberry Pi | 27 | Y16 |
| OV1_SDA | 8 | Raspberry Pi | 24 | F19 |
| OV1_RESET | 9 | Raspberry Pi | 28 | Y17 |
| OV1_D0 | 10 | Raspberry Pi | 29 | Y19 |
| OV1_D1 | 11 | Raspberry Pi | 31 | U18 |
| OV1_D2 | 12 | Raspberry Pi | 32 | B20 |
| OV1_D3 | 13 | Raspberry Pi | 33 | W8 |
| OV1_D4 | 14 | Raspberry Pi | 35 | Y8 |
| OV1_D5 | 15 | Raspberry Pi | 36 | B19 |
| OV1_D6 | 16 | Raspberry Pi | 37 | W9 |
| OV1_D7 | 17 | Raspberry Pi | 38 | A20 |
| OV1_PCLK | 18 | Raspberry Pi | 40 | Y9 |
| OV1_PWDN | 19 | Arduino J4 | D6 / J4-7 | R16 |

此端 25、30、34、39 脚为 GND，不能作信号。D[7:0] 依次排在 29/31/32/33/35/36/37/38 脚，PCLK 放在 40 脚，尽量让像素信号集中在这一端；SCCB 和低速控制放在 23～28 脚。

### 右摄像头 OV2：Raspberry Pi 1～22 脚区域

| 相机信号 | 摄像头 P1 物理脚 | PYNQ-Z2 接头 | 接头物理脚/丝印 | FPGA 封装脚 |
|---|---:|---|---|---|
| OV2_VSYNC | 21 | Raspberry Pi | 3 | W18 |
| OV2_SCL | 22 | Raspberry Pi | 8 | V6 |
| OV2_HREF | 23 | Raspberry Pi | 5 | W19 |
| OV2_SDA | 24 | Raspberry Pi | 10 | Y6 |
| OV2_RESET | 25 | Raspberry Pi | 7 | Y18 |
| OV2_D0 | 26 | Raspberry Pi | 12 | C20 |
| OV2_D1 | 27 | Raspberry Pi | 13 | V7 |
| OV2_D2 | 28 | Raspberry Pi | 15 | U8 |
| OV2_D3 | 29 | Raspberry Pi | 16 | W6 |
| OV2_D4 | 30 | Raspberry Pi | 18 | Y7 |
| OV2_D5 | 31 | Raspberry Pi | 19 | V8 |
| OV2_D6 | 32 | Raspberry Pi | 21 | V10 |
| OV2_D7 | 33 | Raspberry Pi | 22 | F20 |
| OV2_PCLK | 34 | Raspberry Pi | 11 | U7 |
| OV2_PWDN | 20 | Arduino J4 | D7 / J4-8 | U17 |

此端 1、17 脚为 3.3V，2、4 脚为 5V，6、9、14、20 脚为 GND，均不作为相机数字信号。D[7:0] 依次排在 12/13/15/16/18/19/21/22 脚，PCLK 放在 11 脚，慢速控制放在 3～10 脚。

### 时钟、距离与实施边界

- 左 PCLK 使用 40 脚 Y9（IO_L14P_T2_SRCC_13），右 PCLK 使用 11 脚 U7（IO_L11P_T1_SRCC_13）；均为时钟能力管脚的 P 侧。单端时钟须用 P 侧，不能仅因 35 脚 Y8 标为 SRCC 就将其当作独立单端时钟。Y8 在本表只作 D4 普通输入。
- 本分配优化的是外部接线的物理分区和连续性，尚未量得实际线长。各路像素信号跨多个 IO bank，后续需按全局时钟资源和实现报告核验，不能把排针相邻当作 FPGA 内部时序通过，也不以 CLOCK_DEDICATED_ROUTE=FALSE 绕过时钟问题。
- 两路 PCLK 各自独立。84MHz 是已完成配置的计算候选值，不是板上测值；最终输入延迟约束须包含传感器时序、板级/转接/排线差异，不能预填虚构裕量。
- 原手册标注 3、5、27、28 脚 PULL HIGH。本分配的 SCCB 放在 8/10 与 23/24 脚，避开这些标注脚；SCL/SDA 继续开漏/三态，不把基线通用 GPIO 上拉设置直接套入相机工程。
- 供电沿用摄像头 P1-38=3.3V、P1-37/P1-39=GND，电源单独安排；P1-40 不作相机供电。Raspberry Pi 的电源/GND 不计入 28 路 IO，两块设备仍需共地。
- Pmod A 与排针共享的 8 个 IO 已包含在本表 28 路中，不增加 IO 总数；旧 SPI 外部端口及约束已从源码移除；IO 电平/供电复核、整板集成、重建部署与真实相机验收仍待完成。
- 这次只确定接线方案，未写入活动 XDC、未修改 RTL、未重建或下载 bitstream。可机读映射保存于 [physical_pin_map_20261027.json](physical_pin_map_20261027.json)，后续 XDC 应从同一映射派生。

来源：

- [TUL 用户手册 v1.1](https://dpoauwgwqsy2x.cloudfront.net/Download/PYNQ_Z2_User_Manual_v1.1.pdf)：修订记录（PDF 第 2 页）及表 22（PDF 第 30 页）。
- [Xilinx/PYNQ v3.0.1 base.xdc](https://raw.githubusercontent.com/Xilinx/PYNQ/v3.0.1/boards/Pynq-Z2/base/vivado/constraints/base.xdc)：RPi 和共享 Pmod A 映射、Arduino GPIO 6/7。
- [AMD UG472 Clock-Capable Inputs](https://docs.amd.com/api/khub/documents/1kFbRqzm2fhwGy~cLQG2yA/content)：单端时钟的 P 侧连接要求。

## 剩余接线、集成与板上验收项目

- 旧 SPI 外部共享占用已从源码移除；按已落表的 30 根信号分配，确认相机候选顶层端口，补齐完整 XDC；核验两路 PCLK 的时钟资源/布线和输入时序；
- PYNQ-Z2 对应 IO bank 的 VCCO、3.3 V 电源可用电流和转接板走线；
- 已完成配置在真实相机上的 SCCB 读回、输出尺寸/FPS、PCLK 频率、VSYNC/HREF 极性和数据采样时序实测；
- 异步 FIFO、AXI/PS DDR 采集写入、BD 集成、整板综合/实现和配套 bit/HWH，以及板端读帧/回传；
- 两路相机在相同配置下的实际帧相位偏差，以及是否需要帧丢弃/配对策略；
- 连接器的实际插入方向、排线长度和带载后的信号完整性。

另一个资料版本注意项：原理图文件名为 `ATK_Dual_OV5640_V1.8.pdf`，但其图框修订栏标为 V1.1。本文按该文件实际画出的 P1 网络整理；布线前应对照手头模块 PCB 版本/丝印复核，避免把文件名误当作图纸修订号。

本次已确定接线分配，不代表已完成所有电气与实现验收；在相应证据齐备前，不将其直接加入当前运行 W6 工程的活动约束或作为正式发布固件。

## 资料来源

- [ATK-OV5640 双目摄像头模块用户手册](../../../backup/【正点原子】OV5640双目摄像头模块/【正点原子】OV5640双目摄像头模块资料/ATK-OV5640双目摄像头模块用户手册_V1.0.pdf)：第 3-8 页，电气参数、P1 信号表、SCCB/DVP 说明和时序。
- [ATK_Dual_OV5640_V1.8 原理图](../../../backup/【正点原子】OV5640双目摄像头模块/【正点原子】OV5640双目摄像头模块资料/1，ATK-OV5640双目摄像头模块原理图/ATK_Dual_OV5640_V1.8.pdf)：第 1 页，P1 逐针网络、OV1/OV2 上拉、电源和板载 24 MHz 晶振/LDO。
