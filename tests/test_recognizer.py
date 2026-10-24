from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from signrec.features import (  # noqa: E402
    DEFAULT_BACKBONE_PATH,
    MobileNetV2Embedder,
    preprocess_full_frame,
)
from signrec.recognizer import (  # noqa: E402
    ClipTemplate,
    TemplateRecognizer,
    dtw_distance,
    load_templates,
    save_templates,
)


def test_preprocess_full_frame_letterboxes_without_cropping() -> None:
    frame = np.zeros((100, 200, 3), dtype=np.uint8)

    tensor = preprocess_full_frame(frame)

    assert tensor.shape == (1, 3, 224, 224)
    assert np.isfinite(tensor).all()
    # A wide frame is padded vertically; padding is the normalized ImageNet mean.
    assert np.allclose(tensor[:, :, 0, :], 0.0)
    assert np.any(tensor[:, :, 112, :] != 0.0)


def test_dtw_distance_is_zero_for_identical_sequences() -> None:
    features = np.asarray([[1.0, 0.0], [0.8, 0.2], [0.0, 1.0]], dtype=np.float32)
    assert dtw_distance(features, features) == pytest.approx(0.0, abs=1e-7)


def test_dtw_handles_different_sequence_lengths() -> None:
    short = np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    long = np.asarray([[1.0, 0.0], [1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    assert dtw_distance(short, long) == pytest.approx(0.0, abs=1e-7)


def test_template_recognizer_ranks_nearest_label_and_rejects_threshold() -> None:
    templates = [
        ClipTemplate("你好", np.asarray([[1.0, 0.0], [0.8, 0.2]], dtype=np.float32)),
        ClipTemplate("谢谢", np.asarray([[0.0, 1.0], [0.2, 0.8]], dtype=np.float32)),
    ]
    recognizer = TemplateRecognizer(templates)

    result = recognizer.predict(np.asarray([[1.0, 0.0], [0.8, 0.2]], dtype=np.float32), max_distance=0.1)
    assert result[0].label == "你好"
    assert result[0].accepted

    rejected = recognizer.predict(np.asarray([[-1.0, 0.0]], dtype=np.float32), max_distance=0.1)
    assert rejected[0].label == "谢谢"
    assert not rejected[0].accepted


def test_template_archive_round_trips_unicode_labels(tmp_path: Path) -> None:
    templates = [
        ClipTemplate("你好", np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32), "a.mp4"),
        ClipTemplate("谢谢", np.asarray([[0.0, 1.0]], dtype=np.float32), "b.mp4"),
    ]
    archive = tmp_path / "templates.npz"

    save_templates(archive, templates)
    loaded = load_templates(archive)

    assert [item.label for item in loaded] == ["你好", "谢谢"]
    assert [item.source for item in loaded] == ["a.mp4", "b.mp4"]
    assert np.allclose(loaded[0].features, templates[0].features)


def test_mobilenet_v2_produces_normalized_frame_features() -> None:
    if not DEFAULT_BACKBONE_PATH.is_file():
        pytest.skip("optional MobileNetV2 ONNX asset is not installed")
    embedder = MobileNetV2Embedder()
    feature = embedder.embed_frame(np.zeros((240, 320, 3), dtype=np.uint8))

    assert feature.shape == (1280,)
    assert np.isfinite(feature).all()
    assert np.linalg.norm(feature) == pytest.approx(1.0, abs=1e-4)
