#!/usr/bin/env python3
"""Run leave-one-video-out and distance-threshold evaluation for templates."""

from __future__ import annotations

import argparse
import math
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from signrec.recognizer import ClipTemplate, TemplateRecognizer, load_templates  # noqa: E402


@dataclass(frozen=True)
class ThresholdMetrics:
    max_distance: float
    known_coverage: float
    accepted_known_accuracy: float
    singleton_false_accept_rate: float
    singleton_rejection_rate: float
    accepted_known_clips: int
    singleton_clips: int


@dataclass(frozen=True)
class EvaluationResult:
    total_templates: int
    evaluated_clips: int
    evaluated_classes: int
    top1_accuracy: float
    macro_f1: float
    singleton_distractor_rate: float
    thresholds: tuple[ThresholdMetrics, ...]


def evaluate_leave_one_clip_out(
    templates: list[ClipTemplate],
    max_distances: Sequence[float] = (0.05, 0.1, 0.15, 0.2, 0.3),
) -> EvaluationResult:
    if not templates:
        raise ValueError("no templates to evaluate")
    if any(not math.isfinite(value) or value < 0 for value in max_distances):
        raise ValueError("distance thresholds must be finite and non-negative")
    counts = Counter(item.label for item in templates)
    evaluated_labels = sorted(label for label, count in counts.items() if count >= 2)
    evaluated_indices = [
        index for index, item in enumerate(templates) if counts[item.label] >= 2
    ]
    singleton_indices = [
        index for index, item in enumerate(templates) if counts[item.label] == 1
    ]
    if not evaluated_indices:
        raise ValueError("leave-one-out needs at least one class with 2 or more clips")

    true_positive = Counter()
    false_positive = Counter()
    false_negative = Counter()
    known_observations: list[tuple[str, str, float]] = []
    singleton_distances: list[float] = []
    correct = 0
    singleton_predictions = 0

    for held_out_index in evaluated_indices:
        held_out = templates[held_out_index]
        training = templates[:held_out_index] + templates[held_out_index + 1 :]
        prediction = TemplateRecognizer(training).predict(held_out.features, top_k=1)[0]
        predicted = prediction.label
        known_observations.append((held_out.label, predicted, prediction.distance))
        if counts[predicted] == 1:
            singleton_predictions += 1
        if predicted == held_out.label:
            correct += 1
            true_positive[held_out.label] += 1
        else:
            false_negative[held_out.label] += 1
            if predicted in evaluated_labels:
                false_positive[predicted] += 1

    for held_out_index in singleton_indices:
        held_out = templates[held_out_index]
        training = templates[:held_out_index] + templates[held_out_index + 1 :]
        prediction = TemplateRecognizer(training).predict(held_out.features, top_k=1)[0]
        singleton_distances.append(prediction.distance)

    f1_scores = []
    for label in evaluated_labels:
        tp = true_positive[label]
        fp = false_positive[label]
        fn = false_negative[label]
        denominator = 2 * tp + fp + fn
        f1_scores.append(0.0 if denominator == 0 else (2 * tp) / denominator)

    threshold_metrics: list[ThresholdMetrics] = []
    for threshold in max_distances:
        accepted = [
            (truth == predicted)
            for truth, predicted, distance in known_observations
            if distance <= threshold
        ]
        accepted_count = len(accepted)
        false_accept_count = sum(distance <= threshold for distance in singleton_distances)
        singleton_count = len(singleton_distances)
        threshold_metrics.append(
            ThresholdMetrics(
                max_distance=float(threshold),
                known_coverage=accepted_count / len(known_observations),
                accepted_known_accuracy=(
                    sum(accepted) / accepted_count if accepted_count else 0.0
                ),
                singleton_false_accept_rate=(
                    false_accept_count / singleton_count if singleton_count else 0.0
                ),
                singleton_rejection_rate=(
                    1.0 - false_accept_count / singleton_count if singleton_count else 0.0
                ),
                accepted_known_clips=accepted_count,
                singleton_clips=singleton_count,
            )
        )

    return EvaluationResult(
        total_templates=len(templates),
        evaluated_clips=len(evaluated_indices),
        evaluated_classes=len(evaluated_labels),
        top1_accuracy=correct / len(evaluated_indices),
        macro_f1=sum(f1_scores) / len(f1_scores),
        singleton_distractor_rate=singleton_predictions / len(evaluated_indices),
        thresholds=tuple(threshold_metrics),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--templates", type=Path, required=True)
    parser.add_argument(
        "--max-distances",
        type=float,
        nargs="+",
        default=[0.05, 0.1, 0.15, 0.2, 0.3],
        help="candidate DTW distance thresholds to report; none is auto-selected",
    )
    args = parser.parse_args(argv)

    templates = load_templates(args.templates)
    result = evaluate_leave_one_clip_out(templates, args.max_distances)
    print(f"templates={result.total_templates}")
    print(
        f"leave_one_video_out_clips={result.evaluated_clips} "
        f"classes_with_multiple_clips={result.evaluated_classes}"
    )
    print(
        f"top1_accuracy={result.top1_accuracy:.4f} "
        f"macro_f1={result.macro_f1:.4f} "
        f"singleton_distractor_rate={result.singleton_distractor_rate:.4f}"
    )
    for metric in result.thresholds:
        print(
            f"max_distance={metric.max_distance:.3f} "
            f"known_coverage={metric.known_coverage:.4f} "
            f"accepted_known_accuracy={metric.accepted_known_accuracy:.4f} "
            f"singleton_false_accept={metric.singleton_false_accept_rate:.4f} "
            f"singleton_rejection={metric.singleton_rejection_rate:.4f}"
        )
    print("Caveat: singleton clips are only pseudo-unknowns from this same cropped corpus; calibrate rejection on separate camera-known and camera-unknown clips.")
    print("These metrics are not full-frame or cross-signer validation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
