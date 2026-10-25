# 录制视频模拟摄像头 → 关键点叠加 → 板卡 HDMI

当前主线：录制视频（PC 实时节拍回放）→ PC Holistic → 身体/双手骨架 →
最新 1280×720 JPEG → SSH 反向隧道 → 板端既有接收脚本 → HDMI OUT。
不做语义分类；单目 OV5640 未到货，只有 `OV5640MonoSource` 接口占位。
双目代码为历史兼容，不是当前硬件需求，也没有实施管脚分配或采集逻辑。

## 两个终端启动（仓库根目录）

先确保上一次回放/隧道已结束，不要重复占用端口。终端 A：

```powershell
F:\PLD\.venv-vision\Scripts\python.exe -X utf8 -m vision.keypoints.live_demo --source "replay:vision/video/done/wsy/全22课全画幅样本_fullframe_264条_20261021/谢谢/1_谢谢.mp4" --loop --fps 20 --seconds 660 --headless --serve-hdmi --output project/_tmp/keypoints/replay_01
```

可以把 `replay:` 后的路径替换为其他录制视频。不加 `--loop` 则片段结束就退出。
保留原始分辨率做检测；预览/HDMI 输出等比缩放补黑边，不把画面拉伸到 16:9。
画面上 `FRAME` 和 `SOURCE` 必须持续增加，循环时也不回零。

等待出现 `HDMI_FRAME_SERVER` 且第一帧就绪，再在终端 B 执行：

```powershell
F:\PLD\.venv-vision\Scripts\python.exe -X utf8 -m vision.keypoints.hdmi_link --seconds 600 --fps 15 --output project/_tmp/keypoints/hdmi_01
```

按提示输入板卡 sudo 密码（不显示、不保存）。输出目录必须是新目录，重跑请更换末尾编号。
`/state`：`http://127.0.0.1:18780/state`；最新图像：`/frame.jpg`。
HTTP 仅监听本机，板卡经 SSH 访问，不需要开放 Windows 入站端口。

## 重要：到时停帧不是连续播放失败

终端 B 默认运行 **10 分钟**，结束后接收进程与隧道退出，HDMI 保留最后一帧。
终端 A 也有独立时限，应比接收链路更长。原型不是开机常驻服务，不改 Startup/systemd。
要看持续运动，请在 `HDMI_LINK_READY` 之后、时限结束之前检查画面和帧号。

Ctrl-C 可中断本地运行。远端接收有独立 `timeout`，中断后最晚在原定时限退出；
**不要立即另起第二个写屏进程**，新连接遇到已知写屏者会拒绝接管。
显示所有者 `hdmi_display.py` 必须保持存活，不要为了停视频结束它或重新加载 bit。

## 安全检查与验收边界

`hdmi_link` 先检查冷启动结束、bit/hwh 成对哈希、远端脚本哈希与已知写屏者。
不匹配就停止，不自动覆盖文件或杀掉音频显示进程；冲突应先人工确认。
显示所有者不存在时，只启动已核对的 `hdmi_display.py`，其默认 `download=False`。
本轮复用已验收 W6 固件，不做 Vivado/HLS 构建或二次下载。

板端复用 `hdmi_audio_receiver.py` 的通用 JPEG 通路，因此日志仍以 `AUDIO_HDMI` 开头；
这里没有启动音频识别。只有一个最新 JPEG，不积累旧视频帧。
目标 `--fps 15` 是轮询上限，不是达到 15fps 的保证；旧 MMIO/JPEG 通路实际可能明显更慢。
接收日志、网络计数、PC 处理 FPS 不能代替显示器真实刷新率或人眼验收。

当前已确认连续播放与骨架叠加，详见 [实测记录](../analysis/keypoints_hdmi_20261025/README.md)。
