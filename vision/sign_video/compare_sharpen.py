"""Paired CPU sharpening experiment. No model training or FPGA interaction."""
import argparse
import json
import re
import time
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .extract import extract_one, sha256
from .features import feature_schema
from .sharpen import sharpen_u8


def longest_run(bits):
    best = current = 0
    for bit in bits:
        current = current + 1 if bit else 0
        best = max(best, current)
    return best


def detection_metrics(path):
    with np.load(path, allow_pickle=False) as arrays:
        seen = np.isfinite(arrays["hands"]).all(axis=(2, 3))
        assert np.isfinite(arrays["features"]).all()
        assert arrays["features"].shape == (len(seen), feature_schema()["dimension"])
        return {"frames": len(seen), "both_hands_frames": int(seen.all(axis=1).sum()),
                "hand_dropouts": int((seen[:-1] & ~seen[1:]).sum()),
                "left_longest_missing_frames": longest_run(~seen[:, 0]),
                "right_longest_missing_frames": longest_run(~seen[:, 1])}


def preview(source, output):
    """Same source frames, no detection-driven selection or lossy re-encoding."""
    cap = cv2.VideoCapture(str(source))
    try:
        length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_ids = sorted(set((0, length // 2)))
        font = ImageFont.load_default(size=18)
        canvas = Image.new("RGB", (1100, len(frame_ids) * 530 + 60), "#141c28")
        draw = ImageDraw.Draw(canvas)
        draw.text((12, 10), "Same source frames | top: full frame | bottom: nearest-neighbour hand crop",
                  font=font, fill="white")
        records = []
        for row, index in enumerate(frame_ids):
            cap.set(cv2.CAP_PROP_POS_FRAMES, index)
            ok, frame = cap.read()
            if not ok:
                raise ValueError("preview frame decode failed")
            h, w = frame.shape[:2]
            # Fixed image-space ROI, equal in all variants; not a detector crop.
            roi = (int(w * 0.03), int(h * 0.32), int(w * 0.59), h)
            records.append({"source_frame_index": index, "crop_xyxy": list(roi)})
            for col, q in enumerate((0, 1, 2)):
                result = sharpen_u8(frame, q)
                rgb = Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB))
                x, y = col * 365 + 8, row * 530 + 60
                draw.text((x, y), f"frame {index} | strength {q / 4:g}", font=font, fill="white")
                full = rgb.copy()
                full.thumbnail((352, 288), Image.Resampling.NEAREST)
                canvas.paste(full, (x, y + 30))
                # Preserve relative geometry; nearest-neighbour enlarging exposes pixels.
                ratio = min(352 / (roi[2] - roi[0]), 195 / (roi[3] - roi[1]))
                crop = rgb.crop(roi).resize((round((roi[2] - roi[0]) * ratio),
                                             round((roi[3] - roi[1]) * ratio)), Image.Resampling.NEAREST)
                canvas.paste(crop, (x, y + 328))
        canvas.save(output / "comparison.png")
        return {"source_file": str(source), "frames": records,
                "note": "illustrative fixed frame/ROI selection, not a quality score"}
    finally:
        cap.release()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=2)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("repeats must be positive")
    samples = json.loads(args.manifest.read_text(encoding="utf-8"))["samples"]
    ids = [s["id"] for s in samples]
    if not samples or len(ids) != len(set(ids)) or any(not re.fullmatch(r"[A-Za-z0-9_-]+", i) for i in ids):
        parser.error("nonempty samples with unique safe IDs required")
    if any(not s.get("source_group") for s in samples):
        parser.error("source_group required")
    args.output.mkdir(parents=True, exist_ok=False)
    summary = {"status": "incomplete", "purpose": "paired_detection_comparison_not_recognition_accuracy",
               "manifest_sha256": sha256(args.manifest), "repeats": args.repeats,
               "sample_fps": 15, "mediapipe_version": mp.__version__, "opencv_version": cv2.__version__,
               "kernel": "clip((4*C+q*(4*C-N-S-E-W)+2)//4,0,255)",
               "border": "unchanged outermost row/column", "channel_mode": "independent RGB/BGR channels",
               "runs": []}
    (args.output / "schema.json").write_text(json.dumps(feature_schema(), indent=2), encoding="utf-8")
    paired = {}
    for repeat in range(args.repeats):
        # Order alternates to reduce systematic timing warm-up effects; each clip gets a fresh tracker.
        for q in ((0, 1, 2) if repeat % 2 == 0 else (2, 1, 0)):
            directory = args.output / f"q{q}_repeat{repeat + 1}"
            directory.mkdir()
            run = {"quarter_strength": q, "repeat": repeat + 1, "samples": []}
            started = time.perf_counter()
            for sample in samples:
                result = extract_one(sample, args.manifest.parent, directory, 15, 0.5, q)
                path = directory / result["npz"]
                assert sha256(path) == result["npz_sha256"]
                result.update(detection_metrics(path))
                with np.load(path, allow_pickle=False) as arrays:
                    key = sample["id"]
                    signature = (result["source_sha256"], arrays["frame_indices"].copy(), arrays["timestamps_s"].copy())
                    if key in paired:
                        original = paired[key]
                        assert signature[0] == original[0]
                        np.testing.assert_array_equal(signature[1], original[1])
                        np.testing.assert_array_equal(signature[2], original[2])
                    else:
                        paired[key] = signature
                run["samples"].append(result)
            run["frames"] = sum(s["frames"] for s in run["samples"])
            run["both_hands_frames"] = sum(s["both_hands_frames"] for s in run["samples"])
            run["both_hands_rate"] = run["both_hands_frames"] / run["frames"]
            run["hand_dropouts"] = sum(s["hand_dropouts"] for s in run["samples"])
            run["preprocess_mean_ms"] = sum(s["preprocess_total_s"] for s in run["samples"]) * 1000 / run["frames"]
            run["elapsed_s"] = time.perf_counter() - started
            summary["runs"].append(run)
            (directory / "report.json").write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8")
            (args.output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps({k: v for k, v in run.items() if k != "samples"}), flush=True)
    summary["preview"] = preview((args.manifest.parent / samples[0]["file"]).resolve(), args.output)
    summary["status"] = "complete"
    (args.output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
