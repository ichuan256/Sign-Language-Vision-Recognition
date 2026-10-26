# OV5640 OV1 单路抓图候选验收记录

2026-10-27。用户批准的交付：单路抓图测试固件与板端 PNG 保存程序。已完成本机构建、仿真、软件mock测试和成对候选发布；未连接、部署、重启或重新配置板卡。

## 交付

- project/board/ov5640_snapshot/release/：ov5640_snapshot.bit/.hwh、release_manifest.json（成对SHA256、相机和DMA契约、源码SHA）。
- project/board/ov5640_snapshot/capture.py：OV1初始化、下一完整帧接收、RAW/PNG/JSON保存；仅Overlay(download=False)。先DMA后arm；核对camera_done、无错误、DMA IOC/Idle和1843200字节；复位确认Halted后释放buffer。
- project/board/ov5640_snapshot/README.md：硬件前提、冷启动限定、运行与异常处理。

## 实际验证

Vivado/XSim 2024.1，xc7z020clg400-1。隔离工程 project/_tmp/ov5640_snapshot_20261027_v3/vivado/snapshot.xpr。

- tb_snapshot_packet：未arm抑制、下一SOF开始、像素拼接、只在帧末TLAST、校验后done、重arm、短/长/晚到错误、溢出/FIFO复位忙、中途复位。
- tb_snapshot_system：单个SCCB传输器完成309写30读和一次stream-on；OV2复位/PWDN及SCCB释放；4×2 DVP经真实XPM FIFO到AXIS的像素/背压/TLAST；坏帧拒绝、错误映射和复位。
- tb_snapshot_720p：两帧1280×720共921600个32位字，逐字检查像素顺序与仅帧末TLAST；周期背压、重arm、真实4096深FIFO溢出后拒绝及复位。末次RTL改动后全套重新通过。
- 软件9项unittest：RGB565颜色/小端与PNG解压像素和CRC；DMA在arm前启动；成功缓存flush/invalidate与释放；初始化失败/PCLK停止不分配；超时、旧done、相机错、DMA错、短长度重置后释放；无法确认DMA复位时保留buffer；哈希/HWH地址/相机契约拒绝；download=False和100MHz门禁；新目录及冷启动确认要求。具体tests在板端目录，日志python_tests.txt。日志中ERROR文本来自预期拒绝用例，最终OK。

## 实现结果与限制

- 最终routed setup WNS +2.522ns，hold WHS +0.016ns；无无时钟寄存器和无约束内部端点。
- CDC报告只有8项CDC-3与1项CDC-9信息，无Critical。修复了心跳复位跨域及arm首级选择错误；未使用全时钟组屏蔽。
- 全部5023个可布线网完成，routing errors=0。XPM pointer bus skew slack +8.991/+9.109ns。
- Bitgen成功，0 Error、0 Critical Warning；仍有BRAM异步控制(REQP-1839)、IP推导LUT(PDCN-1569)、闲置OV2 SCCB端口(RPBF-3)、IP无负载网(RTSTAT-10)等Warning。详细build/drc.rpt，不称零警告发布。
- 2226 logic LUT、3331寄存器、5.5 BRAM tile（见utilization.rpt）。
- 外部DVP数据/同步10个输入和2个复位输出缺少I/O delay，不能宣称完整板级时序收敛；未编造参数。真实传感器、线缆电气、实际PS DDR DMA、冷启动加载流程尚未板上验收。

当前只能标记candidate_board_unverified。不要在正在运行的旧固件上直接执行抓图或再次加载候选。旧W6发布文件保持原状；接线前先断电并确认旧SPI不再驱动相同引脚。

## 资料依据

AMD PG021（本地AMD文档检索并联网核对原文）：S2MM_LENGTH完成后给出实际字节数；DMACR soft reset完成后才表示复位结束；接收LENGTH必须最后写。
https://docs.amd.com/r/en-US/pg021_axi_dma/S2MM_LENGTH-S2MM-DMA-Buffer-Length-Register-Offset-58h
https://docs.amd.com/r/en-US/pg021_axi_dma/S2MM_DMACR-S2MM-DMA-Control-Register-Offset-30h
