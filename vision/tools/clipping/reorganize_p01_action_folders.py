"""Reorganize the reviewed P01 clip package into one folder per action context.

The script stages and hash-checks a complete replacement before swapping it
into place. The previous package is retained under _inspect/ for recovery.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
PACKAGE = ROOT / "vision/data" / "exports" / "material_fullframe_20261021" / "第一课_动作周期_已核对_20261021"
INSPECT = ROOT / "project/_tmp" / "inspect"
MANIFEST_NAME = "第一课动作周期剪辑清单_20261021.csv"
VALIDATION_NAME = "validation_P01_actions_20261021.json"
README_NAME = "README.md"


def safe_folder(value: str) -> str:
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).strip(" .")
    return value[:80] or "未命名"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_manifest(expected_rows: int | None = 31) -> tuple[list[dict[str, str]], list[str]]:
    with (PACKAGE / MANIFEST_NAME).open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = list(reader.fieldnames or [])
        rows = list(reader)
    if (expected_rows is not None and len(rows) != expected_rows) or not fields:
        raise ValueError(f"Expected {expected_rows} manifest rows with headers, found {len(rows)}")
    return rows, fields


def make_readme(rows: list[dict[str, str]], excluded_ids: list[str]) -> str:
    contexts = sorted({row["词句上下文"] for row in rows})
    solo = sum("单人" in row["目标人物"] for row in rows)
    dialogue = len(rows) - solo
    folders = Counter(row["词句上下文"] for row in rows)
    folder_lines = "\n".join(f"- `{name}/`：{count} 段" for name, count in folders.items())
    return f"""# 第一课已核对动作周期剪辑（2026-10-21）

来源清单：`tools/clipping/中国手语教程_P01对话_已核对动作边界_20261021.csv`  
原片：`{Path(rows[0]['原片路径']).as_posix()}`

- 共 {len(rows)} 段：双人对话 {dialogue} 段，单人示范 {solo} 段。
- 依照旧素材目录方式，按清单 `词句上下文` 建立 {len(contexts)} 个动作文件夹；同一上下文的各次候选、重复周期均收入同一文件夹。
- 本包只整理当前存在的 {len(rows)} 个视频；上次清单中缺少视频文件的 {len(excluded_ids)} 条不纳入本包：{', '.join(excluded_ids)}。
- 文件名保留唯一 `动作编号`，人物、候选编号、周期序号和复核细节以独立清单为准。
- 每段严格按清单的 `起始帧_含` 至 `结束帧_不含` 导出；帧数等于结束帧减起始帧。
- 保留原片全画幅 1920×1080、25 fps，不做画面裁切；输出为 H.264、yuv420p、无音轨，CRF 18。
- 若原清单的动作周期在原片时间上相邻或重叠，仍按各自经核对的帧边界原样保留。
- 原素材库原有 233 条视频及其主清单未改动；本包使用独立清单。

## 动作文件夹

{folder_lines}

