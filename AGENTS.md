# AGENTS.md · 接手工具链操作手册（Sign-Language-Vision-Recognition）

> 面向接手本项目的 AI agent（Kimi / Codex 等）。读完这份文件，你应该能**完全接管**这台机器上的全部工具链：FPGA 构建、板端部署、视频手势识别线、音频线、git 协作。
> 原则：**先读状态文档再动手；危险动作先问用户；一切证据落到文件。**
> 本文档由 `F:\PLD\pld-sign-glove\AGENTS.md`（2026-10-22 版）适配而来，适配日期 2026-10-23。本工程从 pld-sign-glove 移植 HDMI + 音频线，**不含传感器部分**，新增视频输入高动态手势识别线。

> 最近部署和待办只看 [docs/当前状态.md](docs/当前状态.md)（整理于2026-11-01）。本文保留环境、安全规则和按固件区分的操作卡；历史成功记录不代表最近候选已经验收。

## 当前视觉路线覆盖指令（2026-10-28，用户明确要求）【通用】

**保留 PS 已部署的老师模型，只把少量热点算子或连续子图迁到 PL；停止重新训练轻量学生模型。**
当前视觉加速任务仅以 `docs/方案/04_老师模型PS_PL局部迁移.md` 为执行方案。
不继续学生训练、蒸馏、QAT或学生HLS开发，不因性能目标自行换模型、换输入尺寸、删输出头或重新训练；现有实验产物保留为历史证据。
冻结所选老师模型的文件 SHA、结构、权重、输入预处理及输出语义；先按同一视频/ROI、线程数、检测频率和显示设置测 PS 基线，
再剖析热点，首轮只迁一个有收益的算子或连续子图，其余仍由 PS 执行。迁移需实现实际 PS/PL 接入，
对齐子图边界张量及最终结果，并将传输、缓存同步、驱动调度计入端到端时延；局部核加速或 HDMI 帧率不能替代整条链路提速。
默认不量化；若浮点迁移收益不足，先报告证据及限制，不自行转回训练/QAT。
当前手部老师入口为 `project/board/teacher_hands/run_teacher.py`，并非完整身体/双手 Holistic 验收。
详细范围与历史事实区分见 `docs/方案/04_老师模型PS_PL局部迁移.md`。

---

## 0. 可见性约定（2026-10-23 用户指示）

本文档分两类内容，**逐节标注**：

- **【通用】**：工程性知识与流程（构建、部署、契约、踩坑），可直接给队友的 agent 看。
- **【本机专用】**：只在用户本人这台机器上成立的内容——代理端口与网络配置、
  本机绝对路径、板卡局域网地址与凭据、开机自启项。给队友时**整段剔除或替换**，
  不要把本机网络/凭据细节外传。

各节标题后均带标注；未标注的子节默认【通用】。

---

## 1. 环境与路径速查

### 1a. 本机环境【本机专用】

| 项 | 位置 / 值 |
|---|---|
| 仓库根 = 工作区根 | `F:\PLD_new\Sign-Language-Vision-Recognition`（一切产出都在此目录内，别写到别处） |
| 代理 | 猫猫云在 `127.0.0.1:10090`（2026-10-23 起 Clash Verge 退役，统一走猫猫云）；`~/.ssh/config` 里 github.com 的 ProxyCommand 指向 10090。**代理没开时 git 报 `errno=10061`**；大包推送低速期分段推：`git push origin <sha>:main`（见 `F:\网络\网络问题排查与维护记录.md` 第五章） |
| Vivado/Vitis | 2024.1，`F:\APP\Xilinx\Vivado\2024.1\bin\vivado.bat`（**必须走 cmd 批处理调用，见 §4**） |
| 视觉 Python | `F:\PLD\.venv-vision\Scripts\python.exe`（mediapipe 0.10.21、opencv 4.11，工作区外，只引用） |
| 音频/下载 Python | `F:\PLD\.venv-audio\Scripts\python.exe`（sherpa-onnx 等，工作区外，只引用） |
| ASR 模型 | `F:\PLD\asr_test\sherpa-onnx-streaming-zipformer-zh-14M-2023-02-23`（工作区外） |
| 板卡 | PYNQ-Z2 @ `192.168.2.99`，SSH免密已配；sudo凭据由操作者提供，不写入文档；UART在COM5@115200 |
| 机器内存 | 32GB；Vivado 并行构建会 OOM（见 §4） |

