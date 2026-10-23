"""M1 首版评估运行器：在 vision.classify 的 DTW 基线上跑两种协议。

- leave-one-clip-out：逐条留出。同课次片段互为模板，属"已见回放"，
  不作为泛化准确率引用。
- group hold-out：按课次分组留出，--test-groups 指定的组整组进测试集。
  这是本语料目前支持的最小诚实泛化口径。

用法：
  python -m vision.m1.evaluate --features <提取目录>... --output <新目录>
"""
import argparse
import csv
import json
from pathlib import Path

from vision.classify import TemplateClassifier, frame_costs, dtw_distance
from vision.classify.evaluate import holdout_by_group, leave_one_out, summarize

DEFAULT_TEST_GROUPS = [
    "第十课旅游_NL10_100条_20261022",
    "第九课聚会_NL09_102条_20261022",
    "第2 第3课",
]


class RobustTemplateClassifier(TemplateClassifier):
    """逐模板捕获"带内无路径"：该模板距离记为 inf，不中断整体评估。
    另将序列时间重采样到统一长度，消除课次间帧率/时长差异导致的
    带内无路径（重采样的是整条有效特征序列的时间轴，不填补缺失检测）。"""

    def __init__(self, *args, canonical_len: int = 40, **kw):
        super().__init__(*args, **kw)
        self.canonical_len = canonical_len

    def _resample(self, feat):
        import numpy as np
        feat = np.asarray(feat, np.float32)
        n = len(feat)
        if n == self.canonical_len:
            return feat
        x_old = np.linspace(0.0, 1.0, n)
        x_new = np.linspace(0.0, 1.0, self.canonical_len)
        out = np.stack([np.interp(x_new, x_old, feat[:, d])
                        for d in range(feat.shape[1])], axis=1)
        out[:, 288:392] = out[:, 288:392] > 0.5  # 掩码列重采样后重新二值化
        return out.astype(np.float32)

    def fit(self, samples):
        resampled = [dict(s, features=self._resample(s["features"])) for s in samples]
        return super().fit(resampled)

    def predict(self, features):
        import numpy as np
        feat = self._resample(features)
        best_by_label = {}
        for label, _group, _sid, tmpl in self.templates_:
            try:
                cost = frame_costs(feat, tmpl, **self.weights)
                dist, _ = dtw_distance(cost, band_ratio=self.band_ratio)
            except ValueError:
                dist = np.inf
            if label not in best_by_label or dist < best_by_label[label]:
                best_by_label[label] = dist
        if not np.isfinite(min(best_by_label.values())):
            raise ValueError("所有模板都在带内无路径")
        label = min(best_by_label, key=best_by_label.get)
        return label, best_by_label[label], best_by_label


def load_dataset(dirs: list[Path]) -> list[dict]:
    samples = []
    for d in dirs:
        report = json.loads((d / "report.json").read_text(encoding="utf-8"))
        meta = {s["id"]: s for s in report["samples"]}
        for npz_path in sorted(d.glob("*.npz")):
            info = meta.get(npz_path.stem)
            if info is None:
                continue
            import numpy as np
            with np.load(npz_path) as data:
                features = data["features"].copy()
            samples.append({"id": info["id"], "label": info["label"],
                            "group": info["source_group"],
                            "both_hands_rate": info["both_hands_detected_rate"],
                            "features": features})
    return samples


def summarize_robust(results: list[dict]) -> dict:
    """与 classify.summarize 等价，但混淆矩阵允许出现测试集没有的预测标签。"""
    import numpy as np
    labels = sorted({r["label"] for r in results} | {r["prediction"] for r in results})
    per_label = {}
    for label in sorted({r["label"] for r in results}):
        rows = [r for r in results if r["label"] == label]
        per_label[label] = {"n": len(rows),
                            "correct": sum(r["correct"] for r in rows),
                            "accuracy": sum(r["correct"] for r in rows) / len(rows)}
    confusion = {label: {other: 0 for other in labels} for label in labels}
    for r in results:
        confusion[r["label"]][r["prediction"]] += 1
    return {"n": len(results),
            "overall_accuracy": float(np.mean([r["correct"] for r in results])),
            "per_label": per_label, "confusion": confusion}


def write_report(output: Path, name: str, results: list[dict], extra: dict):
    summary = summarize_robust(results)
    payload = {**summary, **extra, "results": results}
    (output / f"{name}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    labels = sorted(summary["confusion"])
    with (output / f"{name}_confusion.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow(["true\\pred"] + labels)
        for a in labels:
            row = [a]
            for b in labels:
                row.append(summary["confusion"].get(a, {}).get(b, 0))
            writer.writerow(row)
    print(f"[{name}] n={summary['n']} overall={summary['overall_accuracy']:.3f}")
    for label in sorted(summary["per_label"]):
        p = summary["per_label"][label]
        print(f"    {label}: {p['correct']}/{p['n']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--band", type=float, default=0.2)
    parser.add_argument("--test-groups", nargs="*", default=DEFAULT_TEST_GROUPS)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)

    samples = load_dataset(args.features)
    if len(samples) < 2:
        raise SystemExit("样本不足")
    factory = lambda: RobustTemplateClassifier(band_ratio=args.band)

    write_report(args.output, "loo", leave_one_out(samples, classifier_factory=factory),
                 {"protocol": "leave_one_clip_out",
                  "caveat": "同源回放口径，不代表跨人泛化准确率",
                  "band_ratio": args.band})
    try:
        write_report(args.output, "group_holdout",
                     holdout_by_group(samples, test_groups=args.test_groups,
                                      classifier_factory=factory),
                     {"protocol": "group_holdout", "test_groups": args.test_groups,
                      "band_ratio": args.band})
    except ValueError as exc:
        print(f"group_holdout 跳过：{exc}")


if __name__ == "__main__":
    main()
