# OV5640 连续采集 Notebook

在板端 Jupyter 打开 `continuous_capture.ipynb`，按顺序运行参数、检查、开始、结果单元。需要已安装 PYNQ 的 **root Python 内核**；检查单元会明确拒绝权限不足或 helper 版本不一致。Notebook、`continuous_capture.py`、原有 `capture.py` 放在同一目录。

本工具只接管冷启动时已经加载的成对固件，始终使用 `Overlay(..., download=False)`，不提供下载位流、重启或修改启动项功能。文件哈希、HWH、boot/download标记用于核验前提，不能单独证明运行位流身份；操作者仍须确认当前位流由冷启动加载且与manifest配套。

## 默认行为

- 采集60秒或总尝试1000次，**任一上限先到即结束**；60秒从初次初始化和预热完成后开始，包含后续坏帧、恢复和日志开销，不含最终清理、RAW落盘及PNG转换。
- 连续失败5次停止；有效帧会清零连续失败计数，累计错误另记。错误类型区分PS按DMA长度拒绝的帧、超时和DMA错误。边界处正在执行的尝试可标记duration/interrupted，不算有效帧或超时。
- 默认丢失门限为5%，且采用严格“小于”比较：单帧缺失像素比例 `<5%` 会作为接受的部分帧计入有效帧；`>=5%`、RGB565奇数字节数或超容量仍由PS按实际DMA长度拒绝。对于1280×720帧，恰好5%丢失为46,080像素，因此至少收到875,521像素才会因比例门限接受。
- 丢失像素数从DMA完成后的S2MM实际接收字节数计算，除以每像素2字节。PL不提供DVP几何错误或像素数诊断；完整帧与部分帧只按DMA长度区分。正常路径只初始化相机一次、申请一个DMA buffer，按`arm ^= 4`循环，并保留capture_done、DMA IOC/Idle与DMA安全停机检查。
- PS长度检查拒绝、超时或DMA错误时，先记录状态、DMA soft reset并确认Halted，再走原有完整相机/采集复位与初始化流程。`initializations`和`recoveries`如实增加；不使用未经专项验证的maintenance快速恢复。发生初始化失败时停止，不无限重试。
- 默认最多3个RAW样本（首次及每100次尝试抽样；只对接受帧取样），采集期间仅保留实际接收字节的内存副本，清理后写盘。`max_samples=0`完全禁用样本。上限10个，避免无限占用板端内存。
- DMA长度恰好完整的样本可由Notebook最后的独立单元显式转成PNG；部分帧只保留RAW，不伪造成完整720p图像。采集循环不编码PNG、不逐帧保存图像。该单元耗时不属于采集速率，转换不会覆盖已有PNG。
- 不额外修改曝光参数；每次完整初始化使用当前固件既有传感器配置。

## 安全停止

点击Jupyter的Interrupt/停止按钮，或CLI按Ctrl-C。SIGINT只设置停止标志，程序仍会确认DMA reset完成且Halted，再释放buffer、复位相机并保存结果。

**若结果`unsafe_dma=true`或提示DMA停机未确认：必须保持当前kernel/进程存活，禁止重跑、重启/关闭kernel或强杀进程。先给板卡断电。** helper会保留物理buffer和fcntl进程锁，并拒绝同kernel再次运行；CLI会停留等待断电。

fcntl锁防止此helper在同机并行运行；启动前另检查旧`capture.py`/`sensor_probe.py`等进程。旧脚本、其他Notebook或直接MMIO操作未必遵守此锁，仍应独占摄像头硬件，不能在其他单元同时操作。

## 输出与速率

- `attempts.jsonl`：每次尝试的类型、状态、DMA实际/缺失像素数、丢失比例、耗时、清理确认和连续错误计数。
- `results.json`：总尝试、有效帧、接受的部分帧、长度拒绝帧、累计缺失像素、最大丢失比例、超时、DMA错误、恢复次数、停止原因及安全清理状态；绑定bit/HWH和运行helper哈希。
- `effective_fps = valid_frames / capture_seconds`，包含坏帧恢复、polling、buffer操作和JSONL开销，是该PS抓帧路径的实际有效吞吐，不能当作传感器输出帧率、显示刷新率或后续识别帧率。
- 逐帧`dma_seconds`是成功帧的DMA采集/状态检查段；`attempt_seconds`还包括该次DMA停机及抽样内存复制。初次初始化与最终清理单列于`total_seconds`。
- `sample_XXXXXX.raw`：限量实际接收的RGB565_LE字节及SHA，包含接收像素数、缺失像素数和丢失比例；只有DMA长度完整的帧可有同名PNG。默认抽样不是“保留最后一帧”，不足采样周期时可能仅1个样本。

`max_errors`参数名字保留简洁，其含义为**连续错误上限**。`completed_without_errors`只在正常达到上限且本轮无错误时为真；达到时长上限不证明长期稳定或完整板级时序验收。

## CLI

板端目录中执行，`captures/continuous_001`必须不存在：

```sh
sudo env XILINX_XRT=/usr /usr/local/share/pynq-venv/bin/python continuous_capture.py \
  --manifest release/release_manifest.json --output captures/continuous_001 \
  --assume-cold-boot --seconds 60 --max-attempts 1000 --max-errors 5 \
  --max-samples 3 --sample-every 100
```

显式后处理（无硬件访问，不覆盖既有PNG）：

```sh
/usr/local/share/pynq-venv/bin/python continuous_capture.py \
  --output captures/continuous_001 --convert-only
```

短测试可用`--seconds 15 --max-attempts 1000 --max-samples 0`。`--seconds 0`表示仅按尝试数/连续错误限制，仍有总尝试硬上限。每帧默认5秒超时，初始化默认30秒；不是无限等待。

## 验证

`test_capture.py`和`test_diagnostics.py`覆盖DMA实际字节数换算、严格5%边界、偶数字节校验、紧凑诊断页和控制/arm位恢复。`test_continuous_capture.py`的mock测试覆盖arm交替、一次初始化与buffer复用、时长/次数/连续错误上限、接受的短帧与拒绝帧、超时/DMA错误分类和完整重初始化、Ctrl-C与清理中的重复中断、不确认Halted时保留buffer并拒绝重跑、部分RAW不转PNG、PNG哈希/拒绝覆盖、进程祖先排除与Linux锁互斥。模拟测试不替代真实传感器/DDR验收。

```sh
python -m unittest discover -s project/board/ov5640_snapshot -p test_continuous_capture.py -v
```

Windows跳过fcntl锁一项；板端Linux需要再跑该项。固件诊断接口升级后必须使用同批次的bit/HWH/manifest。2026-10-28，新候选已冷启动加载，board `release/`、`capture.py` 和 continuous helper/notebook 已同步；真实相机/DDR采集与板端Linux单元测试尚未运行。仓库内原`release/`仍是历史V15，部署和哈希证据见`project/analysis/ov5640_snapshot_20261028/deployment.md`。
