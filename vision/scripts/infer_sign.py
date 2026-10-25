#!/usr/bin/env python3
"""Classify one already-segmented video by temporal template matching."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
sys.path.insert(0, str(ROOT / "vision/src"))

from signrec.dataset import sample_video_frames  # noqa: E402
from signrec.features import DEFAULT_BACKBONE_PATH, MobileNetV2Embedder  # noqa: E402
from signrec.recognizer import TemplateRecognizer, load_templates  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--templates", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=DEFAULT_BACKBONE_PATH)
    parser.add_argument("--frames", type=int, default=8)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--max-distance", type=float, default=None, help="calibrated reject threshold; unset means ranking only")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    video = args.video.expanduser().resolve()
    if not video.is_file():
        raise FileNotFoundError(f"video not found: {video}")
    if args.frames <= 0 or args.top_k <= 0:
        raise ValueError("--frames and --top-k must be positive")

    frames = sample_video_frames(video, sample_count=args.frames)
    embedder = MobileNetV2Embedder(args.model)
    features = embedder.embed_frames(frames)
    recognizer = TemplateRecognizer(load_templates(args.templates))
    results = recognizer.predict(
        features, top_k=args.top_k, max_distance=args.max_distance
    )
    if not results:
        print("no class templates loaded")
        return 2

    for rank, result in enumerate(results, start=1):
        status = "accepted" if result.accepted else "rejected"
        print(
            f"{rank}. {result.label} status={status} "
            f"distance={result.distance:.4f} similarity={result.similarity:.4f}"
        )
    print("Similarity is a template score, not a calibrated probability.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
