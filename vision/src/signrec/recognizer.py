"""Few-shot clip matching with per-frame features and dynamic time warping."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np


@dataclass(frozen=True)
class ClipTemplate:
    label: str
    features: np.ndarray
    source: str = ""


@dataclass(frozen=True)
class Prediction:
    label: str
    distance: float
    similarity: float
    accepted: bool


def _normalize_sequence(features: np.ndarray) -> np.ndarray:
    array = np.asarray(features, dtype=np.float32)
    if array.ndim != 2 or array.shape[0] == 0 or array.shape[1] == 0:
        raise ValueError("features must have shape (frames, dimensions) and be non-empty")
    if not np.isfinite(array).all():
        raise ValueError("features contain non-finite values")
    norms = np.linalg.norm(array, axis=1, keepdims=True)
    return np.divide(array, np.maximum(norms, 1e-12), dtype=np.float32)


def dtw_distance(first: np.ndarray, second: np.ndarray) -> float:
    """Normalized cosine-distance DTW between two feature sequences."""
    left = _normalize_sequence(first)
    right = _normalize_sequence(second)
    if left.shape[1] != right.shape[1]:
        raise ValueError("feature dimensions must match")

    cosine = np.clip(left @ right.T, -1.0, 1.0)
    costs = 1.0 - cosine
    n, m = costs.shape
    previous = np.full(m + 1, np.inf, dtype=np.float32)
    previous[0] = 0.0
    for i in range(n):
        current = np.full(m + 1, np.inf, dtype=np.float32)
        for j in range(m):
            current[j + 1] = costs[i, j] + min(
                previous[j + 1], current[j], previous[j]
            )
        previous = current
    return float(previous[m] / max(n + m, 1))


class TemplateRecognizer:
    """Match a query clip to labeled feature-sequence templates."""

    def __init__(
        self, templates: Sequence[ClipTemplate], templates_per_class: int = 3
    ) -> None:
        if not templates:
            raise ValueError("at least one clip template is required")
        if templates_per_class <= 0:
            raise ValueError("templates_per_class must be positive")
        self.templates_per_class = templates_per_class
        self.templates = [
            ClipTemplate(t.label, _normalize_sequence(t.features), t.source)
            for t in templates
        ]
        dimensions = {t.features.shape[1] for t in self.templates}
        if len(dimensions) != 1:
            raise ValueError("all templates must use the same feature dimension")

    def predict(
        self,
        features: np.ndarray,
        *,
        top_k: int = 5,
        max_distance: float | None = None,
    ) -> list[Prediction]:
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        query = _normalize_sequence(features)
        by_label: dict[str, list[float]] = {}
        for template in self.templates:
            distance = dtw_distance(query, template.features)
            by_label.setdefault(template.label, []).append(distance)

        predictions: list[Prediction] = []
        for label, distances in by_label.items():
            best = sorted(distances)[: self.templates_per_class]
            distance = float(np.mean(best))
            predictions.append(
                Prediction(
                    label=label,
                    distance=distance,
                    similarity=float(np.exp(-distance)),
                    accepted=max_distance is None or distance <= max_distance,
                )
            )
        return sorted(predictions, key=lambda item: item.distance)[:top_k]


def save_templates(path: str | Path, templates: Iterable[ClipTemplate]) -> None:
    items = list(templates)
    if not items:
        raise ValueError("cannot save an empty template set")
    normalized = [_normalize_sequence(item.features) for item in items]
    dimensions = {array.shape[1] for array in normalized}
    if len(dimensions) != 1:
        raise ValueError("all templates must use the same feature dimension")

    offsets = np.zeros(len(items) + 1, dtype=np.int64)
    for index, array in enumerate(normalized, start=1):
        offsets[index] = offsets[index - 1] + array.shape[0]
    packed = np.concatenate(normalized, axis=0).astype(np.float32, copy=False)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        destination,
        features=packed,
        offsets=offsets,
        labels=np.asarray([item.label for item in items], dtype=np.str_),
        sources=np.asarray([item.source for item in items], dtype=np.str_),
    )


def load_templates(path: str | Path) -> list[ClipTemplate]:
    archive_path = Path(path)
    if not archive_path.is_file():
        raise FileNotFoundError(f"template archive not found: {archive_path}")
    with np.load(archive_path, allow_pickle=False) as archive:
        features = archive["features"]
        offsets = archive["offsets"]
        labels = archive["labels"]
        sources = archive["sources"]
        if len(offsets) != len(labels) + 1 or len(sources) != len(labels):
            raise ValueError("template archive metadata lengths are inconsistent")
        if offsets[0] != 0 or offsets[-1] != len(features):
            raise ValueError("template archive offsets are invalid")
        templates = []
        for index, label in enumerate(labels):
            start, stop = int(offsets[index]), int(offsets[index + 1])
            if stop <= start:
                raise ValueError("template archive contains an empty feature sequence")
            templates.append(
                ClipTemplate(
                    label=str(label),
                    features=features[start:stop].copy(),
                    source=str(sources[index]),
                )
            )
    return templates
