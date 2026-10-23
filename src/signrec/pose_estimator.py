"""Pose keypoints for refining person/hand regions, not sign classification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from ._vendor.opencv_zoo.mp_pose import MPPose
from .person_detector import PersonDetection

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POSE_MODEL_PATH = (
    _REPO_ROOT
    / "models"
    / "pose_estimation_mediapipe"
    / "pose_estimation_mediapipe_2023mar_int8bq.onnx"
)

# MediaPipe Pose indices for shoulder/elbow/wrist and coarse hand anchors.
ARM_AND_HAND_INDICES = (11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24)
POSE_CONNECTIONS = (
    (11, 12),
    (11, 13),
    (13, 15),
    (12, 14),
    (14, 16),
    (15, 17),
    (15, 19),
    (15, 21),
    (16, 18),
    (16, 20),
    (16, 22),
    (11, 23),
    (12, 24),
    (23, 24),
)


@dataclass(frozen=True)
class PoseEstimate:
    person_bbox: tuple[int, int, int, int]
    landmarks: np.ndarray  # 39 x 5: x, y, relative z, visibility, presence
    world_landmarks: np.ndarray  # 39 x 3: x, y, z
    segmentation_mask: np.ndarray
    confidence: float

    def upper_body_roi(
        self,
        frame_shape: tuple[int, ...],
        *,
        margin: float = 0.05,
        visibility_threshold: float = 0.25,
        presence_threshold: float = 0.25,
    ) -> tuple[int, int, int, int] | None:
        if len(frame_shape) < 2 or frame_shape[0] <= 0 or frame_shape[1] <= 0:
            raise ValueError("frame_shape must contain positive height and width")
        if not np.isfinite(margin) or margin < 0:
            raise ValueError("margin must be finite and non-negative")
        if not 0.0 <= visibility_threshold <= 1.0 or not 0.0 <= presence_threshold <= 1.0:
            raise ValueError("keypoint thresholds must be between 0 and 1")
        if self.landmarks.shape != (39, 5):
            raise ValueError("pose landmarks must have shape (39, 5)")

        selected = self.landmarks[np.asarray(ARM_AND_HAND_INDICES)]
        valid = (
            np.isfinite(selected[:, :2]).all(axis=1)
            & (selected[:, 3] >= visibility_threshold)
            & (selected[:, 4] >= presence_threshold)
        )
        points = selected[valid, :2]
        if points.shape[0] < 2:
            return None

        height, width = frame_shape[:2]
        min_xy = np.min(points, axis=0)
        max_xy = np.max(points, axis=0)
        span = max(float(np.max(max_xy - min_xy)), 1.0)
        pad = span * margin
        x1 = max(0, int(np.floor(min_xy[0] - pad)))
        y1 = max(0, int(np.floor(min_xy[1] - pad)))
        x2 = min(width, int(np.ceil(max_xy[0] + pad)) + 1)
        y2 = min(height, int(np.ceil(max_xy[1] + pad)) + 1)
        if x2 <= x1 or y2 <= y1:
            return None
        return x1, y1, x2, y2


class PoseEstimator:
    """Run OpenCV Zoo MediaPipe Pose conditioned on a person detection."""

    def __init__(
        self,
        model_path: str | Path = DEFAULT_POSE_MODEL_PATH,
        confidence_threshold: float = 0.5,
    ) -> None:
        self.model_path = Path(model_path)
        if not self.model_path.is_file():
            raise FileNotFoundError(f"pose model not found: {self.model_path}")
        if not hasattr(cv2, "dnn"):
            raise RuntimeError("this OpenCV build has no DNN module")
        self._model = MPPose(
            modelPath=str(self.model_path),
            confThreshold=confidence_threshold,
            backendId=cv2.dnn.DNN_BACKEND_OPENCV,
            targetId=cv2.dnn.DNN_TARGET_CPU,
        )

    def estimate(
        self, frame: np.ndarray, detection: PersonDetection
    ) -> PoseEstimate | None:
        if not isinstance(frame, np.ndarray):
            raise TypeError("frame must be a NumPy array")
        if frame.ndim != 3 or frame.shape[2] != 3 or frame.dtype != np.uint8:
            raise ValueError("frame must be a uint8 three-channel BGR image")
        person_row = np.asarray(
            [
                *detection.bbox,
                *detection.hip_center,
                *detection.full_body,
                *detection.shoulder_center,
                *detection.upper_body,
                detection.confidence,
            ],
            dtype=np.float32,
        )
        output = self._model.infer(frame, person_row)
        if output is None:
            return None
        bbox, landmarks, world_landmarks, mask, _heatmap, confidence = output
        height, width = frame.shape[:2]
        raw = np.asarray(bbox, dtype=np.float32).reshape(2, 2)
        x1 = int(np.clip(np.floor(raw[0, 0]), 0, width - 1))
        y1 = int(np.clip(np.floor(raw[0, 1]), 0, height - 1))
        x2 = int(np.clip(np.ceil(raw[1, 0]), x1 + 1, width))
        y2 = int(np.clip(np.ceil(raw[1, 1]), y1 + 1, height))
        return PoseEstimate(
            person_bbox=(x1, y1, x2, y2),
            landmarks=np.asarray(landmarks, dtype=np.float32),
            world_landmarks=np.asarray(world_landmarks, dtype=np.float32),
            segmentation_mask=np.asarray(mask, dtype=np.uint8),
            confidence=float(confidence),
        )


def draw_pose(frame: np.ndarray, pose: PoseEstimate) -> np.ndarray:
    """Return a copy with person/arm ROI and visible body landmarks."""
    output = frame.copy()
    roi = pose.upper_body_roi(frame.shape)
    if roi is not None:
        cv2.rectangle(output, roi[:2], roi[2:], (0, 255, 0), 2)
    cv2.rectangle(output, pose.person_bbox[:2], pose.person_bbox[2:], (255, 0, 0), 1)
    for first, second in POSE_CONNECTIONS:
        a, b = pose.landmarks[first], pose.landmarks[second]
        if min(float(a[3]), float(a[4]), float(b[3]), float(b[4])) < 0.25:
            continue
        p1 = (int(round(a[0])), int(round(a[1])))
        p2 = (int(round(b[0])), int(round(b[1])))
        cv2.line(output, p1, p2, (0, 255, 255), 1, cv2.LINE_AA)
    for index in ARM_AND_HAND_INDICES:
        point = pose.landmarks[index]
        if min(float(point[3]), float(point[4])) < 0.25:
            continue
        cv2.circle(
            output,
            (int(round(point[0])), int(round(point[1]))),
            2,
            (0, 0, 255),
            -1,
        )
    return output
