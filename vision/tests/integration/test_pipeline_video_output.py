from __future__ import annotations

import sys
import threading
from pathlib import Path

import numpy as np

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
sys.path.insert(0, str(ROOT))

import vision.webapp.pipeline as pipeline_module  # noqa: E402
from vision.webapp.pipeline import SignRecognitionPipeline  # noqa: E402


class FakeCapture:
    def __init__(self, frames: list[np.ndarray], total_frames: int) -> None:
        self.frames = list(frames)
        self.total_frames = total_frames
        self.released = False

    def isOpened(self) -> bool:
        return True

    def get(self, property_id: int) -> float:
        if property_id == pipeline_module.cv2.CAP_PROP_FRAME_COUNT:
            return float(self.total_frames)
        if property_id == pipeline_module.cv2.CAP_PROP_FPS:
            return 20.0
        return 0.0

    def read(self) -> tuple[bool, np.ndarray | None]:
        if not self.frames:
            return False, None
        return True, self.frames.pop(0)

    def release(self) -> None:
        self.released = True


class FakeWriter:
    def __init__(self, output_path: Path) -> None:
        self.output_path = output_path
        self.frames: list[np.ndarray] = []
        self.released = False

    def isOpened(self) -> bool:
        return True

    def write(self, frame: np.ndarray) -> None:
        self.frames.append(frame.copy())

    def release(self) -> None:
        self.released = True
        self.output_path.write_bytes(b"fake-h264-mp4")


class FakeDetector:
    def detect(self, _frame: np.ndarray) -> list[object]:
        return []


class FakeEmbedder:
    def embed_frame(self, _frame: np.ndarray) -> np.ndarray:
        return np.asarray([1.0, 0.0], dtype=np.float32)


class FakeRecognizer:
    def predict(self, _query: np.ndarray, top_k: int) -> list[object]:
        assert top_k == 5
        return []


def test_pipeline_writes_every_annotated_frame_to_output_video(
    tmp_path: Path, monkeypatch
) -> None:
    frames = [np.full((48, 64, 3), value, dtype=np.uint8) for value in (20, 80, 140)]
    source_capture = FakeCapture(frames, total_frames=len(frames))
    validation_capture = FakeCapture([frames[0]], total_frames=1)
    captures = [source_capture, validation_capture]
    writers: list[FakeWriter] = []

    def open_capture(_path: str) -> FakeCapture:
        return captures.pop(0)

    def open_writer(path: str, _backend: int, _codec: int, _fps: float, _size: tuple[int, int]) -> FakeWriter:
        writer = FakeWriter(Path(path))
        writers.append(writer)
        return writer

    monkeypatch.setattr(pipeline_module.cv2, "VideoCapture", open_capture)
    monkeypatch.setattr(pipeline_module.cv2, "VideoWriter", open_writer)

    pipeline = SignRecognitionPipeline.__new__(SignRecognitionPipeline)
    pipeline.detector = FakeDetector()
    pipeline.pose = object()
    pipeline.embedder = FakeEmbedder()
    pipeline.recognizer = FakeRecognizer()
    pipeline.sample_count = 2
    pipeline.detection_stride = 2
    pipeline.pose_stride = 4
    pipeline.preview_stride = 2
    pipeline.preview_max_width = 960
    output_path = tmp_path / "annotated.mp4"

    result = pipeline.process_video(
        tmp_path / "input.mp4",
        emit=lambda _event: None,
        cancelled=threading.Event(),
        annotated_video_path=output_path,
    )

    assert result["frames_processed"] == len(frames)
    assert len(writers) == 1
    assert len(writers[0].frames) == len(frames)
    assert all(frame.shape == frames[0].shape for frame in writers[0].frames)
    assert writers[0].released
    assert source_capture.released and validation_capture.released
    assert output_path.read_bytes() == b"fake-h264-mp4"
