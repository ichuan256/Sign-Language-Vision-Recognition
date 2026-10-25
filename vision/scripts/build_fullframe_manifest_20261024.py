"""Export an explicitly selected, SHA-verified available subset of a manifest.

No directory scan: archive, inbox and caches cannot become samples.
Output CSV and validation JSON must both be new paths.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
FIELDS = ["类别", "输出路径", "样本编号", "part"]


def confined(root: Path, value: str | Path) -> Path:
    text = str(value).replace(chr(92), "/")
    if ".." in PurePosixPath(text).parts:
        raise ValueError(f"Path traversal is not allowed: {value}")
    if PureWindowsPath(text).drive and not Path(text).is_absolute():
        raise ValueError(f"Foreign absolute path is not allowed: {value}")
    path = (root / text).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"Path escapes repository root: {value}")
    return path


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not set(FIELDS).issubset(reader.fieldnames or []):
            raise ValueError(f"Manifest must contain {FIELDS}: {path}")
        return list(reader)


def validate_layout(root, path, row):
    parts = path.relative_to(root).parts
    if len(parts) < 7 or parts[:3] != ("vision", "video", "done"):
        raise ValueError(f"Expected vision/video/done/<contributor>/<batch>/[subfolders/]<label>/<file>: {row['输出路径']}")
    if path.suffix.lower() != ".mp4":
        raise ValueError(f"Expected an MP4 sample: {path}")
    if (row["part"], row["类别"], row["样本编号"]) != (parts[3], parts[-2], path.stem):
        raise ValueError(f"Manifest labels/part/sample_id disagree with path: {row['输出路径']}")


def build_manifest(repo_root, source_manifest, audit_path, output, *, allow_missing=False,
                   skip_sha_mismatch=False, report_path=None):
    root = Path(repo_root).resolve()
    source = confined(root, source_manifest)
    audit_file = confined(root, audit_path)
    target = confined(root, output)
    report = confined(root, report_path or target.with_suffix(target.suffix + ".validation.json"))
    if target == report or target in (source, audit_file) or report in (source, audit_file):
        raise ValueError("Output/report must be separate from inputs and each other")
    for path in (target, report):
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite: {path}")
    rows = read_rows(source)
    audit = json.loads(audit_file.read_text(encoding="utf-8-sig"))
    records = {str(r["path"]).replace(chr(92), "/"): r for r in audit.get("records", [])}
    declared = audit.get("full_manifest", {}).get("sha256")
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    if declared and declared != source_sha:
        raise ValueError("Audit does not describe this exact source manifest (SHA mismatch)")
    accepted, checks, fatal = [], [], []
    for index, row in enumerate(rows, 1):
        entry = {"row": index, "path": row["输出路径"], "sample_id": row["样本编号"]}
        try:
            path = confined(root, row["输出路径"])
            relative = path.relative_to(root).as_posix()
            prior = records.get(relative)
            if not prior or not prior.get("sha256"):
                raise ValueError("No expected SHA in supplied audit")
            if any(prior.get(key) != row[field] for key, field in [("label", "类别"), ("sample_id", "样本编号"), ("contributor", "part")]):
                raise ValueError("Source label/sample_id/contributor differs from audited record")
            entry["expected_sha256"] = prior["sha256"].lower()
            # Missing historical layouts are reported, never repaired or included.
            if not path.is_file():
                entry["status"] = "missing"
                if not allow_missing:
                    fatal.append(entry)
            else:
                validate_layout(root, path, row)
                with path.open("rb") as stream:
                    actual = hashlib.file_digest(stream, "sha256").hexdigest()
                entry["actual_sha256"] = actual
                if actual != entry["expected_sha256"]:
                    entry["status"] = "sha_mismatch"
                    if not skip_sha_mismatch:
                        fatal.append(entry)
                else:
                    entry["status"] = "included"
                    accepted.append({key: row[key] for key in FIELDS})
        except (ValueError, OSError) as error:
            entry.update(status="invalid", error=str(error))
            fatal.append(entry)
        checks.append(entry)
    result = {"source_manifest": source.relative_to(root).as_posix(), "source_sha256": source_sha,
              "audit": audit_file.relative_to(root).as_posix(), "output": target.relative_to(root).as_posix(),
              "input_rows": len(rows), "included_rows": len(accepted), "counts": dict(Counter(r["status"] for r in checks)),
              "allow_missing": allow_missing, "skip_sha_mismatch": skip_sha_mismatch,
              "success": not fatal, "records": checks}
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write(chr(10))
    if fatal:
        raise ValueError(f"{len(fatal)} blocking input errors; CSV not written. See {report}")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(accepted)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--source-manifest", type=Path, required=True, help="Explicit source selection; never scans done/")
    parser.add_argument("--audit", type=Path, required=True, help="JSON records with path/sha256/label/sample_id/contributor")
    parser.add_argument("--output", type=Path, required=True, help="New CSV path inside repository")
    parser.add_argument("--report", type=Path, help="New validation JSON; defaults to <output>.validation.json")
    parser.add_argument("--allow-missing", action="store_true", help="Skip and report missing rows")
    parser.add_argument("--skip-sha-mismatch", action="store_true", help="Explicitly exclude and report SHA mismatches; default fails")
    args = parser.parse_args(argv)
    try:
        result = build_manifest(args.repo_root, args.source_manifest, args.audit, args.output,
            allow_missing=args.allow_missing, skip_sha_mismatch=args.skip_sha_mismatch, report_path=args.report)
    except (ValueError, OSError) as error:
        parser.exit(1, f"{error}" + chr(10))
    print(json.dumps({k:v for k,v in result.items() if k != "records"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
