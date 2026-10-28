# 删除旧 RGB888 输出与 PS 归一化支路

2026-10-28，用户明确要求清理旧支路。本次删除 `rgb888_axis_pack32.v`、其独立 testbench，以及 `preprocess.py` 中的 `rgb888_to_model_tensor` 和专属旧接口测试；从 prepare/OOC/sim 清单移除旧文件及仿真 top，更新当前 README/CONTRACT。

V2 只支持 PL 输出 FP32；FP32 张量读取测试改用测试内部独立 NumPy 参考，不保留可供运行调用的旧 PS 归一化函数。采样器内部 RGB888、颜色展开及整数参考仍为 FP32 通路和独立验证所必需。

## 已执行验证

| 检查 | 内容及结果 | 证据 |
|---|---|---|
| 文件与引用 | 两个旧文件已不存在；活动 board/RTL/TB/生成器/FPGA 脚本没有旧模块或函数引用 | [引用检查](active_reference_check.txt) |
| Python | 16 项通过：实际 256 项 ROM 位模式、零拷贝 RGB NHWC 数值/布局和共享缓冲、旧/短/长包与版本拒绝、原几何/黑边/地址边界及错误/超时保护 | [日志](python.txt)、[测试](../../board/vision_preprocess/test_preprocess.py) |
| normalizer XSim | R/G/B 各覆盖全部 256 值；气泡、单像素/连续帧、长时间及随机背压、R/G/B 阶段 reset；11 完整帧、1134 个背压周期，TEST_PASS | [完整 transcript](xsim/tb_rgb888_axis_fp32_normalize/simulate.log)、[测试](../../fpga/tb/vision_preprocess/tb_rgb888_axis_fp32_normalize.sv) |
| sampler XSim | 16 fixture、19 帧、15 非法配置，包含 720p letterbox/旋转 ROI、负坐标和地址边界、读错误恢复；TEST_PASS | [完整 transcript](xsim/tb_vision_rgb565_affine/simulate.log)、[测试](../../fpga/tb/vision_preprocess/tb_vision_rgb565_affine.sv) |
| wrapper XSim | AXI-Lite 独立 AW/W、WSTRB、响应背压、shadow/start，AXI 读等待/错误/RLAST drain，FP32 顺序和末 B 完成字节数，reset；TEST_PASS | [完整 transcript](xsim/tb_vision_preprocess_axi/simulate.log)、[测试](../../fpga/tb/vision_preprocess/tb_vision_preprocess_axi.sv) |

Vivado 2024.1 使用新工程 `project/_tmp/vp_clean_20261028_231643`，确认只有三份 RTL、三份 TB；三组均重新 compile/elaborate/run，完整日志无 Fatal/Error，汇总见 [regression.txt](xsim/regression.txt)。独立 fixture 复用先前已保存的输入与 NumPy oracle，不依赖被删除代码。`git diff --check` 通过。

## 修改边界

现有三份 RTL、三份 TB，以及 PS 老师的 `teacher_geometry.py`、相机 `capture.py`、HDMI `hdmi_preview.py` 共九份文件的前后 SHA 全部一致，见 [对照](preserved_sources_after.json)。老师基线预处理、相机 RGB 解码及显示颜色转换继续保留。历史报告和构建输出不删除。

本轮删除的是未在 V2 顶层实例化的旧模块，没有改变活动硬件逻辑，未重复 OOC 综合/布局布线；原资源、时序和保留告警仍见 [归一化实现记录](../vision_preprocess_fp32_20261028/README.md)。本轮未访问板卡、加载固件或改变部署状态。

沿用原 `gpt-6.1-sol/high` 子代理完成清理与 Python 检查，主代理复核及执行干净工程 XSim。缺少完整计费用量，实际总 API 费用未知。
