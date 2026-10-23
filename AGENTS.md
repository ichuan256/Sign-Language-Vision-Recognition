# AGENTS.md · 接手工具链操作手册（Sign-Language-Vision-Recognition）

> 面向接手本项目的 AI agent（Kimi / Codex 等）。读完这份文件，你应该能**完全接管**这台机器上的全部工具链：FPGA 构建、板端部署、视频手势识别线、音频线、git 协作。
> 原则：**先读状态文档再动手；危险动作先问用户；一切证据落到文件。**
> 本文档由 `F:\PLD\pld-sign-glove\AGENTS.md`（2026-10-22 版）适配而来，适配日期 2026-10-23。本工程从 pld-sign-glove 移植 HDMI + 音频线，**不含传感器部分**，新增视频输入高动态手势识别线。

---

## 1. 环境与路径速查

| 项 | 位置 / 值 |
|---|---|
| 仓库根 = 工作区根 | `F:\PLD_new\Sign-Language-Vision-Recognition`（一切产出都在此目录内，别写到别处） |
| GitHub 远程 | `git@github.com:ichuan256/Sign-Language-Vision-Recognition.git` —— **走本机代理** |
| 代理 | Clash 在 `127.0.0.1:7897`；`~/.ssh/config` 里 github.com 走 ProxyCommand。**代理没开时 git 报 `errno=10061`** |
| Vivado/Vitis | 2024.1，`F:\APP\Xilinx\Vivado\2024.1\bin\vivado.bat`（**必须走 cmd 批处理调用，见 §4**） |
| 视觉 Python | `F:\PLD\.venv-vision\Scripts\python.exe`（mediapipe 0.10.21、opencv 4.11，工作区外，只引用） |
| 音频/下载 Python | `F:\PLD\.venv-audio\Scripts\python.exe`（sherpa-onnx 等，工作区外，只引用） |
| ASR 模型 | `F:\PLD\asr_test\sherpa-onnx-streaming-zipformer-zh-14M-2023-02-23`（工作区外） |
| 板卡 | PYNQ-Z2 @ `192.168.2.99`，SSH 免密已配；sudo 密码 `xilinx`；UART 在 COM5@115200 |
| 板卡固件 | `pynq-vision/board/w6/kws_hdmi.bit/.hwh`（旧 W6 合一固件：含传感器 SPI+DMA、旧 HLS KWS、音频 codec、HDMI 输出。**传感器与 KWS 在新系统闲置不用**，M0b 重建时剥离，见方案 §5 D3） |
| 机器内存 | 32GB；Vivado 并行构建会 OOM（见 §4） |

## 2. 全局铁律（违者会烧板子/丢数据，已各有血泪史）

1. **运行中的板子绝不二次加载 bitstream**——100% 硬复位。新 bit 一律 scp 覆盖后 `sudo reboot`，由冷启动加载一次；接管已加载的固件一律 `Overlay(path, download=False)`。
2. **不要运行任何加载 `base.bit` 的旧脚本**（`asr/recog_live_ncnn.py`、`asr/recog_ncnn.py` 等）——会覆盖合一固件并硬复位。
3. **bit 与 hwh 必须成对、同目录、同批次部署**，哈希以 `pynq-vision/board/w6/release_manifest.json` 为准核对。
4. **视频媒体本体不入库**（`.gitignore` 已排 `video/` 等）；素材库只留本地。
5. **Cookie/令牌/密码不落盘、不打印、不提交**；**不要碰 Edge 的 Cookie 数据库**（应用绑定加密，碰了会被清空——2026-10-20 已出过一次事故）。
6. 删文件、改启动项、动用户浏览器配置前，先向用户确认。
7. **动手前确认没有并行会话在写本仓库**——2026-10-23 已发生两会话并行写 `vision/` 互相覆盖的事故。发现他人新增文件先读、再合并，不覆盖不删除。

## 3. 常用操作卡片

### 3.1 FPGA 构建（Vivado，Windows 批处理）

```bat
:: 合一固件构建（约 6-8 分钟）
F:\PLD_new\Sign-Language-Vision-Recognition\pynq-vision\fpga\scripts\run_w6_hdmi.bat        :: 先跑：BD 应用幂等补丁
F:\PLD_new\Sign-Language-Vision-Recognition\pynq-vision\fpga\scripts\launch_w6_build.bat    :: 再跑：后台构建+写日志
```

- 构建控制台日志 `fpga/scripts/w6_build_console.log`；产物 `kws_hdmi.bit/.hwh` 对照 `board/w6/release_manifest.json`
- **构建脚本里的幂等补丁**（`w6_hdmi_bd.tcl` 尾部）：剔除陈旧 wrapper、proc_sys_reset_142M 复位补齐、`axis_register_slice_0 TUSER_WIDTH=1`（不修 HDMI 黑屏）
- OOM 或中断后续跑：`run_w6_resume.bat`（串行低内存续跑）
- 判断成功：`STATUS=write_bitstream Complete!` + WNS 非负 + 无 `No ports matched`（除预留 UART 外）
- 一次性路径修正已完成（`fixup_paths.tcl`）：KWS HLS IP 仓库与 master 约束均已指向本仓库副本

### 3.2 板端部署与验证

```bash
# 部署固件（成对）
scp pynq-vision/board/w6/kws_hdmi.bit pynq-vision/board/w6/kws_hdmi.hwh xilinx@192.168.2.99:/home/xilinx/
ssh xilinx@192.168.2.99 "sha256sum /home/xilinx/kws_hdmi.bit"   # 对 release_manifest.json
ssh xilinx@192.168.2.99 "echo xilinx | sudo -S reboot"           # 重启加载

# 板端 Python 环境（pynq 不在系统 python 里！）
sudo env XILINX_XRT=/usr /usr/local/share/pynq-venv/bin/python script.py
```

