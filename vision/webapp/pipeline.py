"""Adapter that streams detector/pose previews and classifies a whole clip."""

from __future__ import annotations

import base64
import os
import time
from pathlib import Path
from threading import Event
from typing import Callable

import cv2
import numpy as np

from signrec.dataset import uniform_frame_indices
from signrec.features import MobileNetV2Embedder
from signrec.person_detector import PersonDetector, draw_detections
from signrec.pose_estimator import PoseEstimator, draw_pose
from signrec.recognizer import TemplateRecognizer, load_templates
from signrec.tracking import PersonTracker


class SignRecognitionPipeline:
    """Run existing CPU OpenCV models over one pre-segmented input video.

    Person/pose overlays stream while frames are processed. The sign label is a
    clip-level DTW result, so it is returned after the uniformly sampled clip
    features are ready.
    """

    def __init__(
        self,
        *,
        person_model: str | Path,
        pose_model: str | Path,
        backbone_model: str | Path,
        templates_path: str | Path,
        sample_count: int = 8,
        detection_stride: int = 2,
        pose_stride: int = 4,
        preview_stride: int = 2,
        preview_max_width: int = 960,
    ) -> None:
        if sample_count <= 0 or detection_stride <= 0 or pose_stride <= 0 or preview_stride <= 0:
            raise ValueError("sample count and frame strides must be positive")
        self.detector = PersonDetector(person_model)
        self.pose = PoseEstimator(pose_model)
        self.embedder = MobileNetV2Embedder(backbone_model)
        self.recognizer = TemplateRecognizer(load_templates(templates_path))
        self.sample_count = sample_count
        self.detection_stride = detection_stride
        self.pose_stride = pose_stride
        self.preview_stride = preview_stride
        self.preview_max_width = preview_max_width

    def process_video(
        self,
        video_path: str | Path,
        emit: Callable[[dict[str, object]], None],
        cancelled: Event,
        annotated_video_path: str | Path | None = None,
    ) -> dict[str, object]:
        path = Path(video_path)
        annotated_path = Path(annotated_video_path) if annotated_video_path is not None else None
        annotated_writer = None
        annotated_frame_count = 0
        capture = cv2.VideoCapture(str(path))
        if not capture.isOpened():
            raise RuntimeError("OpenCV could not open the uploaded video")
        total_frames = int(round(capture.get(cv2.CAP_PROP_FRAME_COUNT)))
        if total_frames <= 0:
            capture.release()
            raise RuntimeError("video frame count is unavailable or empty")

        indices = uniform_frame_indices(total_frames, self.sample_count)
        sample_slots: dict[int, list[int]] = {}
        for feature_index, frame_index in enumerate(indices):
            sample_slots.setdefault(frame_index, []).append(feature_index)
        sampled_features: list[np.ndarray | None] = [None] * self.sample_count
        tracker = PersonTracker()
        started = time.perf_counter()
        frame_index = 0
        detection_frames = 0
        pose_frames = 0
        fps = float(capture.get(cv2.CAP_PROP_FPS))
        if not np.isfinite(fps) or fps <= 0:
            fps = 20.0

        try:
            while frame_index < total_frames:
                if cancelled.is_set():
                    return {"cancelled": True, "frames_processed": frame_index}
                ok, frame = capture.read()
                if not ok:
                    break

                detections = (
                    self.detector.detect(frame)
                    if frame_index % self.detection_stride == 0
                    else []
                )
                tracks = tracker.update(detections)
                detection_frames += int(bool(detections))
                annotated = draw_detections(
                    frame, [track.detection for track in tracks]
                )
                visible_poses = 0
                if frame_index % self.pose_stride == 0:
                    for track in tracks:
                        if track.stale:
                            continue
                        estimate = self.pose.estimate(frame, track.detection)
                        if estimate is not None:
                            annotated = draw_pose(annotated, estimate)
                            visible_poses += 1
                pose_frames += int(visible_poses > 0)

                if annotated_path is not None:
                    if annotated_writer is None:
                        annotated_path.parent.mkdir(parents=True, exist_ok=True)
                        writer_backend = (
                            cv2.CAP_MSMF
                            if os.name == "nt" and hasattr(cv2, "CAP_MSMF")
                            else cv2.CAP_ANY
                        )
                        annotated_writer = cv2.VideoWriter(
                            str(annotated_path),
                            writer_backend,
                            cv2.VideoWriter_fourcc(*"avc1"),
                            fps,
                            (frame.shape[1], frame.shape[0]),
                        )
                        if not annotated_writer.isOpened():
                            annotated_writer.release()
                            annotated_writer = None
                            raise RuntimeError(
                                "OpenCV could not initialize an H.264 MP4 encoder; "
                                "use an OpenCV build with AVC encoding support"
                            )
                    annotated_writer.write(annotated)
                    annotated_frame_count += 1

                if frame_index in sample_slots:
                    feature = self.embedder.embed_frame(frame)
                    for feature_index in sample_slots[frame_index]:
                        sampled_features[feature_index] = feature

                processed = frame_index + 1
                progress = min(processed / total_frames, 1.0)
                elapsed = max(time.perf_counter() - started, 1e-6)
                if frame_index % self.preview_stride == 0 or processed == total_frames:
                    preview = self._preview_frame(annotated)
                    ok, encoded = cv2.imencode(
                        ".jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 72]
                    )
                    if ok:
                        emit(
                            {
                                "type": "frame",
                                "frame_index": frame_index,
                                "total_frames": total_frames,
                                "progress": progress,
                                "people": len(tracks),
                                "raw_detections": len(detections),
                                "poses": visible_poses,
                                "processing_fps": processed / elapsed,
                                "image_base64": base64.b64encode(encoded).decode("ascii"),
                            }
                        )
                if processed % 5 == 0 or processed == total_frames:
                    emit(
                        {
                            "type": "progress",
                            "frame_index": frame_index,
                            "total_frames": total_frames,
                            "progress": progress,
                            "processing_fps": processed / elapsed,
                        }
                    )
                frame_index += 1
        finally:
            capture.release()
            if annotated_writer is not None:
                annotated_writer.release()

        if annotated_path is not None:
            if annotated_frame_count != frame_index or not annotated_path.is_file() or annotated_path.stat().st_size == 0:
                raise RuntimeError("annotated video output is incomplete or empty")
            validation_capture = cv2.VideoCapture(str(annotated_path))
            try:
                if not validation_capture.isOpened() or not validation_capture.read()[0]:
                    raise RuntimeError("generated annotated video cannot be decoded")
            finally:
                validation_capture.release()

        if frame_index != total_frames:
            raise RuntimeError(
                f"video ended early ({frame_index}/{total_frames} frames decoded)"
            )
        if any(feature is None for feature in sampled_features):
            raise RuntimeError("not all temporal feature samples were decoded")

        query = np.stack([feature for feature in sampled_features if feature is not None])
        predictions = self.recognizer.predict(query, top_k=5)
        elapsed = max(time.perf_counter() - started, 1e-6)
        return {
            "frames_processed": frame_index,
            "detection_frames": detection_frames,
            "pose_frames": pose_frames,
            "detection_stride": self.detection_stride,
            "pose_stride": self.pose_stride,
            "elapsed_seconds": elapsed,
            "processing_fps": frame_index / elapsed,
            "result_domain": "cropped-material prototype; full-frame camera validation pending",
            "similarity_note": "similarity is not a calibrated probability; no rejection threshold is selected",
            "predictions": [
                {
                    "label": prediction.label,
                    "distance": prediction.distance,
                    "similarity": prediction.similarity,
                    "accepted": prediction.accepted,
                }
                for prediction in predictions
            ],
        }

    def _preview_frame(self, frame: np.ndarray) -> np.ndarray:
        height, width = frame.shape[:2]
        if width <= self.preview_max_width:
            return frame
        scale = self.preview_max_width / width
        return cv2.resize(
            frame,
            (self.preview_max_width, max(1, int(round(height * scale)))),
            interpolation=cv2.INTER_AREA,
        )
