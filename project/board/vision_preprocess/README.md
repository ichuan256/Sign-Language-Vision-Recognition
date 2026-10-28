# PL 预处理 RTL 验证

此目录定义 PS 端参数生成、整数参考实现和 Python 接口。PL RTL 与自检 testbench 分别位于 `project/fpga/rtl/vision_preprocess/` 和 `project/fpga/tb/vision_preprocess/`。重建由 Tcl 明确列出输入文件，不依赖本机 `.xpr`；生成的项目、向量和 Vivado 报告留在 `project/_tmp/` 与 `project/analysis/`，不作为源文件提交。

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

仿真脚本必须为 packer、sampler、AXI wrapper 三个 testbench 都记录 `PASS`，且各自 transcript 中有 `TEST_PASS`。Lint 报告应结合 Vivado 实际输出检查；不要把旧报告当成新源码的结果。

仿真项目关闭后，独立运行 10 ns OOC 综合、布局布线与时序检查：

```tcl
close_project
set vp_ooc_evidence [file join $vp_root project/analysis/vision_preprocess_YYYYMMDD_HHMMSS/ooc]
source [file join $vp_root project/fpga/scripts/vision_preprocess_ooc.tcl]
```

以新生成的 `result.tcl`、`timing_routed.rpt`、`route_status.rpt` 和 `drc.rpt` 为准。`timing_pass` 必须为 `1` 且脚本输出 `VISION_PREPROCESS_OOC_PASS`，才表示该模块在本次 OOC 条件下通过 10 ns setup/hold 检查。`routed.dcp` 存在本身不代表通过。此 OOC 约束不包含板级 I/O 延迟、系统时钟/复位集成或外部存储器时序，不能作为整板时序或硬件验证结论。

Python 接口和整数参考测试：

```powershell
python .\project\board\vision_preprocess\test_preprocess.py
```

接口、地址范围、AXI 行为和帧错误语义见同目录的 [CONTRACT.md](CONTRACT.md)。本验证不改现有固件、不生成部署位流，也不操作板卡。
