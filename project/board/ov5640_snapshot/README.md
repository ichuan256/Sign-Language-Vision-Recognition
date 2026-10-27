# OV5640 OV1 单路抓图候选

独立测试固件，只启动 OV1（左目），OV2 保持 RESET/PWDN。输出 1280×720 RGB565 小端，每帧 1,843,200 字节；板端生成 frame.png、frame.raw 和 capture.json。此固件不含 HDMI/音频/识别。

## 使用前提

- 检查所用模块、板卡与 project/analysis/ov5640_stereo_20261026/physical_pin_map_20261027.json 一致。只在断电时接线，确认电源、电平、SCCB 上拉及模块时钟；不要让仍运行的旧 SPI 固件驱动相同引脚。
- 本目录 release/ 是同批 bit/HWH 和 SHA256 清单；旧 W6 发布文件不被替换。当前固件是 candidate_board_unverified，真实摄像头、PS DDR DMA 集成和外部 I/O 时序仍待板上验收。
- 必须先安排候选固件在冷启动阶段只加载一次，设置 FCLK0=100MHz，再运行抓图程序。需协调现有固件加载/音频/HDMI服务；本次没有部署、重启或更改服务。不能直接在现有固件上执行 MMIO，不能在运行板上再次 Overlay(download=True)。
- --assume-cold-boot 是操作者对已加载候选的明确确认，不是硬件身份检测。文件哈希和 PL 缓存不能证明运行的固件。程序检查元数据和现有 FCLK，但不能独立证明位流身份。

## 板上抓图（候选已通过上述冷启动加载后）

把 release/ 和 capture.py 放到板端同一测试目录。以下目录是示例测试目录，不是已经部署的位置：

    cd /home/xilinx/ov5640_snapshot
    sudo env XILINX_XRT=/usr /usr/local/share/pynq-venv/bin/python capture.py --manifest release/release_manifest.json --output captures/shot001 --assume-cold-boot

每次使用一个不存在的新输出目录；已有目录拒绝覆盖。成功时查看 captures/shot001/frame.png；从电脑复制该 PNG 即可观察图像。没有板上实拍前，不提供假 PNG。程序只用 Python 标准库编码 PNG，硬件访问时才导入 PYNQ；无需 Pillow。

## 失败诊断

- 初始化错误：检查 SCCB、传感器 ID、供电/RESET/PWDN；错误信息保留 status 原值及错误码。
- PCLK heartbeat 超时：检查模块时钟、PCLK 接线；采集超时也可能是 HREF/VSYNC 极性或帧尺寸不符。
- Capture error/overflow：帧不完整或 FIFO 堵塞，不能当作成功图像。
- DMA error/短长度：保存失败，不写成功 PNG。程序要求 capture_done、无硬件错误、DMA IOC/Idle、精确字节数同时满足。
- 所有已启动 DMA 的退出路径必须先完成 DMA soft reset 并确认 Halted，再释放缓冲；若无法确认，CLI保留进程和缓冲且提示先断电。不要在板仍上电时杀进程或 Ctrl+C 退出。

程序先清空缓存、启动 DMA，再 arm 等待下一完整帧；结束后 invalidate 缓存并保存。每次程序调用重新初始化摄像头。

## 本机验证与复建

在仓库根执行：

    python -m unittest discover -s project/board/ov5640_snapshot -v
    python project/board/ov5640_snapshot/capture.py --manifest project/board/ov5640_snapshot/release/release_manifest.json --output unused --verify-only

固件工程准备：先运行 project/scripts/ov5640/prepare_snapshot_ps.py，再在 Vivado 2024.1 Tcl 中 source project/fpga/scripts/ov5640_snapshot_prepare.tcl；脚本打印新建隔离工程路径。run_snapshot_build.bat 接受该 .xpr 的完整路径，单并发综合/实现；不再依赖 V: 的错误映射。位流生成门禁在 ov5640_snapshot_emit.tcl。

    project/scripts/ov5640/run_snapshot_build.bat <打印出的完整snapshot.xpr路径>
    python project/scripts/ov5640/package_snapshot.py --output <新的发布目录>

RTL 回归入口 project/fpga/scripts/ov5640_snapshot_sim.tcl，仿真工程可重新打开。证据在 project/analysis/ov5640_snapshot_20261027/：packet 边界/错误、SCCB与小帧集成、完整两帧720p与真实FIFO溢出；软件测试覆盖RGB565/PNG、hash/HWH、DMA启动顺序、超时/错误清理和缓冲保留。仿真不包含实际 PS DDR/DMA 硅片，也不等于相机实测。

外部 DVP 输入/RESET 输出延迟没有凭空补值，保留为板级验收事项；内部时序通过只表示已经约束的内部路径满足要求。
