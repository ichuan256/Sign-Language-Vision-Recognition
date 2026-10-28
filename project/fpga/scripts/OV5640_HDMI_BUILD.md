# OV5640 snapshot + HDMI 独立构建

在无工程打开的 Vivado 2024.1 Tcl 会话中运行：

```tcl
source project/fpga/scripts/ov5640_snapshot_hdmi_prepare.tcl
```

入口在 `project/_tmp/ov5640_snapshot_hdmi_20261028` 下创建独立 `vivado/snapshot.xpr`，已存在时递增版本目录。可在 source 前设置 `snapshot_out` 为仓库内新的 `project/_tmp/…` 路径。主 W6 工程不修改，不下载位流。

采集保留 `capture_dma`（`0x40400000`）、`camera_control`（`0x41200000`）和 HP0 写 DDR；新增标准 `video/hdmi_out` 层级与 `video/axi_vdma`，HP2 读 DDR。AXI 与参考时钟全部用 FCLK0 100MHz；层级内部的 `clk_142M` 仅沿用旧名称。动态像素时钟独立生成，AXIS SOF 的 TUSER 宽度固定为 1。显示缓冲是 RGB888，PS 负责把捕获的 RGB565_LE 转换后提交。

保持 W6 显示寄存器地址：VDMA `0x44A00000`、dynclk `0x44A10000`、VTC `0x44A20000`、color_convert `0x40010000`、HPD GPIO `0x40020000`、pixel_unpack `0x40030000`。显示中断经 concat 接入 PS，供 HWH/PYNQ 元数据识别。驱动需采用现有 MM2S-only OutputVDMA 适配。

prepare 在生成 target 后禁用 rgb2dvi 原有错误的 PixelClk→SerialClk 声明，保留原语推导时钟与 OOC/CDC 约束；新的 HDMI XDC 只约束输出使能和转发时钟。原相机 pre-opt 约束、SCCB 结构门禁和 build/emit 保持使用。

prepare 完成后，可在同一会话中按顺序执行下列命令。长命令返回运行中或 MCP 调用超时时，先查询会话状态，不要重复启动：

```tcl
launch_runs synth_1 -jobs 1
wait_on_run synth_1
launch_runs impl_1 -to_step route_design -jobs 1
wait_on_run impl_1
open_run impl_1
set evidence [file normalize project/_tmp/ov5640_hdmi_build_new]
source project/fpga/scripts/ov5640_snapshot_emit.tcl
```

每个 `launch_runs`/`wait_on_run`/`open_run`/`source` 通过 MCP 单独调用。必须检查综合状态为 `synth_design Complete!`、实现状态为 `route_design Complete!`；emit 会检查内部时序、DRC、CDC、SCCB 和构建溯源后才生成固件。证据目录不得已有同名 bit。也可关闭工程后用原 `run_snapshot_build.bat <snapshot.xpr> <新证据目录>` 入口重建；优先使用 Vivado MCP。

发布仍使用 `project/scripts/ov5640/package_snapshot.py --build <new-evidence-directory> --output <new-release-directory> --hdmi-output`。当前相机外部 I/O 时序尚未签核，只有明确接受未签核候选时才加 `--allow-unverified-io`。文件名继续是 `ov5640_snapshot.bit/.hwh`，HDMI 能力由发布 manifest 描述。

prepare 前必须完成所有被 provenance 绑定的 RTL、Tcl、IP、采集/预览与打包脚本修改；中途修改后要重新 prepare。构建通过仍需冷启动加载成对文件，以及显示颜色、画面运动、采集/显示并发和持续运行验证。运行中禁止重新下载位流。
