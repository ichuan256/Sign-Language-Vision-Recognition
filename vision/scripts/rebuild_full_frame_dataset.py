#!/usr/bin/env python3
"""Plan or rebuild uncropped clips from the original source videos."""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath

import cv2

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
DEFAULT_MANIFEST = ROOT / "vision/data" / "legacy" / "material" / "dataset_manifest_20261020.csv"
DEFAULT_OUTPUT_ROOT = Path("vision/data/exports/full_frame_dataset")


@dataclass(frozen=True)
class PlannedClip:
    row_number: int
    row: dict[str, str]
    source_path: Path
    output_path: Path
    start_seconds: float
    end_seconds: float


def _relative_path(root: Path, raw_path: str, field: str, row_number: int) -> Path:
    normalized = raw_path.strip().replace("\\", "/")
    if not normalized or Path(normalized).is_absolute() or PureWindowsPath(normalized).is_absolute():
        raise ValueError(f"row {row_number}: {field} must be a non-empty relative path")
    resolved = (root / Path(normalized)).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"row {row_number}: {field} escapes the repository root") from exc
    return resolved


def _output_relative_path(raw_path: str, row_number: int) -> Path:
    normalized = raw_path.strip().replace("\\", "/")
    pure = PurePosixPath(normalized)
    if pure.is_absolute() or any(part in {"..", "."} for part in pure.parts):
        raise ValueError(f"row {row_number}: invalid output path")
    parts = list(pure.parts)
    if [part.casefold() for part in parts[:4]] == ["vision", "data", "legacy", "material"]:
        parts = parts[4:]
    elif [part.casefold() for part in parts[:3]] == ["data", "legacy", "material"]:
        parts = parts[3:]
    elif parts and parts[0].casefold() == "material":
        parts = parts[1:]
    if not parts:
        raise ValueError(f"row {row_number}: output path has no filename")
    return Path(*parts)


def build_plan(
    manifest_path: str | Path = DEFAULT_MANIFEST,
    repo_root: str | Path = ROOT,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
) -> tuple[list[PlannedClip], Path, list[str]]:
    manifest = Path(manifest_path).expanduser().resolve()
    root = Path(repo_root).expanduser().resolve()
    destination_root_arg = Path(output_root)
    destination_root = (
        destination_root_arg if destination_root_arg.is_absolute() else root / destination_root_arg
    ).resolve()
    try:
        destination_root.relative_to(root)
    except ValueError as exc:
        raise ValueError("output root must remain inside the repository") from exc
    if destination_root == root:
        raise ValueError("output root must be a dedicated subdirectory")
    if not manifest.is_file():
        raise FileNotFoundError(f"manifest not found: {manifest}")

    plans: list[PlannedClip] = []
    seen_outputs: set[Path] = set()
    with manifest.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"类别", "输出路径", "原片路径", "原片起始秒", "原片结束秒"}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError("manifest is missing source, label, output or time columns")
        for row_number, row in enumerate(reader, start=2):
            label = (row.get("类别") or "").strip()
            if not label:
                raise ValueError(f"row {row_number}: empty category")
            source_path = _relative_path(root, row.get("原片路径", ""), "原片路径", row_number)
            output_relative = _output_relative_path(row.get("输出路径", ""), row_number)
            output_path = (destination_root / output_relative).resolve()
            try:
                output_path.relative_to(destination_root)
            except ValueError as exc:
                raise ValueError(f"row {row_number}: output escapes output root") from exc
            if output_path in seen_outputs:
                raise ValueError(f"row {row_number}: duplicate output path {output_path}")
            seen_outputs.add(output_path)
            try:
                start_seconds = float(row["原片起始秒"])
                end_seconds = float(row["原片结束秒"])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"row {row_number}: invalid source interval") from exc
            if not math.isfinite(start_seconds) or not math.isfinite(end_seconds):
                raise ValueError(f"row {row_number}: source times must be finite")
            if start_seconds < 0 or end_seconds <= start_seconds:
                raise ValueError(f"row {row_number}: source interval must have end > start >= 0")
            plans.append(
                PlannedClip(
                    row_number=row_number,
                    row=dict(row),
                    source_path=source_path,
                    output_path=output_path,
                    start_seconds=start_seconds,
                    end_seconds=end_seconds,
                )
            )
    return plans, destination_root, reader.fieldnames or []


