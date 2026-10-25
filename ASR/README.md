# 实时音频字幕与手语视频闭环

2026-10-20 更新。当前工作优先完成此线，传感器与视觉训练扩展暂缓。目标是麦克风实时识别、字幕更新、对应手语视频连播，以及板端 HDMI 复验。

## 统一启动与恢复

在仓库根目录运行以下一条命令，按提示输入板卡 sudo 密码；SSH 使用已有密钥登录。模型目录和初始化过的 SD 素材必须存在，不会在线下载模型或重刷 FPGA。

```powershell
F:/PLD/.venv-audio/Scripts/python.exe -X utf8 ps/asr/run_audio_line.py --model F:/PLD/asr_test/sherpa-onnx-streaming-zipformer-zh-14M-2023-02-23
```

启动器检查发布 bit 的文件哈希与开机加载服务，部署音频和显示接收脚本、编译 PS 采样程序，建立双向隧道，再启动 ASR 和画面接收。已有原显示进程保持运行；不存在时才启动原矩形程序。启动日志不代替屏幕目视确认。

启动器运行期间会恢复退出的隧道和服务。音频断流会清除未确认片段并重连，避免拼接断线前后的语音；画面连接断开时显示恢复提示，恢复后重新写入有效画面。音频格式或原显示所有者、帧地址异常仍报错，不能忽略。

浏览器打开 `http://127.0.0.1:8765`。统一启动默认使用板端麦克风并开始聆听，界面的“停止聆听”仍有效。退出启动器用 Ctrl+C，它清理自己创建的电脑服务与隧道，不重刷 FPGA、不释放原输出进程的帧缓冲。不要同时启动旧手工服务或第二个启动器；端口 18767 防止重复启动，已有其他 8765 服务会报告冲突。

日志在 `project/_tmp/audio_line/`，sudo 密码仅用于当前启动器进程，不写入仓库，也不传给识别服务。这个入口是手动启动后守护，不代表已经安装 Windows 登录启动项或板卡全自动开机服务。

2026-10-20 已实际验证专用 SSH 隧道中断后音频与 HDMI 自动恢复、原显示 PID 保持不变；专项回归增加到 10 项，包括网络恢复与 Windows 子进程退出清理。冷启动后全自动恢复及更长时间负载仍需另行验证，见本轮记录（历史引用，当前仓库未收录原报告）。

## 当前状态

- 2026-10-20 自动恢复后，用户分别测试“你好”“早上好”“谢谢”，明确确认“字幕和三个视频都正常”。五词库基础音频闭环通过本轮现场复验；本次逐条覆盖三条，不据此声称五类定量准确率或完整教学词库已验收。

- 新增电脑端离线流式 ASR 服务，逐块处理音频并更新临时字幕，语音端点确认后生成一次播放任务。
- 实测现有 `你好/000.wav` 经现有中文模型识别为“你好”，字幕图像正确，未配置素材时显示缺失。
- 真实 ASR 输出触发测试视频解码与播放，12 帧测试片段完整播放，任务完成一次；该片段仅验证软件通路，不是手语素材，不用于正式演示。
- 原有识别与播放检查，加上音频断流重连和 Windows 子进程退出清理，共 10 项专项回归通过。
- 用户已接好板端麦克风并重新开机，原矩形已由用户确认可见。当前使用 W6 中的 LINE IN 左声道，不加载 base.bit，也不使用电脑麦克风。
- 板端三秒探测：48 kHz，左声道 RMS 0.0732、峰值 0.8948，右声道接近静音。已部署连续原生采样及本地 HTTP 音频服务，经 SSH 转发供电脑 ASR 使用。
- 已从指定 B 站视频下载 22 个分段，整理第一课的五条静音手语片段，复制到板卡 SD。电脑启动时从 SD 读取并验证哈希后缓存，见[素材共享约定](../docs/协作/共享包说明.md)。
- 现场音频日志已识别“你好”并触发真实手语片段；用户已明确确认“字幕和对应视频都正常”。保存快照时 4 次任务完成，共 176 帧视频，HDMI 接收持续更新，帧地址保持 `0x15c00000`，见联调记录（历史引用，当前仓库未收录原报告）。
- 识别停止后重新开始、实际 SSH 通信中断恢复均已测试。服务累计运行至少 684 秒，恢复后另采样 293 秒、60 次状态检查，无新增异常。更长期稳定性、逐类定量识别、物理断电自动启动仍待验证，没有把首批词库当作任意语句手语翻译。

## 当前板端输入模式

板端服务使用 `AudioADAU1761` 直接附着当前 W6，配置 LINE IN 后由 `board_pcm_capture.c` 按现有 PYNQ 寄存器协议连续采左声道。它运行在 PS 上，不是新增 PL 加速模块。该音频控制器没有为本程序提供可校验的采样序号，仍需评估系统抢占导致的丢采样；不能宣称无损专业音频采集。

板端编译与启动入口：

```bash
gcc -O2 -Wall -Wextra /home/xilinx/board_pcm_capture.c -o /home/xilinx/board_pcm_capture
sudo env XILINX_XRT=/usr /usr/local/share/pynq-venv/bin/python -u /home/xilinx/board_audio_stream.py
```

电脑保持以下同一条双向 SSH 隧道，若端口被占用先核查已有进程，勿重复启动：

```powershell
ssh -N -o ExitOnForwardFailure=yes -L 18766:127.0.0.1:8766 -R 18765:127.0.0.1:8765 xilinx@192.168.2.99
```

电脑启动实际闭环服务：

