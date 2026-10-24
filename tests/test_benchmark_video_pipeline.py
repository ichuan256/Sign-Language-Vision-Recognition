from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from benchmark_video_pipeline import build_report  # noqa: E402


def test_benchmark_report_carries_host_fps_and_exclusions() -> None:
    report = build_report(
        video=Path("clip.mp4"),
        video_info={"width": 640, "height": 480, "frames": 20, "source_fps": 25.0},
        load_seconds=1.0,
        wall_seconds=2.0,
        event_counts=Counter({"frame": 10, "progress": 4}),
        result={"frames_processed": 20, "processing_fps": 10.0, "predictions": []},
        settings={"detection_stride": 2, "pose_stride": 4},
    )

    assert report["timing"]["pipeline_fps"] == 10.0
    assert report["input"]["width"] == 640
    assert report["settings"]["pose_stride"] == 4
    assert "Excludes camera capture/DVP" in report["scope"]
