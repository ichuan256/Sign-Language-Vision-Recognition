# FPGA 与板端模块

- [R3 当前状态](analysis/r3/README.md)：量化训练、CSim 和 HLS 综合证据。
- [R3 复跑脚本](scripts/r3/README.md)
- [移植清单](M0_移植清单.md)、[已发布固件](board/w6/README.md)

`fpga/`、`algo/`、`board/` 保留原硬件工程的内部布局；工程入口为
`fpga/project/glove/glove.xpr`。`board_validation/` 保留板端验收证据。
`_tmp/` 汇总运行日志、训练缓存及生成的 HLS 工程；`_cache/` 放本地工具缓存，二者不入库。

此次目录迁移只做路径与静态检查，没有重新综合、实现、下载固件或操作板卡。
旧 Vivado/HLS 生成缓存仍可能带有历史绝对路径，不能视作迁移后已验收构建。