### 1b. 通用工程参数【通用】

| 项 | 值 |
|---|---|
| GitHub 远程 | `git@github.com:ichuan256/Sign-Language-Vision-Recognition.git`（SSH 协议，勿用 HTTPS） |
| 目标器件 | Zynq-7020 `xc7z020clg400-1`，Vivado 2024.1 工程 `project/fpga/project/glove/glove.xpr` |
| 最近部署 | 以 `docs/当前状态.md` 及其链接的候选清单为准；不同发布包不能混用 |
| 历史 W6 固件 | `project/board/w6/kws_hdmi.bit/.hwh`，含旧传感器/KWS、音频、HDMI和BTN GPIO；不是最近部署，闲置模块是否剥离由资源实测决定 |
| 视觉特征契约 | 392 维 `sign_xy_v1`（`vision/src/vision/sign_video/features.py`）；帧源统一接口 `vision/src/vision/framesource/` |
| 依赖版本 | mediapipe 0.10.21、opencv 4.11、numpy 1.26、sherpa-onnx（流式 zipformer-zh-14M） |

## 2. 全局铁律【通用】（违者会烧板子/丢数据，已各有血泪史）

1. **运行中的板子绝不二次加载 bitstream**——100% 硬复位。新 bit 一律 scp 覆盖后 `sudo reboot`，由冷启动加载一次；接管已加载的固件一律 `Overlay(path, download=False)`。
2. **不要运行任何加载 `base.bit` 的旧脚本**（`ASR/recog_live_ncnn.py`、`ASR/recog_ncnn.py` 等）——会覆盖合一固件并硬复位。
3. **bit 与 hwh 必须成对、同目录、同批次部署**，哈希以所部署候选自身的 release manifest 为准核对；W6 清单只适用于 W6 固件，不能拿旧哈希判断新候选。
4. **视频媒体本体不入库**（`.gitignore` 已排 `vision/video/` 等）；素材库只留本地。
5. **Cookie/令牌/密码不落盘、不打印、不提交**；**不要碰 Edge 的 Cookie 数据库**（应用绑定加密，碰了会被清空——2026-10-20 已出过一次事故）。
6. 删文件、改启动项、动用户浏览器配置前，先向用户确认。
7. **动手前确认没有并行会话在写本仓库**——2026-10-23 已发生两会话并行写 `vision/` 互相覆盖的事故。发现他人新增文件先读、再合并，不覆盖不删除。

## 3. 常用操作卡片【通用流程 + 本机路径】

> 命令里的绝对路径是本机的（见 §1a）；流程与脚本参数【通用】，队友机器上替换路径即可。

### 3.1 历史 W6 构建卡（Vivado，Windows 批处理）

以下命令仅构建 W6，不用于生成最近的 OV1 视听候选。OV 发布包和构建入口见 `project/board/ov5640_snapshot/README.md`；新开发使用隔离工程、串行构建。

```bat
:: 历史 W6 合一固件构建
F:\PLD_new\Sign-Language-Vision-Recognition\project\fpga\scripts\run_w6_hdmi.bat        :: 先跑：BD 应用幂等补丁
F:\PLD_new\Sign-Language-Vision-Recognition\project\fpga\scripts\launch_w6_build.bat    :: 再跑：后台构建+写日志
```

