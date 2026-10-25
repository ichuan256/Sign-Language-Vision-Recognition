# 单手关键点 PL 开发工具

所有命令在仓库根运行，输出须使用未存在的新路径。

| 脚本 | 作用 / 环境 |
|---|---|
| `pl_preflight.py` | TFLite 模型/已装转换入口与历史资源检查，r3 环境 |
| `import_tflite_hand.py` | 原权重重建 tf-keras，逐值比对 TFLite；只导出坐标和手存在分数，r3 环境 |
| `prepare_hand_rois.py` | 从已审计视频与已有关键点结果生成本地 ROI 探针，vision 环境 |
| `fixed_hand_reference.py` | 按来源分组校准与整数数值评估，r3 环境 |
| `run_tile_hls.py` | 独立 MAC 分块核 CSim / HLS 综合 / XSim C-RTL，vision 环境 |
| `publish_hand_stage.py` | 汇总小型证据 JSON，不提交权重和 ROI 图片，vision 环境 |

典型执行顺序：

```powershell
F:\PLD\.venv-vision\Scripts\python.exe project/scripts/keypoints/prepare_hand_rois.py --output project/_tmp/kp_rois_new
F:\PLD\.venv-r3\Scripts\python.exe project/scripts/keypoints/import_tflite_hand.py --model F:/PLD/.venv-vision/Lib/site-packages/mediapipe/modules/hand_landmark/hand_landmark_lite.tflite --rois project/_tmp/kp_rois_new/rois.npz --output project/_tmp/kp_float_new
F:\PLD\.venv-r3\Scripts\python.exe project/scripts/keypoints/fixed_hand_reference.py --model project/_tmp/kp_float_new/hand_landmark_lite_roi.keras --rois project/_tmp/kp_rois_new/rois.npz --weight-bits 12 --output project/_tmp/kp_integer_new
F:\PLD\.venv-vision\Scripts\python.exe project/scripts/keypoints/run_tile_hls.py --output project/_tmp/kp_tile_new --integer-model project/_tmp/kp_integer_new --rois project/_tmp/kp_rois_new/rois.npz --synth --cosim
```

`run_tile_hls.py` 通过 cmd 调用 Vitis HLS 2024.1，不调用 Hardware Manager，不加载任何 bit。
完整网络数值参考、MAC 核 CSim、MAC 核 RTL co-sim 是三个不同门禁，不能互相冒充。
权重/模型从本机原始安装只读导出，派生产物留在忽略的 `project/_tmp/`；本轮没有训练或改媒体。
