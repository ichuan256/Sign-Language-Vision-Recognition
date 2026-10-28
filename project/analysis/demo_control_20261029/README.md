# 演示控制台交接

2026-10-29，用户确认控制台此前已正常，按要求收尾，不再继续切换硬件或执行摄像头测试。

源码：`project/scripts/demo_control.py`、`demo_control.html`、`start_demo_control.bat`。
操作说明：[演示控制台](../../../docs/演示控制台.md)。

已通过12项自动测试：

```powershell
F:/PLD/.venv-vision/Scripts/python.exe -X utf8 -m unittest project/scripts/test_demo_control.py vision/tests/test_ov5640_ssh_source.py -v
```

覆盖本机会话请求校验、摄像头编号传递、并发切换拒绝、无预览时返回失败、未接管PL任务保护、OV5640冷启动确认、OV5640独立固件对W6任务的拦截、RGB565完整帧解码、截断帧和DMA未确认帧拒绝。这些是接口与数据协议测试，不证明真实OV5640采集和显示已经通过。

此前运行事件记录包含teacher/pl/audio/camera成功启动，用户已确认控制台可用。10月29日后续复验时板卡SSH超时，未完成新的硬件验收。临时逐次事件在`project/_tmp/demo_control/*/events.jsonl`，后续失败记录不可覆盖或误替代此前成功证据。

OV5640新增流接口：`project/board/ov5640_snapshot/demo_stream.py`与`vision/src/vision/keypoints/ov5640_ssh_source.py`。它复用已有采集helper的锁、DMA Halted和保留缓冲机制，完整帧才进入电脑教师模型。真实板端采集待验收；独立抓图固件无HDMI/音频/PL关键点，UI不在线更换固件。

长驻控制进程不自动重载源码。收尾未再重启服务，末次固件门禁代码是否已被运行进程加载未复核；下次正常重启后使用。板端任务和固件未因本次收尾改变。
