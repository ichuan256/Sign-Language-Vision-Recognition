# OV5640 固件与采集入口

最近板端状态统一看 **[当前状态](../../../docs/当前状态.md)**。当前AV HPD候选的720p彩条、静态三栏和实时视觉已实屏确认，codec和ASR已接入过；音频交付及指定语音闭环仍待验收，当前运行/暂停状态只看统一入口。

## 发布包兼容关系

| 发布目录 | 能力与记录范围 |
|---|---|
| [release_av_hpd_20261101](release_av_hpd_20261101/release_manifest.json) | 当前硬件配对；OV1＋HDMI＋音频＋状态诊断，HPD输入；彩条和三栏视觉已确认，听觉联合质量未验收 |
| [release_av_runtime_20261101](release_av_runtime_20261101/release_manifest.json) | 已部署的软件更新清单；bit/HWH同上，仅更新采样调度与JPEG发布；AV运行已恢复，交付率及语音闭环待复验 |
| [release_hdmi_isolation_20261101](release_hdmi_isolation_20261101/release_manifest.json) | 无音频对照；彩条曾实屏确认，已备份；随后同一AV候选也通过，不能据此认定音频硬件导致此前黑屏 |
| [release_av_status_20261031](release_av_status_20261031/release_manifest.json) | 历史状态诊断候选，尚未修正HPD方向，不继续作为当前接管清单 |
| [release_av_20261031](release_av_20261031/release_manifest.json) | 历史首次视听合并候选，三栏无信号记录见现场报告 |
| [release_hdmi](release_hdmi/release_manifest.json) | 历史单目＋HDMI候选，用户曾确认分屏和递增帧号；不含音频/lite关键点核 |
| [release_remove_pl_bad_frame_20261028](release_remove_pl_bad_frame_20261028/release_manifest.json) | 历史纯抓图候选，不含HDMI/音频；移除DVP坏帧几何检测 |
| [release](release/release_manifest.json) | 历史V15纯抓图候选，不含HDMI/音频；不是最近部署 |

各包的bit、HWH、helper和manifest须按自身清单成对使用。双路是另一个[独立发布包](../ov5640_stereo/README.md)。

实时接入使用`demo_stream.py`、`split_hdmi_stream.py`和电脑侧`vision.keypoints`；[单目分屏机制](../../../docs/OV单目HDMI分屏.md)、[视听现场记录](../../analysis/av_three_panel_20261031/README.md)分别保留历史验收和最近故障证据。[HDMI_PREVIEW.md](HDMI_PREVIEW.md)是早期独立本地预览入口，不是最近三栏流程。

## 历史纯抓图使用说明

以下仅说明纯抓图候选，不是最近AV配对的运行命令。它只启动OV1（左目），OV2保持RESET/PWDN，输出1280×720 RGB565小端，每帧1,843,200字节；生成frame.png、frame.raw和capture.json，不含HDMI/音频/识别。

## 使用前提

- 检查所用模块、板卡与 project/analysis/ov5640_stereo_20261026/physical_pin_map_20261027.json 一致。只在断电时接线，确认电源、电平、SCCB 上拉及模块时钟；不要让仍运行的旧 SPI 固件驱动相同引脚。
- 本节使用的历史`release/`为V15，或显式选用对应的纯抓图包；不代表板卡已加载它。bit/HWH/manifest必须匹配，冷启动、真实采图及外部I/O验收须分别核对。
- 抓图前使用新候选的 `release_manifest.json`，并确认 bootpy 的当前 boot/download 标记；不能直接在运行板上再次 Overlay(download=True)。
- --assume-cold-boot 是操作者对已加载候选的明确确认，不是硬件身份检测。文件哈希和 PL 缓存不能证明运行的固件。程序检查元数据和现有 FCLK，但不能独立证明位流身份。

### 板上抓图（仅对应纯抓图候选已冷启动时）

把 release/ 和 capture.py 放到板端同一测试目录。以下命令必须在修复候选已完成冷启动加载后执行：

    cd /home/xilinx/jupyter_notebooks/ov5640_snapshot
    sudo env XILINX_XRT=/usr /usr/local/share/pynq-venv/bin/python capture.py --manifest release/release_manifest.json --output captures/shot_no_bad_frame_001 --assume-cold-boot

每次使用不存在的新输出目录，已有目录拒绝覆盖。成功时查看上述输出目录中的frame.png，从电脑复制即可观察。不提供伪造实拍图；程序仅用Python标准库编码PNG，硬件访问时才导入PYNQ，无需Pillow。

## 失败诊断

- 初始化错误：检查 SCCB、传感器 ID、供电/RESET/PWDN；错误信息保留 status 原值及错误码。
- PCLK heartbeat 超时：检查模块时钟、PCLK 接线；采集超时也可能是 HREF/VSYNC 极性或帧尺寸不符。
- Capture error/overflow：AXI packet/FIFO 路径出错；PL 不报告行宽、行数或奇数字节的几何错误。
- DMA error/短长度：DMA 错误会失败；完成长度由 PS 按像素丢失门限检查。短帧只保存实际接收的 RAW 字节，不补造为完整 720p PNG。
- 所有已启动 DMA 的退出路径必须先完成 DMA soft reset 并确认 Halted，再释放缓冲；若无法确认，CLI保留进程和缓冲且提示先断电。不要在板仍上电时杀进程或 Ctrl+C 退出。

程序先清空缓存、启动 DMA，再 arm 等待下一帧；结束后 invalidate 缓存并按 DMA 实际长度校验与保存。每次程序调用重新初始化摄像头。

## 本机验证与复建

在仓库根执行：

    python -m unittest discover -s project/board/ov5640_snapshot -v
    python project/board/ov5640_snapshot/capture.py --manifest project/board/ov5640_snapshot/release/release_manifest.json --output unused --verify-only

固件工程准备：先运行 project/scripts/ov5640/prepare_snapshot_ps.py，再在 Vivado 2024.1 Tcl 中 source project/fpga/scripts/ov5640_snapshot_prepare.tcl；脚本打印新建隔离工程路径。run_snapshot_build.bat 接受该 .xpr 的完整路径，单并发综合/实现；不再依赖 V: 的错误映射。位流生成门禁在 ov5640_snapshot_emit.tcl。

    project/scripts/ov5640/run_snapshot_build.bat <打印出的完整snapshot.xpr路径> <新的构建证据目录>
    python project/scripts/ov5640/package_snapshot.py --build <上述构建证据目录> --output <新的发布目录>

纯抓图RTL回归入口为project/fpga/scripts/ov5640_snapshot_sim.tcl，V15构建证据在project/analysis/ov5640_color_20261027/build_v15_dvp/。最近AV候选以其自身release_manifest溯源；仿真不包含实际PS DDR/DMA硅片，不等于相机实测。

外部 DVP 输入/RESET 输出延迟没有凭空补值，保留为板级验收事项；内部时序通过只表示已经约束的内部路径满足要求。

构建溯源新门禁：必须从 prepare 脚本创建新工程，记录 build_inputs.json 与 project_inputs.json；旧工程/旧构建没有这些记录时拒绝补填追认。打包必须显式指定 --build；外部时序未完成时仅允许追加 --allow-unverified-io 生成工程候选。
