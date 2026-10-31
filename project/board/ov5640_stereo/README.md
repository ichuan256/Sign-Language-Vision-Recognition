# OV5640左右双路网页识别候选

> 这是历史双路候选，不是最近部署；最近已改为单目视听候选。先读[当前状态](../../../docs/当前状态.md)，不要直接运行本页命令接管最近固件。

2026-10-31用户批准冷部署，当时切换到本候选并启动真实双路采集；左右画面和递增帧号均获目视确认，页面为`http://127.0.0.1:18790`。当时已备份W6并停用旧按键监听。

当时短测每路约3.29个完整帧/秒，PC教师每路约31ms。约252秒日志：左路990次尝试，其中935完整帧、55部分帧；右路937次均完整。部分帧不送识别或补造图像，所有日志DMA停机均确认。此为短时观察，不代表长期稳定或曝光帧率，见[实测证据](../../analysis/stereo_web_20261031/live_verification.json)。

## 交付范围

复用原`ov5640_snapshot` RTL两份，`CAMERA=1/2`分别绑定物理OV1/OV2；每路独立AXI GPIO、S2MM DMA和PCLK，DDR经共享HP0互连。没有修改冻结RTL目录，没有关键点网络或HDMI硬件。

| 相机 | 采集IP | DMA基址 | 控制基址 |
|---|---|---|---|
| OV1左目 | camera | 0x40400000 | 0x41200000 |
| OV2右目 | camera_right | 0x40410000 | 0x41210000 |

板端PS调度采集 → SSH完整RGB565帧 → PC两份独立Holistic教师实例 → 网页左右并排骨架。可选5词实验分类头沿用现有模型，其跨来源精度限制不因双路接入而改善。
两路独立采集，不保证曝光同步；网页显示的是**采集完成时间差**，没有标定、视差或三维深度输出。单路失败不会复制成另一幅画面。

## 本地验证

候选`release_20261031/`已生成成对bit/HWH。WNS 0.515ns、WHS 0.021ns；LUT 4820、寄存器6460、BRAM Tile 11、DSP 0。布线、DRC、内部CDC、FIFO bus skew、左右4根SCCB pad的开漏/读回结构门禁通过。
外部DVP输入/输出时延仍未完成板级验证，发布状态为`candidate_board_unverified`，不能用内部时序通过代替真实相机出图。

15项软件/协议与控制台测试通过，包括左右不同帧保持、只有左路不输出双路、非法camera ID拒绝、短帧/DMA未确认拒绝和冷启动确认。没有真实采集FPS或识别率结论。

构建入口：`project/scripts/ov5640/prepare_stereo_candidate.bat`、`build_stereo_candidate.bat <xpr> <新报告目录>`；使用Vivado 2024.1、xc7z020clg400-1，串行构建。独立工程`project/_tmp/ov5640_stereo_20261031_v2/vivado/snapshot.xpr`，报告`project/_tmp/stereo_build_20261031_v1/`。
两路BD扩展、时序及SCCB门禁放在`project/fpga/scripts/ov5640_snapshot_stereo_*.tcl`；既有单路工程、固件和W6不变。

## 板端暂存与下一步

部署目录为`/home/xilinx/ov5640_stereo_20261031/`，bit/HWH及软件SHA已核验。`stereo_stream.py`只接管已冷启动的配套固件，要求本次boot marker和配套SHA，使用`Overlay(download=False)`。
采集复用原helper的DMA Halted/安全释放路径；若停机未确认，保留进程、缓冲和锁，不强杀。

冷启动与回退计划在`project/_tmp/stereo_test_20261031/deployment_plan.json`，启动脚本副本为同目录`boot_stereo_candidate.py`。它保留板上实际网络初始化前缀，替换旧W6加载段，防止在原boot或同一boot重复下载位流。原文件备份在板端`backup_before_coldboot/boot.py`，原W6 bit/HWH与服务状态也已备份。

经用户明确确认后，已备份并替换`/boot/boot.py`、暂停/禁用旧`button-watch.service`、正常重启，由冷启动加载本候选一次。候选没有旧GPIO/音频/HDMI，因此不能继续运行旧按键监听或旧W6演示；回退时先安全停止采集，恢复原启动文件和服务状态后正常重启，禁止运行中重载W6。

首次启动下载后的校验错误地要求无AXI接口的`camera` module_ref进入PYNQ `ip_dict`，已改为核验两路DMA/控制口，并以本次下载记录、FPGA operating状态、SHA及寄存器元数据补验恢复标记，没有再次下载位流。采集前还发现PS FCLK保留62.5MHz；确认两路DMA均Halted、控制值0后设为100MHz，并将该设置加入后续冷启动。两项恢复细节均在`project/_tmp/stereo_test_20261031/`，当前正确启动脚本副本SHA为`073aa2a5090143afe74697ceb26438491dd02e4159d5f436a0584480c3b9ae19`。

控制页入口为`http://127.0.0.1:18790`，按钮“OV双路实时识别”，仅可接管已冷启动的匹配双路固件。当时会话有界3600秒，用户确认两路更新；不是持续运行保证。网页停止请求安全清理，不强杀DMA，刷新网页不结束采集。

证据索引：[本轮记录](../../analysis/stereo_web_20261031/README.md)。
