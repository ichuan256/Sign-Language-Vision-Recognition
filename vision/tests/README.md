# 视觉回归

完整回归使用Python3.12；测试依赖固定项目既有的NumPy1.26、OpenCV4.11和MediaPipe0.10.21，避免OpenCV5改变旧ONNX模型层接口。安装到独立虚拟环境或本仓库project/_cache下，不修改全局环境。

```powershell
python -m pip install -r vision/tests/requirements.txt
python -B -m pytest vision/tests project/tests -q -p no:cacheprovider
```

剪辑路径与模板CLI的stdlib测试不需要MediaPipe。真实媒体来源路径及SHA另用 `python -B project/scripts/check_layout.py` 验收；隔离checkout无忽略媒体时可显式 `--code-only`，不能据此声称媒体通过。

本套件不打开USB摄像头、不上板，不证明实拍准确率或HDMI实时性能；回放与HDMI测试使用可控时钟、本地协议服务和模拟SSH。
