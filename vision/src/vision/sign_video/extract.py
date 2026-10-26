"""Extract MediaPipe Holistic features from explicitly listed videos.

Run from repository root: python -m algo.sign_video.extract --help
Does not load FPGA bitstreams, start cameras or modify original media.
"""
import argparse
import hashlib
import json
import time
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np

from .features import build_features, feature_schema
from .sharpen import sharpen_u8


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def landmarks(value, count, *, visibility=False):
    if value is None:
        return np.full((count, 4 if visibility else 3), np.nan, np.float32)
    return np.asarray([[p.x, p.y, p.z, p.visibility] if visibility else [p.x, p.y, p.z]
                       for p in value.landmark], dtype=np.float32)


def extract_one(sample, manifest_dir, output, target_fps, min_visibility, quarter_strength=0):
    source = (manifest_dir / sample["file"]).resolve()
    source_hash = sha256(source)
    if sample.get("sha256") and sample["sha256"] != source_hash:
        raise ValueError(f"source hash mismatch: {source}")
    cap = cv2.VideoCapture(str(source))
    try:
        if not cap.isOpened():
            raise ValueError(f"cannot decode: {source}")
        fps = cap.get(cv2.CAP_PROP_FPS)
        if not np.isfinite(fps) or fps <= 0:
            raise ValueError(f"invalid source fps: {source}")
        width, height = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        poses, hands, times, indices = [], [], [], []
        hand_seen = []
        best_score, preview = -1, None
        frame_index, next_time = 0, 0.0
        start = time.perf_counter()
        preprocess_s = 0.0
        # Holistic maintains anatomical left/right association through pose tracking.
        with mp.solutions.holistic.Holistic(
            static_image_mode=False, model_complexity=1, smooth_landmarks=True,
            enable_segmentation=False, refine_face_landmarks=False,
            min_detection_confidence=0.5, min_tracking_confidence=0.5,
        ) as detector:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                timestamp = frame_index / fps
                index = frame_index
                frame_index += 1
                if timestamp + 1e-8 < next_time:
                    continue
                next_time += 1.0 / min(target_fps, fps)
                preprocess_start = time.perf_counter()
                frame = sharpen_u8(frame, quarter_strength)
                preprocess_s += time.perf_counter() - preprocess_start
                result = detector.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                pose = landmarks(result.pose_landmarks, 33, visibility=True)
                pair = np.stack((landmarks(result.left_hand_landmarks, 21),
                                 landmarks(result.right_hand_landmarks, 21)))
                poses.append(pose)
                hands.append(pair)
                times.append(timestamp)
                indices.append(index)
                seen = np.isfinite(pair).all(axis=(1, 2))
                hand_seen.append(seen)
                score = int(seen.sum()) * 100 + int(np.sum(pose[:, 3] >= min_visibility))
                if score > best_score:
                    best_score = score
                    preview = frame.copy()
                    draw = mp.solutions.drawing_utils.draw_landmarks
                    draw(preview, result.pose_landmarks, mp.solutions.holistic.POSE_CONNECTIONS)
                    draw(preview, result.left_hand_landmarks, mp.solutions.holistic.HAND_CONNECTIONS)
                    draw(preview, result.right_hand_landmarks, mp.solutions.holistic.HAND_CONNECTIONS)
                    cv2.putText(preview, f'{sample["id"]} frame={index} t={timestamp:.3f}s',
                                (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
        if not poses:
            raise ValueError(f"no decoded frames: {source}")
        pose_array, hand_array = np.stack(poses), np.stack(hands)
        arrays = build_features(pose_array, hand_array, times, width=width, height=height,
                                visibility=min_visibility)
        npz_path = output / f'{sample["id"]}.npz'
        np.savez_compressed(npz_path, pose=pose_array, hands=hand_array,
                            timestamps_s=np.asarray(times), frame_indices=np.asarray(indices), **arrays)
        image_path = output / f'{sample["id"]}.jpg'
        if not cv2.imwrite(str(image_path), preview):
            raise OSError(f"cannot write preview: {image_path}")
        seen = np.stack(hand_seen)
        return {"id": sample["id"], "label": sample.get("label"),
                "signer_id": sample.get("signer_id"), "session_id": sample.get("session_id"),
                "source_group": sample["source_group"], "split": sample.get("split", "unassigned"),
                "annotation_status": sample.get("annotation_status", "unverified"),
                "source_file": str(source), "source_sha256": source_hash,
                "source_start_s": sample.get("source_start_s"), "source_end_s": sample.get("source_end_s"),
                "source_url": sample.get("source_url"),
                "width": width, "height": height, "source_fps": fps,
                "source_frames_decoded": frame_index, "sampled_frames": len(times),
                "timestamp_basis": "frame_index / reported_fps (CFR only; not verified VFR PTS)",
                "feature_shape": list(arrays["features"].shape),
                "body_valid_rate": float(arrays["body_valid"].mean()),
                "left_hand_detected_rate": float(seen[:, 0].mean()),
                "right_hand_detected_rate": float(seen[:, 1].mean()),
                "both_hands_detected_rate": float(seen.all(axis=1).mean()),
                "elapsed_s": round(time.perf_counter() - start, 3),
                "sharpen_quarter_strength": quarter_strength,
                "preprocess_total_s": preprocess_s,
                "preprocess_mean_ms": preprocess_s * 1000 / len(times),
                "npz": npz_path.name, "npz_sha256": sha256(npz_path), "preview": image_path.name}
    finally:
        cap.release()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fps", type=float, default=15)
    parser.add_argument("--visibility", type=float, default=0.5)
    parser.add_argument("--sharpen-quarter", type=int, choices=(0, 1, 2), default=0,
                        help="CPU reference sharpening strength: 0, 0.25, 0.5")
    args = parser.parse_args()
    if not np.isfinite(args.fps) or args.fps <= 0 or not 0 <= args.visibility <= 1:
        parser.error("fps must be positive; visibility must be in [0,1]")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    samples = manifest["samples"]
    ids = [sample["id"] for sample in samples]
    if not samples or len(ids) != len(set(ids)):
        parser.error("manifest needs samples with unique IDs")
    for sample in samples:
        if not sample.get("source_group"):
            parser.error("every sample needs a source_group to prevent source leakage")
        if not sample["id"] or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in sample["id"]):
            parser.error("sample IDs may contain only ASCII letters, digits, underscore, hyphen")
    # Never overwrite existing experiment outputs.
    args.output.mkdir(parents=True, exist_ok=False)
    schema = feature_schema()
    (args.output / "schema.json").write_text(json.dumps(schema, indent=2), encoding="utf-8")
    report = {"purpose": "extraction_smoke_test_not_recognition_accuracy", "schema_version": schema["version"],
              "mediapipe_version": mp.__version__, "opencv_version": cv2.__version__,
              "numpy_version": np.__version__, "manifest_sha256": sha256(args.manifest),
              "sample_fps_requested": args.fps, "pose_visibility_threshold": args.visibility,
              "sharpen_quarter_strength": args.sharpen_quarter,
              "model": "MediaPipe Solutions Holistic, model_complexity=1",
              "samples": [], "errors": []}
    for sample in samples:
        try:
            result = extract_one(sample, args.manifest.parent, args.output, args.fps, args.visibility,
                                 args.sharpen_quarter)
            report["samples"].append(result)
            print(json.dumps(result, ensure_ascii=False), flush=True)
        except Exception as exc:
            report["errors"].append({"id": sample["id"], "error": str(exc)})
            print(f'ERROR {sample["id"]}: {exc}', flush=True)
        (args.output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if report["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
