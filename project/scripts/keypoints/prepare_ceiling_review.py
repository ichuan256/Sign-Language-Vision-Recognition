"""Ceiling-review batch generator (2026-10-28).

Purpose: measure the teacher's TRUE systematic error against independent
human annotation. The first review round was contaminated: the offline tool
pre-fills teacher suggestions (initial_xy), and accepting without dragging
yields bit-identical "human" labels (9/11 coordinate items had zero
deviation). This batch therefore:

- strips initial_xy so every point must be placed independently;
- quotas by split, prioritising held-out generalization (test/validation);
- excludes every sample_id already present in the review jsonl;
- caps per-clip picks and same-frame duplicates, same as the pilot policy.

Output is a standard review package (review.html + context/ + provenance),
annotated by a human, exported to a jsonl, then compared to teacher labels
with the same NME/PCK protocol as training.
"""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import cv2
from vision.keypoints.student_data import digest
from vision.keypoints.student_review import write_review
from vision.keypoints.review_geometry import source_affine, review_context

SPLIT_QUOTA = {"test": 20, "validation": 15, "train": 15}
MAX_PER_CLIP = 2
MIN_TIME_GAP_S = 0.4


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--reviews", type=Path, required=True,
                   help="existing review jsonl; its sample_ids are excluded")
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    if out.exists() or not out.is_relative_to(ROOT / "project/_tmp"):
        raise ValueError("New bounded project/_tmp review output required")
    records = [json.loads(s) for s in (a.data / "records.jsonl").read_text(encoding="utf-8").splitlines()]
    reviewed = {json.loads(l)["sample_id"]
                for l in a.reviews.read_text(encoding="utf-8-sig").splitlines() if l.strip()}

    picked, seen_frames, clip_count, clip_times = [], set(), {}, {}
    for split, quota in SPLIT_QUOTA.items():
        pool = [r for r in records if r["split"] == split and r["kind"] == "teacher_positive"
                and r["sample_id"] not in reviewed]
        pool.sort(key=lambda r: (-r.get("focus_score", 0), r["sample_id"]))
        for r in pool:
            if len([x for x in picked if x["split"] == split]) >= quota:
                break
            src = r["source_sha256"]
            frame = (src, r["source_frame"])
            if frame in seen_frames or clip_count.get(src, 0) >= MAX_PER_CLIP:
                continue
            if any(abs(r["source_timestamp_s"] - t) < MIN_TIME_GAP_S - 1e-8
                   for t in clip_times.get(src, [])):
                continue
            row = dict(r)
            row.pop("initial_xy", None)     # force independent annotation
            picked.append(row)
            seen_frames.add(frame)
            clip_count[src] = clip_count.get(src, 0) + 1
            clip_times.setdefault(src, []).append(r["source_timestamp_s"])

    out.mkdir(parents=True)
    (out / "context").mkdir()
    checked = set()
    for row in picked:
        image = (a.data / "review" / row["image"]).resolve()
        source = (ROOT / row["source_path"]).resolve()
        if not image.is_relative_to(a.data.resolve()) or not image.is_file() \
                or not source.is_relative_to(ROOT):
            raise ValueError("Missing/conflicting review image")
        if source not in checked:
            if digest(source) != row["source_sha256"]:
                raise ValueError("Source SHA mismatch")
            checked.add(source)
        cap = cv2.VideoCapture(str(source))
        try:
            cap.set(cv2.CAP_PROP_POS_FRAMES, row["source_frame"])
            ok, frame_img = cap.read()
            if not ok:
                raise ValueError("Cannot decode context frame")
        finally:
            cap.release()
        ctx = out / "context" / (row["sample_id"] + ".jpg")
        if not ctx.resolve().is_relative_to(out) or not cv2.imwrite(
                str(ctx), review_context(frame_img, source_affine(row), row.get("initial_xy"))):
            raise ValueError("Invalid context output")
        row["image"] = Path(os.path.relpath(image, out)).as_posix()
        row["context"] = ctx.relative_to(out).as_posix()

    count = write_review(out, picked, len(picked), preserve_order=True)
    report = dict(
        purpose="teacher_ceiling_review_v2_no_suggestions",
        selection_count=count,
        split_counts={s: sum(1 for r in picked if r["split"] == s) for s in SPLIT_QUOTA},
        initial_xy_stripped=True,
        reviewed_ids_excluded=len(reviewed),
        records_sha256=digest(a.data / "records.jsonl"),
        human_labels_created=False,
    )
    (out / "provenance.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                         encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
