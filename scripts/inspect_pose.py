#!/usr/bin/env python3
"""Visualize person anchors and MediaPipe body/arm keypoints on a clip."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from signrec.person_detector import DEFAULT_MODEL_PATH, PersonDetector, draw_detections  # noqa: E402
from signrec.pose_estimator import DEFAULT_POSE_MODEL_PATH, PoseEstimator, draw_pose  # noqa: E402
from signrec.tracking import PersonTracker  # noqa: E402

IMAGE_SUFFIXES = {".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}


def read_image(path: Path) -> np.ndarray:
    image = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"cannot decode image: {path}")
    return image


def render_frame(
    frame: np.ndarray, detector: PersonDetector, pose_model: PoseEstimator, tracker: PersonTracker
) -> tuple[np.ndarray, int, int]:
    detections = detector.detect(frame)
    tracks = tracker.update(detections)
    output = draw_detections(frame, [item.detection for item in tracks])
    pose_count = 0
    for item in tracks:
        pose = pose_model.estimate(frame, item.detection)
        if pose is not None:
            output = draw_pose(output, pose)
            pose_count += 1
    return output, len(detections), pose_count


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="input still image or video")
    parser.add_argument("--output", "-o", required=True, type=Path, help="annotated image or .mp4 output")
    parser.add_argument("--person-model", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--pose-model", type=Path, default=DEFAULT_POSE_MODEL_PATH)
    parser.add_argument("--max-frames", type=int, default=None, help="optional video frame cap for a smoke run")
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source = args.input.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"input not found: {source}")
    if source == output:
        raise ValueError("output must not overwrite the source")
    if output.exists() and not args.overwrite:
        raise FileExistsError(f"output exists; pass --overwrite: {output}")
    if args.max_frames is not None and args.max_frames <= 0:
        raise ValueError("--max-frames must be positive")

    detector = PersonDetector(args.person_model)
    pose_model = PoseEstimator(args.pose_model)
    tracker = PersonTracker()
    if source.suffix.lower() in IMAGE_SUFFIXES:
        frame = read_image(source)
        rendered, people, poses = render_frame(frame, detector, pose_model, tracker)
        output.parent.mkdir(parents=True, exist_ok=True)
        ok, encoded = cv2.imencode(output.suffix or ".png", rendered)
        if not ok:
            raise RuntimeError(f"cannot encode output image: {output}")
        encoded.tofile(output)
        print(f"people={people} poses={poses} output={output}")
        return 0

    if output.suffix.lower() != ".mp4":
        raise ValueError("video output must use .mp4")
    capture = cv2.VideoCapture(str(source))
    if not capture.isOpened():
        raise RuntimeError(f"cannot open video: {source}")
    writer = None
    frame_count = raw_people = pose_frames = 0
    try:
        fps = float(capture.get(cv2.CAP_PROP_FPS))
        if not np.isfinite(fps) or fps <= 0:
            fps = 20.0
        while args.max_frames is None or frame_count < args.max_frames:
            ok, frame = capture.read()
            if not ok:
                break
            if writer is None:
                output.parent.mkdir(parents=True, exist_ok=True)
                height, width = frame.shape[:2]
                writer = cv2.VideoWriter(
                    str(output), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
                )
                if not writer.isOpened():
                    raise RuntimeError(f"cannot create video output: {output}")
            rendered, people, poses = render_frame(frame, detector, pose_model, tracker)
            frame_count += 1
            raw_people += bool(people)
            pose_frames += bool(poses)
            writer.write(rendered)
            if args.show:
                cv2.imshow("Pose ROI inspection", rendered)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    finally:
        capture.release()
        if writer is not None:
            writer.release()
        if args.show:
            cv2.destroyAllWindows()
    if frame_count == 0:
        raise RuntimeError(f"video contains no decodable frames: {source}")
    print(f"frames={frame_count} detector_frames={raw_people} pose_frames={pose_frames} output={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
