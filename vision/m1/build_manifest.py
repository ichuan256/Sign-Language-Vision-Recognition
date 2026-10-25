"""从 video/done 精剪素材构建 M1 词表 manifest。

词表 v1（8 类 29 条，2026-10-23 定）：优先词语/短句类动态手势，
含跨课次来源（不同 source_group）以便分组评估。
输出 N 个分片 manifest（默认每片 10 条），供分块提取避免长任务中断全丢。
"""
import argparse
import hashlib
import json
from pathlib import Path

VOCAB = {
    "谢谢": "greeting",
    "早上": "greeting",
    "很": "word",
    "待会儿见": "phrase",
    "再见": "greeting",
    "没关系": "phrase",
    "可以。": "phrase",
    "服务": "word",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect(repo_root: Path, manifest_dir: Path) -> list[dict]:
    import os
    samples = []
    for label in VOCAB:
        hits = sorted(p for p in repo_root.glob(f"vision/video/done/*/*/{label}/*.mp4"))
        if not hits:
            print(f"警告：标签 {label!r} 无片段，跳过")
            continue
        for clip in hits:
            group = clip.parent.parent.name  # 课次目录 = 来源分组
            samples.append({
                "id": f"c{len(samples) + 1:03d}",
                # 提取器按 manifest 所在目录解析相对路径
                "file": os.path.relpath(clip, manifest_dir),
                "label": label,
                "sha256": sha256(clip),
                "source_group": group,
                "signer_id": None,
                "session_id": None,
                "split": "loo_eval",
                "annotation_status": "reviewed_boundaries_20261021_22",
            })
    return samples


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--per-part", type=int, default=10)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    samples = collect(args.repo_root, args.output.resolve())
    labels = sorted({s["label"] for s in samples})
    print(f"共 {len(samples)} 条，{len(labels)} 类：{labels}")
    for start in range(0, len(samples), args.per_part):
        part = {"purpose": "m1_dtw_baseline", "samples": samples[start:start + args.per_part]}
        path = args.output / f"m1_part{start // args.per_part + 1}.json"
        path.write_text(json.dumps(part, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"写出 {path.name}：{len(part['samples'])} 条")
    (args.output / "vocab.json").write_text(
        json.dumps({"vocab": VOCAB, "n_samples": len(samples)}, ensure_ascii=False, indent=2),
        encoding="utf-8")


if __name__ == "__main__":
    main()
