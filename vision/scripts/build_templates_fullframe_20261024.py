#!/usr/bin/env python3
"""w2：用全画幅精剪清单重建 MobileNetV2 模板（兼容本机 cv2 4.11 层名）。

与 scripts/build_templates.py 的差别只有一处：特征层名做动态解析
（本机 cv2 4.11 导入 ONNX 后层名为 GlobalAveragePool_97，
缺省值 onnx_node!GlobalAveragePool_97 在本机不存在）。
不改动曹同学文件。清单由 build_fullframe_manifest_20261024.py 生成。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
sys.path.insert(0, str(ROOT / "vision/src"))

import cv2  # noqa: E402
from signrec.dataset import load_manifest, sample_video_frames  # noqa: E402
from signrec.features import DEFAULT_BACKBONE_PATH, MobileNetV2Embedder  # noqa: E402
from signrec.recognizer import ClipTemplate, save_templates  # noqa: E402


def resolve_feature_layer(model_path: Path, preferred: str) -> str:
    net = cv2.dnn.readNet(str(model_path))
    if net.getLayerId(preferred) > 0:
        return preferred
    candidates = [n for n in net.getLayerNames() if "GlobalAveragePool" in n]
    if not candidates:
        raise ValueError(f"no GlobalAveragePool layer in {model_path}")
    return candidates[-1]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path,
                    default=ROOT / "vision/data" / "manifests" / "manifest_fullframe_20261024.csv")
    ap.add_argument("--repo-root", type=Path, default=ROOT)
    ap.add_argument("--model", type=Path, default=DEFAULT_BACKBONE_PATH)
    ap.add_argument("--output", type=Path,
                    default=ROOT / "vision/models" / "sign_templates_fullframe_20261024.npz")
    ap.add_argument("--frames", type=int, default=8)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    layer = resolve_feature_layer(args.model, "onnx_node!GlobalAveragePool_97")
    print(f"feature layer: {layer}")
    embedder = MobileNetV2Embedder(args.model, feature_layer=layer)

    records = load_manifest(args.manifest, repo_root=args.repo_root)
    if args.limit:
        records = records[: args.limit]
    templates: list[ClipTemplate] = []
    for i, record in enumerate(records, 1):
        frames = sample_video_frames(record.path, sample_count=args.frames)
        features = embedder.embed_frames(frames)
        source = record.path.resolve().relative_to(args.repo_root.resolve()).as_posix()
        templates.append(ClipTemplate(label=record.label, features=features, source=source))
        if i % 50 == 0 or i == len(records):
            print(f"encoded {i}/{len(records)}")
    save_templates(args.output, templates)
    print(f"templates={len(templates)} classes={len({t.label for t in templates})} "
          f"dim={templates[0].features.shape[1]} output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
