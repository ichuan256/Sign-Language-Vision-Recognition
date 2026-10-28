# AGENTS.md · 接手工具链操作手册（Sign-Language-Vision-Recognition）

> 面向接手本项目的 AI agent（Kimi / Codex 等）。读完这份文件，你应该能**完全接管**这台机器上的全部工具链：FPGA 构建、板端部署、视频手势识别线、音频线、git 协作。
> 原则：**先读状态文档再动手；危险动作先问用户；一切证据落到文件。**
> 本文档由 `F:\PLD\pld-sign-glove\AGENTS.md`（2026-10-22 版）适配而来，适配日期 2026-10-23。本工程从 pld-sign-glove 移植 HDMI + 音频线，**不含传感器部分**，新增视频输入高动态手势识别线。

## 当前视觉路线覆盖指令（2026-10-28，用户明确要求）【通用】

**保留 PS 已部署的老师模型，只把少量热点算子或连续子图迁到 PL；停止重新训练轻量学生模型。**
当前视觉加速任务仅以 `docs/方案/04_老师模型PS_PL局部迁移.md` 为执行方案。
不继续这些工作，不因性能目标自行换模型、换输入尺寸、删输出头或重新训练；现有实验产物保留为历史证据。
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
| 板卡 | PYNQ-Z2 @ `192.168.2.99`，SSH 免密已配；sudo 密码 `xilinx`；UART 在 COM5@115200 |
| 机器内存 | 32GB；Vivado 并行构建会 OOM（见 §4） |

### 1b. 通用工程参数【通用】

| 项 | 值 |
|---|---|
| GitHub 远程 | `git@github.com:ichuan256/Sign-Language-Vision-Recognition.git`（SSH 协议，勿用 HTTPS） |
| 目标器件 | Zynq-7020 `xc7z020clg400-1`，Vivado 2024.1 工程 `project/fpga/project/glove/glove.xpr` |
| 板卡固件 | `project/board/w6/kws_hdmi.bit/.hwh`（旧 W6 合一固件：含传感器 SPI+DMA、旧 HLS KWS、音频 codec、HDMI 输出、BTN0-3 GPIO。**传感器与 KWS 在新系统闲置不用**，M0b 重建时剥离，见方案 §5 D3） |
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

### 3.1 FPGA 构建（Vivado，Windows 批处理）

```bat
:: 合一固件构建（约 6-8 分钟）
F:\PLD_new\Sign-Language-Vision-Recognition\project\fpga\scripts\run_w6_hdmi.bat        :: 先跑：BD 应用幂等补丁
F:\PLD_new\Sign-Language-Vision-Recognition\project\fpga\scripts\launch_w6_build.bat    :: 再跑：后台构建+写日志
```

- 构建控制台日志 `fpga/scripts/w6_build_console.log`；产物 `kws_hdmi.bit/.hwh` 对照 `board/w6/release_manifest.json`
- **构建脚本里的幂等补丁**（`w6_hdmi_bd.tcl` 尾部）：剔除陈旧 wrapper、proc_sys_reset_142M 复位补齐、`axis_register_slice_0 TUSER_WIDTH=1`（不修 HDMI 黑屏）
- OOM 或中断后续跑：`run_w6_resume.bat`（串行低内存续跑）
- 判断成功：`STATUS=write_bitstream Complete!` + WNS 非负 + 无 `No ports matched`（除预留 UART 外）
- 一次性路径修正已完成（`fixup_paths.tcl`）：KWS HLS IP 仓库与 master 约束均已指向本仓库副本

### 3.2 板端部署与验证

```bash
# 部署固件（成对）
scp project/board/w6/kws_hdmi.bit project/board/w6/kws_hdmi.hwh xilinx@192.168.2.99:/home/xilinx/
ssh xilinx@192.168.2.99 "sha256sum /home/xilinx/kws_hdmi.bit"   # 对 release_manifest.json
ssh xilinx@192.168.2.99 "echo xilinx | sudo -S reboot"           # 重启加载

# 板端 Python 环境（pynq 不在系统 python 里！）
sudo env XILINX_XRT=/usr /usr/local/share/pynq-venv/bin/python script.py
```

- HDMI 验证脚本（`project/board/w6/`）：`hdmi_probe.py`、`hdmi_go.py`、`vdma_canary.py`、`hdmi_display.py`
- **验收必须目视屏幕**，脚本 EXIT=0 不等于画面正常

### 3.3 视频手势识别线（M1，电脑侧）

```powershell
# 仓库根目录，视觉环境
F:\PLD\.venv-vision\Scripts\python.exe -X utf8 -m vision.m1.build_manifest --output vision/data/manifests/m1_8class
F:\PLD\.venv-vision\Scripts\python.exe -X utf8 -m vision.sign_video.extract --manifest vision/data/manifests/m1_8class/m1_part1.json --output <新目录> --fps 15
F:\PLD\.venv-vision\Scripts\python.exe -X utf8 -m vision.m1.evaluate --features <提取目录>... --output <新目录>
F:\PLD\.venv-vision\Scripts\python.exe -X utf8 -m vision.m1.live_demo --source file:<片段> --templates <提取目录>...
```

- 帧源抽象 `vision/src/vision/framesource/`：file:/usb: 可用；hdmi:/ov5640: 为 M2/M3 占位，接口已冻结
- 特征契约 392 维 sign_xy_v1（`vision/src/vision/sign_video/features.py`），掩码不插值、同源同组
- 首版基线结果与复现细节：`vision/src/vision/m1/README.md`

