from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
sys.path.insert(0, str(ROOT / "vision/src"))

from signrec.dataset import load_manifest, uniform_frame_indices  # noqa: E402


def _write_manifest(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=["类别", "样本编号", "part", "输出路径"]
        )
        writer.writeheader()
        writer.writerows(rows)


def test_load_manifest_preserves_chinese_label_and_path(tmp_path: Path) -> None:
    clip = tmp_path / "material" / "你好" / "clip.mp4"
    clip.parent.mkdir(parents=True)
    clip.write_bytes(b"fixture")
    manifest = tmp_path / "material" / "dataset.csv"
    _write_manifest(
        manifest,
        [{"类别": "你好", "样本编号": "1", "part": "p01", "输出路径": "material/你好/clip.mp4"}],
    )

    records = load_manifest(manifest, repo_root=tmp_path)

    assert len(records) == 1
    assert records[0].label == "你好"
    assert records[0].part == "p01"
    assert records[0].sample_id == "1"
    assert records[0].path == clip.resolve()


def test_load_manifest_rejects_missing_video(tmp_path: Path) -> None:
    manifest = tmp_path / "material" / "dataset.csv"
    _write_manifest(
        manifest,
        [{"类别": "你好", "样本编号": "1", "part": "p01", "输出路径": "material/你好/missing.mp4"}],
    )

    with pytest.raises(FileNotFoundError, match="missing video"):
        load_manifest(manifest, repo_root=tmp_path)


def test_load_manifest_rejects_path_traversal(tmp_path: Path) -> None:
    manifest = tmp_path / "material" / "dataset.csv"
    _write_manifest(
        manifest,
        [{"类别": "你好", "样本编号": "1", "part": "p01", "输出路径": "../../outside.mp4"}],
    )

    with pytest.raises(ValueError, match="escapes"):
        load_manifest(manifest, repo_root=tmp_path)


def test_load_manifest_rejects_duplicate_paths(tmp_path: Path) -> None:
    clip = tmp_path / "material" / "你好" / "clip.mp4"
    clip.parent.mkdir(parents=True)
    clip.write_bytes(b"fixture")
    manifest = tmp_path / "material" / "dataset.csv"
    row = {"类别": "你好", "样本编号": "1", "part": "p01", "输出路径": "material/你好/clip.mp4"}
    _write_manifest(manifest, [row, row])

    with pytest.raises(ValueError, match="duplicate"):
        load_manifest(manifest, repo_root=tmp_path)


def test_uniform_frame_indices_include_endpoints() -> None:
    assert uniform_frame_indices(5, 3) == (0, 2, 4)


def test_uniform_frame_indices_repeat_short_clip_for_fixed_length() -> None:
    assert uniform_frame_indices(2, 4) == (0, 0, 1, 1)


def test_sample_video_frames_keeps_source_resolution() -> None:
    sample = ROOT / "vision/data" / "legacy" / "material" / "你好" / "01_你好_示范01.mp4"
    if not sample.is_file():
        pytest.skip("bundled sample clip is unavailable")

    from signrec.dataset import sample_video_frames

    frames = sample_video_frames(sample, sample_count=5)

    assert frames.shape == (5, 250, 200, 3)
    assert frames.dtype == np.uint8


def test_uniform_frame_indices_reject_invalid_sizes() -> None:
    with pytest.raises(ValueError, match="total_frames"):
        uniform_frame_indices(0, 4)
    with pytest.raises(ValueError, match="sample_count"):
        uniform_frame_indices(4, 0)
