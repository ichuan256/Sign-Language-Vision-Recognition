# 视听三栏现场记录 · 2026-10-31至11-01

> 本文按发生顺序保存历史排查过程，旧boot、PID和无信号结果不是当前状态。后续同一AV HPD候选的彩条及三栏实时视觉已实屏确认，见[最新接入记录](../av_integration_20261101/README.md)和[当前状态](../../../docs/当前状态.md)。指定语音闭环及联合质量仍待验收。

目标：HDMI 左栏 OV1 原始实时画面，中栏对应来源帧的教师关键点叠加，右栏板卡 LINE IN → PC 流式语音识别 → 字幕及手语视频。三条显示区域独立更新，右栏播放不能阻塞左栏取景。本文故障阶段当时尚未通过实屏；后续三栏视觉已确认，真实语音联合验收单独记录，不能把写帧计数当作成功显示。

已实现 `av_layout.py` 三栏合成、`audio_loop.py` 原子发布的 `/panel.jpg` 与元数据、控制台 `av` 模式、视听 SSH 隧道及显式匹配合并固件的板端音频服务。教师模型及输入未更改，没有训练或新增 PL 关键点推理。中栏计算仍由 PC 的冻结 Holistic 教师完成。

首版候选为 `project/board/ov5640_snapshot/release_av_20261031/`：bit SHA256 `355c08eda3329c07fce6936d495f1d52151697b557f9796c3ebfb23ffbd1828e`；hwh SHA256 `6fa4b01568e1e236b4273773ef6bdb22b5ab4d0013caa8d1e137f6652e1286b6`。仅在隔离工程整合既有音频 IP；实现 WNS 0.816 ns、WHS 0.018 ns，布线无错误。此包已被后续诊断候选替换，构建通过不能代替实屏验收。

## 排查时间线（历史步骤）

1. 用户确认新合并固件三栏无画面，暂停采集及听觉识别后，纯彩条仍无信号。音频配置完成后重新启动输出，也未恢复。
2. 检查显存四条颜色、色彩矩阵、VTC Core Enable、输出地址和帧完成标志。显存正确，清除 VDMA IOC 后重新出现完成标志；只能说明数据送帧仍在继续，不能证明物理 HDMI 信号正常。
3. 只读检查已布线 DCP：帧起始 TUSER 沿 VDMA → pixel_unpack → register_slice → color_convert → video_out 传递，没有常量驱动；输出引脚与旧方案一致。未因 IP XML 的 TUSER_WIDTH=0 元数据而盲改 RTL 或重新构建。
4. HDMI 输出使能短暂拉低再恢复，用户仍确认无信号。
5. 按此前授权的失败恢复方案，确认两路 DMA Halted 后恢复旧单目＋HDMI 配对文件并正常重启。旧固件 bit SHA `37189d24a396326dd849a55ed135dd3c97287ada3a2a0c562d2718cae7610beb`，启动周期 `4458b5f4-4fb9-4e5b-b217-d70345b21455`，彩条 owner PID 1003、地址 `0x15e00000`。用户仍报告无信号。
6. 保持板卡及同一输出进程，曾记录屏幕断电约十秒、重新插紧HDMI后的反馈为“已恢复彩条”。**用户于2026-11-01明确更正：该反馈是误输入，实际未恢复彩条。** 原反馈仅保留作追溯，不再作为实屏验收或“显示端重新锁定后恢复”的证据；相关推论撤销。
7. 已安全停止上述 owner，并正常重启以恢复同一视听合并候选。新启动周期 `bf1907da-f7b9-47ea-a7ed-e30c75f834d9`；先配置音频，再启动 720p 彩条 owner PID 2604。用户重开屏幕及单独拔插 HDMI 后仍确认无信号；原进程中重新触发动态时钟配置已完成，也未恢复。旧版回退和合并候选在该阶段均没有有效实屏恢复记录，不能构造“旧版恢复、新版失败”的成功/失败对照。
8. 安全停止 720p owner、确认 Halted 后，以同一固件尝试标准 640×480 彩条，owner PID 7441、帧地址 `0x15a00000`，用户仍确认无信号。清除 VTC 生成器帧中断标志后，50ms 内重复读到新帧中断；清除 VDMA IOC 后也再次出现完成标志。VTC 和送帧在继续，仍缺视频输出核的实际同步状态。
9. JTAG枚举未发现目标。当时在隔离工程准备只读诊断候选，新增`video_status_gpio`（0x41210000）及XPM采样，观测status、MMCM/video_out锁定及FIFO错误，不改原有功能连接。此时尚未构建或上板；后续构建与部署结果见步骤10、12。
10. 首版诊断候选完成布线后，CDC 检查发现原 `video_out locked` 发射寄存器同时进入 IP 内部同步器和新增诊断同步器，产生两项 CDC-11，已阻止生成位流。新版为诊断 tap 增加源域寄存，保持原视频内部连接；使用 Vivado 2024.1 原生 IP 缓存重建，而非手工复制生成的 runs。首版失败检查保留在 `project/_tmp/ov1_av_status_build_20261031/`，新版在同名 `_v2` 目录。
11. 当时彩条owner PID16865到一小时上限并安全退出，记录`active=false, Halted=true`；该阶段boot为`bf1907da-f7b9-47ea-a7ed-e30c75f834d9`，摄像头和语音暂停。控制/画面协议16项测试通过；语音服务已加载新统计代码，停止解码补零不再计入真实采样，模型与词表未变。
12. 新版诊断候选已生成并冷部署，WNS1.047/WHS0.011ns、CDC无Critical。bit SHA `e1a7c81eeeed41d9f8cb98d960d73cb7db1c012c126b2d1c9ae82edee5ed990e`，hwh SHA `054e93ba8bd0031e21413e4910e8bbb16c228b1c186ac2425de435023baac065`；新boot `98f9b392-6b7c-4aa9-b0fb-677b4d54372c`。彩条 owner PID3201，在先配置音频后启动。`status_color_output.json`显示16次采样MMCM与video_out均锁定、无overflow/underflow，用户仍确认无信号。内部同步通过不等于物理HDMI通过。
13. 对照原厂资料发现继承自W6的方向错误：R19是反相热插拔检测输入`HDMI_TX_HPDN`，却被作为GPIO输出。旧`HDMI_enable`字段只是该输出值，不能当作使能或接屏证据。当时将旧输出置低并准备输入修正；保留旧AXI GPIO地址，物理R19改为只连诊断采样，字段为`HPD_n`。完成结果见步骤14，不能断言它是黑屏唯一原因。
14. HPD修正候选完成构建及冷部署，bit `b3d53bb0586818f9f1ae7e1908547d7a99d4707a8ba9b64b1da3618d82d61f27`，hwh `8c454fd0e20b68ef0f37212a44cf85345397c4955560117b08fc400649496b6b`，WNS1.379/WHS0.014ns、CDC无Critical；boot为`a105798e-9796-4819-9070-06b6b4729513`。当时仅启动固定彩条owner PID1928，codec未配置，麦克风/相机/三栏未启动。`hpd_fixed_output.json`及接回J11开屏后的`hpd_after_connection_confirmed.json`均显示内部锁定、无FIFO错误，HPD_n持续为1；用户确认仍无信号，未做电脑同屏同线对照。修正没有单独解决黑屏；owner有一小时上限，继续操作必须重新核对存活。
15. 用户要求比较正常旧版与当前版本，已完成板端备份与活动软件比较、HWH全参数比较及共同源文件规范化核验。HDMI初始化文件当时逐字节相同；三个采集helper仅换行差异；HDMI参数及视频HDL无逻辑差异；31个共同源文件SHA差异全部来自LF/CRLF。首次三栏实质增加音频IP/时钟并重新实现整机，同时变更显示并发软件。详见 `working_vs_active_software.json`、`working_vs_candidates.json`、`common_source_differences.json`及[对比说明](../../../docs/视听三栏_旧版对比_20261101.md)。
16. 只读复核已部署HPD候选的routed DCP：物理端口 `hdmi_out_hpd[0]` 为IN、PACKAGE_PIN=R19、缓冲为IBUF；诊断bit6第一级同步器D的驱动确为该IBUF输出。不是把旧GPIO输出误读成HPD输入。证据 `diagnostics/hpd_input_route.txt`。当前外部接屏检测未建立，仍需同屏同线接电脑的对照结果；不把这一读数直接断言成线未插或屏幕损坏。

