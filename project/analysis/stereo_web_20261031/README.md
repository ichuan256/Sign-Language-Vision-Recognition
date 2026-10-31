# 双路实时识别与网页接入准备

> 历史双路采集验收。后续已部署其他候选；最近状态看[统一入口](../../../docs/当前状态.md)，以下boot和进程记录仅适用当时窗口。

2026-10-31。用户请求双目实时识别投到现有选择网页，随后明确同意冷部署。已从旧W6切换至双路候选并启动真实采集，用户确认两路可见、帧号均增加。

- Vivado route：独立双路BD → 综合 → 实现 → bitstream；随后按用户同意方案正常重启，冷加载一次。
- bit SHA256：`20bcd0b0681529aadb55ddbc266e1f4f4f850ceba8f74d3ae8d3528bd9920cc2`。
- HWH SHA256：`6b66cbea66a7fd7a8ebfceb2c28eb33c8609980773ce60cded7b072eab3df44c`。
- WNS/WHS：0.515/0.021ns；LUT4820、FF6460、BRAM11、DSP0；左右SCL/SDA四pad结构通过。
- 15项软件/控制协议测试通过，后续补充尺寸检查后的3项双路测试再次通过。
- 配对和软件SHA核验通过，启动脚本及原固件已备份，旧按键服务禁用；当时boot为`f30dca2d-6ef8-41d8-bddd-bd163ba86289`。
- 网页真实左右视角、递增帧号已由用户确认，PC分别执行两份Holistic。未做三维标定、曝光同步、物理曝光帧率或手语准确率验收；外部I/O约束完整性和长期运行仍待验收。

源码和步骤见[双路候选说明](../../board/ov5640_stereo/README.md)。发布包`project/board/ov5640_stereo/release_20261031/`，原始构建在`project/_tmp/stereo_build_20261031_v1/`，板卡核验与暂存/回退计划在`project/_tmp/stereo_test_20261031/`。

网页程序`vision/src/vision/keypoints/stereo_demo.py`两路分别运行PC Holistic，实时合成左右骨架，并明确报告两路采集完成时间差；没有三维标定或硬件曝光同步。板端采集程序`project/board/ov5640_stereo/stereo_stream.py`不执行神经网络。

实测：[live_verification.json](live_verification.json)。约10秒窗口，两路完整帧各增33，约3.29帧/秒/路。约252秒板端日志抽查：左990次（935完整、55接受的部分帧），右937次均完整，所有日志DMA停机均确认；部分帧从未送入网页识别。此为完整帧交付吞吐，不是曝光帧率或识别准确率。

初次冷下载已成功，但随后无AXI `camera`模块的错误元数据断言使boot服务报错；核对本次attempt、位流SHA、FPGA operating及两路DMA/控制口后补验恢复，没有重下位流。另在两路DMA Halted及控制0时把PS FCLK从62.5设为100MHz，启动脚本已修正。恢复记录为`metadata_recovery.json`、`clock_fixed.json`、`coldboot_verified.json`，均在本轮临时证据目录。
