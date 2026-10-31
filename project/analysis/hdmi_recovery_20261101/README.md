# HDMI 恢复过程与实屏证据 · 2026-11-01

最新进展：同一AV候选的彩条、静态三栏和实时视觉均已实屏确认；音频联合验收和软件更新仍在进行，见[三栏接入记录](../av_integration_20261101/README.md)及[当前状态](../../../docs/当前状态.md)。以下按先后顺序保留过程，旧boot、PID、无信号与未启动描述只适用于当时窗口。

## 最初接线诊断（历史窗口）

最初用户说明当时接法为 **板卡 HDMI OUT 直接接笔记本 HDMI 口**。该接法不能作为显示器输入验收，也不能用 Windows 未出现外接显示器推断板卡 HDMI 损坏；之后已接回独立显示器。

只读现场结果：

- 电脑：LENOVO 83F4，SystemFamily / Version 为 Legion Y9000P IAX10。
- Windows 当前仅枚举内置 `DISPLAY\SDC420B`，友好名 Lenovo DisplayHDR；WmiMonitorConnectionParams 的 VideoOutputTechnology 为 2147483648（内部显示）。
- Camera / Image 及名称包含 capture、采集、USB Video 的设备筛选仅发现 Integrated Camera；没有枚举到 HDMI 采集设备。
- 板卡 boot_id 仍为 `a105798e-9796-4819-9070-06b6b4729513`，本轮 `ps` 证实彩条 owner PID 1928 存活，观察时 elapsed 2305 秒。其标记文件仍为 active=true，但本轮未读取 DMA 寄存器，因此不以标记宣称真实输出成功。
- 前一轮重新核验 bit/HWH 哈希与 `release_av_hpd_20261101` 一致，`/boot/boot.py` SHA256 仍为 `f96330498c2f488ae043d4d5e3b4a3e3eec313e2c3754481bee111eb190cd625`。
- 本轮没有下载位流、重启、停止进程或修改启动项。尚无新的实屏成功结果。

下一步正确连接：板卡 J11 HDMI OUT → 独立显示器 HDMI IN。若要使用笔记本预览，应接板卡 HDMI OUT → HDMI 采集卡输入 → USB → 笔记本；笔记本 HDMI 输出口不作为采集输入。

用户此前曾反馈“电脑能正常显示”，随后说明当前是板卡直连电脑；两项反馈保留，尚需明确同屏同线的电脑输出对照是否实际完成。不能将本次输出对输出的连接当作那个对照。

