# 六条人工训练ROI的拟合诊断（2026-10-27）

**96网络通过小样本拟合诊断。** 固定6条人工训练ROI、关闭增强、只监督可见XY，
150个优化步后，独立重载模型得到全部126个点和30个指尖的PCK@0.05均为100%。
这是训练样本记忆能力，不能替代泛化或部署精度。结构化证据、模型和输入SHA见[overfit6.json](overfit6.json)。

| 对照 | 全点PCK@0.05 | 全点NME | 指尖PCK@0.05 |
|---|---:|---:|---:|
| 训练前 | 11.90% | 0.14526 | 3.33% |
| 单一平均手形 | 11.90% | 0.14526 | 3.33% |
| 拟合后，推理模式 | 100% | 0.00512 | 100% |
| 所有输入换为同一张图 | 33.33% | 0.18631 | 30.00% |
| 循环打乱输入，5种错位平均 | 16.35% | 见JSON逐项 | 见JSON逐项 |

NME/PCK沿用完整可见手包围框对角线归一化。打乱的是图像顺序，标签顺序保持固定。
拟合后红色预测与绿色人工点重合，支持网络根据图像输出不同手型，而非仅输出一个平均形状。

## 使用范围与检查

- 只选冻结17项复核中`split=train`、`pose_source=human`的6个ROI，来自4条视频、2个课级来源组。
  包含同视频邻近帧，不能当6次独立泛化试验。完整数据加载器校验来源绑定；训练只接收冻结的6张图。
- 原96结构、固定seed20261026、Adam 1e-3、BN momentum0.9、整批6张、Huber delta0.03。
  不作数据增强，只优化可见XY；z、presence、handedness没有监督。
- 诊断目标为训练PCK≥95%，每25步检查；100、125、150步连续3次为100%，最佳步150。
  这个目标用于判断基本拟合能力，未改变正式独立精度门禁。
- loss及梯度范数有限，所有可训练参数均连接梯度；未监督输出列的head参数变化严格为0。
- 最终BN训练模式与推理模式的PCK均100%；独立进程重载后NME差为0。
- 验证集与开发留出未用于训练、选步或评测；未修改原标注、原数据集及前次泛化模型。
- 206项测试和32项子测试通过。未量化、综合或操作板卡。

本机模型、固定输入、前后对照图：`project/_tmp/hand_overfit6_20261027_v1/`；
独立重载结果：`project/_tmp/hand_overfit6_verify_20261027_v1/`。
模型名带`OVERFIT_DIAGNOSTIC`，不能作为正式定位模型使用。

## 结论与下一步

这组实验支持当前结构、坐标监督及梯度通路具有基本拟合能力。
它不能证明原先的增强、多输出损失或混合来源BN统计都合适，也不能排除大规模任务需要更强网络。
前次320/106/188划分的泛化门禁仍未通过，当前板端仍为0.49秒旧图。

下一步固定训练/验证数据、seed和预算，分别比较增强开关与XY-only/原多输出监督，
只用验证集选方案；同时排查教师难例质量并增加有效手型覆盖。
选定方案后另建覆盖不同人物/背景的人工测试集，不用本次6个样本的100%对外报告识别率。

复跑（输出目录必须新建）：

```powershell
F:\PLD\.venv-r3\Scripts\python.exe -X utf8 project/scripts/keypoints/overfit_hand_student.py fit --data project/_tmp/hand_teacher_clear_v3 --reviews project/_tmp/hand_review_intake_final_20261027_v1/reviews_original.jsonl --output project/_tmp/overfit_new --size 96 --steps 1500
F:\PLD\.venv-r3\Scripts\python.exe -X utf8 project/scripts/keypoints/overfit_hand_student.py verify --run project/_tmp/overfit_new --output project/_tmp/overfit_verify_new
```
