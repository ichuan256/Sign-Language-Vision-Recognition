#!/usr/bin/env python3
"""Build per-clip MobileNetV2 feature templates from a labeled manifest."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from signrec.dataset import load_manifest, sample_video_frames  # noqa: E402
from signrec.features import DEFAULT_BACKBONE_PATH, MobileNetV2Embedder  # noqa: E402
from signrec.recognizer import ClipTemplate, save_templates  # noqa: E402

DEFAULT_MANIFEST = ROOT / "data" / "legacy" / "material" / "dataset_manifest_20261020.csv"
DEFAULT_OUTPUT = ROOT / "models" / "sign_templates_cropped.npz"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--model", type=Path, default=DEFAULT_BACKBONE_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--frames", type=int, default=8)
    parser.add_argument("--limit", type=int, default=None, help="optional clip limit for a smoke build")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.frames <= 0:
        raise ValueError("--frames must be positive")
    if args.limit is not None and args.limit <= 0:
        raise ValueError("--limit must be positive")
    output = args.output.expanduser().resolve()
    if output.exists() and not args.overwrite:
        raise FileExistsError(f"template archive exists; pass --overwrite to replace: {output}")

    records = load_manifest(args.manifest, repo_root=args.repo_root)
    if args.limit is not None:
        records = records[: args.limit]
    if not records:
        raise ValueError("manifest contains no video records")

    embedder = MobileNetV2Embedder(args.model)
    templates: list[ClipTemplate] = []
    for index, record in enumerate(records, start=1):
        frames = sample_video_frames(record.path, sample_count=args.frames)
        features = embedder.embed_frames(frames)
        source = record.path.resolve().relative_to(args.repo_root.resolve()).as_posix()
        templates.append(ClipTemplate(label=record.label, features=features, source=source))
        if index % 25 == 0 or index == len(records):
            print(f"encoded {index}/{len(records)} clips")

    save_templates(output, templates)
    print(
        f"templates={len(templates)} classes={len({item.label for item in templates})} "
        f"frames_per_clip={args.frames} feature_dim={templates[0].features.shape[1]} output={output}"
    )
    print("Note: the default manifest is cropped material; use a full-frame manifest before camera claims.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