- 构建控制台日志 `project/fpga/scripts/w6_build_console.log`；产物 `kws_hdmi.bit/.hwh` 对照 `project/board/w6/release_manifest.json`
- **构建脚本里的幂等补丁**（`w6_hdmi_bd.tcl` 尾部）：剔除陈旧 wrapper、proc_sys_reset_142M 复位补齐、`axis_register_slice_0 TUSER_WIDTH=1`（不修 HDMI 黑屏）
- OOM 或中断后续跑：`run_w6_resume.bat`（串行低内存续跑）
- 判断成功：`STATUS=write_bitstream Complete!` + WNS 非负 + 无 `No ports matched`（除预留 UART 外）
- 一次性路径修正已完成（`fixup_paths.tcl`）：KWS HLS IP 仓库与 master 约束均已指向本仓库副本

### 3.2 板端部署与验证

1. 先核对 `docs/当前状态.md`，再读取实际 boot、进程和已部署配对文件。接管仅用 `Overlay(path, download=False)`。
2. 新候选按其自身 `release_manifest.json` 核验 bit/HWH及helper，保存原部署与启动项备份；修改启动项前按第2节确认。
3. 安全停止采集与输出，确认 DMA Halted 后成对部署；正常重启，由新启动周期只加载一次。不能直接使用旧W6部署命令替换最近候选。
4. 先验收固定图实屏，再接入采集、识别和音频；**脚本 EXIT=0、内部锁定及写帧计数均不等于画面正常**。

板端 Python 环境（pynq 不在系统 python 中）：

```bash
sudo env XILINX_XRT=/usr /usr/local/share/pynq-venv/bin/python script.py
```

OV候选的发布包与验证入口见 `project/board/ov5640_snapshot/README.md`。`project/board/w6/` 下的 `hdmi_probe.py`、`hdmi_go.py`、`vdma_canary.py`、`hdmi_display.py` 仅用于对应历史W6流程，不自动适配最近候选。

### 3.3 历史 M1 基线复现（电脑侧）

仅用于复现旧骨架词语实验，不是当前教师局部迁移的前置任务。

```powershell
# 仓库根目录，视觉环境
F:\PLD\.venv-vision\Scripts\python.exe -X utf8 -m vision.m1.build_manifest --output vision/data/manifests/m1_8class
F:\PLD\.venv-vision\Scripts\python.exe -X utf8 -m vision.sign_video.extract --manifest vision/data/manifests/m1_8class/m1_part1.json --output <新目录> --fps 15
F:\PLD\.venv-vision\Scripts\python.exe -X utf8 -m vision.m1.evaluate --features <提取目录>... --output <新目录>
F:\PLD\.venv-vision\Scripts\python.exe -X utf8 -m vision.m1.live_demo --source file:<片段> --templates <提取目录>...
```

- 旧帧源抽象 `vision/src/vision/framesource/` 中 file:/usb: 可用，hdmi:/ov5640: 为占位；实际 OV 采集接入位于 `vision/src/vision/keypoints/ov5640_ssh_source.py`，需配套固件及启动核验
- 特征契约 392 维 sign_xy_v1（`vision/src/vision/sign_video/features.py`），掩码不插值、同源同组
- 首版基线结果与复现细节：`vision/src/vision/m1/README.md`

### 3.4 历史 W6 音频线（一键启动）

**仅在匹配 W6 固件已冷启动并验收后使用。** 最近 OV 视听候选使用控制台显式候选核验，先恢复实屏再接听觉；不得直接运行下列旧监督入口。

```powershell
F:/PLD/.venv-audio/Scripts/python.exe -X utf8 ASR/run_audio_line.py --model F:/PLD/asr_test/sherpa-onnx-streaming-zipformer-zh-14M-2023-02-23
```

- 启动器自带：bit 哈希核对 → 板端脚本部署 → gcc 编译 → 双向隧道 → ASR + 画面接收
- 浏览器 `http://127.0.0.1:8765`；板端资产根 `/home/xilinx/video/`
- 细节与验收顺序：`ASR/README.md`

### 3.5 Git 协作

```bash
git add -A
git pull --no-rebase --no-edit origin main  # 本仓库一贯 merge 风格
git push origin main
```

- `non-fast-forward` = 远程有新提交，先 pull
- 【本机专用】代理没开先开猫猫云；大包低速期分段推 `git push origin <sha>:main`

