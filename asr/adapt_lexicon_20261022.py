# adapt_lexicon_20261022.py - adapt material_fullframe_20261021 into the live lexicon
# Policy: one best sample per phrase (置信度 高>中>低, tie -> more frames);
# phrases already in the field-verified existing 5 stay untouched.
import csv, hashlib, json, re, unicodedata
from pathlib import Path

SRC = Path(r"F:\PLD\_tmp\material_check\material_fullframe_20261021")
MANIFEST = SRC / "dataset_manifest_fullframe_20261021.csv"
VIDEO_ROOT = Path(r"F:\PLD\pld-sign-glove\video")
DEST_SUB = "clips_22parts"
DEST = VIDEO_ROOT / DEST_SUB
PHRASES = VIDEO_ROOT / "phrases.json"
PHRASES_SD = VIDEO_ROOT / "phrases_sd.json"

def normalize(text):
    return ''.join(c for c in text if not c.isspace()
                   and not unicodedata.category(c).startswith('P'))

def safe_name(text):
    t = re.sub(r'[\\/:*?"<>|\s]+', '_', text).strip('._')
    return t[:40] or "unnamed"

def sha256(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    existing_sd = json.loads(PHRASES_SD.read_text(encoding='utf-8-sig'))
    existing_phrases = {normalize(ph) for e in existing_sd['clips'] for ph in e['phrases']}
    print("existing phrases:", sorted(existing_phrases))

    rows = list(csv.DictReader(open(MANIFEST, encoding='utf-8-sig')))
    conf_rank = {"高": 3, "中": 2, "低": 1}
    groups = {}
    for r in rows:
        key = normalize(r["类别"])
        groups.setdefault(key, []).append(r)

    picked, skipped_dup, skipped_existing = [], [], []
    for key, items in groups.items():
        if key in existing_phrases:
            skipped_existing.append(key)
            continue
        best = max(items, key=lambda r: (conf_rank.get(r.get("置信度", ""), 0),
                                         int(r.get("帧数") or 0)))
        picked.append((key, best, len(items)))

    DEST.mkdir(exist_ok=True)
    new_entries = []
    for key, r, n_samples in sorted(picked):
        cat = r["类别"]
        rel = r["输出路径"].split("material_fullframe_20261021")[-1].lstrip("\\/")
        src_file = SRC / Path(rel)
        if not src_file.is_file():
            print("MISSING", rel); continue
        dest_rel = "%s/%s/%s_%s.mp4" % (DEST_SUB, safe_name(cat),
                                        r["样本编号"], safe_name(cat))
        dest_file = VIDEO_ROOT / dest_rel
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        if not dest_file.exists():
            dest_file.write_bytes(src_file.read_bytes())
        if sha256(dest_file) != r["SHA256"]:
            raise ValueError("sha mismatch after copy: " + dest_rel)
        new_entries.append({
            "phrases": [cat],
            "label": cat,
            "file": dest_rel.replace("\\", "/"),
            "source_part": r.get("part"),
            "source_start": float(r["原片起始秒"]),
            "source_end": float(r["原片结束秒"]),
            "sha256": r["SHA256"],
            "samples_in_source": n_samples,
        })

    out_sd = dict(existing_sd)
    out_sd["clips"] = existing_sd["clips"] + new_entries
    out_sd["adapted_from"] = ("material_fullframe_20261021/dataset_manifest_fullframe_20261021.csv; "
                              "one best sample per phrase; existing 5 phrases kept")
    out_sd["adapted_on"] = "2026-10-22"
    PHRASES_SD.write_text(json.dumps(out_sd, ensure_ascii=False, indent=2), encoding="utf-8")

    existing_plain = json.loads(PHRASES.read_text(encoding='utf-8-sig'))
    out_plain = dict(existing_plain)
    out_plain["clips"] = existing_plain["clips"] + [dict(e) for e in new_entries]
    PHRASES.write_text(json.dumps(out_plain, ensure_ascii=False, indent=2), encoding="utf-8")

    print("picked %d new phrases (from %d source categories), %d samples chosen"
          % (len(new_entries), len(groups), len(picked)))
    print("skipped existing:", sorted(skipped_existing))
    print("clips copied to:", DEST)
    print("manifests updated: phrases.json + phrases_sd.json")

if __name__ == "__main__":
    main()
