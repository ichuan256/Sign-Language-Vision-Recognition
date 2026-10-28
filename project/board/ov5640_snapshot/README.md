# OV5640 OV1 单路抓图候选

> 工作区清理后，`release/` 为原 V15 本地候选，bit SHA256 `486a6c68523d18cbbe76d1b8b7edfba74e59194bacbb90a95a9df2cac1a82bbc`。V14及以前的发布包、构建和历史诊断记录已移到 Windows 回收站；当前构建与溯源证据保留在 `project/analysis/ov5640_color_20261027/build_v15_dvp/`。目录整理没有部署或重启板卡，候选状态不变。

> 2026-10-28，移除 DVP 坏帧几何检测的新候选位于 `release_remove_pl_bad_frame_20261028/`，已部署到板端固定启动目录并由冷启动加载一次。bootpy 显示 FCLK0=100 MHz；板端哈希、manifest/HWH 校验通过。外部 DVP I/O 时序和真实相机采图尚未验收；构建与部署证据见 `project/analysis/ov5640_snapshot_20261028/deployment.md`。板端上一版文件保存在 `.backup_remove_pl_bad_frame_20261028/`。



独立测试固件，只启动 OV1（左目），OV2 保持 RESET/PWDN。输出 1280×720 RGB565 小端，每帧 1,843,200 字节；板端生成 frame.png、frame.raw 和 capture.json。此固件不含 HDMI/音频/识别。

## 使用前提

- 检查所用模块、板卡与 project/analysis/ov5640_stereo_20261026/physical_pin_map_20261027.json 一致。只在断电时接线，确认电源、电平、SCCB 上拉及模块时钟；不要让仍运行的旧 SPI 固件驱动相同引脚。
- 本地 `release/` 仍是原 V15 候选；当前板卡已冷启动加载 `release_remove_pl_bad_frame_20261028/` 对应的新候选。bit/HWH/manifest 必须成对使用；真实摄像头、PS DDR DMA 集成和外部 I/O 时序仍待板上验收。
- 抓图前使用新候选的 `release_manifest.json`，并确认 bootpy 的当前 boot/download 标记；不能直接在运行板上再次 Overlay(download=True)。
- --assume-cold-boot 是操作者对已加载候选的明确确认，不是硬件身份检测。文件哈希和 PL 缓存不能证明运行的固件。程序检查元数据和现有 FCLK，但不能独立证明位流身份。

## 板上抓图（候选已通过上述冷启动加载后）

把 release/ 和 capture.py 放到板端同一测试目录。以下命令必须在修复候选已完成冷启动加载后执行：

    cd /home/xilinx/jupyter_notebooks/ov5640_snapshot
    sudo env XILINX_XRT=/usr /usr/local/share/pynq-venv/bin/python capture.py --manifest release/release_manifest.json --output captures/shot_no_bad_frame_001 --assume-cold-boot

每次使用一个不存在的新输出目录；已有目录拒绝覆盖。成功时查看 captures/shot001/frame.png；从电脑复制该 PNG 即可观察图像。没有板上实拍前，不提供假 PNG。程序只用 Python 标准库编码 PNG，硬件访问时才导入 PYNQ；无需 Pillow。

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

RTL 回归入口 project/fpga/scripts/ov5640_snapshot_sim.tcl，仿真工程可重新打开。V14及以前的历史回归输出已移入回收站；保留当前RTL与软件测试入口，可按需重新运行。当前构建证据在 project/analysis/ov5640_color_20261027/build_v15_dvp/。仿真不包含实际 PS DDR/DMA 硅片，也不等于相机实测。

外部 DVP 输入/RESET 输出延迟没有凭空补值，保留为板级验收事项；内部时序通过只表示已经约束的内部路径满足要求。

构建溯源新门禁：必须从 prepare 脚本创建新工程，记录 build_inputs.json 与 project_inputs.json；旧工程/旧构建没有这些记录时拒绝补填追认。打包必须显式指定 --build；外部时序未完成时仅允许追加 --allow-unverified-io 生成工程候选。
