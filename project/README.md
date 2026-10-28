# FPGA 与板端模块

- [当前方案：PS 老师网络的 PL 局部加速](../docs/方案/04_老师模型PS_PL局部迁移.md)
- [PS full 老师运行入口](board/teacher_hands/README.md)、[模型图与候选证据](analysis/teacher_partition_20261028/README.md)
- [开发工具入口](scripts/keypoints/README.md)
- [历史 lite 整网 PL 实测](analysis/keypoints_pl_20261026/stream_wide.md)：不是 full 老师局部加速结果。
- [历史 R3 分类器](analysis/r3/README.md)、[移植验收](M0_移植清单.md)、[W6 固件](board/w6/README.md)

`fpga/`、`algo/`、`board/` 保留硬件布局；原工程为 `fpga/project/glove/glove.xpr`。
新候选使用隔离工程、独立寄存器映射及发布清单，不修改冻结 RTL。
`_tmp/` 放运行日志与生成工程，`_cache/` 放本地工具缓存，二者不入库。

本轮不重新训练学生或推进其 HLS。尚未建立新 delegate/浮点子图核，也未构建或部署新的局部加速固件。
