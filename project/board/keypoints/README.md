# 单手关键点 PL 驱动

`hand_runtime.py` 的硬件路径只在 PS 做索引、分块、DDR 复制和输出尺度还原，全部神经网络算子调用
`kp_mac` / `kp_vector`。`DLLBackend` 是显式命名的主机验证后端，不是板端回退。
`run_hand_board.py` 先核对候选 bit/hwh、新 boot ID 和 bootpy 已完成，再以 `download=False` 接管。
核超时直接报错，不切换到 CPU。

当前实际数值与时延见 [流式加速记录](../../analysis/keypoints_pl_20261026/stream_wide.md)：
PC ROI→PL 单手 21 点，12.28→1.86→0.56→0.49 秒/ROI；三次重复逐值对齐，仍未达到 5Hz。
该入口尚不是任意视频实时识别。`hand_layer_runtime.py` 实现整层调度、参数常驻及卷积链输出地址复用，
旧 `HardwareBackend` 仍用于首版固件，不能混用寄存器映射。

## 部署与运行

主机工具位于 [scripts/keypoints](../../scripts/keypoints/README.md)。以下路径均为本机当前证据示例，
复跑时须选新输出目录。密码只由临时 `KEYPOINT_BOARD_SUDO_PASSWORD` 环境变量传入，禁止写到文件、命令行参数或日志。
部署默认只准备候选；只有显式 `--apply` 才会备份、替换并冷重启。

```powershell
F:\PLD\.venv-vision\Scripts\python.exe project/scripts/keypoints/deploy_hand_board.py --build project/_tmp/kp_stream_system_v2b --model project/_tmp/kp_stream_model_v2 --output project/_tmp/kp_stream_deploy_new --apply
# 等待新 boot ID、bootpy exited、成对哈希匹配；绝不运行中下载 bit
F:\PLD\.venv-vision\Scripts\python.exe project/scripts/keypoints/run_hand_remote.py --deployment project/_tmp/kp_stream_deploy_new --reference project/_tmp/kp_stream_model_v2/probes.npz --output project/_tmp/kp_stream_result_new --repeat 3
```

输出 `report.json` 含逐层时间与核调用数，`alignment.json` 含整网对齐和延迟，`output.npy` 含 63 坐标＋presence。
同一 ROI 的重复试验只是数值/时延试验，不增加独立样本数。首次进程初始化耗时与前向耗时分别记录。

## 连续视频，不是静态验收图

```powershell
F:\PLD\.venv-vision\Scripts\python.exe -u -m vision.keypoints.dynamic_pl --deployment project/_tmp/kp_stream_deploy_v2 --probes project/_tmp/kp_rois_v1 --output project/_tmp/kp_dynamic_pl_new --seconds 600 --fps 15
```

该命令循环播放一个 SHA 匹配的已知视频，使用既有 PC ROI 轨迹裁剪；板端 `stream_hand_board.py`
在同一进程复用实际 PL 图，SSH 只传 ROI 和 64 个结果，不重复初始化，不加载 bit。
视频线程与推理线程分开，待处理 ROI 仅一个，旧请求丢弃。输入和响应 SHA、源帧号均校验。
左侧是持续运动视频及黄色 PC ROI 框；右侧是上次实际 PL 输入与结果，不把旧姿态重锚到当前视频。
姿态年龄明确显示，PC 发布目标 15fps、当前 PL 并发前向约 0.51～0.57 秒/ROI，HDMI 刷新率另计；不称作自主实时追踪。

已有动态目视验收见 [动态快照](../../analysis/keypoints_pl_20261025/dynamic_replay.json)。
运行有界 10 分钟，到时最后一帧会留在屏幕。`live.json` 是进度观测，最终 `report.json`
在退出后生成；不要仅凭遗留画面或历史观测文件断定进程仍在运行。

## 固件边界与恢复

候选固件保留了旧 W6 HDMI、音频、按键和闲置模块；本轮验收范围只有单手 PL 推理与 HDMI，未宣称音频回归完成。
旧 W6 本地发布文件保持原样，旧演示的固件哈希检查仍可拒绝候选；不要为绕过检查重载 FPGA。
HDMI 验证可用 `--release-manifest project/analysis/keypoints_pl_20261026/stream_wide.json` 显式接受这份成对哈希，
不会修改全局已接受列表。

部署记录 `project/_tmp/kp_stream_deploy_v2/deployment.json` 保存了板端上一版 0.56 秒固件的备份位置；
更早 W6 固件备份仍在 `project/_tmp/kp_board_deploy_v2/deployment.json` 指向的位置。
如需恢复，先核对备份两份哈希，与原 pair 一致后再成对恢复到启动路径并重启一次；
禁止运行中 `Overlay(download=True)`，禁止修改 boot.py 或调用旧 base.bit 脚本。
恢复会中断板端画面，应按 AGENTS.md 的危险操作约定执行。
