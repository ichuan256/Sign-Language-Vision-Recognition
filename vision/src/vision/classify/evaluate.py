"""Evaluation helpers for the DTW baseline, honoring the data contract.

Two reports are always produced separately:
- leave-one-clip-out over the vocabulary: same-source, same-signer replay.
  This is "已见回放" and must never be quoted as recognition accuracy.
- group hold-out (train/test split by source_group): the smallest honest
  generalization claim this corpus supports; per the contract, clips that
  share a source video never straddle the split.
"""
import numpy as np


def leave_one_out(samples, *, classifier_factory):
    """samples: dicts with keys id, label, group, features.

    Returns a list of result dicts, one per left-out sample.
    """
    results = []
    for i, probe in enumerate(samples):
        train = [s for j, s in enumerate(samples) if j != i]
        clf = classifier_factory().fit(train)
        pred, dist, margins = clf.predict(probe["features"])
        results.append({"id": probe["id"], "label": probe["label"],
                        "group": probe["group"], "prediction": pred,
                        "correct": pred == probe["label"], "distance": dist,
                        "margins": {k: float(v) for k, v in margins.items()}})
    return results


def holdout_by_group(samples, *, test_groups, classifier_factory):
    """Train on samples whose group is not in test_groups; test on the rest."""
    test_groups = set(test_groups)
    train = [s for s in samples if s["group"] not in test_groups]
    test = [s for s in samples if s["group"] in test_groups]
    if not train or not test:
        raise ValueError("both sides of the hold-out must be non-empty")
    clf = classifier_factory().fit(train)
    results = []
    for probe in test:
        pred, dist, margins = clf.predict(probe["features"])
        results.append({"id": probe["id"], "label": probe["label"],
                        "group": probe["group"], "prediction": pred,
                        "correct": pred == probe["label"], "distance": dist,
                        "margins": {k: float(v) for k, v in margins.items()}})
    return results


def summarize(results):
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
