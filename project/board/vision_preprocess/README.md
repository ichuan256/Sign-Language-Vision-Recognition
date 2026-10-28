# PL 预处理 FP32 V2 RTL 验证

旧 RGB888 输出与 PS 归一化支路已删除，当前三组 XSim 和 Python 回归见 [清理验证](../../analysis/vision_preprocess_fp32_cleanup_20261028/README.md)。

FP32 实现的原始四组 XSim、Python、独立资源/时序及保留告警核对见 [2026-10-28 验证记录](../../analysis/vision_preprocess_fp32_20261028/README.md)。当前活动源码仅支持 V2 FP32，包含 normalizer、sampler、AXI wrapper 三组自检；旧支路清理后的验证另行记录。当前仍是独立模块版本，未部署到板卡。

此目录定义 PS 端参数生成、整数参考实现和 Python 接口。V2 在 PL 完成 RGB888 到精确 float32/255 的归一化，输出可直接作为 RGB NHWC tensor 的缓冲视图；192×192 为 442368 字节，224×224 为 602112 字节。输入 RGB565、仿射与双线性舍入规则不变。PL RTL 与自检 testbench 分别位于 `project/fpga/rtl/vision_preprocess/` 和 `project/fpga/tb/vision_preprocess/`。重建由 Tcl 明确列出输入文件，不依赖本机 `.xpr`；生成的项目、向量和 Vivado 报告留在 `project/_tmp/` 与 `project/analysis/`，不作为源文件提交。

## 从干净工作区运行

要求 Vivado 2024.1（目标器件 `xc7z020clg400-1`）和 Python 3.9+、NumPy。OpenCV 是可选依赖；安装后向量生成会额外执行量化 remap 对照，可用 `--require-opencv` 要求该对照必须运行。每次使用新的运行标记：向量目录须不存在，Vivado 项目目录须是新目录且其中不得有同名 `.xpr`。

在仓库根目录的 PowerShell 中生成独立向量：

```powershell
$run = Get-Date -Format 'yyyyMMdd_HHmmss'
python .\project\scripts\vision_preprocess\generate_vectors.py `
  --output ".\project\_tmp\vision_preprocess_vectors_$run"
```

启动 Vivado Tcl 会话后，在 Tcl Console 中设置同一个 `$run` 对应的绝对路径并执行准备脚本。以下目录必须此前不存在：

```tcl
set vp_root {C:/path/to/Sign-Language-Vision-Recognition}
set vp_project_dir [file join $vp_root project/_tmp/vision_preprocess_run_YYYYMMDD_HHMMSS]
set vp_vectors [file join $vp_root project/_tmp/vision_preprocess_vectors_YYYYMMDD_HHMMSS]
source [file join $vp_root project/fpga/scripts/vision_preprocess_prepare.tcl]
```

把示例中的 `vp_root` 和两个运行标记替换为本机仓库路径及刚生成的同一标记。PowerShell 的 `$run` 变量不会传入 Vivado Tcl，两个 Tcl 目录中的时间标记需手动填入该变量值。准备完成后运行 lint 和三个 XSim 自检 testbench：

```tcl
set vp_evidence [file join $vp_root project/analysis/vision_preprocess_YYYYMMDD_HHMMSS/xsim]
file mkdir [file dirname $vp_evidence]
synth_design -top vision_preprocess_axi -part xc7z020clg400-1 -lint -file [file join [file dirname $vp_evidence] linter.rpt]
source [file join $vp_root project/fpga/scripts/vision_preprocess_sim.tcl]
```

仿真脚本必须为 normalizer、sampler、AXI wrapper 三个 testbench 都记录 `PASS`，且各自 transcript 中有 `TEST_PASS`。Lint 报告应结合 Vivado 实际输出检查；不要把旧报告当成新源码的结果。

仿真项目关闭后，独立运行 10 ns OOC 综合、布局布线与时序检查：

```tcl
close_project
set vp_ooc_evidence [file join $vp_root project/analysis/vision_preprocess_YYYYMMDD_HHMMSS/ooc]
source [file join $vp_root project/fpga/scripts/vision_preprocess_ooc.tcl]
```

以新生成的 `result.tcl`、`timing_routed.rpt`、`route_status.rpt` 和 `drc.rpt` 为准。`timing_pass` 必须为 `1` 且脚本输出 `VISION_PREPROCESS_OOC_PASS`，才表示该模块在本次 OOC 条件下通过 10 ns setup/hold 检查。`routed.dcp` 存在本身不代表通过。此 OOC 约束不包含板级 I/O 延迟、系统时钟/复位集成或外部存储器时序，不能作为整板时序或硬件验证结论。

归一化 RTL 的 256 项常量来自精确整数算法；独立仿真 golden 来自 NumPy float32 除法，不复用 RTL 表。需要修改生成规则时运行 `python project/scripts/vision_preprocess/generate_normalize_rtl.py`，随后重新生成向量。每组采样向量同时保存 RGB888 golden 和新增的 FP32 golden；独立 normalizer TB 逐位验证所有 256 个值在 R/G/B 通道的结果，并覆盖气泡、背压、连续帧及 R/G/B 阶段 reset。wrapper TB 核对末 B 受阻时 busy、done 和字节计数。

Python 接口和整数参考测试：

```powershell
python .\project\board\vision_preprocess\test_preprocess.py
```

接口、地址范围、AXI 行为和帧错误语义见同目录的 [CONTRACT.md](CONTRACT.md)。本验证不改现有固件、不生成部署位流，也不操作板卡。


PS V2 接入时先配置 S2MM 长度为 `job.output_bytes`，执行现有 `Preprocessor.start/wait`，确认 DMA 完成并 invalidate 输出缓冲，最后调用 `fp32_to_model_tensor(buffer,job.dst_width,job.dst_height)`；其零拷贝视图不再做除法。`Preprocessor` 拒绝 V1 硬件版本；只支持 V2 FP32 输出，已移除 RGB888 输出及 PS 归一化支路。未创建板端部署、未改变老师模型，也未将本地仿真等同于板上加速收益。
