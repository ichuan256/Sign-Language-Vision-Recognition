# 双目测距代码评审（2026-10-24，Tomcat）

> 历史评审快照：本次整理未重新核查列出的问题是否已修复，不作为当前缺陷清单。

对象：曹同学 cfx 合并的 `src/signrec/stereo.py`、`scripts/calibrate_stereo.py`、
`scripts/measure_stereo_range.py`、`tests/test_stereo.py`。
**仓库中目前没有双目摄像头 RTL**（OV5640 采集控制器属方案 M3 待写）；
本次评审的是已入库的双目 Python 侧代码。

## 结论

代码质量好：标定流程标准（单目标定 → `CALIB_FIX_INTRINSIC` 双目标定 →
`stereoRectify`），单位契约一致（物体点 mm → 平移 mm → 基线 mm → 深度 mm），
输入校验与 NaN 处理完备，`tests/test_stereo.py` **10/10 通过**
（本机 .venv-vision，opencv 4.11）。

## 发现的问题

### 1.【重要】`num_disparities=64` 默认值覆盖不了手势工作距离

AR 眼镜的手势发生在 0.3–0.5 m。按 640×480 采集（焦距约 500–700 px）、
双目基线 60–70 mm 估算（`depth = f·B/d`）：

| 距离 | 视差（f=500, B=60） | 视差（f=700, B=70） |
|---|---|---|
| 300 mm | 100 px | 163 px |
| 400 mm | 75 px | 122 px |
| 500 mm | 60 px | 98 px |
| 800 mm | 38 px | 61 px |

默认 64 px 视差范围在 0.5 m 以内基本全超界 → SGBM 无有效视差 →
`measure_range_mm` 返回 None。建议：默认提到 **128**（SGBM 要求 16 的倍数），
并在文档标注「工作距离下限 ≈ f·B/num_disparities」。

### 2. `stereoRectify(alpha=0)` 裁边与近距离大手势

alpha=0 把无效区裁净，但近距离张开双臂的手势容易出有效帧。
建议评估 alpha=0.7–1.0（保留视野、容忍黑边），或至少在测距报告中记录裁边比例。

### 3. 小点

- 单目标定的 RMS 算了但没存进 `StereoCalibration`（对诊断标定质量有用）；
- `StereoCalibration.load` 不校验数组形状（3×3/3×4/4×4），错文件会延迟到
  运行时才炸；
- `calibrate_stereo_pairs` 对同一张图转灰度两次（find + subPix），无碍正确性。

## 无问题确认项

`cornerSubPix` 参数顺序（winSize/zeroZone）正确；视差 ÷16 正确；
`median_depth_mm` 的 ROI 裁剪与 min_pixels 守门正确；
`pair_image_files` 按基名配对并报告未匹配项；保存/加载 roundtrip 用
`allow_pickle=False`，安全。

## 备注

M3 需要的 OV5640 DVP 采集 RTL（SCCB 配置 + 并口采样 + 行缓存 + VDMA 写 DDR）
仓库中尚不存在；可参考例程：xupsh/Pynq-CV-OV5640（PYNQ-Z2 + Pmod 并口）、
gitee pynq-cv-stero（PYNQ-Z2 + 正点原子双目）。
