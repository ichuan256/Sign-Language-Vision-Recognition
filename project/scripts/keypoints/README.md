# 单手关键点 PL 开发工具

所有命令在仓库根运行，输出须使用未存在的新路径。

| 脚本 | 作用 / 环境 |
|---|---|
| `pl_preflight.py` | TFLite 模型/已装转换入口与历史资源检查，r3 环境 |
| `import_tflite_hand.py` | 原权重重建 tf-keras，逐值比对 TFLite；只导出坐标和手存在分数，r3 环境 |
| `prepare_hand_rois.py` | 从已审计视频与已有关键点结果生成本地 ROI 探针，vision 环境 |
| `fixed_hand_reference.py` | 按来源分组校准与整数数值评估，r3 环境 |
| `run_tile_hls.py` | 独立 MAC 分块核 CSim / HLS 综合 / XSim C-RTL，vision 环境 |
| `publish_hand_stage.py` | 汇总小型证据 JSON，不提交权重和 ROI 图片，vision 环境 |
| `pack_hand_model.py` | 将定点候选打包为纯整数权重、bias 和控制参数，vision 环境 |
| `validate_hand_runtime.py` | 编译真实 HLS C 核并执行完整网络，对齐整数参考，vision 环境 |
| `build_vector_hls.py` | 非 MAC 算子的 CSim / HLS 综合 / C-RTL / IP 导出，vision 环境 |
| `build_layer_hls.py` | 整层卷积/专用 depthwise/融合 ReLU 的 CSim、综合、C-RTL、IP 导出 |
| `make_register_map.py` | 从 HLS 生成的驱动头解析寄存器偏移，vision 环境 |
| `run_system_build.py` | 独立 Vivado 工程 inspect / prepare / synth / impl，串行构建 |
| `deploy_hand_board.py` | 校验、备份当前 pair、成对替换并冷重启；默认只准备清单 |
| `run_hand_remote.py` | 执行实际板端 PL 推理、回传输出与延迟、对齐整数参考 |
| `show_hand_result.py` | 将已验证的 PL 坐标叠加到静态 ROI，有界显示 HDMI |
| `publish_hand_board.py` | 从板端输出、实现报告和 HDMI 验收生成紧凑证据 JSON |

当前已通过的实际部署状态见 [第二阶段加速记录](../../analysis/keypoints_pl_20261025/single_hand_acceleration.md)，
驱动和板端入口见 [board/keypoints](../../board/keypoints/README.md)。

典型执行顺序：

```powershell
F:\PLD\.venv-vision\Scripts\python.exe project/scripts/keypoints/prepare_hand_rois.py --output project/_tmp/kp_rois_new
F:\PLD\.venv-r3\Scripts\python.exe project/scripts/keypoints/import_tflite_hand.py --model F:/PLD/.venv-vision/Lib/site-packages/mediapipe/modules/hand_landmark/hand_landmark_lite.tflite --rois project/_tmp/kp_rois_new/rois.npz --output project/_tmp/kp_float_new
F:\PLD\.venv-r3\Scripts\python.exe project/scripts/keypoints/fixed_hand_reference.py --model project/_tmp/kp_float_new/hand_landmark_lite_roi.keras --rois project/_tmp/kp_rois_new/rois.npz --weight-bits 12 --output project/_tmp/kp_integer_new
F:\PLD\.venv-vision\Scripts\python.exe project/scripts/keypoints/run_tile_hls.py --output project/_tmp/kp_tile_new --integer-model project/_tmp/kp_integer_new --rois project/_tmp/kp_rois_new/rois.npz --synth --cosim
```

`run_tile_hls.py` 通过 cmd 调用 Vitis HLS 2024.1，不调用 Hardware Manager，不加载任何 bit。
增加 `--export-ip` 可在通过综合/C-RTL 后导出 MAC IP。
完整网络数值参考、MAC 核 CSim、MAC 核 RTL co-sim 是三个不同门禁，不能互相冒充。
权重/模型从本机原始安装只读导出，派生产物留在忽略的 `project/_tmp/`；本轮没有训练或改媒体。

整网与硬件工程的复跑示例（目录换成新的，HLS IP 路径需与 `keypoints_system.tcl` 中的已验证导出位置一致）：

```powershell
F:\PLD\.venv-vision\Scripts\python.exe project/scripts/keypoints/validate_hand_runtime.py --model project/_tmp/kp_packed_v1 --output project/_tmp/kp_graph_c_new --samples 7
F:\PLD\.venv-vision\Scripts\python.exe project/scripts/keypoints/run_system_build.py inspect --output project/_tmp/kp_system_new
F:\PLD\.venv-vision\Scripts\python.exe project/scripts/keypoints/run_system_build.py prepare --output project/_tmp/kp_system_new
F:\PLD\.venv-vision\Scripts\python.exe project/scripts/keypoints/run_system_build.py synth --output project/_tmp/kp_system_new
# 先核对综合资源，再进入实现
F:\PLD\.venv-vision\Scripts\python.exe project/scripts/keypoints/run_system_build.py impl --output project/_tmp/kp_system_new
```

不要把原工程打开和新工程创建放进同一个 Vivado 进程；导出 Tcl 后退出再 prepare。
构建过程中不要启动其他 Vivado 综合/实现。`constraints_resume` 仅用于已停止的隔离工程补齐旧 W6
时序配置并重置顶层运行；`--attempt` 用于保留不同重试日志，不覆盖失败证据。
所有候选都须通过 routed setup/hold、时钟方法学和实际板端数值门禁；已有旧接口告警边界见当前记录。

整层版本：主机验证加 `--layer`；`build_layer_hls.py --export-ip` 导出层核后，
`run_system_build.py prepare --layer-ip <导出 impl/ip>` 选择该核，`make_register_map.py --layer-ip <同一路径>`
生成 `whole_layer_v2` 寄存器映射。不要混用旧分块固件和新寄存器文件。
板端测速可用 `run_hand_remote.py --repeat 3`，同进程复用模型和缓冲区，逐次核对完整输出。

`show_hand_result.py` 只显示静态验收 ROI。连续动态演示用 `python -m vision.keypoints.dynamic_pl`，
具体命令见 [板端说明](../../board/keypoints/README.md)；两种入口不能混称视频实时追踪。