def frame_window(
    start_seconds: float, end_seconds: float, fps: float, total_frames: int
) -> tuple[int, int]:
    """Convert a half-open time interval to a clamped frame interval."""
    if not math.isfinite(fps) or fps <= 0:
        raise ValueError("fps must be finite and positive")
    if total_frames <= 0:
        raise ValueError("total_frames must be positive")
    if start_seconds < 0 or end_seconds <= start_seconds:
        raise ValueError("interval must have end > start >= 0")
    first = max(0, min(total_frames, math.floor(start_seconds * fps)))
    stop = max(first, min(total_frames, math.ceil(end_seconds * fps)))
    if first >= total_frames or stop <= first:
        raise ValueError("source interval does not include any video frames")
    return first, stop


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _rebuild_clip(
    plan: PlannedClip, staging_path: Path, repo_root: Path
) -> dict[str, str]:
    capture = cv2.VideoCapture(str(plan.source_path))
    if not capture.isOpened():
        raise RuntimeError(f"cannot open source video: {plan.source_path}")
    writer = None
    written = 0
    try:
        fps = float(capture.get(cv2.CAP_PROP_FPS))
        total_frames = int(round(capture.get(cv2.CAP_PROP_FRAME_COUNT)))
        width = int(round(capture.get(cv2.CAP_PROP_FRAME_WIDTH)))
        height = int(round(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        start_frame, stop_frame = frame_window(
            plan.start_seconds, plan.end_seconds, fps, total_frames
        )
        if width <= 0 or height <= 0:
            raise RuntimeError(f"invalid source frame dimensions: {plan.source_path}")
        staging_path.parent.mkdir(parents=True, exist_ok=True)
        if not capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame):
            raise RuntimeError(f"cannot seek source video: {plan.source_path}")
        writer = cv2.VideoWriter(
            str(staging_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
        )
        if not writer.isOpened():
            raise RuntimeError(f"cannot create output video: {staging_path}")
        for _ in range(start_frame, stop_frame):
            ok, frame = capture.read()
            if not ok:
                break
            if frame.shape[:2] != (height, width):
                raise RuntimeError(f"source video changes resolution: {plan.source_path}")
            writer.write(frame)
            written += 1
    finally:
        capture.release()
        if writer is not None:
            writer.release()
    expected = stop_frame - start_frame
    if written != expected:
        raise RuntimeError(
            f"row {plan.row_number}: expected {expected} frames, wrote {written} from {plan.source_path}"
        )

    verify = cv2.VideoCapture(str(staging_path))
    if not verify.isOpened():
        raise RuntimeError(f"cannot reopen generated clip: {staging_path}")
    decoded = 0
    try:
        while True:
            ok, _ = verify.read()
            if not ok:
                break
            decoded += 1
    finally:
        verify.release()
    if decoded != written:
        raise RuntimeError(
            f"generated clip decode count mismatch for {staging_path}: {decoded} != {written}"
        )

    updated = dict(plan.row)
    updated["输出路径"] = plan.output_path.relative_to(repo_root).as_posix()
    updated["裁剪"] = "full_frame"
    updated["分辨率"] = f"{width}x{height}"
    updated["帧率"] = f"{fps:g}"
    updated["音轨"] = "0"
    updated["完整解码"] = "passed"
    updated["帧数"] = str(decoded)
    updated["SHA256"] = _sha256(staging_path)
    return updated


def run_rebuild(
    plans: list[PlannedClip],
    repo_root: Path,
    output_root: Path,
    fieldnames: list[str],
    *,
    apply: bool = False,
) -> dict[str, int]:
    missing_sources = sorted({plan.source_path for plan in plans if not plan.source_path.is_file()})
    existing_outputs = [plan.output_path for plan in plans if plan.output_path.exists()]
    staging_root = output_root.with_name(output_root.name + ".staging")
    if not apply:
        return {
            "clips": len(plans),
            "sources": len({plan.source_path for plan in plans}),
            "available_sources": len({plan.source_path for plan in plans if plan.source_path.is_file()}),
            "missing_sources": len(missing_sources),
            "existing_outputs": len(existing_outputs),
        }
    if missing_sources:
        preview = ", ".join(str(path) for path in missing_sources[:3])
        raise FileNotFoundError(
            f"{len(missing_sources)} source videos are missing (e.g. {preview}); no output was created"
        )
    if existing_outputs or output_root.exists() or staging_root.exists():
        raise FileExistsError(
            f"refusing to overwrite existing dataset/output directory: {output_root}"
        )

    staging_root.mkdir(parents=True)
    updated_rows: list[dict[str, str]] = []
    try:
        for plan in plans:
            relative_output = plan.output_path.relative_to(output_root)
            staging_path = staging_root / relative_output
            updated_rows.append(_rebuild_clip(plan, staging_path, repo_root))
        manifest_output = staging_root / "dataset_manifest_fullframe.csv"
        with manifest_output.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(updated_rows)
        staging_root.replace(output_root)
    except Exception:
        # Preserve the staging tree for inspection; never overwrite source data.
        raise
    return {
        "clips": len(updated_rows),
        "sources": len({plan.source_path for plan in plans}),
        "available_sources": len({plan.source_path for plan in plans}),
        "missing_sources": 0,
        "existing_outputs": 0,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--apply", action="store_true", help="write new uncropped clips; default is dry-run")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.repo_root.expanduser().resolve()
    plans, output_root, fieldnames = build_plan(
        args.manifest, root, args.output_root
    )
    summary = run_rebuild(
        plans, root, output_root, fieldnames, apply=args.apply
    )
    print(
        f"clips={summary['clips']} sources={summary['sources']} "
        f"available_sources={summary['available_sources']} "
        f"missing_sources={summary['missing_sources']} "
        f"existing_outputs={summary['existing_outputs']} "
        f"mode={'apply' if args.apply else 'dry-run'} output={output_root}"
    )
    if not args.apply:
        print("Dry-run only; pass --apply after all original videos are present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
