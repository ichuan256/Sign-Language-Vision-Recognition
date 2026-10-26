"""Full-frame person detection adapted for sign-language video input."""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np

from ._vendor.opencv_zoo.mp_persondet import MPPersonDet

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = (
    _REPO_ROOT
    / "data" / "models"
    / "person_detection_mediapipe"
    / "person_detection_mediapipe_2023mar.onnx"
)


@dataclass(frozen=True)
class PersonDetection:
    """Upstream face box plus four body anchor points.

    The upstream detector's first four values are a face-region box, not a
    full-person box. Use derive_body_roi() for body/upper-body regions.
    """

    bbox: tuple[int, int, int, int]
    confidence: float
    hip_center: tuple[int, int]
    full_body: tuple[int, int]
    shoulder_center: tuple[int, int]
    upper_body: tuple[int, int]


Point = tuple[int, int]


def _clip_point(x: float, y: float, width: int, height: int) -> Point:
    px = int(round(float(np.clip(x, 0, max(0, width - 1)))))
    py = int(round(float(np.clip(y, 0, max(0, height - 1)))))
    return px, py


def derive_body_roi(
    detection: PersonDetection,
    frame_shape: tuple[int, ...],
    *,
    region: str = "upper_body",
    margin: float = 0.05,
) -> tuple[int, int, int, int]:
    """Derive an in-memory ROI from the detector's center/radius anchors.

    `upper_body` uses the shoulder-center/upper-body anchors; `full_body` uses
    the hip-center/full-body anchors. The source frame remains unmodified.
    """
    if len(frame_shape) < 2 or frame_shape[0] <= 0 or frame_shape[1] <= 0:
        raise ValueError("frame_shape must contain positive height and width")
    if not math.isfinite(margin) or margin < 0:
        raise ValueError("margin must be finite and non-negative")
    if region == "upper_body":
        center, edge = detection.shoulder_center, detection.upper_body
    elif region == "full_body":
        center, edge = detection.hip_center, detection.full_body
    else:
        raise ValueError("region must be 'upper_body' or 'full_body'")

    height, width = frame_shape[:2]
    radius = max(1.0, math.hypot(edge[0] - center[0], edge[1] - center[1]))
    radius *= 1.0 + margin
    x1 = max(0, int(math.floor(center[0] - radius)))
    y1 = max(0, int(math.floor(center[1] - radius)))
    x2 = min(width, int(math.ceil(center[0] + radius)) + 1)
    y2 = min(height, int(math.ceil(center[1] + radius)) + 1)
    return x1, y1, x2, y2


def convert_results(
    results: np.ndarray | Iterable[Iterable[float]] | None,
    frame_width: int,
    frame_height: int,
) -> list[PersonDetection]:
    """Convert OpenCV Zoo rows to clamped integer coordinates.

    Each upstream row contains a face-region xyxy box, four (x, y) body
    anchors, and score.
    """
    if frame_width <= 0 or frame_height <= 0:
        raise ValueError("frame dimensions must be positive")
    if results is None:
        return []

    rows = np.asarray(results, dtype=np.float32)
    if rows.size == 0:
        return []
    if rows.ndim == 1:
        rows = rows.reshape(1, -1)
    if rows.ndim != 2 or rows.shape[1] < 13:
        raise ValueError("detector rows must have at least 13 values")

    detections: list[PersonDetection] = []
    for row in rows:
        if not np.isfinite(row[:13]).all():
            continue
        raw_x1, raw_y1, raw_x2, raw_y2 = (float(v) for v in row[:4])
        if (
            raw_x2 <= raw_x1
            or raw_y2 <= raw_y1
            or raw_x2 <= 0
            or raw_y2 <= 0
            or raw_x1 >= frame_width
            or raw_y1 >= frame_height
        ):
            continue
        x1 = int(np.clip(np.floor(raw_x1), 0, frame_width - 1))
        y1 = int(np.clip(np.floor(raw_y1), 0, frame_height - 1))
        x2 = int(np.clip(np.ceil(raw_x2), x1 + 1, frame_width))
        y2 = int(np.clip(np.ceil(raw_y2), y1 + 1, frame_height))
        points = [
            _clip_point(row[i], row[i + 1], frame_width, frame_height)
            for i in (4, 6, 8, 10)
        ]
        detections.append(
            PersonDetection(
                bbox=(x1, y1, x2, y2),
                confidence=float(np.clip(row[12], 0.0, 1.0)),
                hip_center=points[0],
                full_body=points[1],
                shoulder_center=points[2],
                upper_body=points[3],
            )
        )
    return detections


class PersonDetector:
    """Run the OpenCV Zoo MediaPipe detector on an entire BGR frame.

    The upstream model internally resizes with aspect-preserving padding; it
    does not crop the camera frame.
    """

    def __init__(
        self,
        model_path: str | Path = DEFAULT_MODEL_PATH,
        score_threshold: float = 0.5,
        nms_threshold: float = 0.3,
    ) -> None:
        self.model_path = Path(model_path)
        if not self.model_path.is_file():
            raise FileNotFoundError(
                f"person detector model not found: {self.model_path}; see models/person_detection_mediapipe/README.md"
            )
        if not hasattr(cv2, "dnn"):
            raise RuntimeError("this OpenCV build has no DNN module")
        self._model = MPPersonDet(
            modelPath=str(self.model_path),
            scoreThreshold=score_threshold,
            nmsThreshold=nms_threshold,
        )

    def detect(self, frame: np.ndarray) -> list[PersonDetection]:
        if not isinstance(frame, np.ndarray):
            raise TypeError("frame must be a NumPy array")
        if frame.ndim != 3 or frame.shape[2] != 3:
            raise ValueError("frame must be a three-channel BGR image")
        if frame.shape[0] == 0 or frame.shape[1] == 0:
            raise ValueError("frame must not be empty")
        if frame.dtype != np.uint8:
            raise ValueError("frame dtype must be uint8")

        rows = self._model.infer(frame)
        return convert_results(rows, frame.shape[1], frame.shape[0])


def draw_detections(
    frame: np.ndarray, detections: Iterable[PersonDetection]
) -> np.ndarray:
    """Return an annotated copy; never mutate the camera/source frame."""
    output = frame.copy()
    for detection in detections:
        face_x1, face_y1, face_x2, face_y2 = detection.bbox
        full_roi = derive_body_roi(detection, frame.shape, region="full_body")
        upper_roi = derive_body_roi(detection, frame.shape, region="upper_body")
        cv2.rectangle(output, full_roi[:2], full_roi[2:], (255, 0, 0), 1)
        cv2.rectangle(output, upper_roi[:2], upper_roi[2:], (0, 255, 0), 2)
        cv2.rectangle(output, (face_x1, face_y1), (face_x2, face_y2), (0, 165, 255), 1)
        cv2.putText(
            output,
            f"face-det {detection.confidence:.2f}",
            (face_x1, max(16, face_y1 - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 165, 255),
            1,
            cv2.LINE_AA,
        )
        for point in (
            detection.hip_center,
            detection.full_body,
            detection.shoulder_center,
            detection.upper_body,
        ):
            cv2.circle(output, point, 3, (0, 0, 255), -1)
    return output
