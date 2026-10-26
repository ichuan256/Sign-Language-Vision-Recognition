"""Check the four-module code layout and the SHA-bound current local media set."""
from pathlib import Path
import argparse
import ast
import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".wmv", ".mpg", ".mpeg", ".mts", ".m2ts", ".3gp"}
SKIP = {"_tmp", "_cache", "__pycache__", "video", "ip_repo", "losslesscut"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def confined(root, relative):
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()), f"Path outside repository: {relative}")
    return path


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def bound_csv(root, pointer, field):
    info = json.loads(confined(root, pointer).read_text(encoding="utf-8-sig"))
    path = confined(root, info[field])
    require(sha256(path) == info["sha256"], f"Pointer SHA mismatch: {pointer}")
    data = rows(path)
    require(len(data) == info["rows"], f"Pointer row count mismatch: {pointer}")
    return info, data


def check_media(root):
    historical = rows(root / "vision/data/manifests/manifest_fullframe_20261024.csv")
    require(len(historical) == 636, "Historical full-frame row count changed")
    require(len(rows(root / "vision/data/legacy/material/dataset_manifest_20261020.csv")) == 225, "Historical cropped row count changed")
    info, current = bound_csv(root, "vision/data/manifests/current_available_fullframe.json", "manifest")
    require(len(current) == 551, "Expected the reviewed 551-row available subset")
    audit = json.loads((root / "vision/analysis/dataset/label_source_audit_20261025.json").read_text(encoding="utf-8-sig"))
    require(sha256(confined(root, audit["full_manifest"]["path"])) == audit["full_manifest"]["sha256"], "Full manifest/audit SHA mismatch")
    audited = {r["path"]: r for r in audit["records"]}
    accepted = set()
    for r in current:
        p = r["输出路径"]
        require(p not in accepted, f"Duplicate current sample: {p}")
        accepted.add(p)
        a = audited[p]
        require((r["类别"], r["样本编号"], r["part"]) == (a["label"], a["sample_id"], a["contributor"]), f"Sample identity mismatch: {p}")
        require(sha256(confined(root, p)) == a["sha256"], f"Current media SHA mismatch: {p}")
    pending = rows(confined(root, info["pending_manifest"]))
    require(len(pending) == 85, "Expected 85 pending versions")
    for r in pending:
        require(r["path"] not in accepted and r["included_in_current_verified_manifest"].lower() == "false", "Pending version entered available subset")
        require(sha256(confined(root, r["path"])) == r["sha256"], f"Pending media changed: {r['path']}")
        require(r["sha256"] != r["old_expected_sha256"], "Pending version no longer differs from historical SHA")
    _, sources = bound_csv(root, "vision/data/manifests/source_registry_current.json", "registry")
    require(len(sources) == 32, "Expected 32 current source videos")
    for r in sources:
        require(sha256(confined(root, r["path"])) == r["sha256"], f"Source media changed: {r['path']}")
    protected = rows(root / "vision/analysis/materials/20261025_merge/protected_media_layout.csv")
    require(len(protected) == 816, "Protected media count changed")
    for r in protected:
        p = confined(root, r["path"])
        require(p.stat().st_size == int(r["bytes"]) and sha256(p) == r["sha256"], f"Protected media changed: {r['path']}")
    actual = {p.relative_to(root).as_posix() for folder in ("vision/video", "ASR/.sd_cache", "vision/data/legacy/material")
              for p in (root / folder).rglob("*") if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS}
    require(actual == {r["path"] for r in protected}, "Actual media path set differs from protected inventory")
    require(len(list((root / "ASR/.sd_cache").glob("*.mp4"))) == 142, "ASR vocabulary count changed")
    require(len(list((root / "vision/data/legacy/material").rglob("*.mp4"))) == 1, "Legacy deleted media was restored")
    index = root / "vision/video/sources.json"
    source_rows = json.loads(index.read_text(encoding="utf-8-sig"))
    require(len(source_rows) == 22, "BV runtime source index count changed")
    for r in source_rows:
        p = (index.parent / r["file"]).resolve()
        require(p.is_relative_to(root) and sha256(p) == r["sha256"], "BV runtime source index mismatch")
    for manifest in (root / "vision/data/manifests/m1_8class").glob("*.json"):
        for sample in json.loads(manifest.read_text(encoding="utf-8")).get("samples", []):
            require((manifest.parent / sample["file"]).is_file(), f"M1 sample missing: {sample['file']}")
    print("PASS current551 SHA/identity; pending85 isolated; sources32; protected816; ASR142; legacy1; BV22")


