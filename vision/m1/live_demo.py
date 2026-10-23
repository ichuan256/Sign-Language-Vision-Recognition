"""滑窗实时识别演示：证明换输入只换 FrameSource，下游代码不变。

帧源迭代与降采样由 vision.framesource 负责；关键点与特征复用
vision.keypoints / vision.sign_video 的同一契约；分类用 DTW 模板基线
（含统一长度重采样）。M2/M3 输入实现后仅 --source 参数变为 hdmi:/ov5640:。

用法：
  python -m vision.m1.live_demo --source file:路径.mp4 --templates <npz目录>...
  python -m vision.m1.live_demo --source usb:0 --templates <npz目录>...
"""
import argparse
import json
from collections import defaultdict, deque
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np

from vision.framesource import USBCamSource, VideoFileSource
from vision.keypoints.holistic import _landmarks
from vision.m1.evaluate import RobustTemplateClassifier
from vision.sign_video.features import build_features

HOLISTIC_OPTS = dict(static_image_mode=False, model_complexity=1, smooth_landmarks=True,
                     enable_segmentation=False, refine_face_landmarks=False,
                     min_detection_confidence=0.5, min_tracking_confidence=0.5)


def make_source(spec: str, max_fps: float):
    """spec 形如 file:路径 或 usb:0；hdmi:/ov5640: 在 M2/M3 实现后接入。"""
    kind, _, arg = spec.partition(":")
    if kind == "file":
        return VideoFileSource(arg, max_fps=max_fps)
    if kind == "usb":
        return USBCamSource(int(arg or 0), max_fps=max_fps)
    if kind == "hdmi":
        from vision.framesource.hdmi_in import HDMIInSource
        return HDMIInSource(arg)
    if kind == "ov5640":
        from vision.framesource.ov5640 import OV5640StereoSource
        return OV5640StereoSource(arg)
    raise ValueError(f"unknown frame source spec: {spec!r}")


def load_templates(dirs: list[Path], exclude_id: str | None = None):
    templates = defaultdict(list)
    for d in dirs:
        report = json.loads((d / "report.json").read_text(encoding="utf-8"))
        meta = {s["id"]: s for s in report["samples"]}
        for npz_path in sorted(d.glob("*.npz")):
            info = meta.get(npz_path.stem)
            if info is None or npz_path.stem == exclude_id:
                continue
            with np.load(npz_path) as data:
                templates[info["label"]].append(
                    {"label": info["label"], "group": info["source_group"],
                     "id": info["id"], "features": data["features"].copy()})
    return [s for seqs in templates.values() for s in seqs]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="file:路径 | usb:N | hdmi: | ov5640:")
    parser.add_argument("--templates", type=Path, nargs="+", required=True)
    parser.add_argument("--exclude-id", default=None, help="演示输入自身 id，避免它当自己的模板")
    parser.add_argument("--window-s", type=float, default=2.0)
    parser.add_argument("--fps", type=float, default=15)
    parser.add_argument("--band", type=float, default=0.2)
    parser.add_argument("--max-frames", type=int, default=0, help="0=直到流结束")
    args = parser.parse_args()

    samples = load_templates(args.templates, exclude_id=args.exclude_id)
    clf = RobustTemplateClassifier(band_ratio=args.band).fit(samples)
    labels = sorted({s["label"] for s in samples})
    print(f"模板 {len(samples)} 条 / {len(labels)} 类：{labels}")

    buf = deque()          # (pose, hands, pts)
    n_pred = 0
    with make_source(args.source, max_fps=args.fps) as src, \
            mp.solutions.holistic.Holistic(**HOLISTIC_OPTS) as detector:
        for bgr, frame_id, pts in src:
            if args.max_frames and frame_id >= args.max_frames:
                break
            result = detector.process(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
            pose = _landmarks(result.pose_landmarks, 33, visibility=True)
            hands = np.stack((_landmarks(result.left_hand_landmarks, 21),
                              _landmarks(result.right_hand_landmarks, 21)))
            buf.append((pose, hands, pts))
            while buf and buf[0][2] < pts - args.window_s:
                buf.popleft()
            times = [t for _, _, t in buf]
            if len(buf) < 5 or times[-1] - times[0] < 0.5:
                continue
            arr = build_features(np.stack([p for p, _, _ in buf]),
                                 np.stack([h for _, h, _ in buf]),
                                 np.asarray(times),
                                 width=bgr.shape[1], height=bgr.shape[0])
            pred, dist, margins = clf.predict(arr["features"])
            n_pred += 1
            ranked = sorted(margins.items(), key=lambda kv: kv[1])[:3]
            print(f"t={pts:6.2f}s  预测={pred}  前三={[(k, round(v, 3)) for k, v in ranked]}",
                  flush=True)
    print(f"结束，共 {n_pred} 次窗口预测")


if __name__ == "__main__":
    main()
