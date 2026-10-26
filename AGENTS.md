# AGENTS.md · 接手工具链操作手册（Sign-Language-Vision-Recognition）

> 面向接手本项目的 AI agent（Kimi / Codex 等）。读完这份文件，你应该能**完全接管**这台机器上的全部工具链：FPGA 构建、板端部署、视频手势识别线、音频线、git 协作。
> 原则：**先读状态文档再动手；危险动作先问用户；一切证据落到文件。**
> 本文档由 `F:\PLD\pld-sign-glove\AGENTS.md`（2026-10-22 版）适配而来，适配日期 2026-10-23。本工程从 pld-sign-glove 移植 HDMI + 音频线，**不含传感器部分**，新增视频输入高动态手势识别线。

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
3. **bit 与 hwh 必须成对、同目录、同批次部署**，哈希以 `project/board/w6/release_manifest.json` 为准核对。
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
`http://127.0.0.1:8765` 的停止钮，或再按 BTN0（当前版本为幂等开始，停止走网页）。

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
| `project/analysis/r3/README.md` | 当前 PL 阶段状态及量化训练、HLS 对齐、综合证据 |
| `vision/data/README.md` + `vision/tools/README.md` | 数据/清单与辅助工具目录；原剪辑记录在 `vision/data/manifests/`，原剪裁方法在 `vision/tools/clipping/` |
| `docs/协作/素材工作区约定.md` | 当前551条可用子集、待审版本及路径映射 |
| `vision/video/`（不入库） | 素材库；精剪清单在 `vision/video/done/*/manifest_*_reviewed_*.csv` |

## 6. 当前未结待办【通用】（接手时核对）

- 当前优先级（2026-10-25）：先做无语义的通用身体/双手实时关键点，再做动作/词义分类；纯关键点入口 `vision/src/vision/keypoints/live_demo.py`，用法 `vision/src/vision/keypoints/README.md`，文件源基准 `vision/analysis/keypoints_20261025/README.md`。USB 实时、交叉/遮挡和快速运动尚未验收，文件 FPS 不能当摄像头实时 FPS。
- 通用关键点 PL：单手 21 点完整网络已上板，PC 提供规范化 ROI，PL 执行网络、PS 调度。当前流式/宽访存版为 62 次调用/ROI、36 层直接复用输入地址；同一 ROI 三次 64 输出均对整数参考完全一致，前向 0.505/0.490/0.490 秒，约 2Hz，仍未达到 5Hz。当前时延及哈希见 `project/analysis/keypoints_pl_20261026/stream_wide.md/.json`；0.56 秒、1.86 秒与 12.28 秒记录保留为历史。整板 WNS 0.307ns、WHS 0.010ns，DSP 165/220、LUT 37742/53200、BRAM Tile 119.5/140。不能把 HDMI 刷新率当关键点帧率，该路线不是 R3 词语分类 CNN。
- 独立实时方向（2026-10-26 用户选定）：`docs/方案/03_Zynq7020独立实时关键点方案.md`。目标双手各20Hz、板内视频叠加；单目到货前用板端raw帧回放。教师指 MediaPipe Holistic 软件模型，不是视频授课人。40视频/674帧已导出997个有手伪标ROI，坐标试训670/136/191，96/128浮点学生已试训但人工精度、QAT/HLS/上板未验收。旧200项复核队列164项来自352×288，暂不用于正式精度标注；先重做清晰度/来源平衡。报告 `project/analysis/keypoints_student_20261026/README.md`，理论预算仍在 `project/analysis/keypoints_pl_20261026/realtime_budget/`。新学生65输出禁止混用旧64项驱动，身体网络及离线找手器需另验。
- 视觉目录物理归并（2026-10-26）：`vision/`只保留src、scripts、tests、data、analysis、tools、video七个主目录。运行源码在`vision/src/vision/`，旧嵌入库在`vision/src/signrec/`；模型`vision/data/models/`，M1清单`vision/data/manifests/m1_8class/`，旧特征`vision/data/cache/m1/`。根`vision/__init__.py`维持原`python -m vision.*`入口。不要在顶层重新创建keypoints/m1/models目录；媒体路径不变。
- 【本机专用】板上当前为整层加速候选，旧 W6 本地发布文件未覆盖；HDMI 接管显式指定当前 `--release-manifest`。旧 ASR 固件核验可能拒绝，未验收本候选音频；禁止为迁就旧哈希运行中重载 bit。上一版 12.276 秒固件备份记录在 `project/_tmp/kp_layer_deploy_v1/deployment.json`，更早 W6 备份在 `project/_tmp/kp_board_deploy_v2/deployment.json`。
- PL 动态演示入口：`python -m vision.keypoints.dynamic_pl`，板端常驻 `stream_hand_board.py`；使用已知视频及缓存 PC ROI 定位，没有 CPU 网络回退。当前左侧仅黄色 PC ROI 框，右侧实际 PL 输入与骨架，不重锚旧姿态。PC 发布目标 15fps 不等于 HDMI 或 PL 帧率，流式版并发前向约 0.51～0.57 秒/ROI。新版动态 HDMI 已由用户确认视频正常、PL 持续更新；证据见 `project/analysis/keypoints_pl_20261026/stream_wide.md/.json`。600 秒有界运行结束后保留最后一帧，长期稳定性未据此验收。`show_hand_result.py` 只用于静态验收。
- M0 已完成：新工程全量重建出 bit、板端点亮 + 音频回路复验通过（2026-10-23，见移植清单）
- M0b：从空目录重建脚本化（源工程此路径未验收过）；剥离传感器 SPI/DMA 与旧 HLS KWS，释放 PL 资源
- 视觉线：`再见` 缺一条片段待核对；短词类（很/服务/待会儿见）DTW 混淆待排查；USB 摄像头实测未做
- 音频线：长期稳定性与断电自动启动未验收；BTN0 停止语义（当前幂等开始，停止走网页）
- 当前输入路线（2026-10-25 用户更新）：单目 OV5640 未到货，只留 `OV5640MonoSource` 接口；原双目路线改为历史兼容。先用 `replay:` 录制视频按实时节拍模拟摄像头，PC 叠加关键点后传到板卡 HDMI；操作卡 `vision/src/vision/keypoints/HDMI_REPLAY.md`。连续运动已目视确认；接收有时限，到时保留最后一帧，不能误当作仍在播放。
- 路线 3：HLS C 综合已跑通，资源/时序门禁未通过，未导出 IP；阶段状态与证据只在 `project/analysis/r3/README.md` 汇总，复跑脚本放 `project/scripts/r3/`。
- 数据：清单审计已完成，语义清洗/人物标注/补采未完成；当前样本与补采只在 `vision/analysis/dataset/README.md` 汇总，审计工具放 `vision/scripts/dataset/`。提交者署名不能当人物 ID。

