# 教师网络局部迁移：状态与证据（2026-10-28）

当前执行见 [04 方案](../../../docs/方案/04_老师模型PS_PL局部迁移.md)，PS 入口见 [老师说明](../../board/teacher_hands/README.md)。
当前包含模型静态核验、[P0 基线/诊断](p0.md) 及 [P1 后处理/边界验证](p1.md)。没有新的 PL 加速或部署验收结果。

P1 的两轮各 120 帧配对中，PS 后处理优化使平均处理约 1.57→1.01 秒/帧，全部网络输出及跟踪状态一致。
100 个真实 ROI 的边界捕获、单块和双块独立重放均逐值一致；CMA 复制/缓存维护约 1.386ms。
当前选择相邻双块作为一个连续分区的接图候选，待测 XNNPACK 拆分和实际 PL 成本；不需要人工标注或训练。
最新证据 [p1.json](p1.json)，原单块参数清单 [partition_manifest.json](partition_manifest.json)，历史核验 [p0_verification.json](p0_verification.json)。

| 模型 | 文件字节 | SHA256 | Conv/DW MAC |
|---|---:|---|---:|
| palm_detection_full | 2,339,846 | 1b14e9422c6ad006cde6581a46c8b90dd573c07ab7f3934b5589e7cea3f89a54 | 337,333,248 |
| hand_landmark_full | 5,478,917 | 11c272b891e1a99ab034208e23937a8008388cf11ed2a9d776ed3d01d0ba00e3 | 330,821,344 |

源文件在 project/board/teacher_hands/，P0/P1 已核对在线板卡模型 SHA 与本地一致；板端状态以每次实测前后快照为准。
[model_inventory.json](model_inventory.json) 保存所有节点 ID、输入输出张量/形状、Conv/DW 参数、MAC 与存储类型。
模型常量主要以 FP16 存储，激活和 DEQUANTIZE 输出为 FP32，不代表本方案采用 FP16 算术。

普通卷积计 N×OH×OW×CO×KH×KW×CI，DW 计 N×OH×OW×CO×KH×KW，一次乘累加记一 MAC；
不计 FC、ADD、激活和运行时开销。使用本机 r3 TensorFlow schema 解析，没有训练或改模型。
本机脚本留在 project/_tmp/inspect_teacher_plan_20261028.py；跨机器复核以模型 SHA 和 JSON 的形状/节点重新计算，不把临时脚本当运行入口。

## 候选

landmark 87/90/93/94 为 Conv→DW→Conv→Add，入口 134、出口 138 均为 1×14×14×112 FP32。
Conv/DW 共 32,796,288 MAC，另有 21,952 次残差加法；动态边界 175,616 字节，FP32 参数约 675,136 字节，
中间 tensor 135/136 各 526,848 字节。P1 将相邻 97/100/103/104 一并作为一个连续分区候选，出口改为 142，边界字节数不增加。
单块/双块的运行时边界及独立 CPU 重放已验证；实际 delegate 接图、PL 访存/计算和完整净收益仍待测。
编号间穿插 DEQUANTIZE，不将 87～94 的编号范围直接当作无依赖的连续列表。

静态依赖检查确认：外部入口包括动态 tensor 134 与六个参数 tensor 171/189/196/200/236/261，
外部出口仅 tensor 138。此处为原单块静态清单；双块及运行时边界 SHA 见 P1，实际分区接入仍待验证。

## 历史基线边界

project/_tmp/teacher_board_20261027_v1/benchmark_report.json 记录 2 线程零输入，palm 约 550ms、landmark 约 490ms，
各重复 5 次；运行库 SHA 为 18f9b3c16f84b1ea2e09f8cb5b85ffa204a90155639fe3d19940bb47a317107e。
零输入不是视频基准。短视频中存在帧数不足或 completed=false 的记录，均不作为新方案正式验收值。
旧 lite 整网 PL 约 490ms/ROI 与 full CPU 数字接近，但模型和范围不同，不能由此算加速比。

## 清理证据

[document_cleanup.json](document_cleanup.json) 记录第一批 16 份入口/历史文档的清理前后 SHA。
移除当前入口的学生计划、过期状态和训练启动示例；日期实验数值保留并标记停用。
首批文档清理没有删除媒体、模型、标注或 RTL/HLS 源码，没有覆盖其他会话未提交的代码；该阶段没有构建或部署。
后续新增/更新的 04 方案、老师说明及本页以 Git diff 为准，不把文档整理当成加速已完成。

[verification.json](verification.json) 汇总本轮 Markdown 的本地链接/围栏检查、两模型 SHA、
Conv/DW 总量及候选边界/参数字节的独立复算结果；不包含板端性能或硬件验收。
