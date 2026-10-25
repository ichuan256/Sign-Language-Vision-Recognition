# 通用身体/手部关键点基线（不涉及语义）

入口只做单人 MediaPipe Holistic 身体 33 点、双手各 21 点检测与叠加。
不读取词表/模板，不加载 DTW/CNN，不预测任何词义，也不把模型相对 z 当作公制深度。
现有 `HolisticTracker.run()` 仍保留为批量特征入口；新的逐帧演示不累积分类特征。

## 摄像头演示

仓库根目录执行（会打开明确指定的摄像头及预览窗口）：

```powershell
F:\PLD\.venv-vision\Scripts\python.exe -X utf8 -m vision.keypoints.live_demo --source usb:0 --width 640 --height 480 --fps 30 --seconds 60 --scenario general --output project/_tmp/keypoints/usb_general_01
```

Q / Esc 或关闭窗口停止。再次运行必须使用新的输出目录。左右手沿用模型解剖学定义，
不镜像输入；绿点为左手、橙点为右手，不能按预览左右位置判定身份。
`--save-landmarks` 将每帧原始坐标写入 JSONL，缺失为 null；默认只写检测存在性与计时。
代码不主动保存原始视频或截图，不操作板卡、ASR、启动项。

文件源验证（不打开摄像头，不显示窗口）：

```powershell
F:\PLD\.venv-vision\Scripts\python.exe -X utf8 -m vision.keypoints.live_demo --source "file:<片段路径>" --fps 30 --headless --output project/_tmp/keypoints/file_01
```

文件源不按原速等待，报告始终标为 `offline_file_throughput`，不能算摄像头实测。
`--model-complexity 0/1/2` 可供后续受控对比，默认 1，与旧提取基线一致。

## 指标定义与边界

输出 `report.json` 汇总、`frames.jsonl` 逐帧记录：

- `processed_fps`：处理帧数 / 主机循环耗时；包含逐帧预览与 JSONL 写入，排除源/模型初始化和最后汇总。没有排除预热帧。
- `inference_ms`：BGR→RGB 与 detector.process 的耗时，给出 P50/P95、均值及首帧。
- `host_result_ms`：调用 read 之前到关键点结果完成；包含读帧/限帧等待。不是传感器曝光到结果的延迟。
- `host_preview_submit_ms`：read 之前到 imshow/waitKey 返回。无显示时为 null；不是显示器实际呈现延迟。
- 左/右/双手覆盖率：对应帧是否返回 landmarks / 处理帧数。身体项仅表示 pose 是否返回，**不是旧报告的肩部归一化有效率**。
- 连续未检出：帧数，以及首次未检出采样时间到再次检出的跨度；结尾未恢复只统计至最后采样时间。手本来不在画面时也会计入，不等于漏检率。

USB 时间戳是主机 read 返回后的时钟，没有曝光时间戳；驱动缓冲帧龄未知。
没有人工关键点真值，不能报告定位准确率、左右手身份正确率或真实遮挡恢复延迟。
静止抖动和左右手交换目前需人工观察，本工具不把主动动作幅度误当作抖动分数。
60 秒默认时限也不能中断正在阻塞的摄像头驱动 read。

## 首轮实测清单（待人工执行）

在同一摄像头、分辨率、距离和光照下分别记录：

| scenario | 建议过程 | 观察重点 |
|---|---|---|
| static | 双手完整入画保持静止，再缓慢张合 | 关键点抖动、手指是否贴合 |
| fast_motion | 左右/上下快速移动、张合 | 脱手、丢失帧、拖影 |
| crossing | 双手交叉后分开、轮流遮挡 | 左右手关联是否交换 |
| occlusion | 完全遮挡后重新入画，重复多次 | 重检出与错误骨架；需另记真实重新可见时刻 |

每项独立新目录、建议 60 秒。上述是测试设计，不是已通过的性能指标。
目前只验证文件源，摄像头预览和真实连续运动验收仍待执行。
