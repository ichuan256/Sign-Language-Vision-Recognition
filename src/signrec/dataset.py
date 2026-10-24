"""Manifest-driven loading and uniform sampling for sign-language clips."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
import cv2
import numpy as np


@dataclass(frozen=True)
class VideoRecord:
    """A labeled, already-segmented video referenced by the manifest."""

    label: str
    path: Path
    part: str = ""
    sample_id: str = ""


def load_manifest(
    manifest_path: str | Path,
    repo_root: str | Path | None = None,
    *,
    check_files: bool = True,
) -> list[VideoRecord]:
    """Read the CSV manifest and resolve its relative paths from repo_root.

    By default, the repository root is the parent of the manifest's directory
    (a conventional one-level manifest layout). For nested manifests such as
    ``data/legacy/material/``, pass the repository root explicitly. No path-prefix
    remapping or image cropping/resizing is performed.
    """
    manifest = Path(manifest_path).expanduser().resolve()
    if not manifest.is_file():
        raise FileNotFoundError(f"manifest not found: {manifest}")
    root = (
        Path(repo_root).expanduser().resolve()
        if repo_root is not None
        else manifest.parent.parent.resolve()
    )

    records: list[VideoRecord] = []
    seen_paths: set[Path] = set()
    with manifest.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"类别", "输出路径"}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError("manifest requires columns 类别 and 输出路径")

        for line_number, row in enumerate(reader, start=2):
            label = (row.get("类别") or "").strip()
            raw_path = (row.get("输出路径") or "").strip()
            if not label or not raw_path:
                raise ValueError(f"manifest row {line_number} has an empty label or path")

            normalized = raw_path.replace("\\", "/")
            if Path(normalized).is_absolute() or PureWindowsPath(normalized).is_absolute():
                raise ValueError(f"manifest row {line_number} must use a relative path")
            path = (root / Path(normalized)).resolve()
            try:
                path.relative_to(root)
            except ValueError as exc:
                raise ValueError(f"manifest row {line_number} escapes the repository root") from exc

            if path in seen_paths:
                raise ValueError(f"duplicate manifest path at row {line_number}: {raw_path}")
            seen_paths.add(path)
            if check_files and not path.is_file():
                raise FileNotFoundError(f"manifest row {line_number} points to missing video: {path}")

            records.append(
                VideoRecord(
                    label=label,
                    path=path,
                    part=(row.get("part") or "").strip(),
                    sample_id=(row.get("样本编号") or "").strip(),
                )
            )
    return records


def uniform_frame_indices(total_frames: int, sample_count: int) -> tuple[int, ...]:
    """Return deterministic, endpoint-inclusive frame indices.

    Repeated indices are allowed when a clip is shorter than sample_count so
    downstream models can receive a fixed temporal length.
    """
    if total_frames <= 0:
        raise ValueError("total_frames must be positive")
    if sample_count <= 0:
        raise ValueError("sample_count must be positive")
    if sample_count == 1:
        return (total_frames // 2,)
    return tuple(
        int(round(index * (total_frames - 1) / (sample_count - 1)))
        for index in range(sample_count)
    )


def sample_video_frames(video_path: str | Path, sample_count: int = 16) -> np.ndarray:
    """Uniformly sample a video without cropping or resizing its frames.

    Returns a uint8 BGR array with shape ``(T, H, W, 3)``. Frames remain at
    their decoded source resolution; model-specific letterboxing belongs in
    the detector/recognizer, not in this data loader.
    """
    path = Path(video_path).expanduser()
    if sample_count <= 0:
        raise ValueError("sample_count must be positive")
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise RuntimeError(f"cannot open video: {path}")

    try:
        total_frames = int(round(capture.get(cv2.CAP_PROP_FRAME_COUNT)))
        if total_frames <= 0:
            raise RuntimeError(f"cannot determine frame count for video: {path}")
        indices = uniform_frame_indices(total_frames, sample_count)
        slots: dict[int, list[int]] = {}
        for output_index, frame_index in enumerate(indices):
            slots.setdefault(frame_index, []).append(output_index)

        selected: list[np.ndarray | None] = [None] * sample_count
        frame_index = 0
        while frame_index < total_frames:
            ok, frame = capture.read()
            if not ok:
                break
            for output_index in slots.get(frame_index, ()):
                selected[output_index] = frame.copy()
            frame_index += 1

        missing = [index for index, frame in enumerate(selected) if frame is None]
        if missing:
            raise RuntimeError(
                f"video ended before requested samples were decoded ({len(missing)} missing): {path}"
            )
        shapes = {frame.shape for frame in selected if frame is not None}
        if len(shapes) != 1:
            raise ValueError(f"video changes frame dimensions: {path}")
        return np.stack(selected, axis=0).astype(np.uint8, copy=False)
    finally:
        capture.release()