清单：`{MANIFEST_NAME}`  
验证汇总：`{VALIDATION_NAME}`
"""


def main() -> None:
    global ROOT, PACKAGE, INSPECT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--package", type=Path)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    ROOT = args.repo_root.resolve()
    PACKAGE = args.package or ROOT / "vision/data/exports/material_fullframe_20261021/第一课_动作周期_已核对_20261021"
    INSPECT = ROOT / "project/_tmp/inspect"
    if args.preflight:
        print(json.dumps({"package": str(PACKAGE), "exists": PACKAGE.is_dir(), "inspection_root": str(INSPECT)}, ensure_ascii=False))
        return
    if not PACKAGE.is_dir():
        raise FileNotFoundError(PACKAGE)
    INSPECT.mkdir(parents=True, exist_ok=True)
    manifest_rows, fields = read_manifest()
    rows: list[dict[str, str]] = []
    excluded_ids: list[str] = []
    old_paths: set[Path] = set()
    seen_ids: set[str] = set()

    for row in manifest_rows:
        action_id = row["动作编号"]
        if action_id in seen_ids:
            raise ValueError(f"Duplicate action id: {action_id}")
        seen_ids.add(action_id)
        old = (PACKAGE / Path(row["输出相对路径"])).resolve()
        if not old.is_relative_to(PACKAGE.resolve()):
            raise ValueError(f"Output path escapes the package: {old}")
        if not old.exists():
            excluded_ids.append(action_id)
            continue
        if not old.is_file():
            raise ValueError(f"Output path is not a file: {old}")
        if sha256(old) != row["SHA256"]:
            raise ValueError(f"Existing clip hash differs from manifest: {old}")
        old_paths.add(old)
        rows.append(row)

    if len(rows) != 27 or len(excluded_ids) != 4:
        raise ValueError(
            f"Expected the user's current 27 clips and 4 missing rows; found {len(rows)} and {len(excluded_ids)}"
        )

    actual_clips = {path.resolve() for path in PACKAGE.rglob("*.mp4") if path.is_file()}
    if actual_clips != old_paths:
        raise ValueError("Current package MP4 inventory differs from its manifest")

    stage = Path(tempfile.mkdtemp(prefix="p01_action_folders_20261021_", dir=INSPECT))
    backup = INSPECT / f"p01_package_before_action_folders_{datetime.now():%Y%m%d_%H%M%S}"
    try:
        staged_rows: list[dict[str, str]] = []
        for row in rows:
            old = PACKAGE / Path(row["输出相对路径"])
            folder = safe_folder(row["词句上下文"])
            new_relative = Path(folder) / old.name
            new = stage / new_relative
            new.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(old, new)
            if sha256(new) != row["SHA256"]:
                raise ValueError(f"Hash mismatch while staging: {new}")
            updated = dict(row)
            updated["输出相对路径"] = new_relative.as_posix()
            staged_rows.append(updated)

        with (stage / MANIFEST_NAME).open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(staged_rows)

        (stage / README_NAME).write_text(make_readme(rows, excluded_ids), encoding="utf-8")
        validation_path = PACKAGE / VALIDATION_NAME
        validation = json.loads(validation_path.read_text(encoding="utf-8"))
        validation["output_directory"] = PACKAGE.relative_to(ROOT).as_posix()
        validation["output_clips"] = len(rows)
        validation["source_manifest_rows_before_filter"] = len(manifest_rows)
        validation["excluded_missing_clip_action_ids"] = excluded_ids
        validation["counts_by_folder"] = dict(Counter(row["词句上下文"] for row in rows))
        validation["counts_by_target_person"] = dict(Counter(row["目标人物"] for row in rows))
        validation["folder_layout"] = "one folder per exact 词句上下文; action ids retained in filenames"
        validation["checks"]["manifest_rows"] = len(rows)
        validation["checks"]["staging_file_count"] = len(
            [path for path in stage.rglob("*.mp4") if path.is_file()]
        )
        validation["checks"]["staging_hash_mismatches"] = 0
        (stage / VALIDATION_NAME).write_text(
            json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        if len(list(stage.rglob("*.mp4"))) != len(rows):
            raise ValueError(f"Staged MP4 count is not {len(rows)}")
        if len([path for path in stage.iterdir() if path.is_dir()]) != len(
            {row["词句上下文"] for row in rows}
        ):
            raise ValueError("Staged action folder count is unexpected")

        if backup.exists():
            raise FileExistsError(backup)
        shutil.copytree(PACKAGE, backup)

        # Add and verify the new action-folder copies first, so originals stay
        # available if any copy, manifest write, or validation fails.
        new_paths: set[Path] = set()
        for row in staged_rows:
            source = stage / Path(row["输出相对路径"])
            target = PACKAGE / Path(row["输出相对路径"])
            if target.exists():
                raise FileExistsError(target)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            if sha256(target) != row["SHA256"]:
                raise ValueError(f"Final copy hash mismatch: {target}")
            new_paths.add(target.resolve())

        # Replace sidecar files only after every new video has been copied and
        # verified; use temporary siblings so readers never see partial text.
        manifest_tmp = PACKAGE / (MANIFEST_NAME + ".tmp")
        with manifest_tmp.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(staged_rows)
        os.replace(manifest_tmp, PACKAGE / MANIFEST_NAME)

        readme_tmp = PACKAGE / (README_NAME + ".tmp")
        readme_tmp.write_text(make_readme(rows, excluded_ids), encoding="utf-8")
        os.replace(readme_tmp, PACKAGE / README_NAME)

        validation_tmp = PACKAGE / (VALIDATION_NAME + ".tmp")
        validation_tmp.write_text(json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(validation_tmp, PACKAGE / VALIDATION_NAME)

        final_rows, _ = read_manifest(expected_rows=len(rows))
        for row in final_rows:
            path = (PACKAGE / Path(row["输出相对路径"])).resolve()
            if not path.is_file() or sha256(path) != row["SHA256"]:
                raise RuntimeError(f"Post-copy verification failed: {path}")

        # Remove only the exact old, manifest-verified files after the new
        # package and its index have been fully verified.
        for old in sorted(old_paths):
            old.unlink()
        for old_folder in (PACKAGE / "双人对话", PACKAGE / "单人示范"):
            if old_folder.is_dir() and not any(old_folder.iterdir()):
                old_folder.rmdir()

        final_clips = {path.resolve() for path in PACKAGE.rglob("*.mp4") if path.is_file()}
        if final_clips != new_paths:
            raise RuntimeError(
                f"Post-cleanup MP4 inventory mismatch: expected {len(new_paths)}, found {len(final_clips)}"
            )
        for row in final_rows:
            path = (PACKAGE / Path(row["输出相对路径"])).resolve()
            if not path.is_file() or sha256(path) != row["SHA256"]:
                raise RuntimeError(f"Post-cleanup verification failed: {path}")

        stage_safe = stage.resolve().is_relative_to(INSPECT.resolve())
        if not stage_safe:
            raise RuntimeError(f"Unexpected staging location; leaving it in place: {stage}")
        shutil.rmtree(stage)

        print(f"Package: {PACKAGE}")
        print(f"Action folders: {len({row['词句上下文'] for row in rows})}")
        print(f"Clips preserved and hash verified: {len(final_clips)}")
        print(f"Previous layout backup: {backup}")
    except Exception:
        if stage.exists():
            print(f"Staging preserved for diagnosis: {stage}")
        raise


if __name__ == "__main__":
    main()
