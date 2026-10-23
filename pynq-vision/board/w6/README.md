# W6 HDMI 收尾记录（2026-10-18）

## 当前基线

目标为 Zynq-7020（xc7z020clg400），现有工程使用 Vivado 2024.1。
原已点亮基线于 2026-10-18 10:07:50 完成 bitstream，10:08:10 导出，
已保存到 `baseline_20261018_visible/`。当前版本为时钟约束修正版，
12:06:45 完成构建与导出，已部署、正常重启并恢复 720p 输出；
用户目视确认“已亮，画面稳定”。

交付文件必须成对部署：`kws_hdmi.bit` 和同名 `kws_hdmi.hwh`。
已逐一核对它们与当前实现目录 bitstream、当前生成的 HWH 哈希相同；
详见 `release_manifest.json`。该核对证明本地文件一致，不代替板上版本核对。

## 黑屏根因与修复

`pixel_unpack -> axis_register_slice_0 -> color_convert -> frontend/vid_out`
的视频链中，寄存器片默认 `TUSER_WIDTH=0` 切断 SOF，导致
`color_convert/stream_in_24_TUSER` 在生成网表中接常量 0。
`fpga/scripts/w6_hdmi_bd.tcl` 已包含幂等修复，显式设置该参数为 1。
当前生成网表确认 TUSER 和 TLAST 均从 unpack 经寄存器片、转换器传入 frontend。

HLS C++ 读取完整 pixel，修改 data 后写出完整 pixel，并未主动清除 user。
但现有 color_convert 导出包的 component.xml 将接口 TUSER_WIDTH 标为 0，
同时又映射了实体 TUSER 端口；这是需保留的接口元数据差异。
本轮沿用已出图的 BD 补偿方案，没有手改生成包或重新综合 HLS。
重新导出 HLS 或升级工具后，必须再次通过网表检查，不可只看 C++ 接口。

## 复现与防回归

版本边界：本次 W6 沿用旧 HLS KWS 合一工程，寄存器协议与 main 新的
`kws_mlp_accel` 不同。发布固件用于本次 HDMI 验收，不代表包含 main 后续的
传感器量程、映射或 RTL KWS 更新。下列脚本作用于已存在的 HLS 合一工程；
从空目录重建 W6 的完整项目生成流程尚未验收，当前 main 的 W4 生成脚本
也不能直接替代该前置工程。旧 KWS HLS 源码现位于 `archive/kws_hls/`。

1. 准备已有的 W6 HLS 合一工程并打开其中的 system BD，再执行
   `fpga/scripts/w6_hdmi_bd.tcl`，应用 SOF 及已有时钟、复位补丁。
   当前仓库不跟踪 `fpga/project/glove/glove.xpr`；`fpga/project/w5_pose4_build/`
   是另一条 W5 生成工程，不能当作 W6 工程替代。没有外部 W6 工程时，本文只提供
   已发布 bit/HWH、时序证据和板端验收记录，不宣称 W6 可从空目录重建。
2. 执行 `fpga/scripts/w6_hdmi_build.tcl`。现在构建会先检查寄存器片宽度，
   再检查生成网表 SOF/EOL 各跳连接；发现旧配置或常量断路会在综合前退出。
3. 构建成功后将本目录同名 bit/hwh 一起部署到板上 `/home/xilinx/`。
   沿用已有启动流程，每次冷启动由 boot.py 加载一次 overlay。
4. 当前无中断验收入口是 `hdmi_display.py`：接管已加载 overlay，手动绑定仅输出
   VDMA，持续持有帧缓冲并显示 1280×720、24 位测试画面。
   必须目视确认屏幕画面；程序返回不代表显示验收通过。

批处理入口使用相对于脚本的位置定位仓库。先把 Vivado 2024.1 加入 PATH，
或设置 `VIVADO_BAT` 为本机 Vivado 2024.1 的完整路径，再运行
`fpga/scripts/run_w6_hdmi.bat` 与 `run_w6_hdmi_build.bat`。

仅输出设计存在驱动自动绑定与中断解析限制，验收入口使用无需中断等待的
手动 VDMA 绑定；不再发布旧的轮换 overlay、短时显示或阻塞读写诊断入口。
已有记录显示运行中重载 overlay 可能使板重启，验收脚本采用 download=False。

## 验证边界与待办

2026-10-18 补充：本次会话用户已目视确认原基线“深色底色、蓝色矩形”，
HDMI 出图通过。颜色与预设不同，暂未校正；不能仅凭观察断定具体映射原因。
新增 `hdmi_display.py` 持续持有帧缓冲，避免短脚本退出后缓冲区被回收。
时序修复构建现在写入 `timing_candidate/`，不直接覆盖本目录已点亮基线；
进度和预算边界见 [时序审计](../../analysis/timing_20261018/README.md)。

当前路由报告 WNS=0.451 ns、TNS=0、WHS=0.017 ns、THS=0。
TIMING-4、TIMING-27、TIMING-36 已修复，并已重新实现与上板验证。
SPI/音频已补慢速外部时钟、完整 min/max 延迟和 CE 多周期约束；
未约束内部端点与缺失输入延迟均为 0。保留的 TIMING-18 延迟关联告警、
三条 TMDS 数据线缺少接收端参数、旧 UART 空端口约束等见时序审计记录。
这些边界未被屏蔽，仍不能宣称整机全部 I/O 已完成签核。

视频流沿用上一轮切换后的 100 MHz 域，`clk_142M` 名称为历史名称。
本次没有恢复 142 MHz，也没有验证 1080p、长时间稳定性或音频/KWS 并发。
已完成正常重启后自动加载和恢复显示，尚未测试断电再上电。
这些属于下一轮系统验收，不能由单次出图推断通过。
