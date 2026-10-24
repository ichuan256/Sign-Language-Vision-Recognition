from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from signrec.dataset import sample_video_frames  # noqa: E402
from signrec.person_detector import DEFAULT_MODEL_PATH, PersonDetector  # noqa: E402
from signrec.pose_estimator import (  # noqa: E402
    DEFAULT_POSE_MODEL_PATH,
    PoseEstimate,
    PoseEstimator,
    draw_pose,
)


def make_pose() -> PoseEstimate:
    landmarks = np.zeros((39, 5), dtype=np.float32)
    for index, point in zip(
        (11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24),
        ((40, 30), (60, 30), (30, 50), (70, 50), (20, 70), (80, 70), (18, 72), (82, 72), (16, 74), (84, 74), (22, 72), (78, 72), (45, 90), (55, 90)),
    ):
        landmarks[index, :2] = point
        landmarks[index, 3:] = 1.0
    return PoseEstimate(
        person_bbox=(25, 10, 75, 100),
        landmarks=landmarks,
        world_landmarks=np.zeros((39, 3), dtype=np.float32),
        segmentation_mask=np.zeros((120, 100), dtype=np.uint8),
        confidence=0.95,
    )


def test_pose_roi_uses_visible_shoulders_arms_and_hand_anchors() -> None:
    pose = make_pose()

    roi = pose.upper_body_roi((120, 100, 3), margin=0.1)

    assert roi == (9, 23, 92, 98)


def test_pose_roi_returns_none_when_no_arm_points_are_visible() -> None:
    pose = make_pose()
    landmarks = pose.landmarks.copy()
    landmarks[11:25, 3:] = 0.0
    hidden = PoseEstimate(
        pose.person_bbox, landmarks, pose.world_landmarks, pose.segmentation_mask, pose.confidence
    )

    assert hidden.upper_body_roi((120, 100, 3)) is None


def test_draw_pose_does_not_modify_source_frame() -> None:
    pose = make_pose()
    frame = np.zeros((120, 100, 3), dtype=np.uint8)

    annotated = draw_pose(frame, pose)

    assert annotated.shape == frame.shape
    assert np.any(annotated)
    assert not np.any(frame)


def test_pose_estimator_extracts_landmarks_from_sample_clip() -> None:
    if not DEFAULT_MODEL_PATH.is_file() or not DEFAULT_POSE_MODEL_PATH.is_file():
        pytest.skip("detector/pose ONNX assets are not installed")
    video = ROOT / "data" / "legacy" / "material" / "你好" / "01_你好_示范01.mp4"
    if not video.is_file():
        pytest.skip("sample clip is unavailable")

    frame = sample_video_frames(video, sample_count=1)[0]
    detection = PersonDetector().detect(frame)
    assert detection
    pose = PoseEstimator().estimate(frame, detection[0])

    assert pose is not None
    assert pose.landmarks.shape == (39, 5)
    assert pose.world_landmarks.shape == (39, 3)
    assert pose.segmentation_mask.shape == frame.shape[:2]
    assert pose.confidence >= 0.5
    roi = pose.upper_body_roi(frame.shape)
    assert roi is not None
    assert 0 <= roi[0] < roi[2] <= frame.shape[1]
    assert 0 <= roi[1] < roi[3] <= frame.shape[0]
