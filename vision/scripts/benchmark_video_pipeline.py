#!/usr/bin/env python3
"""Benchmark the full file-to-top-k pipeline on a host or PYNQ target."""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from collections import Counter
from pathlib import Path
from threading import Event
from typing import Any

import cv2

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
sys.path.insert(0, str(ROOT / "vision/src"))
sys.path.insert(0, str(ROOT))

from signrec.features import DEFAULT_BACKBONE_PATH  # noqa: E402
from signrec.person_detector import DEFAULT_MODEL_PATH  # noqa: E402
from signrec.pose_estimator import DEFAULT_POSE_MODEL_PATH  # noqa: E402
from vision.webapp.pipeline import SignRecognitionPipeline  # noqa: E402

DEFAULT_TEMPLATES = ROOT / "vision/data/models" / "sign_templates_cropped.npz"


def inspect_video(path: Path) -> dict[str, Any]:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise RuntimeError(f"cannot open video: {path}")
    try:
        width = int(round(capture.get(cv2.CAP_PROP_FRAME_WIDTH)))
        height = int(round(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        frame_count = int(round(capture.get(cv2.CAP_PROP_FRAME_COUNT)))
        fps = float(capture.get(cv2.CAP_PROP_FPS))
    finally:
        capture.release()
    return {"width": width, "height": height, "frames": frame_count, "source_fps": fps}


def build_report(
    *,
    video: Path,
    video_info: dict[str, Any],
    load_seconds: float,
    wall_seconds: float,
    event_counts: Counter[str],
    result: dict[str, Any],
    settings: dict[str, Any],
) -> dict[str, Any]:
    frames = int(result.get("frames_processed", 0))
    return {
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "machine": platform.machine(),
            "opencv": cv2.__version__,
            "opencv_dnn": hasattr(cv2, "dnn"),
            "cpu_count": os.cpu_count(),
        },
        "input": {"path": str(video.resolve()), **video_info},
        "settings": settings,
        "timing": {
            "model_load_seconds": float(load_seconds),
            "pipeline_seconds": float(wall_seconds),
            "pipeline_fps": float(frames / wall_seconds) if wall_seconds > 0 else 0.0,
            "reported_internal_fps": float(result.get("processing_fps", 0.0)),
        },
        "events": dict(event_counts),
        "result": {
            "domain_note": result.get("result_domain"),
            "similarity_note": result.get("similarity_note"),
            "predictions": result.get("predictions", []),
        },
        "scope": "Includes file decode, person detection, tracking, pose at configured stride, preview JPEG encode and final DTW. Excludes camera capture/DVP, stereo range, browser/network overhead and FPGA acceleration.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--person-model", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--pose-model", type=Path, default=DEFAULT_POSE_MODEL_PATH)
    parser.add_argument("--backbone-model", type=Path, default=DEFAULT_BACKBONE_PATH)
    parser.add_argument("--templates", type=Path, default=DEFAULT_TEMPLATES)
    parser.add_argument("--sample-count", type=int, default=8)
    parser.add_argument("--detection-stride", type=int, default=2)
    parser.add_argument("--pose-stride", type=int, default=4)
    parser.add_argument("--preview-stride", type=int, default=2)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)

    video = args.video.expanduser().resolve()
    if not video.is_file():
        raise FileNotFoundError(f"video not found: {video}")
    video_info = inspect_video(video)
    settings = {
        "sample_count": args.sample_count,
        "detection_stride": args.detection_stride,
        "pose_stride": args.pose_stride,
        "preview_stride": args.preview_stride,
    }
    started = time.perf_counter()
    pipeline = SignRecognitionPipeline(
        person_model=args.person_model,
        pose_model=args.pose_model,
        backbone_model=args.backbone_model,
        templates_path=args.templates,
        sample_count=args.sample_count,
        detection_stride=args.detection_stride,
        pose_stride=args.pose_stride,
        preview_stride=args.preview_stride,
    )
    load_seconds = time.perf_counter() - started
    event_counts: Counter[str] = Counter()
    started = time.perf_counter()
    result = pipeline.process_video(
        video,
        lambda event: event_counts.update([str(event.get("type", "unknown"))]),
        Event(),
    )
    wall_seconds = time.perf_counter() - started
    report = build_report(
        video=video,
        video_info=video_info,
        load_seconds=load_seconds,
        wall_seconds=wall_seconds,
        event_counts=event_counts,
        result=result,
        settings=settings,
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output is None:
        print(rendered)
    else:
        output = args.output.expanduser().resolve()
        if output.exists() and not args.overwrite:
            raise FileExistsError(f"report exists; pass --overwrite: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
        print(f"benchmark report saved: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