- 本机素材（2026-10-26）：活动池仍为551条，CSV/SHA不变；第二三课现存85条匹配原审计SHA，位于`done/wsy/第2 第3课`，仍单列待审，不自动纳入551池。新待审表由`current_available_fullframe.json`绑定。`protected_media_current.json`登记780个在场媒体与36个缺失（31原片、5旧演示）；32行来源索引仅1个原片在场，旧BV sources.json也缺失。逐项证据见`docs/协作/媒体清单修复_20261026.md`。新素材先放inbox，新输出绑定审核清单/SHA；禁止盲扫覆盖旧清单。旧裁剪测试样例1条、ASR词库142条必须保留。
- 轻量关键点R1（2026-10-27）：用户覆盖后的17项人工结果已冻结导入（11坐标、1部分手有手判断、2无手、2ROI退回、1无法判断），无需再导回网页。40条1080p视频的614个手ROI按320/106/188分组，人工坐标6/3/2。训练仅1个负例，本轮显式禁用presence损失及辅助零损失图片；presence出口不可用。训练集中发现8ROI/99个教师点投影到画外，新增几何掩码（全划分312点），原值及人工标签保留。96/128已重新浮点训练并独立复评，教师留出NME 0.1856/0.1890、PCK@0.05 8.88%/7.05%，未过定位门禁；人工留出仅2帧，开发留出已多次查看，不能报告通用/跨人物精度。训练在`project/_tmp/hand_student_reviewed_20261027_v2`，当前证据`project/analysis/keypoints_student_20261027/README.md`及`reviewed_training.json`；旧试跑保留历史。未QAT/HLS/部署新学生，板上仍为0.49秒旧图。204测试＋32子测试通过。
- 板内视频V1：720p raw短循环120秒2880次写入，约24次/秒、0错过时隙，复制P95 5.55ms；这是帧缓冲吞吐，不含网络推理。用户暂时无法目视，VSync、无撕裂、物理帧率、端到端帧龄、断网及推理并发均未验收。证据`project/analysis/keypoints_pl_20261026/raw_video.md/.json`；有界测试已结束，HDMI保留最后一帧。
- R1拟合诊断（2026-10-27）：仅用冻结17项复核中的6条人工训练ROI（4视频、2来源组），96网络固定输入、无增强、只监督XY，150步后全点126/126及指尖30/30的PCK@0.05均100%，连续3次检查达标；平均手形仅11.90%，5种输入错位对照平均16.35%，独立重载NME差0，未监督head列参数变化0。模型/输入在`project/_tmp/hand_overfit6_20261027_v1`，证据`project/analysis/keypoints_student_20261027/overfit6.md/.json`，脚本`overfit_hand_student.py fit/verify`。这只是记忆诊断，不是识别率或泛化通过；验证/开发留出未参与，正式模型及板卡未变。下一步固定训练/验证数据与预算做增强/监督消融并补数据，不能将诊断模型用于QAT或板端。206测试＋32子测试通过。
