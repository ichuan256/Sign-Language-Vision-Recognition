# FPGA 与板端模块

- [OV5640 → HDMI 720p](board/ov5640_snapshot/HDMI_PREVIEW.md)：相机采集与 HDMI 的本地固件/预览软件已构建，内部时序和配对校验通过；2026-10-28 本轮板卡未开机，实际显示待验收。[验证记录](analysis/ov5640_hdmi_20261028/README.md)。

- [单手关键点 PL 实施](analysis/keypoints_pl_20261025/single_hand_stage1.md)：用户已确认单手先行；模型转换与 MAC 核 C/RTL 验证已完成，完整关键点网络未上板。
- [R3 当前状态](analysis/r3/README.md)：量化训练、CSim 和 HLS 综合证据。
- [R3 复跑脚本](scripts/r3/README.md)
- [移植清单](M0_移植清单.md)、[已发布固件](board/w6/README.md)

`fpga/`、`algo/`、`board/` 保留原硬件工程的内部布局；工程入口为
`fpga/project/glove/glove.xpr`。`board_validation/` 保留板端验收证据。
`_tmp/` 汇总运行日志、训练缓存及生成的 HLS 工程；`_cache/` 放本地工具缓存，二者不入库。

此次目录迁移只做路径与静态检查，没有重新综合、实现、下载固件或操作板卡。
旧 Vivado/HLS 生成缓存仍可能带有历史绝对路径，不能视作迁移后已验收构建。
