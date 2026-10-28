# 关键点工具入口

更新：2026-10-28。当前任务仅为 [PS 教师网络的 PL 局部加速](../../../docs/方案/04_老师模型PS_PL局部迁移.md)。
PS 老师在 [board/teacher_hands](../../board/teacher_hands/README.md)；已完成的静态图核验见
[模型清单](../../analysis/teacher_partition_20261028/README.md)。P0 基线与 [P1 后处理/边界验证](../../analysis/teacher_partition_20261028/p1.md) 已执行；新 delegate 与 FP32 子图核尚待实现，不能把下面的旧整网脚本当作新流程。

## 已实现的本轮工具

| 工具 | 作用 |
|---|---|
| `run_teacher_p0.py inspect/build-probe/baseline/status/postprocess` | 只读核对、隔离诊断库构建、有界原库基线、进度与原后处理计时；不训练、不加载 FPGA |
| `freeze_teacher_partition.py` | 按 full 模型 SHA 导出原子图参数与依赖；没有拟合、量化或校准 |
| `analyze_teacher_p0.py` | 区分原库、XNNPACK 与内置算子诊断，汇总计时、数值差异及推断收益上限 |
| `run_teacher_p1.py postprocess/boundary/transfer` | 隔离后处理配对、100 ROI 边界/CPU 重放、实际 CMA 复制与缓存微基准；transfer 不加载 overlay |
| `prepare_teacher_replay.py` | 提取原单块/双块的诊断 CPU 子图，精确展开原常量；不是部署替代模型 |
| `analyze_teacher_p1.py` | 核验逐帧摘要、真实边界、原参数与板端不变项，汇总新基线和迁移敏感性预算 |

板端脚本 `teacher_p0_board.py` 与 C++ `teacher_probe.cpp` 位于 `project/board/teacher_hands/`。
每次运行必须使用新的 `project/_tmp/` 输出目录；板端实验同样隔离，不覆盖原模型或运行库。
P1 的 `boundary` 需要新建的边界诊断库 `--probe` 和 `--replay-models` 目录。
`transfer` 使用 XRT 实际报告的 PSDDR 目标；必要时用 `--sudo-password-prompt` 隐藏读取凭据，不在命令行、文件或报告中保存密码。
当前 P0/P1 对比脚本绑定原部署 geometry SHA；不要覆盖冻结目录再把新版后处理当成旧基线。

## 当前执行顺序

1. P0：核对板端 full 模型/运行库/固件 SHA，固定输入与线程，采集真实视频 PS 基线和算子剖析。
2. P1：冻结一个候选子图的完整依赖、边界张量和权重，核算计算与传输净收益。
3. P2：在原 TFLite 图中接入一个 delegate 分区，先用显式 CPU 测试实现验证边界。
4. P3：FP32 核 C/RTL、代表尺寸综合、整板实现与成对冷部署，再验收端到端收益。

新脚本名称、产物与门禁详见 04 方案；本文不提供尚未实现的启动命令。

## 可参考的历史工具

| 工具 | 可参考部分与限制 |
|---|---|
| `prepare_raw_video.py`、`run_raw_video.py` | 有界视频准备、原片 SHA 和 HDMI 接管；写帧吞吐不等于推理速度 |
| `pl_preflight.py`、`import_tflite_hand.py` | 旧模型检查/重建经验；不用于更换当前 full 老师或删输出头 |
| `fixed_hand_reference.py`、`pack_hand_model.py`、`validate_hand_runtime.py` | 旧整数整网协议与 C 对照；不适用于本轮 FP32 delegate |
| `run_tile_hls.py`、`build_vector_hls.py`、`build_layer_hls.py` | cmd 调用、C/RTL 和报告归档；原核/测试向量属于旧整数图 |
| `run_system_build.py`、`make_register_map.py` | 隔离工程、串行构建和寄存器解析；新核须独立配置，不能复用旧映射 |
| `deploy_hand_board.py`、`run_hand_remote.py` | 成对核验、冷部署和时延记录经验；原驱动执行旧 lite 整网，不是 full 老师子图 |
| `publish_hand_stage.py`、`publish_hand_board.py` | 紧凑证据汇总格式 |
| `show_hand_result.py`、`vision.keypoints.dynamic_pl` | 历史静态/动态展示；存在 PC ROI 输入，不作为本轮板端自主验收入口 |

## 停用路线

`plan_realtime_hand.py`、`build_hand_student.py`、`prepare_student_manifest.py`、`export_hand_teacher.py`、
`prepare_hand_review.py`、`audit_hand_reviews.py`、`train_hand_student.py`、`evaluate_hand_student.py`、
`overfit_hand_student.py`、`fixed_student_reference.py`、`prepare_ceiling_review.py` 以及学生 HLS 工程
均不再作为当前任务执行入口。已删除本页的学生训练、扩数据和 QAT 启动示例；代码与实验原件保留。

不要运行旧脚本恢复学生路线。不要将旧 64 项、学生 65 项协议接到 full 老师四输出链路。
当前 bit/hwh 必须按所选发布清单现场核对，不根据历史文档直接重载或部署。
