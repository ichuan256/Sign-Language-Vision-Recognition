#!/usr/bin/env python3
"""Estimate range from a synchronized stereo image pair and calibration."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from signrec.stereo import StereoCalibration, StereoRangeEstimator  # noqa: E402


def read_image(path: Path) -> np.ndarray:
    raw = np.fromfile(path, dtype=np.uint8)
    image = cv2.imdecode(raw, cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"cannot decode image: {path}")
    return image


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--left", type=Path, required=True)
    parser.add_argument("--right", type=Path, required=True)
    parser.add_argument("--calibration", type=Path, required=True)
    parser.add_argument("--roi", nargs=4, type=int, metavar=("X", "Y", "W", "H"), help="optional person box")
    parser.add_argument("--num-disparities", type=int, default=64)
    parser.add_argument("--block-size", type=int, default=5)
    parser.add_argument("--min-valid-pixels", type=int, default=16)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    calibration = StereoCalibration.load(args.calibration)
    estimator = StereoRangeEstimator(
        calibration,
        num_disparities=args.num_disparities,
        block_size=args.block_size,
    )
    left = read_image(args.left)
    right = read_image(args.right)
    roi = tuple(args.roi) if args.roi is not None else None
    distance = estimator.measure_range_mm(
        left, right, roi=roi, min_pixels=args.min_valid_pixels
    )
    if distance is None:
        print("range_unavailable: insufficient valid disparity pixels")
        return 2
    print(f"range_mm={distance:.1f} baseline_mm={calibration.baseline_mm:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
