#!/usr/bin/env python3
"""Calibrate a stereo pair from synchronized, matched checkerboard images."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from signrec.stereo import calibrate_stereo_pairs, pair_image_files  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--left-dir", type=Path, required=True, help="directory of left-camera chessboard images")
    parser.add_argument("--right-dir", type=Path, required=True, help="directory of right-camera chessboard images")
    parser.add_argument("--columns", type=int, default=9, help="checkerboard inner-corner columns")
    parser.add_argument("--rows", type=int, default=6, help="checkerboard inner-corner rows")
    parser.add_argument("--square-size-mm", type=float, required=True, help="physical checkerboard square size in millimeters")
    parser.add_argument("--min-pairs", type=int, default=8)
    parser.add_argument("--output", type=Path, default=ROOT / "models" / "stereo_calibration.npz")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output = args.output.expanduser().resolve()
    if output.exists() and not args.overwrite:
        raise FileExistsError(f"calibration exists; pass --overwrite to replace: {output}")
    pairs, unmatched = pair_image_files(args.left_dir, args.right_dir)
    print(f"matched_pairs={len(pairs)} unmatched_images={len(unmatched)}")
    if unmatched:
        print("unmatched basenames: " + ", ".join(unmatched[:10]))
    calibration = calibrate_stereo_pairs(
        pairs,
        pattern_size=(args.columns, args.rows),
        square_size_mm=args.square_size_mm,
        min_pairs=args.min_pairs,
    )
    calibration.save(output)
    print(
        f"pairs_used={calibration.pairs_used} image_size={calibration.image_size} "
        f"baseline_mm={calibration.baseline_mm:.3f} rms_px={calibration.rms_error:.4f} "
        f"output={output}"
    )
    print("Important: left/right images must be synchronized and captured at the same resolution.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