- HDMI 验证脚本（`pynq-vision/board/w6/`）：`hdmi_probe.py`、`hdmi_go.py`、`vdma_canary.py`、`hdmi_display.py`
- **验收必须目视屏幕**，脚本 EXIT=0 不等于画面正常

### 3.3 视频手势识别线（M1，电脑侧）

```powershell
# 仓库根目录，视觉环境
F:\PLD\.venv-vision\Scripts\python.exe -X utf8 -m vision.m1.build_manifest --output vision/m1/manifests
F:\PLD\.venv-vision\Scripts\python.exe -X utf8 -m vision.sign_video.extract --manifest vision/m1/manifests/m1_part1.json --output <新目录> --fps 15
F:\PLD\.venv-vision\Scripts\python.exe -X utf8 -m vision.m1.evaluate --features <提取目录>... --output <新目录>
F:\PLD\.venv-vision\Scripts\python.exe -X utf8 -m vision.m1.live_demo --source file:<片段> --templates <提取目录>...
```

- 帧源抽象 `vision/framesource/`：file:/usb: 可用；hdmi:/ov5640: 为 M2/M3 占位，接口已冻结
- 特征契约 392 维 sign_xy_v1（`vision/sign_video/features.py`），掩码不插值、同源同组
- 首版基线结果与复现细节：`vision/m1/README.md`

### 3.4 音频线（一键启动）

```powershell
F:/PLD/.venv-audio/Scripts/python.exe -X utf8 asr/run_audio_line.py --model F:/PLD/asr_test/sherpa-onnx-streaming-zipformer-zh-14M-2023-02-23
```

- 启动器自带：bit 哈希核对 → 板端脚本部署 → gcc 编译 → 双向隧道 → ASR + 画面接收
- 浏览器 `http://127.0.0.1:8765`；板端资产根 `/home/xilinx/video/`
- 细节与验收顺序：`asr/README.md`

### 3.5 Git 协作

```bash
git add -A
git pull --no-rebase --no-edit origin main  # 本仓库一贯 merge 风格
git push origin main
```

- 代理没开先开代理；`non-fast-forward` = 远程有新提交，先 pull

## 4. 踩过的坑速查（别再踩）

| 现象 | 根因 | 处置 |
|---|---|---|
| 板子换 bit 死机 | Zynq 此板重配置必硬复位 | 冷启动加载一次，见 §2.1 |
| HDMI 黑屏、PS 读 PL 寄存器死机 | 142M 域复位/时钟链路缺驱动 + 切片 TUSER_WIDTH=0 截断 SOF | `w6_hdmi_bd.tcl` 补丁已修复 |
| **Git Bash 直调 vivado 无输出/假死** | MSYS 环境缺 UCRT DLL，且 batch 模式挂 stdin 成僵尸 | **一律 `cmd //c run_*.bat`**；僵尸用 `taskkill //PID <pid> //F`（PID 以 tasklist 为准，ps -W 列错位） |
| **残留 vivado.exe 导致新构建 BD 打开报 `bd.tcl: No error`** | 僵尸进程锁安装目录文件 | tasklist 查、`taskkill //F` 清干净再构建（2026-10-23 实测） |
| Vivado `bad allocation`/OOM | 并行 IP 综合内存爆 | 清残留 vivado.exe，跑 `run_w6_resume.bat`（串行续跑） |
| 板上 `import pynq` 失败 | pynq 在 pynq-venv，不在系统 python | `sudo env XILINX_XRT=/usr /usr/local/share/pynq-venv/bin/python` |
| ping 不通板子 | JP1 不在 SD 侧 / eth0 别名未生效 | 跳线 SD 侧；上电后等 1~3 分钟 |
| 并行会话改仓库互相覆盖 | 两 agent 同写 `vision/` | 铁律 §2.7；合并记录见 `vision/m1/README.md` |
| 板端 ASR 旧脚本 | 会加载 base.bit | 已标记过期，禁止运行 |

## 5. 状态与证据入口（动手前必读）

| 文档 | 内容 |
|---|---|
| `docs/方案/01_PYNQ-Z2移植与视频手势识别总体方案.md` | 系统级唯一当前方案（移植范围、三阶段路线、决策点） |
| `pynq-vision/M0_移植清单.md` | 移植资产清单与点亮步骤 |
| `pynq-vision/board/w6/README.md` + `release_manifest.json` | HDMI 合一固件验收、黑屏根因、发布哈希 |
| `vision/m1/README.md` | 视频识别线现状、首版基线结果、并行合并说明 |
| `asr/README.md` | 音频线现状、启动、验收顺序 |
| `video/`（不入库） | 素材库；精剪清单在 `video/done/*/manifest_*_reviewed_*.csv` |

## 6. 当前未结待办（接手时核对）

- M0 收尾：新工程全量构建出 bit 并与 release 对照；板端点亮 + 音频回路复验
- M0b：从空目录重建脚本化（源工程此路径未验收过）；剥离传感器 SPI/DMA 与旧 HLS KWS，释放 PL 资源
- 视觉线：`再见` 缺一条片段待核对；短词类（很/服务/待会儿见）DTW 混淆待排查；USB 摄像头实测未做
- 音频线：长期稳定性与断电自动启动未验收
- M2/M3：HDMI 输入子系统、OV5640 双目（Pmod JA/JB + Arduino IO 已预留）
