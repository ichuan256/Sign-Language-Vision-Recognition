"""MediaPipe Holistic keypoint extraction over any FrameSource.

This is the M1 live/streaming counterpart of vision/src/vision/sign_video/extract.py:
same detector settings, same NaN-on-missing convention, same
sign_xy_v1 feature contract — only the frame provider is abstracted.
extract.py stays the batch/experiment entry; this module serves
FrameSource-driven pipelines (files today, USB cam, board HDMI in or
OV5640 later) with identical downstream features.
"""
import cv2
import mediapipe as mp
import numpy as np

from ..sign_video.features import build_features


def _landmarks(value, count, *, visibility=False):
    if value is None:
        return np.full((count, 4 if visibility else 3), np.nan, np.float32)
    return np.asarray([[p.x, p.y, p.z, p.visibility] if visibility else [p.x, p.y, p.z]
                       for p in value.landmark], dtype=np.float32)


class HolisticTracker:
    """Accumulates pose/hands landmarks and sign_xy_v1 features from a source.

    Usage:
        with VideoFileSource(path, max_fps=15) as src, HolisticTracker() as t:
            arrays = t.run(src)

    Downsampling is the FrameSource's job (VideoFileSource(max_fps=...),
    USBCamSource(max_fps=...)), so this class never decides frame timing.
    """

    def __init__(self, *, model_complexity=1, min_detection_confidence=0.5,
                 min_tracking_confidence=0.5):
        self._options = dict(static_image_mode=False, model_complexity=model_complexity,
                             smooth_landmarks=True, enable_segmentation=False,
                             refine_face_landmarks=False,
                             min_detection_confidence=min_detection_confidence,
                             min_tracking_confidence=min_tracking_confidence)
        self._detector = None

    def __enter__(self):
        self._detector = mp.solutions.holistic.Holistic(**self._options)
        return self

    def __exit__(self, exc_type, exc, tb):
        self._detector.close()
        self._detector = None
        return False

    def run(self, source, *, min_visibility=0.5):
        """Consume a FrameSource fully; return the same arrays extract.py saves."""
        if self._detector is None:
            raise RuntimeError("HolisticTracker must be used as a context manager")
        poses, hands, times, indices = [], [], [], []
        for bgr, frame_id, timestamp in source:
            result = self._detector.process(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
            poses.append(_landmarks(result.pose_landmarks, 33, visibility=True))
            hands.append(np.stack((_landmarks(result.left_hand_landmarks, 21),
                                   _landmarks(result.right_hand_landmarks, 21))))
            times.append(timestamp)
            indices.append(frame_id)
        if not poses:
            raise ValueError(f"no frames read from source: {source.name}")
        pose_array, hand_array = np.stack(poses), np.stack(hands)
        height, width = bgr.shape[:2]
        arrays = build_features(pose_array, hand_array, times, width=width,
                                height=height, visibility=min_visibility)
        arrays.update(pose=pose_array, hands=hand_array,
                      timestamps_s=np.asarray(times), frame_indices=np.asarray(indices),
                      source_name=source.name)
        return arrays
