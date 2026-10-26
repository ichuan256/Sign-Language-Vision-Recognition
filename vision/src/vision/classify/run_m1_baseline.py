"""M1 baseline runner: npz features -> DTW leave-one-out + group hold-out.

Loads extract.py outputs (one .npz per manifest sample), evaluates the
DTW template classifier under two distinct protocols, and writes
report.json + README.md. The two protocols are never merged:

- loo: leave-one-clip-out inside the whole vocabulary — same source,
  same signer, "已见回放" replay numbers only.
- group_holdout: train/test split by source_group. Only labels that
  actually appear on both sides of the split produce rows here; with the
  v1 corpus that is 谢谢 (p01 vs p04) and nothing else.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from .dtw import TemplateClassifier
from .evaluate import leave_one_out, holdout_by_group, summarize


def load_samples(manifest_path, npz_dir):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    samples = []
    for entry in manifest["samples"]:
        npz_path = Path(npz_dir) / f'{entry["id"]}.npz'
        if not npz_path.is_file():
            raise FileNotFoundError(f"missing extract output: {npz_path}")
        with np.load(npz_path) as data:
            samples.append({"id": entry["id"], "label": entry["label"],
                            "group": entry["source_group"],
                            "features": data["features"],
                            "annotation_status": entry["annotation_status"],
                            "n_frames": int(data["features"].shape[0]),
                            "duration_s": float(data["timestamps_s"][-1]),
                            "body_valid_rate": float(data["body_valid"].mean())})
    return manifest, samples


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--npz-dir", type=Path, required=True,
                        help="extract.py output directory containing <id>.npz")
    parser.add_argument("--output", type=Path, required=True,
                        help="must not exist yet (experiment outputs are immutable)")
    parser.add_argument("--band-ratio", type=float, default=0.2)
    parser.add_argument("--velocity-weight", type=float, default=0.5)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)

    manifest, samples = load_samples(args.manifest, args.npz_dir)

    def factory():
        return TemplateClassifier(band_ratio=args.band_ratio,
                                  velocity_weight=args.velocity_weight)

    loo_results = leave_one_out(samples, classifier_factory=factory)
    loo_summary = summarize(loo_results)

    # group hold-out: for every label that spans multiple groups, hold each
    # group out in turn (train on the rest of the vocabulary too, so the
    # decision is "this label vs everything else", not "this label vs itself")
    holdout_results = []
    by_label = {}
    for s in samples:
        by_label.setdefault(s["label"], set()).add(s["group"])
    spanned = {label: groups for label, groups in by_label.items() if len(groups) > 1}
    for label, groups in sorted(spanned.items()):
        for test_group in sorted(groups):
            subset = [s for s in samples if s["label"] == label or s["group"] not in groups]
            try:
                rows = holdout_by_group(subset, test_groups={test_group},
                                        classifier_factory=factory)
            except ValueError:
                continue
            for row in rows:
                row["holdout_label"] = label
            holdout_results.extend(rows)
    holdout_summary = summarize(holdout_results) if holdout_results else None

    report = {
        "purpose": "m1_dtw_baseline_first_run",
        "claimer": "loo numbers are same-source same-signer replay, NOT recognition accuracy",
        "config": {"band_ratio": args.band_ratio, "velocity_weight": args.velocity_weight},
        "vocabulary": manifest["vocabulary"],
        "n_samples": len(samples),
        "loo": {"summary": loo_summary, "results": loo_results},
        "group_holdout": ({"summary": holdout_summary, "results": holdout_results}
                          if holdout_results else None),
        "samples": [{k: v for k, v in s.items() if k != "features"} for s in samples],
    }
    (args.output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_readme(args.output / "README.md", report)
    print(json.dumps({"loo_overall": loo_summary["overall_accuracy"],
                      "holdout": (holdout_summary["overall_accuracy"]
                                  if holdout_summary else None),
                      "report": str(args.output / "report.json")}, ensure_ascii=False))


def write_readme(path, report):
    lines = ["# M1 DTW 基线首轮结果", "",
             "口径：**leave-one-clip-out 为同源同录制者已见回放，不是识别准确率**；"
             "group hold-out 才是本语料目前唯一诚实的泛化读数（仅谢谢跨 p01/p04）。", "",
             f"- 词表 {len(report['vocabulary'])} 类 / {report['n_samples']} 段",
             f"- 配置 band_ratio={report['config']['band_ratio']} "
             f"velocity_weight={report['config']['velocity_weight']}", "",
             "## Leave-one-clip-out（已见回放口径）", "",
             f"整体回放量：{report['loo']['summary']['overall_accuracy']:.3f}", "",
             "| 标签 | 段数 | 回放正确 |", "|---|---|---|"]
    for label, row in report["loo"]["summary"]["per_label"].items():
        lines.append(f"| {label} | {row['n']} | {row['correct']}/{row['n']} "
                     f"({row['accuracy']:.2f}) |")
    lines += ["", "## 混淆矩阵（行=真值，列=预测）", "",
              "| 真值 \\ 预测 | " + " | ".join(report["loo"]["summary"]["confusion"].keys()) + " |",
              "|" + "---|" * (len(report["loo"]["summary"]["confusion"]) + 1)]
    for label, row in report["loo"]["summary"]["confusion"].items():
        lines.append(f"| {label} | " + " | ".join(str(row[c]) for c in report["loo"]["summary"]["confusion"]) + " |")
    if report.get("group_holdout"):
        h = report["group_holdout"]
        lines += ["", "## Group hold-out（未见分组口径）", "",
                  f"整体：{h['summary']['overall_accuracy']:.3f}（样本即唯一跨 part 标签的测试段）", "",
                  "| 标签 | 测试组 | 段数 | 正确 |", "|---|---|---|---|"]
        for row in h["results"]:
            lines.append(f"| {row['label']} | {row['group']} | 1 | "
                         f"{'✓' if row['correct'] else '✗ → ' + row['prediction']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
