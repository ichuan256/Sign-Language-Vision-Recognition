from __future__ import annotations

import csv
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from rebuild_full_frame_dataset import build_plan, frame_window, run_rebuild  # noqa: E402


def _write_manifest(path: Path, row: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "类别",
        "样本编号",
        "part",
        "原片起始秒",
        "原片结束秒",
        "输出路径",
        "原片路径",
        "裁剪",
        "分辨率",
        "帧率",
        "音轨",
        "完整解码",
        "帧数",
        "SHA256",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerow(row)


def _manifest_row(source: str = "video/source.mp4") -> dict[str, str]:
    return {
        "类别": "你好",
        "样本编号": "1",
        "part": "p01",
        "原片起始秒": "0.1",
        "原片结束秒": "0.3",
        "输出路径": "material/你好/clip.mp4",
        "原片路径": source,
        "裁剪": "x=0,y=22,w=200,h=250",
        "分辨率": "200x250",
        "帧率": "20",
        "音轨": "0",
        "完整解码": "passed",
        "帧数": "4",
        "SHA256": "old",
    }


def test_frame_window_uses_half_open_source_interval() -> None:
    assert frame_window(0.1, 0.3, 20.0, 20) == (2, 6)


def test_build_plan_targets_separate_full_frame_root(tmp_path: Path) -> None:
    manifest = tmp_path / "material" / "manifest.csv"
    _write_manifest(manifest, _manifest_row())

    plans, output_root, _ = build_plan(manifest, tmp_path)

    assert len(plans) == 1
    assert output_root == (tmp_path / "data/exports/full_frame_dataset").resolve()
    assert plans[0].output_path == (tmp_path / "data/exports/full_frame_dataset" / "你好" / "clip.mp4").resolve()
    assert plans[0].source_path == (tmp_path / "video" / "source.mp4").resolve()


def test_build_plan_rejects_source_path_traversal(tmp_path: Path) -> None:
    manifest = tmp_path / "material" / "manifest.csv"
    _write_manifest(manifest, _manifest_row(source="../../outside.mp4"))

    with pytest.raises(ValueError, match="escapes"):
        build_plan(manifest, tmp_path)


def test_dry_run_reports_missing_sources_without_creating_output(tmp_path: Path) -> None:
    manifest = tmp_path / "material" / "manifest.csv"
    _write_manifest(manifest, _manifest_row())
    plans, output_root, fields = build_plan(manifest, tmp_path)

    result = run_rebuild(plans, tmp_path, output_root, fields, apply=False)

    assert result["clips"] == 1
    assert result["missing_sources"] == 1
    assert not output_root.exists()


def test_apply_recuts_without_changing_source_frame_dimensions(tmp_path: Path) -> None:
    source = tmp_path / "video" / "source.mp4"
    source.parent.mkdir(parents=True)
    writer = cv2.VideoWriter(
        str(source), cv2.VideoWriter_fourcc(*"mp4v"), 20.0, (64, 48)
    )
    if not writer.isOpened():
        pytest.skip("mp4v encoder is not available")
    for index in range(10):
        frame = np.full((48, 64, 3), index * 10, dtype=np.uint8)
        writer.write(frame)
    writer.release()

    manifest = tmp_path / "material" / "manifest.csv"
    _write_manifest(manifest, _manifest_row())
    plans, output_root, fields = build_plan(manifest, tmp_path)

    result = run_rebuild(plans, tmp_path, output_root, fields, apply=True)

    output = output_root / "你好" / "clip.mp4"
    capture = cv2.VideoCapture(str(output))
    ok, frame = capture.read()
    capture.release()
    assert result["clips"] == 1
    assert ok
    assert frame.shape[:2] == (48, 64)
    rebuilt = list(csv.DictReader((output_root / "dataset_manifest_fullframe.csv").open(encoding="utf-8-sig")))
    assert rebuilt[0]["裁剪"] == "full_frame"
    assert rebuilt[0]["分辨率"] == "64x48"
