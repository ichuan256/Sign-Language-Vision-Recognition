# 视觉运行源码

| 包 | 职责 |
|---|---|
| `vision/framesource/` | 文件、USB、实时节拍回放与待实现的单目相机接口 |
| `vision/keypoints/` | 当前无语义关键点、显示连接与学生数据工具 |
| `vision/{m1,classify,sign_video}/` | 保留的骨架特征/DTW实验；`sign_video` 有共享特征契约 |
| `vision/webapp/` | 旧词语识别网页 |
| `signrec/` | 旧视觉嵌入/人体检测/DTW库，含明确标记的第三方封装 |

仓库根 `vision/__init__.py` 提供导入锚点，`python -m vision.keypoints.live_demo` 等模块名保持兼容。
脚本直接路径已改为 `vision/src/vision/webapp/run_fullframe_20261024.py`。
模型在 `vision/data/models/`，清单在 `vision/data/manifests/`；代码目录不再放M1缓存。