## 4. 踩过的坑速查【通用】（别再踩）

| 现象 | 根因 | 处置 |
|---|---|---|
| 板子换 bit 死机 | Zynq 此板重配置必硬复位 | 冷启动加载一次，见 §2.1 |
| 历史 W6 黑屏、PS 读 PL 寄存器死机 | 当时的142M域复位/时钟链及TUSER问题 | 对应 `w6_hdmi_bd.tcl` 补丁；不是最近无信号的已证实根因 |
| 历史 `HDMI_enable` 字段误导 | R19本应是反相HPD输入，却被旧设计作为GPIO输出 | 新候选改为输入；字段改看 `HPD_n`，不能将旧GPIO写高当作显示恢复操作 |
| **Git Bash 直调 vivado 无输出/假死** | MSYS 环境缺 UCRT DLL，且 batch 模式挂 stdin 成僵尸 | **一律 `cmd //c run_*.bat`**；僵尸用 `taskkill //PID <pid> //F`（PID 以 tasklist 为准，ps -W 列错位） |
| **残留 vivado.exe 导致新构建 BD 打开报 `bd.tcl: No error`** | 僵尸进程锁安装目录文件 | tasklist 查、`taskkill //F` 清干净再构建（2026-10-23 实测） |
| Vivado `bad allocation`/OOM | 并行 IP 综合内存爆（有残留进程时更易发） | 清残留 vivado.exe，跑 `run_w6_resume.bat`（串行续跑） |
| **重建固件 module_ref 报参数不存在** | BD 用旧参数集（如 merge_stream 的 CLK_FREQ_HZ），main 新版 RTL 已删 | `fpga/rtl/` 是发布当日冻结版，见该目录 README；**勿在此目录做新开发** |
| 板上 systemd 服务里 pynq 报 `No Devices Found` | 缺 XRT 环境变量 | service 里加 `Environment=XILINX_XRT=/usr`（button-watch.service 2026-10-23 已踩） |
| 板上 `import pynq` 失败 | pynq 在 pynq-venv，不在系统 python | `sudo env XILINX_XRT=/usr /usr/local/share/pynq-venv/bin/python` |
| ping 不通板子 | JP1 不在 SD 侧 / eth0 别名未生效 | 跳线 SD 侧；上电后等 1~3 分钟 |
| 并行会话改仓库互相覆盖 | 两 agent 同写 `vision/` | 铁律 §2.7；合并记录见 `vision/src/vision/m1/README.md` |
| 板端 ASR 旧脚本 | 会加载 base.bit | 已标记过期，禁止运行 |

## 4b. 历史 W6 的 BTN0 音频演示【设计通用；部署实例本机专用】

以下为2026-10-23的部署说明，仅适用于对应 W6 固件。最近 OV 视听候选不含该按钮链，旧 `button-watch` 已禁用；不得把下面的开机和按键行为当作当前保证。

**用法**：板子通电 → 等 2~3 分钟（固件冷启动 + PC 常驻服务就绪）→ 按一下 **BTN0**
（LD0 旁的按钮）→ 约 1 秒后开始识别，HDMI 出字幕与手语视频。停止用网页
`http://127.0.0.1:8765` 的停止钮，（重复按 BTN0 仍为幂等开始）。

**链路**：BTN0 → `axi_gpio_btns`（0x43C10000，固件 build_manifest_20261023_btngpio）
→ 板端 `button-watch.service`（`project/board/w6/button_watch.py`）
→ ssh 触发隧道（板端 18770 → PC 18770，免防火墙入站规则）
→ PC 常驻服务 `ASR/audio_resident.py`（开机自启：Startup 文件夹
`audio_resident_autostart.bat`；ASR 模型开机预载，app 待机不识别）
→ POST `/start` 开始识别。演示监督仍由 `run_audio_line.py` 负责（被收养不重复加载）。

**注意**：板子先开、PC 后开时按键会被忽略（隧道未建），PC 就绪后再按一次。
日志：PC 侧 `project/_tmp/audio_resident.log`；板侧 `journalctl -u button-watch.service`。

