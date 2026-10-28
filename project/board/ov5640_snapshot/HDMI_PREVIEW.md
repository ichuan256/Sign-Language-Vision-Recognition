# OV5640 → HDMI 720p 预览

`hdmi_preview.py` 将 OV1 的 1280×720 RGB565_LE 采集帧转换为 BGR888 内存帧，交给板内 HDMI 输出。相机经 HP0 写 DDR，显示 VDMA 经 HP2 读 DDR；无需电脑逐帧传图，不运行关键点网络。实现仍由 PS 调度每次采集和颜色转换，实际相机预览速率需上板测量。

必须使用新增的 **相机＋HDMI 成对固件**，仓库输出目录为 `release_hdmi/`。原 `release/` 和 `release_remove_pl_bad_frame_20261028/` 都没有 HDMI 硬件，不能运行此预览。固件/软件构建状态见 [本轮记录](../../analysis/ov5640_hdmi_20261028/README.md)，重建步骤见 [构建说明](../../fpga/scripts/OV5640_HDMI_BUILD.md)。

## 板卡开机后的操作

本轮只完成本地版本。后续部署时，把新发布包中的 bit、HWH、manifest 和 provenance 成对复制到板卡既有启动加载目录，并同步 `capture.py`、`continuous_capture.py`、`hdmi_preview.py`。如果还使用连续采集 Notebook，也同步本次更新的 `continuous_capture.ipynb`。核对哈希后正常重启，由既有冷启动流程加载一次新固件；运行中的板卡禁止再次下载位流。

下列命令假设板端已将新包部署到 `/home/xilinx/jupyter_notebooks/ov5640_snapshot/release/`，冷启动已经完成，且 boot/download marker 与本次 boot ID 相同。`--assume-cold-boot` 是操作者对固件身份的确认，哈希和 marker 不能独立证明运行中的位流身份。

显示器连接 PYNQ-Z2 的 **HDMI OUT**。在板端执行：

```sh
cd /home/xilinx/jupyter_notebooks/ov5640_snapshot
sudo env XILINX_XRT=/usr /usr/local/share/pynq-venv/bin/python capture.py \
  --manifest release/release_manifest.json --output unused --verify-only
sudo env XILINX_XRT=/usr /usr/local/share/pynq-venv/bin/python hdmi_preview.py \
  --manifest release/release_manifest.json --output captures/hdmi_001 \
  --assume-cold-boot --seconds 60 --max-attempts 1000 --max-errors 5
```

输出目录必须是新的。默认在 60 秒、1000 次采集或连续 5 次失败中任一上限到达时结束；`--seconds 0` 仅取消时长上限，尝试次数上限仍保留。FCLK0 必须已为 100MHz，脚本不修改时钟。它只调用 `Overlay(..., download=False)`，没有下载固件的选项。

运行中按 Ctrl-C 会请求停止。正常退出会先确认采集 DMA 和 HDMI MM2S DMA 都已 Halted，再释放各自缓冲，并关闭 HDMI 前端。因此**测试结束后不继续显示最后一帧**。若报告停机未确认，脚本会持有缓冲和进程锁并等待：先断电，再结束进程；不要直接强杀或重启 Notebook 内核。

## 画面和结果

- 初始缓冲为黑色，第一次完整相机帧完成后更新；黑色初始画面不计为相机帧。
- 沿用现有采集政策：PS 允许小于 5% 丢失的部分帧，但预览只显示实际字节数完整的帧。部分帧记入 `skipped_partial`，保留当前显示帧，不补齐或伪造画面。
- 颜色转换逐位扩展 RGB565，再按 PYNQ `PIXEL_BGR` 排列内存。所有显示缓冲由进程持有，先填充非活动缓冲，提交 park 指针后有界等待成为活动帧。
- `attempts.jsonl`/`results.json` 记录采集结果；`preview_results.json` 额外记录显示数量、跳过的部分帧、显示错误及两路停机状态。`display_effective_fps` 是软件提交且观察到活动指针的有效速率，**不是屏幕物理帧率**。
- 相机和显示超时默认分别为 5 秒和 2 秒；显示切换失败会终止本轮，随后执行停机清理。摄像头恢复流程仍使用原连续采集实现。

不要与其他相机采集程序、旧 HDMI owner 或直接操作同一硬件的 Notebook 单元并行运行。脚本使用已有相机进程锁，并扫描已知相机/HDMI 进程；未遵守锁的自定义 MMIO 程序仍需操作者排除。

## 本地验证与上板验收边界

针对性测试在 `test_hdmi_preview.py`，覆盖全部 65,536 种 RGB565 值与旧参考逐点对齐、完整/部分帧、非活动缓冲更新、帧切换超时、DMA 停机失败时保留缓冲、回调失败和仅接管不下载。`test_package_hdmi.py` 防止纯采集 HWH、缺少显示模块或错误 VDMA/HP2 配置被标记为 HDMI 发布包。完整测试记录在本轮分析目录。

板卡本轮未开机，真实相机＋HDMI 并发、色序、运动连续性、撕裂、屏幕帧率和持续运行均待验收。相机 DVP 外部 I/O 时序约束仍不完整；内部时序通过不能代替板级验收。

接口依据：[PYNQ v3.0.1 视频层级驱动](https://github.com/Xilinx/PYNQ/blob/v3.0.1/pynq/lib/video/hierarchies.py)、[VDMA 驱动与 park/active 指针](https://github.com/Xilinx/PYNQ/blob/v3.0.1/pynq/lib/video/dma.py)、[AMD AXI VDMA PG020](https://docs.amd.com/r/en-US/pg020_axi_vdma/Documentation)。本机未提供 AMD 本地文档搜索 MCP，本轮核对的是以上官方在线原文。
