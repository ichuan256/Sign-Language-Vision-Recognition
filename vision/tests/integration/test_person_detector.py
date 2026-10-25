from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
sys.path.insert(0, str(ROOT / "vision/src"))

from signrec.person_detector import (  # noqa: E402
    PersonDetection,
    PersonDetector,
    convert_results,
    draw_detections,
    derive_body_roi,
)


def test_convert_results_empty_returns_empty() -> None:
    assert convert_results(np.empty((0, 13), dtype=np.float32), 320, 240) == []
    assert convert_results(None, 320, 240) == []


def test_convert_results_clamps_box_and_body_points_to_frame() -> None:
    row = np.array([[-10, -5, 400, 300, -1, 10, 100, 200, 50, 80, 90, 100, 0.9]], dtype=np.float32)

    detections = convert_results(row, 320, 240)

    assert len(detections) == 1
    detection = detections[0]
    assert detection.bbox == (0, 0, 320, 240)
    assert detection.hip_center == (0, 10)
    assert detection.full_body == (100, 200)
    assert detection.shoulder_center == (50, 80)
    assert detection.upper_body == (90, 100)
    assert detection.confidence == pytest.approx(0.9)


def test_convert_results_drops_inverted_and_fully_offscreen_boxes() -> None:
    rows = np.zeros((2, 13), dtype=np.float32)
    rows[0, :4] = [100, 40, 20, 200]
    rows[1, :4] = [400, 10, 500, 200]

    assert convert_results(rows, 320, 240) == []


def test_convert_results_rejects_malformed_rows() -> None:
    with pytest.raises(ValueError, match="13 values"):
        convert_results(np.zeros((1, 12), dtype=np.float32), 320, 240)


def test_detect_rejects_invalid_frame_before_inference() -> None:
    detector = PersonDetector.__new__(PersonDetector)
    with pytest.raises(ValueError, match="three-channel"):
        detector.detect(np.zeros((240, 320), dtype=np.uint8))


def test_derive_body_roi_uses_anchor_radius_not_face_box() -> None:
    detection = PersonDetection(
        bbox=(80, 80, 120, 120),
        confidence=0.9,
        hip_center=(100, 180),
        full_body=(100, 230),
        shoulder_center=(100, 100),
        upper_body=(100, 40),
    )

    upper = derive_body_roi(detection, (240, 320, 3), region="upper_body", margin=0.0)
    full = derive_body_roi(detection, (240, 320, 3), region="full_body", margin=0.0)

    assert upper == (40, 40, 161, 161)
    assert full == (50, 130, 151, 231)
    assert upper[2] - upper[0] > detection.bbox[2] - detection.bbox[0]


def test_draw_detections_keeps_source_frame_unchanged() -> None:
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    detection = PersonDetection(
        bbox=(20, 30, 180, 220),
        confidence=0.95,
        hip_center=(100, 180),
        full_body=(100, 230),
        shoulder_center=(100, 80),
        upper_body=(100, 120),
    )

    annotated = draw_detections(frame, [detection])

    assert annotated.shape == frame.shape
    assert not np.array_equal(annotated, frame)
    assert not np.any(frame)


def test_model_runs_on_full_frame_blank_image() -> None:
    detector = PersonDetector()
    detections = detector.detect(np.zeros((240, 320, 3), dtype=np.uint8))
    assert detections == []
