from __future__ import annotations

import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from webapp.app import _expire_job, create_app  # noqa: E402


class FakePipeline:
    def __init__(self) -> None:
        self.upload_bytes: bytes | None = None
        self.annotated_video_bytes = b"annotated-mp4-content"

    def process_video(self, video_path, emit, cancelled, annotated_video_path=None):
        self.upload_bytes = Path(video_path).read_bytes()
        if annotated_video_path is not None:
            Path(annotated_video_path).write_bytes(self.annotated_video_bytes)
        emit({
            "type": "frame",
            "frame_index": 0,
            "total_frames": 1,
            "progress": 1.0,
            "people": 1,
            "poses": 1,
            "processing_fps": 12.0,
            "image_base64": "c21va2U=",
        })
        emit({"type": "progress", "frame_index": 0, "total_frames": 1, "progress": 1.0})
        return {
            "predictions": [
                {"label": "谢谢", "distance": 0.12, "similarity": 0.89, "accepted": True}
            ],
            "result_domain": "test fixture",
        }


def cleanup_test_job(app, job_id: str) -> None:
    job = app.state.jobs[job_id]
    job.completed_at = time.time() - app.state.video_retention_seconds - 1
    _expire_job(app, job_id)


def test_default_upload_limit_is_512_mib() -> None:
    app = create_app(pipeline_factory=FakePipeline)

    assert app.state.max_upload_bytes == 512 * 1024 * 1024


def test_home_and_health_routes_are_available() -> None:
    client = TestClient(create_app(pipeline_factory=FakePipeline))

    home = client.get("/")
    health = client.get("/api/health")

    assert home.status_code == 200
    assert "Sign Vision" in home.text
    assert "processedVideo" in home.text
    assert "downloadButton" in home.text
    assert health.status_code == 200
    assert "assets" in health.json()


def test_upload_processes_job_and_exposes_clip_result() -> None:
    fake_pipeline = FakePipeline()
    app = create_app(pipeline_factory=lambda: fake_pipeline)
    client = TestClient(app)

    response = client.post(
        "/api/jobs",
        files={"file": ("sign.mp4", b"fake-video-bytes", "video/mp4")},
    )

    assert response.status_code == 200
    job_id = response.json()["job_id"]
    job = client.get(f"/api/jobs/{job_id}").json()
    assert job["status"] == "completed"
    assert job["result"]["predictions"][0]["label"] == "谢谢"
    assert job["result"]["video_url"] == f"/api/jobs/{job_id}/video"
    assert fake_pipeline.upload_bytes == b"fake-video-bytes"
    cleanup_test_job(app, job_id)


def test_websocket_delivers_preview_and_final_result() -> None:
    app = create_app(pipeline_factory=FakePipeline)
    client = TestClient(app)
    response = client.post(
        "/api/jobs",
        files={"file": ("sign.mp4", b"fake-video-bytes", "video/mp4")},
    )
    job_id = response.json()["job_id"]

    with client.websocket_connect(f"/ws/jobs/{job_id}") as websocket:
        messages = [websocket.receive_json()]
        for _ in range(6):
            message = websocket.receive_json()
            messages.append(message)
            if message.get("type") == "completed":
                break

    assert any(item.get("type") == "frame" for item in messages)
    assert any(item.get("type") == "completed" for item in messages)
    cleanup_test_job(app, job_id)


def test_completed_job_serves_inline_video_and_user_download() -> None:
    fake_pipeline = FakePipeline()
    app = create_app(pipeline_factory=lambda: fake_pipeline)
    client = TestClient(app)
    response = client.post(
        "/api/jobs",
        files={"file": ("sign clip.mp4", b"fake-video-bytes", "video/mp4")},
    )
    job_id = response.json()["job_id"]

    playback = client.get(f"/api/jobs/{job_id}/video")
    partial = client.get(
        f"/api/jobs/{job_id}/video", headers={"Range": "bytes=0-3"}
    )
    download = client.get(f"/api/jobs/{job_id}/video?download=true")

    assert playback.status_code == 200
    assert partial.status_code == 206
    assert partial.content == fake_pipeline.annotated_video_bytes[:4]
    assert playback.headers["content-type"] == "video/mp4"
    assert playback.headers["content-disposition"].startswith("inline;")
    assert playback.content == fake_pipeline.annotated_video_bytes
    assert download.status_code == 200
    assert download.headers["content-disposition"].startswith("attachment;")
    disposition = download.headers["content-disposition"]
    assert "sign%20clip-annotated.mp4" in disposition or "sign clip-annotated.mp4" in disposition
    assert app.state.jobs[job_id].active_video_requests == 0
    cleanup_test_job(app, job_id)


def test_expired_video_job_removes_artifact() -> None:
    fake_pipeline = FakePipeline()
    app = create_app(pipeline_factory=lambda: fake_pipeline)
    client = TestClient(app)
    response = client.post(
        "/api/jobs",
        files={"file": ("sign.mp4", b"fake-video-bytes", "video/mp4")},
    )
    job_id = response.json()["job_id"]
    job = app.state.jobs[job_id]
    job.completed_at = time.time() - (app.state.video_retention_seconds + 1)

    _expire_job(app, job_id)

    assert job_id not in app.state.jobs
    assert not job.temp_dir.exists()

def test_app_shutdown_cleans_retained_video_artifact() -> None:
    app = create_app(pipeline_factory=FakePipeline)
    with TestClient(app) as client:
        response = client.post(
            "/api/jobs",
            files={"file": ("sign.mp4", b"fake-video-bytes", "video/mp4")},
        )
        job_id = response.json()["job_id"]
        job = app.state.jobs[job_id]
        temp_dir = job.temp_dir
        assert job.status == "completed"
        assert temp_dir.exists()

    assert not temp_dir.exists()
    assert job_id not in app.state.expiry_timers


def test_upload_rejects_wrong_type_and_over_limit_files() -> None:
    client = TestClient(create_app(pipeline_factory=FakePipeline, max_upload_bytes=4))

    unsupported = client.post(
        "/api/jobs", files={"file": ("notes.txt", b"abc", "text/plain")}
    )
    oversized = client.post(
        "/api/jobs", files={"file": ("big.mp4", b"12345", "video/mp4")}
    )

    assert unsupported.status_code == 415
    assert oversized.status_code == 413
