from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
sys.path.insert(0, str(ROOT / "vision/src"))

from signrec.person_detector import PersonDetection  # noqa: E402
from signrec.tracking import PersonTracker  # noqa: E402


def detection(box: tuple[int, int, int, int], confidence: float = 0.9) -> PersonDetection:
    x1, y1, x2, y2 = box
    center = ((x1 + x2) // 2, (y1 + y2) // 2)
    return PersonDetection(
        bbox=box,
        confidence=confidence,
        hip_center=center,
        full_body=(center[0], y2),
        shoulder_center=(center[0], y1 + (y2 - y1) // 3),
        upper_body=(center[0], y1 + (y2 - y1) // 2),
    )


def test_tracker_associates_and_smooths_overlapping_boxes() -> None:
    tracker = PersonTracker(smoothing=0.5, min_iou=0.1)
    first = tracker.update([detection((0, 0, 100, 100))])[0]

    second = tracker.update([detection((10, 0, 110, 100))])[0]

    assert second.track_id == first.track_id
    assert second.detection.bbox == (5, 0, 105, 100)
    assert not second.stale


def test_tracker_holds_short_miss_then_expires() -> None:
    tracker = PersonTracker(max_missing_frames=1)
    first = tracker.update([detection((0, 0, 100, 100))])[0]

    stale = tracker.update([])
    assert len(stale) == 1
    assert stale[0].track_id == first.track_id
    assert stale[0].stale
    assert stale[0].detection.confidence < first.detection.confidence

    assert tracker.update([]) == []


def test_tracker_reacquires_after_short_miss() -> None:
    tracker = PersonTracker(max_missing_frames=1)
    first = tracker.update([detection((0, 0, 100, 100))])[0]
    tracker.update([])

    reacquired = tracker.update([detection((4, 0, 104, 100))])[0]

    assert reacquired.track_id == first.track_id
    assert not reacquired.stale


def test_tracker_keeps_two_people_separate() -> None:
    tracker = PersonTracker(smoothing=1.0, min_iou=0.1)
    initial = tracker.update(
        [detection((0, 0, 80, 160)), detection((220, 0, 300, 160))]
    )
    initial_ids = {item.detection.bbox: item.track_id for item in initial}

    next_frame = tracker.update(
        [detection((225, 0, 305, 160)), detection((5, 0, 85, 160))]
    )

    assert len(next_frame) == 2
    assert {item.detection.bbox: item.track_id for item in next_frame} == {
        (5, 0, 85, 160): initial_ids[(0, 0, 80, 160)],
        (225, 0, 305, 160): initial_ids[(220, 0, 300, 160)],
    }


def test_tracker_rejects_invalid_parameters() -> None:
    with pytest.raises(ValueError, match="smoothing"):
        PersonTracker(smoothing=1.1)
    with pytest.raises(ValueError, match="max_missing_frames"):
        PersonTracker(max_missing_frames=-1)
