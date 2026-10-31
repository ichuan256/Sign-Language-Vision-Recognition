# 视听三栏接入 · 2026-11-01

运行状态统一见[当前状态](../../../docs/当前状态.md)。本轮使用AV HPD候选，bit b3d53bb0…、HWH 8c454fd0…，boot `8eb07956-cc57-43f6-a252-cb0c4e106eb5`。全程复用HDMI owner PID1237、start ticks12657及显存0x15e00000，没有重新配置视频前端或下载位流。

## 已确认与待完成

- 静态三栏写入同一显存后，用户确认“三栏清楚可见”；见`static_write.json`、`static_three.png`和`physical_feedback.json`。
- 控制台AV模式已运行OV1采集、PC冻结Holistic教师回传、板端LINE IN及PC ASR面板；用户确认“三栏可见，左右画面会更新”。这是视觉实屏确认，不代表语音逐句准确性或关键词定位精度。
- 首轮run为`/home/xilinx/ov1_hdmi_20261031/captures/ui_1793471536522120500`；绘制PID6176。PC控制日志在`project/_tmp/demo_control/20261031_221537/`，对应worker目录为`single_hdmi_1793471535366540000/`。
- 曾观测到ASR返回文本、5个播放任务完成、398个视频帧。尚未得到用户对指定真实话语、字幕、对应手语视频和视觉同时更新的闭环确认，不作为完整听觉验收。
- 联合音频初步交付约2.6万样本/秒；把绘制/音频HTTP放CPU0、PCM采样放CPU1并设普通调度nice=-12后，短窗口约3.8万样本/秒，仍低于声明48000Hz。无硬件样本序号，不宣称无丢样。原始采样见`observe_*.jsonl`，调度变更见`scheduling_*.json`。
- 网页预览曾读到正在写入的JPEG，出现部分解码画面；它与用户实屏三栏正常的事实分开记录。已部署临时文件编码后原子替换的修正，修正后的预览效果尚待复验。

## 软件更新与恢复运行

控制台曾正常切到idle完成软件更新，HDMI owner保留最后一帧。`runtime_1793472780504782300/applied.json`记录新采样器在板端以gcc -O2 -Wall -Wextra编译通过，无编译警告；源文件和原二进制已备份至板端`/home/xilinx/av_runtime_20261101/1793472780504782300/backup/`。更新包括AV进程CPU分工、PCM采样可选CPU绑定和普通优先级、避免正常采样热循环调用时钟、JPEG原子发布。源码改动前本机副本在`project/_tmp/av_integration_20261101/source_before_tuning/`，12项现有面板/控制测试通过。

运行时发布包为`project/board/ov5640_snapshot/release_av_runtime_20261101/`，bit/HWH与原AV HPD候选完全相同，manifest更新软件和板端二进制SHA。板端二进制SHA为c42d2c7f…；没有重启、下载位流或重配HDMI，owner仍为PID1237、显存0x15e00000。

更新后控制台已恢复AV模式，busy=false、error=null。新运行目录为`/home/xilinx/ov1_hdmi_20261031/captures/ui_1793472945994267000`；最新本机单调时钟37702.5秒的API采样中，教师返回19次结果、来源帧号141，音频真实采样计数926400且接收时间戳继续更新。旧final、completed、video_frames计数跨启停保留，不作为本轮新增语音成功的证据。持续采样交付率、修正后网页预览及指定真实语音闭环尚待复验；原始采样保存在`observe_*.jsonl`。

教师模型、输入尺寸、预处理、词表和固件均未修改。中栏教师和ASR仍在电脑计算，板端负责采集、合成、显示与音频接口；没有新增PL教师推理。