参考：[对应 83F4 的联想用户指南入口](https://iknow.lenovo.com.cn/detail/422828)、[同系列官方指南 HDMI 用途说明](https://download.lenovo.com/pccbbs/pubs/legion_pro7_16_10/user_guide/en/index.html)。

辅助只读入口：`project/scripts/hdmi_readonly_diagnose.py`。先前本机终端尝试未通过 sudo 认证，`probe_1793466658931836100/samples.jsonl` 为空；不能把该目录当作新的寄存器采样证据。该工具通过隐藏输入读取密码，仅经 SSH stdin 传递，不保存凭据。

## 接回屏幕后继续排查

用户确认接回屏幕，仍黑屏，随后明确屏幕提示“无信号”。与旧记录不同，此次 **HPD_n=0**，已经检测到屏幕，不能继续沿用此前 HPD_n=1 的结论。

1. `probe_1793467029200770400/samples.jsonl`：配对哈希及 boot.py SHA 再次通过；720p owner PID1928 身份匹配；90次、间隔2秒的采样中 HPD_n 均为0、MMCM/video_out均锁定，无FIFO错误，VDMA状态0x11000、采集DMA Halted。只读采样正常结束。
2. `relock_1793467206059910400/result.jsonl`：保持同一 owner 和帧地址，重新触发原有动态时钟配置，完成后配置寄存器未变、内部重新锁定，用户仍反馈无信号。没有加载位流或重启。
3. `vga_1793467417290292600/result.jsonl`：720p显存四个取样点的BGR值依次为 `[255,255,255]`、`[0,0,255]`、`[0,255,0]`、`[255,0,0]`，内容正确。向经身份核验的PID1928发送SIGINT，确认进程退出且VDMA Halted后，启动同一固件下的640×480彩条。
4. VGA owner为PID22650，物理帧地址0x15a00000，使用新目录 `/home/xilinx/ov1_hdmi_20261031/vga_recovery_1793467417290292600/` 中从当前HPD适配helper派生的脚本，没有改原helper。用户仍反馈黑屏。`probe_1793467579989570700/samples.jsonl`显示HPD_n=0、MMCM锁定、video_out未锁定、无FIFO错误；不能把此次模式初始化成功当作VGA输出通过。
5. `cold_cycle_1793467717697662300/preflight.jsonl`：同候选重启方案只读预检通过，bit/HWH、boot.py和原720p helper SHA匹配，无其他硬件worker。此预检未停机或重启。
6. 用户明确授权“允许，安全停止后正常重启”。执行入口为 `project/_tmp/hdmi_recovery_20261101/cold_cycle.py --execute`，只在确认原owner退出及两路DMA Halted后正常重启；使用现有启动脚本在新boot加载一次同一候选，后续helper仍使用download=False。没有更换固件或修改启动项。执行结果以新建的 `cold_cycle_*/preflight.jsonl`、`new_boot.jsonl` 为准；没有成功结果文件不能视为重启或恢复已通过。

当前仍无已确定根因。HPD低只说明接屏检测建立，内部锁定、显存正确和写帧计数均不能替代TMDS物理输出或实屏验收。

## 正常重启结果与后续核查

`cold_cycle_1793467835983893300/preflight.jsonl`证实旧owner安全退出、采集DMA状态1与输出VDMA状态69633（0x11001）均为Halted，然后发出正常重启。SSH被重启断开，首版自动脚本将该退出视为失败而提前结束；随后增加明确的`--resume-from`接续入口，只接续核验和输出启动，不再次重启。

`cold_cycle_1793467947595704500/new_boot.jsonl`：新boot `c53952b2-56cd-4545-b989-2039c708b9d0`，同候选配对哈希、boot.py及720p helper通过核验；新owner PID1134、start ticks12788、帧地址0x15c00000，1280×720。状态0x04000186、flags179：HPD_n=0，MMCM和video_out均锁定，无FIFO错误，VDMA状态0x11000。用户反馈仍黑屏，故此次正常重启未恢复实屏。

用户补充屏幕独立供电，此前多次正常显示并完成正常功能，合并后出现故障。后续以合并回归为重点，不把目前无信号直接归咎于屏幕或线材。

PS HWH全参数差异核查：新增I2C1并选EMIO，I2C外设目标频率字段改变，其余PS参数未变；旧单目包和当前包的I2C0均标禁用，MIO48~53配置未改变。板端Linux仍枚举I2C0（e0004000）和I2C1（e0005000）；这些元数据不能代替实际MIO状态核查。

`tmds_netlist_01/connections.txt`及`clocks.rpt`为Vivado2024.1打开当前routed.dcp后的只读检查结果：四对TMDS均为OBUFDS输出、TMDS_33和原引脚；时钟serializer为10位DDR，CLK来自动态时钟BUFIO、CLKDIV来自BUFR、OCE为1、RST来自LockLostReset，时钟串行数据为5个0接5个1。HPD为R19输入。该检查没有综合、重新实现、生成位流或编程，不代表实板引脚波形已经测得。

## 用户更正与完整备份实物比较

用户于2026-11-01明确说明，历史22:08“已恢复彩条”为误输入，实际未恢复。撤销依赖这条反馈的“旧版回退恢复”“屏幕断电重插恢复”和“旧版成功/新版失败”对照推论；保留合并前分屏正常的独立记录。原始反馈在`screen_feedback.json`中保留，并标为不可用于验收。

已只读取回板端`backup_before_av`与当前部署，保存在`backup_compare_1793469575911180500/before/`和`after/`；逐文件及全HWH参数报告为该目录`comparison.json`，源码差异在`diffs/`。备份和活动文件均未修改。

| 项目 | 实物比较结果 |
|---|---|
| 旧bit/HWH | 分别为37189d24…、47628383…，与旧备份manifest及本地release_hdmi完全匹配 |
| 当前bit/HWH | 分别为b3d53bb0…、8c454fd0…，与当前manifest及本地HPD候选完全匹配 |
| /boot/boot.py | 旧备份与当前逐字节一致，SHA f9633049… |
| capture、continuous_capture、hdmi_preview | 规范LF后及Python AST均一致 |
| 彩条初始化程序 | 当前仅比旧备份多HPD输入适配判断，跳过旧GPIO写高；首次合并时该程序未改 |
| 共同HWH模块参数 | 仅PS7的7个I2C相关参数及control_bus的NUM_MI（3→5）改变；共同视频模块无参数差异 |
| 新增硬件 | 音频IP、音频时钟及5个诊断模块；物理HPD方向后续由输出修正为输入 |
| 三栏与音频软件 | 存在真实源码变化；当前纯彩条无信号时未运行三栏绘制和采音，不能直接归因三栏绘图 |

另发现溯源资料不一致：旧板端备份未包含manifest引用的build_provenance.json；当前板端该文件SHA为288b96a6…，不符合当前manifest要求的602b348e…。bit/HWH自身配对均通过，此元数据残留不能直接解释物理黑屏，但后续部署应同步完整发布资料。

目前可确认整份FPGA固件和部署软件在合并时改变，不能确认某一个新增IP或某项显示端行为就是根因；不会把源码/参数相同解释为实际输出已经通过。

## 无音频对照候选：已构建，已授权切换

隔离工程`project/_tmp/ov1_hdmi_no_audio_20261101/vivado/snapshot.xpr`已串行完成综合、实现及位流生成，发布包为`project/board/ov5640_snapshot/release_hdmi_isolation_20261101/`。WNS1.244ns、WHS0.021ns；现有门禁检查通过，DRC无Error、CDC无Critical。外部I/O及实屏仍未验收。

- bit SHA256：`e7b78376ea3555efed570d5790d68c6e47d409073f00dcc54b6b8b26ef9040bc`。
- HWH SHA256：`7ff8d8d65683445a1de460b3d5d4ddcaf55d8861fc3e225fa35987b6186e668a`。
- 对当前HPD候选的共同视频、相机、DMA及诊断模块参数比较均无差异；仅删除`audio_codec_ctrl_0`和`clk_wiz_audio`及其接口，关闭PS I2C1，控制互连少一个输出口。保留R19输入和0x41210000诊断。
- 使用当前源码创建新的原生工程，不复制旧runs；未改教师模型或RTL算法。初次综合因沙箱拒绝WSH子进程而未启动，确认旧等待进程退出后在沙箱外串行续跑。
- 准备入口`project/_tmp/hdmi_recovery_20261101/deploy_isolation.py --candidate <发布包>`仅暂存、核验和备份；`--execute-plan <proposal>`会安全停止owner、确认两路DMA Halted，成对切换发布目录并正常重启，必须另行获得用户部署授权。

用户随后明确回复“可以”，授权上述冷部署。`isolation_1793470065562692900/action.json`记录再次核验旧boot c53952b2…、owner PID1134及候选配对哈希后，安全停止owner、确认两路DMA状态分别为1和69633（Halted），切换完整发布目录并请求正常重启。`/boot/boot.py`未改，没有运行中重载位流；原活动发布目录另存于暂存目录下`active_release_before_swap/`，完整备份仍在`backup_release/`。

Windows SSH在重启断开时返回了脚本未接受的退出码，首段自动脚本提前结束。增加`--resume-plan`入口后，只接续等待新boot、核验新配对文件并启动彩条，不再次切换或重启。新boot和实屏结果以该接续目录的`new_boot.json`及用户反馈为准，不能仅据`reboot_requested=true`宣布冷部署验收完成。

## 最新结果：无音频候选彩条已实屏恢复

`isolation_1793470158028262300/new_boot.json`记录新boot为`d4bf5a68-8212-4f81-8e7a-1c731d10e833`，同上无音频候选bit/HWH已核验，启动文件SHA未变。彩条owner PID1187、start ticks12213、帧地址0x15f00000，1280×720。16次采样状态0x04000186、flags163/179、VDMA0x11000：HPD_n=0、MMCM/video_out锁定，无FIFO错误。

用户随后明确选择 **“出现白、红、绿、蓝四条彩条”**。此为当次无音频候选的实屏证据，与此前已撤回的误输入无关；当时相机和三栏未接回、固件无音频接口。之后已恢复AV并接入三栏，不能使用本段旧owner作为当前身份。

当时据对照推测排查范围缩至AV合并的集成/实现差异；该推论随后因用户补充供电条件不确定而撤回，见下节。无音频候选的实屏确认本身保留。

## 供电条件补充与AV复测授权

用户随后提出“可能是刚才屏幕没有通电，再试一下”，并明确选择“恢复含音频固件测彩条”。这是供电条件可能不一致的补充，尚未证实此前屏幕确实断电；既不能据原对照锁定音频硬件集成，也不能直接认定屏幕未通电是唯一根因。

按新授权保持屏幕通电，恢复同一AV HPD候选（bit b3d53bb0…、HWH 8c454fd0…），只启动720p彩条，不同时启动相机、codec采音或三栏。使用本地完整AV发布包，bit/HWH与此前备份一致，同时包含manifest匹配的build_provenance文件，避免复制板端旧批次溯源残留。保留当前无音频完整发布包作为备份。入口`retest_av_powered.py`复用已审阅的安全停机、配对切换、正常重启及新boot核验流程；不运行中重载位流。

复测准备`isolation_1793470604238595100/action.json`：确认当前d4bf5a68…启动中的owner PID1187存活，备份当前无音频发布包于`/home/xilinx/hdmi_no_audio_20261101/isolation_1793470604238595100/backup_release/`；新暂存AV的bit/HWH及构建溯源SHA均通过。执行`isolation_1793470698204692100/action.json`记录用户授权、两路DMA Halted（1、69633）、完整目录切换及正常重启请求。启动文件未改，新boot及实屏结果待下述接续记录。

## AV彩条复测结果（之后已进入三栏联调）

`isolation_1793470698204692100/new_boot.json`：新boot `8eb07956-cc57-43f6-a252-cb0c4e106eb5`，bit b3d53bb0…、HWH 8c454fd0…与原AV HPD候选一致。bootpy成功完成；彩条owner PID1237、start ticks12657，帧地址0x15e00000，1280×720。16次采样状态0x04000186、flags163/179、VDMA0x11000，HPD_n=0、MMCM/video_out锁定，无FIFO错误。codec、相机、采音和三栏均未启动。

按“屏幕保持通电”条件询问后，用户明确回答 **“能看到四条彩条”**。独立验收记录为同目录`display_acceptance.json`。原合并候选本身具备正常固定图物理输出能力，保留当前owner及显存，下一步逐级原位接入功能。

因此撤销“只有移除音频硬件后才恢复”及“故障已缩至AV硬件集成/实现”的归因。用户补充的是此前屏幕**可能**未通电，历史供电状态未经测得，不能由本次成功倒推唯一根因。当次仅验收彩条；后续三栏实时视觉确认见最新接入记录，指定语音联合闭环仍待验收。
