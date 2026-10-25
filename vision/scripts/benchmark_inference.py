#!/usr/bin/env python3
"""Preflight OpenCV DNN assets and benchmark one full-frame inference pass."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
sys.path.insert(0, str(ROOT / "vision/src"))

from signrec.features import DEFAULT_BACKBONE_PATH, MobileNetV2Embedder  # noqa: E402
from signrec.person_detector import DEFAULT_MODEL_PATH, PersonDetector  # noqa: E402


def summarize_ms(samples: Iterable[float]) -> dict[str, float]:
    values = np.asarray(list(samples), dtype=np.float64)
    if values.ndim != 1 or values.size == 0 or not np.isfinite(values).all():
        raise ValueError("timing samples must be a non-empty finite sequence")
    return {
        "mean": float(np.mean(values)),
        "p50": float(np.percentile(values, 50)),
        "p95": float(np.percentile(values, 95)),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def total_memory_bytes() -> int | None:
    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
        page_count = os.sysconf("SC_PHYS_PAGES")
        return int(page_size * page_count)
    except (AttributeError, OSError, ValueError):
        return None


def benchmark(
    *,
    width: int = 640,
    height: int = 480,
    warmup: int = 3,
    iterations: int = 20,
    seed: int = 7,
    detector_model: Path = DEFAULT_MODEL_PATH,
    backbone_model: Path = DEFAULT_BACKBONE_PATH,
) -> dict[str, object]:
    if width <= 0 or height <= 0:
        raise ValueError("frame dimensions must be positive")
    if warmup < 0 or iterations <= 0:
        raise ValueError("warmup must be non-negative and iterations positive")

    detector_model = Path(detector_model)
    backbone_model = Path(backbone_model)
    detector = PersonDetector(detector_model)
    embedder = MobileNetV2Embedder(backbone_model)
    rng = np.random.default_rng(seed)
    frame = rng.integers(0, 256, (height, width, 3), dtype=np.uint8)

    for _ in range(warmup):
        detector.detect(frame)
        embedder.embed_frame(frame)

    detector_ms: list[float] = []
    backbone_ms: list[float] = []
    pipeline_ms: list[float] = []
    last_detection_count = 0
    last_feature_dim = 0
    for _ in range(iterations):
        start = time.perf_counter()
        detections = detector.detect(frame)
        middle = time.perf_counter()
        features = embedder.embed_frame(frame)
        finish = time.perf_counter()
        detector_ms.append((middle - start) * 1000.0)
        backbone_ms.append((finish - middle) * 1000.0)
        pipeline_ms.append((finish - start) * 1000.0)
        last_detection_count = len(detections)
        last_feature_dim = int(features.size)

    return {
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "machine": platform.machine(),
            "opencv": cv2.__version__,
            "opencv_dnn": hasattr(cv2, "dnn"),
            "cpu_count": os.cpu_count(),
            "memory_total_bytes": total_memory_bytes(),
        },
        "input": {
            "width": width,
            "height": height,
            "channels": 3,
            "source": "synthetic full-frame BGR; capture/decode excluded",
        },
        "models": {
            "person_detector": {"path": str(detector_model), "sha256": sha256_file(detector_model)},
            "mobilenetv2_backbone": {"path": str(backbone_model), "sha256": sha256_file(backbone_model)},
        },
        "warmup_iterations": warmup,
        "measured_iterations": iterations,
        "last_person_detections": last_detection_count,
        "feature_dimension": last_feature_dim,
        "latency_ms": {
            "person_detection": summarize_ms(detector_ms),
            "feature_extraction": summarize_ms(backbone_ms),
            "combined_inference": summarize_ms(pipeline_ms),
        },
        "note": "This is a host/target software-inference preflight only; it does not measure camera capture, stereo processing, or FPGA acceleration.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--detector-model", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--backbone-model", type=Path, default=DEFAULT_BACKBONE_PATH)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)

    report = benchmark(
        width=args.width,
        height=args.height,
        warmup=args.warmup,
        iterations=args.iterations,
        seed=args.seed,
        detector_model=args.detector_model,
        backbone_model=args.backbone_model,
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output is None:
        print(rendered)
    else:
        output = args.output.expanduser().resolve()
        if output.exists() and not args.overwrite:
            raise FileExistsError(f"report exists; pass --overwrite to replace: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
        print(f"benchmark report saved: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