### 3.4 音频线（一键启动）

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
| HDMI 黑屏、PS 读 PL 寄存器死机 | 142M 域复位/时钟链路缺驱动 + 切片 TUSER_WIDTH=0 截断 SOF | `w6_hdmi_bd.tcl` 补丁已修复 |
| **Git Bash 直调 vivado 无输出/假死** | MSYS 环境缺 UCRT DLL，且 batch 模式挂 stdin 成僵尸 | **一律 `cmd //c run_*.bat`**；僵尸用 `taskkill //PID <pid> //F`（PID 以 tasklist 为准，ps -W 列错位） |
| **残留 vivado.exe 导致新构建 BD 打开报 `bd.tcl: No error`** | 僵尸进程锁安装目录文件 | tasklist 查、`taskkill //F` 清干净再构建（2026-10-23 实测） |
| Vivado `bad allocation`/OOM | 并行 IP 综合内存爆（有残留进程时更易发） | 清残留 vivado.exe，跑 `run_w6_resume.bat`（串行续跑） |
| **重建固件 module_ref 报参数不存在** | BD 用旧参数集（如 merge_stream 的 CLK_FREQ_HZ），main 新版 RTL 已删 | `fpga/rtl/` 是发布当日冻结版，见该目录 README；**勿在此目录做新开发** |
| 板上 systemd 服务里 pynq 报 `No Devices Found` | 缺 XRT 环境变量 | service 里加 `Environment=XILINX_XRT=/usr`（button-watch.service 2026-10-23 已踩） |
| 板上 `import pynq` 失败 | pynq 在 pynq-venv，不在系统 python | `sudo env XILINX_XRT=/usr /usr/local/share/pynq-venv/bin/python` |
| ping 不通板子 | JP1 不在 SD 侧 / eth0 别名未生效 | 跳线 SD 侧；上电后等 1~3 分钟 |
| 并行会话改仓库互相覆盖 | 两 agent 同写 `vision/` | 铁律 §2.7；合并记录见 `vision/src/vision/m1/README.md` |
| 板端 ASR 旧脚本 | 会加载 base.bit | 已标记过期，禁止运行 |

## 4b. BTN0 一键启动音频演示（2026-10-23 起）【设计通用；部署实例本机专用】

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
| `docs/方案/01_PYNQ-Z2移植与视频手势识别总体方案.md` | 系统级唯一当前方案（移植范围、三阶段路线、决策点） |
| `project/M0_移植清单.md` | 移植资产清单与点亮步骤 |
| `project/board/w6/README.md` + `release_manifest.json` | HDMI 合一固件验收、黑屏根因、发布哈希 |
| `vision/src/vision/m1/README.md` | 视频识别线现状、首版基线结果、并行合并说明 |
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

## 6. 当前未结待办【通用】（2026-10-28）

- **视觉首要任务**：冻结 PS 已部署的 `palm_detection_full` 与 `hand_landmark_full`，按 04 方案完成基线、热点剖析、单段 PL 接入和端到端对照。首轮只接入 landmark 的一个候选子图，palm、跟踪和其他计算留在 PS；候选是否采用由实测收益决定。
- **当前进度**：P1 已完成 PS 后处理等价优化，两轮各 120 帧配对的全部网络输入/输出和跟踪状态一致，平均处理约 1.57→1.01 秒/帧（不写屏，PS 优化）。100 个真实 ROI 的四输出及单块/双块独立重放逐值一致；CMA 复制/缓存维护约 1.386ms。当前接图候选为 87/90/93/94/97/100/103/104 相邻双块组成的一个连续分区；先测 cpu_test 接图及 XNNPACK 拆分损耗，再决定 HLS。证据 `project/analysis/teacher_partition_20261028/p1.md`。原部署模型/库/源码和固件未覆盖，未实现新 PL 加速；不需要人工标注或训练。历史 0.49 秒/ROI 属于旧 lite 整网 PL 路线。
- **板端状态需现场核对**：先读当前 bit/hwh、运行库 SHA 和进程，再接管或安排冷部署。历史记录不能代表当前已加载固件；不能为迁就旧 ASR 核验哈希在运行中重载 bit。
- **精度验证**：对齐冻结老师的所有输出和连续跟踪行为，不再用学生 PCK 或人工标注补采驱动训练。保留已有数据与实验原件，停止学生训练、蒸馏、QAT 和学生 HLS 开发。
- **视频输入与显示**：先用板内有界视频/原始帧回放验证；摄像头采集状态另按硬件证据核对。HDMI 扫描率、raw 写帧吞吐、视频播放率均不能当关键点新结果率；同时记录颜色、帧号和帧龄。
- **硬件构建**：现有 M0 HDMI/音频移植已验收；新增加速器用隔离工程串行构建。是否剥离闲置传感器/KWS 由实测资源决定，不把旧 lite 整网核一并带入新方案。音频/按键/视频契约与冷启动安全规则继续有效。
- **音频待验收**：长期稳定性、断电自动启动，以及 BTN0 停止语义；现有实现重复按键为开始，停止走网页。
- **其余视觉任务暂停推进**：词义分类、R3 分类器优化、学生训练及历史复核队列均非本轮前置条件。现有数据审计不等于语义清洗或跨人物精度验收。
- **目录约定**：`vision/` 的主目录仍为 src、scripts、tests、data、analysis、tools、video；运行源码在 `vision/src/vision/`，模型在 `vision/data/models/`。不要重建顶层 keypoints/m1/models，媒体路径保持原样。
- **素材边界**：551 条活动池与 85 条待审版本分开；新素材进 inbox，新输出绑定清单/SHA，不盲扫覆盖旧清单。旧裁剪样例与 ASR 词库保留。完整核验记录见 `docs/协作/媒体清单修复_20261026.md`。
