"""Small CPU-side association and smoothing for frame-by-frame detections."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .person_detector import PersonDetection


@dataclass(frozen=True)
class TrackedPerson:
    track_id: int
    detection: PersonDetection
    stale: bool = False


@dataclass
class _TrackState:
    track_id: int
    detection: PersonDetection
    missing_frames: int = 0


class PersonTracker:
    """Greedy IoU association with EMA smoothing and short gap tolerance.

    This is intended for the small number of people expected in a sign clip;
    it is not a full multi-object tracker or an optical-flow tracker.
    """

    def __init__(
        self,
        *,
        max_missing_frames: int = 2,
        smoothing: float = 0.65,
        min_iou: float = 0.1,
        stale_confidence_decay: float = 0.8,
    ) -> None:
        if max_missing_frames < 0:
            raise ValueError("max_missing_frames must be non-negative")
        if not 0.0 <= smoothing <= 1.0:
            raise ValueError("smoothing must be between 0 and 1")
        if not 0.0 <= min_iou <= 1.0:
            raise ValueError("min_iou must be between 0 and 1")
        if not 0.0 <= stale_confidence_decay <= 1.0:
            raise ValueError("stale_confidence_decay must be between 0 and 1")

        self.max_missing_frames = max_missing_frames
        self.smoothing = smoothing
        self.min_iou = min_iou
        self.stale_confidence_decay = stale_confidence_decay
        self._tracks: dict[int, _TrackState] = {}
        self._next_track_id = 1

    def reset(self) -> None:
        self._tracks.clear()
        self._next_track_id = 1

    def update(self, detections: list[PersonDetection]) -> list[TrackedPerson]:
        """Associate detections from one frame and return current tracks.

        Tracks missed for up to max_missing_frames are returned with stale=True
        and a decayed confidence.
        """
        old_ids = list(self._tracks)
        matches: list[tuple[float, int, int]] = []
        for track_id in old_ids:
            previous = self._tracks[track_id].detection
            for detection_index, detection in enumerate(detections):
                overlap = _intersection_over_union(previous.bbox, detection.bbox)
                if overlap >= self.min_iou:
                    matches.append((overlap, track_id, detection_index))

        assigned_tracks: set[int] = set()
        assigned_detections: set[int] = set()
        for _, track_id, detection_index in sorted(matches, reverse=True):
            if track_id in assigned_tracks or detection_index in assigned_detections:
                continue
            state = self._tracks[track_id]
            state.detection = _smooth_detection(
                state.detection, detections[detection_index], self.smoothing
            )
            state.missing_frames = 0
            assigned_tracks.add(track_id)
            assigned_detections.add(detection_index)

        for detection_index, detection in enumerate(detections):
            if detection_index in assigned_detections:
                continue
            track_id = self._next_track_id
            self._next_track_id += 1
            self._tracks[track_id] = _TrackState(track_id, detection)
            assigned_tracks.add(track_id)

        stale_ids: list[int] = []
        for track_id in old_ids:
            if track_id in assigned_tracks:
                continue
            state = self._tracks[track_id]
            state.missing_frames += 1
            if state.missing_frames > self.max_missing_frames:
                stale_ids.append(track_id)
            else:
                state.detection = replace(
                    state.detection,
                    confidence=state.detection.confidence * self.stale_confidence_decay,
                )
        for track_id in stale_ids:
            del self._tracks[track_id]

        return [
            TrackedPerson(
                track_id=track_id,
                detection=self._tracks[track_id].detection,
                stale=self._tracks[track_id].missing_frames > 0,
            )
            for track_id in sorted(self._tracks)
        ]


def _intersection_over_union(
    first: tuple[int, int, int, int], second: tuple[int, int, int, int]
) -> float:
    ax1, ay1, ax2, ay2 = first
    bx1, by1, bx2, by2 = second
    x1, y1 = max(ax1, bx1), max(ay1, by1)
    x2, y2 = min(ax2, bx2), min(ay2, by2)
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
    union = area_a + area_b - intersection
    return 0.0 if union <= 0 else intersection / union


def _smooth_point(
    previous: tuple[int, int], current: tuple[int, int], alpha: float
) -> tuple[int, int]:
    return (
        round((1 - alpha) * previous[0] + alpha * current[0]),
        round((1 - alpha) * previous[1] + alpha * current[1]),
    )


def _smooth_detection(
    previous: PersonDetection, current: PersonDetection, alpha: float
) -> PersonDetection:
    box = tuple(
        round((1 - alpha) * old + alpha * new)
        for old, new in zip(previous.bbox, current.bbox)
    )
    x1, y1, x2, y2 = box
    if x2 <= x1:
        x2 = x1 + 1
    if y2 <= y1:
        y2 = y1 + 1
    return PersonDetection(
        bbox=(x1, y1, x2, y2),
        confidence=current.confidence,
        hip_center=_smooth_point(previous.hip_center, current.hip_center, alpha),
        full_body=_smooth_point(previous.full_body, current.full_body, alpha),
        shoulder_center=_smooth_point(
            previous.shoulder_center, current.shoulder_center, alpha
        ),
        upper_body=_smooth_point(previous.upper_body, current.upper_body, alpha),
    )
