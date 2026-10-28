# PL 预处理 RTL 当前状态（2026-10-28）

本目录记录独立 `vision_preprocess` V1 的检查和修复证据。实现已完成流水化修复，最终 RTL 在 Vivado 2024.1 下通过 lint、三组 XSim 自检和 10 ns OOC route/timing 检查。最终修复摘要见 [`after_fix_final/FINAL_SUMMARY.md`](after_fix_final/FINAL_SUMMARY.md)。

## 最终验证

- Vivado RTL lint：0 条 lint 消息，报告 `after_fix/linter_final2.rpt`。
- XSim：packer、sampler、AXI wrapper 三组均 PASS，最终 transcript 在 `after_fix_final/xsim/`。采样器覆盖 16 个独立向量 fixture、15 类非法配置、背压、错误后续清零及后续任务恢复；Python 几何/驱动回归 14 项通过。
- OOC 约束 10.000 ns：WNS +0.188 ns、TNS 0、WHS +0.096 ns、THS 0；4,231 个 setup/hold 端点均无失败。3,513/3,513 个可路由 nets 完成路由，routing errors 为 0。报告在 `after_fix_final/ooc/`。
- OOC DRC 余 10 条 warning（DSP 流水建议和独立 OOC 缺少 PS7 的提示），不等于时序失败；详情见最终 DRC 报告。

## 历史基线与差异

初始基线报告和原始失败证据保留在本目录根部的 `vivado_agentic_ai_reports/` 与 `ooc/`。这些报告描述修改前状态：原 WNS −10.558 ns、330 个 setup 失败端点、39 条 OOC DRC warning，不能代表当前 RTL。修改后证据全部单独保存在 `after_fix_final/`，不会覆盖原始日志。

## 工程范围

RTL / testbench / Tcl 重建文件是独立功能线，均未接入 W6 或 OV5640 发布工程。本次未生成部署位流、未部署或操作板卡。OOC 未包含真实板级 I/O 延迟、AXI/DDR 时序及系统复位集成；不能据此宣称整板时序或硬件验收通过。更多运行步骤见 [`project/board/vision_preprocess/README.md`](../../board/vision_preprocess/README.md)。