```powershell
F:/PLD/.venv-audio/Scripts/python.exe -X utf8 ps/asr/audio_loop.py --model F:/PLD/asr_test/sherpa-onnx-streaming-zipformer-zh-14M-2023-02-23 --manifest vision/video/phrases_sd.json --board-audio-url http://127.0.0.1:18766/pcm
```

浏览器点击开始后读的是板端麦克风。启动前必须先让板端音频/素材服务与隧道可用。局域服务连接显式绕过系统 HTTP 代理，避免本机端口被系统代理转成 502。

## 电脑端启动

工作区独立环境为 `F:/PLD/.venv-audio`，模型复用 `F:/PLD/asr_test/sherpa-onnx-streaming-zipformer-zh-14M-2023-02-23`。电脑选用 ONNX 版本是为了复用已有模型与 Windows 运行环境；历史板端 ncnn 路线保留。

```powershell
F:/PLD/.venv-audio/Scripts/python.exe -X utf8 ps/asr/audio_loop.py --model F:/PLD/asr_test/sherpa-onnx-streaming-zipformer-zh-14M-2023-02-23 --manifest ps/asr/videos.example.json
```

浏览器打开 `http://127.0.0.1:8765`，点击“开始聆听”，说完一句后稍作停顿。临时字幕会修订，最终句才触发视频。点击“停止聆听”结束麦克风采集。默认绑定本机，不需要云端语音服务；应用不保存麦克风原始录音。

独立文件验证：

```powershell
F:/PLD/.venv-audio/Scripts/python.exe -X utf8 ps/asr/audio_loop.py --model F:/PLD/asr_test/sherpa-onnx-streaming-zipformer-zh-14M-2023-02-23 --wav algo/kws/data/你好/000.wav
```

这属于录音文件识别，不代表现场麦克风测试通过。需要指定麦克风时使用 `--device`；用 sounddevice 的设备清单核对编号。

## 接入真实视频

`videos.example.json` 默认词库为空，不附带伪造手语画面。创建本机素材清单，例如：

```json
{
  "clips": [
    {"phrases": ["你好"], "file": "D:/sign-videos/hello.mp4", "label": "你好"},
    {"phrases": ["谢谢", "谢谢你"], "file": "D:/sign-videos/thanks.mp4", "label": "谢谢"}
  ]
}
```

以上路径是格式示例，必须替换成存在且动作语义核对过的文件。支持一段完整短句或多个词片段的最长匹配，去掉标点与空格后按顺序播放。未知文字显示缺失提示，不用别的词替代；重复说同一句仍产生新任务。队列最多保留四个待播句子，积压后报告本句未入队。

启动前检查文件存在性，播放时检查可解码性及帧率。字幕区显示最新识别内容，底部单独显示“当前片段所属字幕”，避免新语音覆盖旧视频对应关系。片段与其标签由同一播放器时钟推进；这是确认句后的顺序播放，尚未验收字幕边界误差或自然动作衔接。

实际首批素材已保存于板卡 SD，并在当前电脑服务启动时读取、校验。其他新增片段也必须复制并更新索引；只在电脑端保存一份不算新增 SD 素材验收通过。

## FPGA HDMI 接收

`board_validation/w6/hdmi_audio_receiver.py` 只把完整画面写入已有固定帧缓冲，不加载 Overlay，不重配视频，不分配或释放输出帧。它核对原 `hdmi_display.py` 所有者 PID/启动身份、720p 模式及四槽帧地址，变化时停止。

先按 W6 已验证恢复步骤让矩形可见并确认，再启动接收器；不要同时运行旧绘制进程。可在电脑建立 SSH 反向转发，让板卡访问本机服务，无需扩大 HTTP 监听范围：

```powershell
ssh -N -o ExitOnForwardFailure=yes -R 18765:127.0.0.1:8765 xilinx@192.168.2.99
```

板端执行（PID 必须换成当前真实所有者）：

```bash
sudo env XILINX_XRT=/usr /usr/local/share/pynq-venv/bin/python -u /home/xilinx/hdmi_audio_receiver.py --owner-pid 真实PID --url http://127.0.0.1:18765/frame.jpg --fps 10
```

接收器已在本次板卡上运行，原输出所有者 PID 为 1366，后续重启必须重新核对，不能硬编码这个 PID。画面动态效果仍以用户目视为准。网络失败时接收器显示连接恢复提示并重试；原显示所有者或帧地址变化时仍停止，交由启动器核对恢复，不能把旧画面仍在显示当作服务仍在线。接收器仍需原输出所有者保持缓冲区所有权，单靠 PID 和寄存器检查无法保护对方进程主动释放内存的情况。

不要直接运行旧 `recog_live_ncnn.py` 保持 HDMI：它会加载 `base.bit`，覆盖当前配置。

## 验收顺序

1. 连续说三条不同短句，看到临时字幕和最终字幕；包括两次重复同句、停顿、停止再启动。
2. 配置至少两条真实手语视频，识别后各自动播放；句中未知词明确提示，播放记录与字幕对应。
3. 板卡恢复可见基线后接入同一画面，用户确认 HDMI 的字幕和动态视频；持续运行至少 10 分钟。
4. 验证素材读取、失联、缺文件、队列积压与恢复，记录实际计算位置、输入设备与素材存储。

完成上述步骤才称音频线闭环验收通过。当前输入设备、素材和板卡已就位，正在进行现场字幕与动作确认，其余验收项继续记录。

参考：[sherpa-onnx 官方实时麦克风示例](https://github.com/k2-fsa/sherpa-onnx/blob/master/python-api-examples/speech-recognition-from-microphone.py)。