def check_root_dirs(root):
    dirs = {p.name for p in root.iterdir() if p.is_dir() and p.name != ".git"}
    expected = {"ASR", "docs", "project", "vision"}
    require(expected.issubset(dirs), f"Missing main modules: {sorted(expected-dirs)}")
    extras = dirs - expected
    if not extras:
        return []
    evidence = root / "vision/analysis/materials/20261025_merge/local_layout_residue.json"
    require(evidence.is_file(), f"Unexpected root directories: {sorted(extras)}")
    records = json.loads(evidence.read_text(encoding="utf-8-sig"))["roots"]
    require(extras.issubset(records), f"Undocumented root residue: {sorted(extras-set(records))}")
    for name in extras:
        recorded = {r["path"]: r for r in records[name]}
        actual = {p.relative_to(root).as_posix() for p in (root/name).rglob("*") if p.is_file()}
        require(actual == set(recorded), f"Local residue path set changed: {name}")
        for relative, row in recorded.items():
            require(relative.startswith(name + "/"), "Invalid residue root")
            path = confined(root, relative)
            require(path.stat().st_size == row["bytes"] and sha256(path) == row["sha256"], f"Local residue SHA changed: {relative}")
    return sorted(extras)


def check_code(root):
    residue = check_root_dirs(root)
    check_vision_dirs(root)
    if residue:
        print("LOCAL RESIDUE SHA verified; Windows refused rename, originals retained: " + ", ".join(residue))
    count = 0
    for folder in ("ASR", "vision", "project/scripts", "project/tests"):
        for p in (root / folder).rglob("*.py"):
            if SKIP.intersection(p.relative_to(root).parts) or any(x.endswith((".runs", ".gen", ".cache")) for x in p.parts):
                continue
            ast.parse(p.read_text(encoding="utf-8-sig"), filename=str(p))
            count += 1
    manifest = root / "project/board/w6/release_manifest.json"
    for r in json.loads(manifest.read_text(encoding="utf-8"))["artifacts"]:
        require(sha256(manifest.parent / r["file"]) == r["sha256"], f"Release SHA mismatch: {r['file']}")
    xpr = root / "project/fpga/project/glove/glove.xpr"
    source_refs = []
    for node in ET.parse(xpr).findall(".//File"):
        value = node.get("Path", "")
        if value.startswith("$PPRDIR/"):
            source_refs.append(xpr.parent / value.removeprefix("$PPRDIR/"))
        elif value.startswith("$PSRCDIR/") and value.endswith(".bd"):
            source_refs.append(xpr.parent / "glove.srcs" / value.removeprefix("$PSRCDIR/"))
    require(all(p.is_file() for p in source_refs), f"Missing FPGA sources: {[str(p) for p in source_refs if not p.is_file()]}")
    broken = []
    for p in root.rglob("*.md"):
        rel = p.relative_to(root)
        if ".git" in rel.parts or SKIP.intersection(rel.parts) or any(x.endswith((".runs", ".gen", ".cache")) for x in rel.parts):
            continue
        for value in re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)", p.read_text(encoding="utf-8-sig")):
            if value.startswith(("http:", "https:", "#", "/", "mailto:", "codex:")):
                continue
            if not (p.parent / value.split("#")[0]).exists():
                item = (str(rel), value)
                broken.append(item)
    require(not broken, f"Broken current Markdown links: {broken}")
    print(f"PASS root layout; {count} Python sources; release hashes; {len(source_refs)} FPGA sources; current Markdown links")


def check_vision_dirs(root):
    expected={'src','scripts','tests','data','analysis','tools','video'}
    actual={p.name for p in (root/'vision').iterdir() if p.is_dir() and p.name!='__pycache__' and not p.name.startswith('.')}
    require(actual==expected,f'Vision directory layout differs: {sorted(actual)}')
    for package in ('framesource','keypoints','m1','classify','sign_video','webapp'):
        require((root/'vision/src/vision'/package).is_dir(),'Missing canonical vision package: '+package)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code-only", action="store_true", help="Check isolated checkout code; explicitly omit local ignored media")
    args = parser.parse_args()
    check_code(ROOT)
    if args.code_only:
        print("SKIP local media: isolated checkout code-only mode")
    else:
        check_media(ROOT)


if __name__ == "__main__":
    main()
