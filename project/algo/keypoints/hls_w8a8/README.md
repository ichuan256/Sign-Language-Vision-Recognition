# HLS W8/A8 有界综合（可行性实验）— 环境阻塞记录（2026-10-28）

## 目标
dw_3 / pw_3 / stem 三层有界综合（Vitis HLS 2024.1，xc7z020clg400-1），
先 C 仿真对拍（`build_csim.tcl`）再综合（`build_synth.tcl`）。

## 已就绪
- `kp_hls_kernels.cpp`：三核模板实现（int64 累加 + M/F 契约再量化，TF 一致 padding）。
- `kp_hls_tb.cpp`：读 `--vectors-c` 裸向量逐位对拍。
- `build_csim.tcl` / `build_synth.tcl`。
- 运行配方 `run_hls.bat`（settings64 + Vitis lib/JRE 补 PATH + RDI_DATADIR/TCL_LIBRARY）。

## 阻塞（证据链）
1. 官方 `vitis_hls.bat` wrapper 在任何**非交互、句柄被重定向**的上下文
   （Git Bash→cmd、原生 bat、python subprocess、PowerShell、start /wait）
   全部静默退出、零输出。loader 链内部有裸 `exit`，会杀掉宿主 cmd。
2. 直调 `unwrapped/win64.o/vitis_hls.exe`：
   - `-version` 正常（工具本体完好）；
   - 批处理模式必现 `source {} -notrace` + `ERROR [common-17-76]`——
     脚本名参数无法到达 tcl 层（试过 -f/-source/-mode tcl/stdin/-exec 等 8 种变体）。
3. 已解决的沿途问题（写入 run_hls.bat）：xv_common*.dll 在 Vitis lib、
   jvm.dll 用自带 JRE、RDI_DATADIR、TCL_LIBRARY、builtin.tcl 需 scripts junction
   （`mklink /J scripts <tool>/scripts`）、工具根只读需可写 cwd。

## 有界综合结果（2026-10-28，人工交互控制台跑通）

环境阻塞已解决（wrapper 只认真交互控制台）。C 仿真三层逐位一致 PASS；
有界综合（Vitis HLS 2024.1，xc7z020clg400-1，10ns 目标，估计 7.3ns≈137MHz）：

| 层 | BRAM18K | DSP | FF | LUT | 延迟(cycles) |
|---|---:|---:|---:|---:|---:|
| dw_3 | 21 | 16 | 6.7K | 10.7K | 68,151 |
| pw_3 | 8 | 38 | 20.3K | **34.6K** | 236,911 |
| stem | 104 | 26 | 15.4K | 33.5K | 2,249,951 |
| 三层合计 | 133/280 | 80/220 | 42.4K | **78.8K/53.2K = 148%** | — |

**结论：朴素直写路线不可行**——11 层里的 3 层 LUT 就已超预算 48%（pw_3 单层占 65%），
stem 单层延迟 2.25M cycles ≈ 16ms。成本驱动：每个乘法器带 int64 累加 + 全展开 +
padding 大数组驻留 BRAM + batch N=2 折算。必须按 03 方案 §4 做数据流架构
（DSP48 int8 乘加共享累加器、行缓存、层间 FIFO、阵列复用、batch=1）。
数据存 synthesis_feasibility_20261028.json。

## pw_3 数据流迭代（2026-10-28，CSim 每轮逐位一致）

| 版本 | LUT | DSP | FF | BRAM | 流水线 | 关键教训 |
|---|---:|---:|---:|---:|---|---|
| v1 朴素 | 34,580 (65%) | 38 | 20.3K | 8 | 违例 | 每乘 int64 + II=1 放错层 |
| v2d | 10,222 (19%) | 12 | 6.5K | 4 | II=32 违例 | 单 m_axi 口串行化 load |
| **v3 数据流** | **6,389 (12%)** | **12** | 3.8K | 20 | **II=1 满足** | 转置权重+BRAM 驻留+chunk 流水+int32 共享累加+ap_int 窄乘 |

v3 结论：最大 PW 层 12% LUT / 12 DSP / II=1，数据流架构在 xc7z020 上成立；
全网络按 §4 层复用阵列可装下。数值契约全程逐位一致（RNE/M/F/int32 界）。

## 人工操作记录（本机 Vitis HLS 只在真交互控制台工作）

agent 侧所有重定向/管道调用均静默失败；人工 cmd 窗口跑通。命令：
```
cd /d F:\PLD_new\Sign-Language-Vision-Recognition\project\algo\keypoints\hls_w8a8
F:\APP\Xilinx\Vitis_HLS\2024.1\bin\vitis_hls.bat -f build_csim.tcl   :: PASS
F:\APP\Xilinx\Vitis_HLS\2024.1\bin\vitis_hls.bat -f build_synth.tcl  :: 3/3 done
```
