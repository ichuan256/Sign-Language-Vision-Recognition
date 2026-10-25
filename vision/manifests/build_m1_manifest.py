"""Build the M1 DTW vocabulary manifest from the reviewed wsy fullframe CSV.

Selection rule (v1, documented for the record): labels with >= 3 clips in
dataset_manifest_fullframe_20261021.csv. 谢谢 is the only label spanning
two source parts (p01+p04), making it the single label that supports an
honest group hold-out; everything else is trained/tested same-source and
must be reported as 已见回放, never as recognition accuracy.
"""
import csv
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CSV_PATH = (REPO / "vision/video/done/wsy/全22课全画幅样本_fullframe_264条_20261021"
            / "dataset_manifest_fullframe_20261021.csv")
MEDIA_ROOT = CSV_PATH.parent
OUT = Path(__file__).resolve().parent / "m1_vocabulary_20261023.json"

MIN_CLIPS = 3
CONF_TO_STATUS = {"高": "reviewed_boundary_high_confidence",
                  "中高": "reviewed_boundary_medium_high",
                  "中": "reviewed_boundary_medium"}


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    with open(CSV_PATH, encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    counts = {}
    for row in rows:
        counts[row["类别"]] = counts.get(row["类别"], 0) + 1
    chosen = sorted(label for label, n in counts.items() if n >= MIN_CLIPS)
    samples, errors = [], []
    seq = 0
    for row in rows:
        label = row["类别"]
        if label not in chosen:
            continue
        rel_media = Path("vision/video/done/wsy") / CSV_PATH.parent.name / label / Path(row["输出路径"]).name
        media = REPO / rel_media
        if not media.is_file():
            errors.append({"label": label, "missing": str(media)})
            continue
        seq += 1
        part = row["part"].strip()
        samples.append({
            "id": f"m1_{part}_{seq:03d}",
            "file": str(Path("../../") / rel_media),
            "label": label,
            "sha256": sha256(media),
            "source_group": f"wsy_fullframe_{part}",
            "signer_id": None,
            "session_id": None,
            "split": "unassigned",
            "annotation_status": CONF_TO_STATUS.get(row["置信度"].strip(),
                                                    "reviewed_boundary_unspecified"),
            "source_start_s": float(row["原片起始秒"]),
            "source_end_s": float(row["原片结束秒"]),
        })
    manifest = {
        "purpose": "m1_dtw_baseline_vocabulary",
        "vocabulary": chosen,
        "selection_rule": f"labels with >= {MIN_CLIPS} clips in {CSV_PATH.name}",
        "media_root_note": "file paths are relative to this manifest's directory",
        "source_csv": CSV_PATH.name,
        "samples": samples,
    }
    OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"vocabulary": chosen, "n_samples": len(samples),
                      "n_errors": len(errors), "errors": errors}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
