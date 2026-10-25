#!/usr/bin/env python3
"""Run low-resolution full-frame person detection on an image or video file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
sys.path.insert(0, str(ROOT / "vision/src"))

from signrec.person_detector import DEFAULT_MODEL_PATH, PersonDetector, draw_detections  # noqa: E402
from signrec.tracking import PersonTracker  # noqa: E402

IMAGE_SUFFIXES = {".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}


def read_image(path: Path) -> np.ndarray:
    data = np.fromfile(path, dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"cannot decode image: {path}")
    return image


def write_image(path: Path, image: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, encoded = cv2.imencode(path.suffix or ".png", image)
    if not ok:
        raise RuntimeError(f"cannot encode output image: {path}")
    encoded.tofile(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="input image or video file")
    parser.add_argument("--output", "-o", required=True, type=Path, help="annotated output image/video; video output must be .mp4")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH, help="OpenCV Zoo person detector ONNX model")
    parser.add_argument("--score-threshold", type=float, default=0.5)
    parser.add_argument("--nms-threshold", type=float, default=0.3)
    parser.add_argument("--show", action="store_true", help="show an interactive preview while processing video")
    parser.add_argument("--overwrite", action="store_true", help="allow replacing the output file")
    return parser


def run_image(detector: PersonDetector, source: Path, output: Path) -> int:
    frame = read_image(source)
    detections = detector.detect(frame)
    annotated = draw_detections(frame, detections)
    write_image(output, annotated)
    for detection in detections:
        print(f"person score={detection.confidence:.3f} bbox={detection.bbox}")
    print(f"detections={len(detections)} output={output}")
    return len(detections)


def run_video(
    detector: PersonDetector, source: Path, output: Path, show: bool = False
) -> tuple[int, int, int, int]:
    if output.suffix.lower() != ".mp4":
        raise ValueError("video output path must end in .mp4")
    capture = cv2.VideoCapture(str(source))
    if not capture.isOpened():
        raise RuntimeError(f"cannot open video: {source}")

    writer = None
    frame_count = 0
    frames_with_detection = 0
    frames_with_track = 0
    max_people = 0
    tracker = PersonTracker()
    try:
        fps = float(capture.get(cv2.CAP_PROP_FPS))
        if not np.isfinite(fps) or fps <= 0:
            fps = 20.0
        while True:
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
                    raise RuntimeError(f"cannot open video writer: {output}")

            detections = detector.detect(frame)
            frame_count += 1
            if detections:
                frames_with_detection += 1
            tracks = tracker.update(detections)
            if tracks:
                frames_with_track += 1
                max_people = max(max_people, len(tracks))
            tracked_detections = [track.detection for track in tracks]
            annotated = draw_detections(frame, tracked_detections)
            writer.write(annotated)
            if show:
                cv2.imshow("Full-frame person detection", annotated)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    finally:
        capture.release()
        if writer is not None:
            writer.release()
        if show:
            cv2.destroyAllWindows()

    if frame_count == 0:
        raise RuntimeError(f"video contains no decodable frames: {source}")
    print(
        f"frames={frame_count} raw_detection_frames={frames_with_detection} "
        f"tracked_frames={frames_with_track} max_tracks={max_people} output={output}"
    )
    return frame_count, frames_with_detection, frames_with_track, max_people


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source = args.input.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"input file not found: {source}")
    if source == output:
        raise ValueError("output path must not overwrite the input")
    if output.exists() and not args.overwrite:
        raise FileExistsError(f"output already exists (pass --overwrite to replace): {output}")

    detector = PersonDetector(
        model_path=args.model,
        score_threshold=args.score_threshold,
        nms_threshold=args.nms_threshold,
    )
    if source.suffix.lower() in IMAGE_SUFFIXES:
        run_image(detector, source, output)
    else:
        run_video(detector, source, output, show=args.show)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