全过程未运行中二次下载位流，未修改 `/boot/boot.py`，没有强杀 DMA owner。板端备份在 `/home/xilinx/av_three_panel_20261031/backup_before_av/`；冷部署及恢复记录分别保留在该目录及本机 `project/_tmp/av_three_panel_20261031/`。启动周期与当前进程必须现场读取，历史 PID 不作当前身份依据。

## 软件观测的边界

`live_verification.json` 是先前黑屏期间的真实运行计数，**不是成功实屏验收**。该窗口完整采集约 2.26 帧/秒、左栏新画面约 1.53 次/秒、缓冲区写入约 4.52 次/秒、给 PC 发帧约 1.02 帧/秒；都不是 HDMI 扫描率或 PL 教师推理速度。

原始统计曾给出约 15882 样本/秒，但其分母包含末次板端 SSH 快照等待，低估了音频速率，该数字已停用。按音频自身时间戳重算：393600 个样本、18.234 秒，约 **21586 样本/秒**，详见 `audio_joint_delivery_correction.json`。接口声明格式仍是 48000 Hz PCM16；联合交付不足，不能称为无丢样 48 kHz 采集。真实说话、字幕命中、手语播放及视觉同时更新仍须单独验收。语音停止时用于流式解码收尾的补零不能计入真实采集样本。

在相机与 ASR 均未启动时，板端 PCM 接口预热两块后交付 57600 个样本，耗时 1.1824 秒，约 48715 样本/秒。它是短时交付观测，不能替代联合负载或无丢样验证。联合负载下降的具体调度和传输原因尚待拆分测试。

诊断字段依据 [AMD PG044 Common Interface](https://docs.amd.com/r/en-US/pg044_v_axis_vid_out/Common-Interface)；`status[8]` 为 Fine Align Locked，`status[31:16]` 为 VTG Lag。XPM 数组对各位独立同步，不能将一次读取的多位状态视为原子快照或 ILA 波形；仅解释重复稳定的状态与独立标志。

HPD方向依据 [PYNQ-Z2原厂参考手册](https://dpoauwgwqsy2x.cloudfront.net/Download/pynqz2_user_manual_v1_0.pdf) 第13节表7及[原厂原理图](https://dpoauwgwqsy2x.cloudfront.net/Download/TUL_PYNQ_Schematic_R12.pdf) 第6页；R19为反相HPD输入，不能由FPGA作为输出驱动。后续使用 `hdmi_hpd_input=true` 的新候选，颜色输出程序跳过历史GPIO写高操作。

`layout_preview.jpg` 仅为布局预览。`latest.jpg` 是当时板端合成内容，均不等同于实屏照片。
