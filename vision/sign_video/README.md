# 视频手语特征提取

2026-10-20 用户启动视觉识别线。本模块先完成 **视频 → 关键点时序 → 特征与漏检报告**，运行在电脑；不连接开发板、不重载固件、不修改音频或显示服务。

## 已实现的输入与输出

使用固定版本 MediaPipe Solutions Holistic 0.10.21，单人视频输入。双手按模型的解剖学左/右保存，不主动镜像；源视频若已镜像，必须在标注中注明。多人、画中画、切镜和遮挡需要先切片或单独核查，本入口不做人物身份跟踪。

每个片段输出 `.npz`、一张检测较完整帧的骨架叠加 `.jpg`。整个运行输出 `schema.json` 和 `report.json`：

- 原始姿态：33 点，每点 x/y/z/visibility；双手各 21 点，每点 x/y/z。未检测到填 NaN。
- 分类候选只使用二维坐标，避免把不同模型的 z 原点误作同一三维空间。
- 选取鼻、肩、肘、腕、髋共 9 个身体点，加双手 42 点，共 51 点；肩中点为原点、肩宽为单位，纵坐标先按画面宽高比修正。
- `sign_xy_v1` 每帧 **392 维**：身体相对坐标 102、速度 102、以各手腕为原点的手形坐标 84、坐标有效掩码 51、速度有效掩码 51、局部手形有效掩码 2。顺序以 `schema.json` 为准。
- 肩膀不可靠时身体相对坐标无效，但可保留有效的局部手形；速度仅在连续两帧坐标都有效时计算，单位是肩宽/秒。缺失处零填充并保留掩码，不插值。
- 默认约 15 帧/秒采样。时间来自源帧号/视频报告帧率；当前按恒定帧率素材处理，不宣称已支持可变帧率的精确 PTS。
- 来源 SHA256、源视频分组、标签、录制者、会话、划分状态、处理耗时和检测覆盖率进入报告。检测覆盖率不是识别准确率，也不是逐点置信度。

不做旋转归一化，以保留手臂方向；不将左右手合并。当前未把表情、口型加入特征，因此不是完整自然手语语言表征。

## 运行

使用独立环境，不在现有音频环境安装：

```powershell
F:/PLD/.venv-audio/Scripts/python.exe -m venv F:/PLD/.venv-vision
F:/PLD/.venv-vision/Scripts/python.exe -m pip install -r algo/sign_video/requirements.txt
F:/PLD/.venv-vision/Scripts/python.exe -m pytest tests/test_sign_video_features.py -q
F:/PLD/.venv-vision/Scripts/python.exe -X utf8 -m algo.sign_video.extract --manifest algo/sign_video/smoke_manifest.json --output analysis/sign_video_20261020/run01
```

输出目录必须不存在，避免覆盖已有实验。新增视频通过独立 manifest 接入，文件路径相对 manifest 所在目录；不自动扫描另一个 agent 尚在下载的文件。样本字段示例见 `smoke_manifest.json`。每个样本必填唯一 `id`、`file`、`source_group`；建议提供 `sha256`，提取前校验。长课程须先人工确认动作起止、去掉讲解和标题页，再建立训练片段；本入口把整个输入文件作为一个待提取序列。

## 当前验证与后续

首轮输入是已有“你好、早上好、你好吗、很好、谢谢”五个播放片段，来自同一原始课程第 1 集。它们只用于提取流程验证，动作起止沿用此前人工初划范围，**没有作为训练集或测试集**。录制者/会话未知，不虚构被试身份；全部 `split=unassigned`，共享同一 `source_group`。

首轮实际提取成功：139 个采样帧，双手同时检测覆盖 115 帧（82.7%），七项特征测试通过。发现“谢谢”片段预览仍显示“早上好”字幕，须复核动作语义和切片边界；不能直接按旧播放标签训练。完整结果、预览与限制见[首轮记录](../../analysis/sign_video_20261020/README.md)。

下载的新教程接入后，先按约 5～10 个动作建词表、逐段标注、检查左右手与漏检，再增加独立录制样本，建立 DTW 或小型时序分类基线。同源切片、抽帧、锐化与其他增强版本必须归同一分组，不能随机拆到训练和测试集。按完整源视频分组只是最低要求；跨人或跨会话泛化需要相应身份标签和独立样本。不能用五条模板匹配自身得出的结果宣称识别准确率。

锐化默认关闭；原图提取通过后才单独对比锐化版本的检测覆盖和识别结果。

2026-10-20 已完成三条件、两轮的 CPU 锐化对照：原图双手检测覆盖 82.7%，α=0.25 为 71.2%，α=0.5 为 28.1%，两轮计数一致。因此当前素材识别继续使用原图；这不是分类准确率实验。详见[锐化对照记录](../../analysis/sharpen_compare_20261020/README.md)。可用 `python -m algo.sign_video.compare_sharpen --manifest algo/sign_video/smoke_manifest.json --output <新目录> --repeats 2` 复现。提取入口也支持 `--sharpen-quarter 0/1/2`；输出记录 CPU 预处理参数与耗时，不表示已有 FPGA 核。

参考：[MediaPipe Holistic 官方实现与说明](https://github.com/google-ai-edge/mediapipe/blob/master/docs/solutions/holistic.md)、[固定版本 Python 包](https://pypi.org/project/mediapipe/0.10.21/)。