## 5. 状态与证据入口【通用】（动手前必读）

| 文档 | 内容 |
|---|---|
| `docs/当前状态.md` | 接手第一入口：最近部署、实屏结果、计算位置与未结待办 |
| `docs/方案/01_PYNQ-Z2移植与视频手势识别总体方案.md` | 系统总体背景；视觉加速范围以04方案及用户覆盖指令为准 |
| `project/M0_移植清单.md` | 移植资产清单与点亮步骤 |
| `project/board/w6/README.md` + `release_manifest.json` | 历史W6固件验收、当时黑屏根因与发布哈希 |
| `vision/src/vision/m1/README.md` | 历史M1基线结果与复现、并行合并说明 |
| `ASR/README.md` | 音频线现状、启动、验收顺序 |
| `vision/analysis/README.md` | 分析目录索引；区分当前资料和历史实验证据 |
| `vision/analysis/dataset/README.md` | 当前样本总量、有效评测限制、标签复核与补采计划 |
| `docs/方案/04_老师模型PS_PL局部迁移.md` | 当前教师网络局部加速方案、阶段交付及验收 |
| `project/board/teacher_hands/README.md` | PS 老师模型、运行库与接入边界 |
| `project/analysis/teacher_partition_20261028/README.md` | 老师模型实际图清单与候选子图证据 |
| `project/analysis/r3/README.md` | 历史词语分类器的量化/HLS 证据；不属于当前关键点加速任务 |
| `vision/data/README.md` + `vision/tools/README.md` | 数据/清单与辅助工具目录；原剪辑记录在 `vision/data/manifests/`，原剪裁方法在 `vision/tools/clipping/` |
| `docs/协作/素材工作区约定.md` | 当前551条可用子集、待审版本及路径映射 |
| `vision/video/`（不入库） | 素材库；精剪清单在 `vision/video/done/*/manifest_*_reviewed_*.csv` |

## 6. 当前任务与接手顺序【通用】（整理于 2026-11-01）

**最近部署、实屏结果、已完成项和待办统一看 [docs/当前状态.md](docs/当前状态.md)。** 不再在本文件累加相互覆盖的“当前状态”；原状态段保存在 [清理前历史快照](project/analysis/av_three_panel_20261031/AGENTS状态快照_清理前_20261101.md)。

- **显示接管**：先按统一状态核对最新实屏验收，复用已点亮的owner及显存，再逐级接入视觉与听觉；不重复初始化视频前端。旧无信号记录、旧双目网页和单目分屏不能覆盖后续已完成的彩条/三栏验收。
- **接管先核对**：读取当前 boot、bit/HWH/manifest、进程身份与 DMA 状态，再复用已有输出。旧 PID 和 active=true 文件不证明存活；不能为迁就 W6 哈希重载位流。
- **教师局部迁移**：只按04方案，保留 PS full 教师，P1 后处理及边界重放已验证；下一步测 cpu_test 连续分区接图及 XNNPACK 拆分损耗，再决定 HLS。尚无新 PL 加速，不需要人工标注或训练。
- **听觉**：557项映射/575种写法/563份播放视频已入活动清单，SD同步核验完成；最新固件的真实语音与视觉联合闭环、音频交付和长期稳定性仍待验收。
- **USB语义实验**：用户另行授权的5词时序模板演示保留，来源留出3/11不能作为摄像头准确率；不恢复关键点学生训练。其余历史分类器、蒸馏、QAT与学生HLS不继续推进。
- **数据与目录**：551条活动素材、85条待审版本与ASR播放素材按各自清单统计；不盲扫覆盖、不改媒体路径。vision主目录保持 src、scripts、tests、data、analysis、tools、video，源码位于 vision/src/vision；视频本体不入库。

更换固件、启动项和安全停机继续遵守第2节。最近部署不含旧 W6 BTN0/lite PL 关键点链，禁止直接使用历史一键启动卡片。
