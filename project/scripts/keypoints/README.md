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
| `plan_realtime_hand.py` | 只读分析旧图，生成 96/128 学生模型的 MAC/容量与双手预算，不预测板端 FPS |
| `build_hand_student.py` | r3 环境构建未训练学生网络，逐层核对形状和 kernel 数；不训练、不部署 |
| `prepare_student_manifest.py` | vision环境；校验551素材池SHA，固定原片分组并抽取教师工程试跑清单 |
| `export_hand_teacher.py` | vision环境；重新运行Holistic，导出手部ROI/伪标签与未知区域、离线人工复核工具 |
| `prepare_hand_review.py` | vision环境；绑定候选元数据SHA，重筛清晰度、来源和时间门禁下的复核队列，不创建人工标签 |
| `audit_hand_reviews.py` | 校验返回的人工JSONL、原片SHA及裁剪像素；保留原件，挂起指定疑点，生成原裁剪不变的预填复核页 |
| `train_hand_student.py` | r3环境；固定来源划分、掩码损失、浮点蒸馏，人工精度和教师一致性分别报告 |
| `evaluate_hand_student.py` | r3环境；独立评测已保存模型，输出点位对照图与掩码指标 |
| `overfit_hand_student.py` | r3环境；只用人工训练ROI做固定XY拟合诊断，含输入打乱、BN模式对照及独立重载；不评测泛化 |
| `prepare_raw_video.py` | vision环境；从已核验片段生成有界720p raw短循环包，不修改原视频 |
| `run_raw_video.py` | 校验并暂存raw包，接管既有HDMI缓冲做板端吞吐测试；不加载bitstream |

当前已通过的实际部署状态见 [流式加速记录](../../analysis/keypoints_pl_20261026/stream_wide.md)，
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

缓存/流式候选复跑时，`validate_hand_runtime.py --stream` 与 `build_layer_hls.py --stream --export-ip`
会同时启用缓存、宽访存和生产者/消费者流水线；单独 `--cached` 保留已测缓存版。
`make_register_map.py --layer-ip <该轮IP> --vector-ip <fast-vector-IP> --vector-capacity 65536 --stream`
记录 64 字节参数对齐，板端逐层参数池补齐且检查所有传入地址。
旧寄存器表不得搭配新流式固件；宽度上限 128bit 不代表每个 AXI 端口都实际达到 128bit。

独立实时路线见 [专题方案](../../../docs/方案/03_Zynq7020独立实时关键点方案.md)。结构/预算复现：

```powershell
F:\PLD\.venv-vision\Scripts\python.exe project/scripts/keypoints/plan_realtime_hand.py --graph project/_tmp/kp_stream_model_v2/graph.json --baseline project/analysis/keypoints_pl_20261026/stream_wide.json --output project/_tmp/realtime_budget_new
F:\PLD\.venv-r3\Scripts\python.exe project/scripts/keypoints/build_hand_student.py --output project/_tmp/hand_student_new
```

`hand_student_v1.json` 仅定义候选；导出文件带 `UNTRAINED` 标记。形状验证不是精度、量化或 HLS 验收。

教师试训已实际执行，当前数据边界及结果见[试跑记录](../../analysis/keypoints_student_20261026/README.md)。
教师是MediaPipe模型，教师未检出区域保持未知，不能自动当无手负例。人工复核以`--reviews <JSONL>`显式覆盖，
必须有复核者、`annotation_origin=human`和`human_verified=true`；没有确认的负样本时禁用presence训练。
旧200项队列低清占比过高，不再作为本轮入口；新20帧队列与步骤见[清晰复核说明](../../analysis/keypoints_student_20261026/清晰复核说明.md)。
不需要逐帧标注全部录像，先做3～5帧校准流程；无法判断样本清零掩码，不当作无手。
最新17项人工结果已冻结导入，96/128已复训；当前结果见[训练记录](../../analysis/keypoints_student_20261027/README.md)。
`roi_rejected`或`roi_status=wrong`的记录不会成为无手标签；原裁剪/坐标不自动变换。

本轮旧数据复训使用`--mask-outside-source --disable-presence`：前者屏蔽投影到原画外的教师点，
不改原标签或人工坐标；后者因训练负例仅1条而关闭presence损失，并排除只提供辅助判断的图片，
避免零损失图片影响BN。新教师导出默认写画外点掩码；复现旧报告时不要隐式加新策略。
评测同样加`--mask-outside-source`，指尖误差沿用完整可见手包围框对角线归一化。
BLAS线程默认1；本机并行评测曾分配内存失败，当前批次串行运行，不更改系统环境。

6条人工训练ROI的拟合诊断已通过，复跑命令和证据见[诊断记录](../../analysis/keypoints_student_20261027/overfit6.md)。
固定输入与模型带`OVERFIT_DIAGNOSTIC`标记，不覆盖正式试训模型，也不读取留出集指标作选择。

```powershell
# 以下为工程闭环示例；输出目录均须是新的。正式标注前先完成清晰度与来源配额重筛。
F:\PLD\.venv-vision\Scripts\python.exe -X utf8 project/scripts/keypoints/prepare_student_manifest.py --output vision/data/manifests/teacher_plan_new.json --max-clips 40
F:\PLD\.venv-vision\Scripts\python.exe -X utf8 project/scripts/keypoints/export_hand_teacher.py --plan vision/data/manifests/teacher_plan_new.json --output project/_tmp/teacher_new --fps 5
F:\PLD\.venv-r3\Scripts\python.exe -X utf8 project/scripts/keypoints/train_hand_student.py --data project/_tmp/teacher_new --output project/_tmp/student_train_new --epochs 60 --sizes 96 128
F:\PLD\.venv-r3\Scripts\python.exe -X utf8 project/scripts/keypoints/evaluate_hand_student.py --model project/_tmp/student_train_new/hand_student_96_FLOAT_PILOT.keras --data project/_tmp/teacher_new --output project/_tmp/student_eval_new
```

整层版本：主机验证加 `--layer`；`build_layer_hls.py --export-ip` 导出层核后，
`run_system_build.py prepare --layer-ip <导出 impl/ip>` 选择该核，`make_register_map.py --layer-ip <同一路径>`
生成 `whole_layer_v2` 寄存器映射。不要混用旧分块固件和新寄存器文件。
板端测速可用 `run_hand_remote.py --repeat 3`，同进程复用模型和缓冲区，逐次核对完整输出。

`show_hand_result.py` 只显示静态验收 ROI。连续动态演示用 `python -m vision.keypoints.dynamic_pl`，
具体命令见 [板端说明](../../board/keypoints/README.md)；两种入口不能混称视频实时追踪。
