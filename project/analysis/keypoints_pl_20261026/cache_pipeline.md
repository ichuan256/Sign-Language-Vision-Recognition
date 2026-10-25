# 输入缓存与流水线优化（2026-10-26）

当前板端版本：双向 burst 已上板，三次前向为 **0.566204 / 0.563820 / 0.563270 秒**，
每次 64 输出均与整数参考一致。比 1.86 秒版本约快 3.3 倍，仍未达到 200ms/5Hz。
结构化证据和发布哈希见 [cache_pipeline.json](cache_pipeline.json)。对比基线是
[上一轮 1.86 秒版本](../keypoints_pl_20261025/single_hand_acceleration.md)。

## 本轮实现

- PL 使用 128KiB、16 通道分银行的 BRAM 输入缓存，每块处理 4 个输出行。片外输入按块读入，
  depthwise 的相邻窗口和普通卷积的输出通道块复用同一缓存；片内通道填充到 16，片外格式不变。
- 普通卷积及 depthwise 的乘法保留 DSP，48bit 累加反馈使用 fabric，加上有边界的地址位宽，
  两个计算循环实际 HLS II 均为 1；卷积中间饱和、ReLU 及第二次舍入边界保持原样。
- vector 的 Add/ReLU/Scale 独立流水，4 元素池化使用专门路径；单次容量从 4096 提到 65536。
  平均池化与 sigmoid 保留严格整数语义。寄存器映射显式记录容量，不把旧固件误当新容量使用。
- 同一模型、量化参数及校准探针不变。每 ROI 49 次整层调用＋13 次 vector，共 62 次（上一版 115 次）。
- 下一轮动态显示左侧只画 PC ROI 框，右侧画实际 PL 输入及其骨架，去掉旧姿态随 ROI 变换产生的快速绿色点。

## 证据与门禁

| 项目 | 结果 |
|---|---|
| 整网 HLS C | 7 ROI 对整数参考逐值一致，最大差 0 |
| 缓存核 C/RTL | 10 组 PASS；含跨 4 行块边界、尾行、5×5 depthwise、17 通道尾块和 672 输入通道 |
| 快速 vector C/RTL | 11 组 PASS；含 4097、50003、65536 元素 Add 和原有符号/舍入/饱和探针 |
| 缓存核 HLS 资源 | BRAM18K 87、DSP 84、LUT 27158、FF 21585；不是整板布线资源 |
| vector HLS 资源 | BRAM18K 5、DSP 3、LUT 14470、FF 9707；不是整板布线资源 |
| 软件回归 | 157 项通过，32 subtest 通过，2 条既有 protobuf 警告 |

首个缓存实现功能通过但索引计算使用通用位宽，HLS DSP 估计 100；按已检查边界收窄地址乘法后降至 84，
重新进行了整网整数验证与 C/RTL。两版证据分别保留于 `kp_cached_ip_v1` / `v2`，不覆盖。
增加 BRAM 是本轮速度换资源的选择；能否装下、时序是否通过，以整板综合/实现为准。

## 本机路径

- 完整图 C：`project/_tmp/kp_cached_c_v1/`、`kp_cached_c_v2/`；最终源码复验另存新目录。
- 验证后导出 IP：`project/_tmp/kp_cached_ip_v2/`、`project/_tmp/kp_vector_fast_v1/`。
- 独立整板工程：`project/_tmp/kp_cached_system_v1/`。
- 同模型、新寄存器元数据：`project/_tmp/kp_cached_model_v1/`。

工程只导入基线 BD Tcl、冻结源文件和约束，未复制旧 runs/cache。通过 Vivado `config_ip_cache`
引用其内容校验 IP 缓存，工具自动决定是否复用；不把旧实现结果直接当成本轮布局布线结果。
板端仍遵守 bit/hwh 成对、先备份、冷重启一次、`download=False` 接管。
首版缓存整板资源为 LUT 38860/53200、DSP 186/220、BRAM Tile 91/140；
WNS 0.140ns、WHS 0.016ns，TNS/THS=0，81929 条可布线网络全部完成、0 路由错误。
固件按冷启动部署，上板输出最大差 0；完整证据 `project/_tmp/kp_cached_board_v1/`，
成对固件及上一版备份位置在 `project/_tmp/kp_cached_deploy_v1/deployment.json`。

该版分项为普通卷积 0.490 秒、depthwise 0.304 秒、vector 总调用 0.041 秒；
HLS 未为该版输入加载形成 burst。因此继续补齐连续输入与整块写回，不把 0.87 秒称为实时。

连续读取版 `kp_cached_ip_v3` 已通过 C/RTL；双向 burst 版 `kp_cached_ip_v4` 同样通过，
输入行与输出块都有明确 burst 推断日志。后者增加 64KiB 输出块缓存，HLS 估计 BRAM18K 119、DSP 75、
LUT 27462、FF 20226。全图 C 再次在 7 ROI 上逐值一致，证据 `project/_tmp/kp_burst_c_v2/`。
整板候选为 `project/_tmp/kp_burst_system_v1/`，模型/寄存器为 `project/_tmp/kp_burst_model_v1/`。
双向 burst 版已完成整板实现：LUT 39327/53200（73.92%）、DSP 179/220（81.36%）、BRAM Tile 107/140，
WNS 0.026ns、WHS 0.007ns、TNS/THS=0；81078 条可布线网络全部完成，0 错误。
冷启动部署记录 `project/_tmp/kp_burst_deploy_v1/`，实际三次输出 `project/_tmp/kp_burst_board_v1/`。
分项普通卷积 0.339 秒、depthwise 0.145 秒、vector 总调用 0.040 秒；输入复制/刷新 0.028 秒。
CPU 只在需要读 PL 输出时才失效缓存，直接交给下一 PL 层的输出不做多余同步，保持独占写入约定。

90 秒动态接收验收已正常结束：1903 帧视频、168 次实际 PL 结果、400 次已确认写屏，
所有输入传输逐帧 SHA 校验。用户查看时程序已结束，不能据最后静止画面判断 PL 卡死；
该轮没有把“结束后未观察到更新”记成动态目视通过。随后已启动 600 秒演示，
日志 `project/_tmp/kp_burst_dynamic_live_v1/`。左侧仅黄色 PC ROI 框，右侧实际 PL 输入与骨架。

用户随后要求继续提速，下一轮将检查 AXI 自动位宽扩展和输出流水重叠；未验证前不替换本版记录。
