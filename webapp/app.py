"""Local FastAPI server for uploaded sign clips and streamed overlays."""

from __future__ import annotations

import asyncio
import queue
from contextlib import asynccontextmanager
import shutil
import sys
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.background import BackgroundTask
import cv2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from signrec.features import DEFAULT_BACKBONE_PATH  # noqa: E402
from signrec.person_detector import DEFAULT_MODEL_PATH
from signrec.pose_estimator import DEFAULT_POSE_MODEL_PATH  # noqa: E402
from webapp.pipeline import SignRecognitionPipeline  # noqa: E402

STATIC_DIR = Path(__file__).resolve().parent / "static"
TEMPLATE_PATH = ROOT / "models" / "sign_templates_cropped.npz"
ALLOWED_SUFFIXES = {".mp4", ".avi", ".mov", ".mkv"}
TERMINAL_STATES = {"completed", "error", "cancelled"}
VIDEO_RETENTION_SECONDS = 60 * 60


@dataclass
class VideoJob:
    job_id: str
    filename: str
    input_path: Path
    temp_dir: Path
    annotated_video_path: Path
    status: str = "queued"
    progress: float = 0.0
    frame_index: int = 0
    total_frames: int = 0
    processing_fps: float = 0.0
    result: dict[str, Any] | None = None
    error: str | None = None
    completed_at: float | None = None
    active_video_requests: int = 0
    events: queue.Queue = field(default_factory=lambda: queue.Queue(maxsize=3))
    cancel_event: threading.Event = field(default_factory=threading.Event)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def emit(self, event: dict[str, Any]) -> None:
        with self._lock:
            kind = event.get("type")
            if kind in {"frame", "progress"}:
                self.progress = float(event.get("progress", self.progress))
                self.frame_index = int(event.get("frame_index", self.frame_index))
                self.total_frames = int(event.get("total_frames", self.total_frames))
                self.processing_fps = float(event.get("processing_fps", self.processing_fps))
            if kind == "status":
                self.status = str(event.get("status", self.status))
        try:
            self.events.put_nowait(event)
        except queue.Full:
            try:
                self.events.get_nowait()
            except queue.Empty:
                pass
            try:
                self.events.put_nowait(event)
            except queue.Full:
                pass

    def set_status(self, status: str) -> None:
        with self._lock:
            self.status = status
        self.emit({"type": "status", "status": status})

    def finish(self, result: dict[str, Any]) -> None:
        with self._lock:
            self.status = "completed"
            self.progress = 1.0
            self.result = result
        self.emit({"type": "completed", "progress": 1.0, "result": result})

    def fail(self, message: str) -> None:
        with self._lock:
            self.status = "error"
            self.error = message
        self.emit({"type": "error", "error": message})

    def cancel(self) -> None:
        self.cancel_event.set()
        self.emit({"type": "status", "status": "cancelling"})

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "job_id": self.job_id,
                "filename": self.filename,
                "status": self.status,
                "progress": self.progress,
                "frame_index": self.frame_index,
                "total_frames": self.total_frames,
                "processing_fps": self.processing_fps,
                "result": self.result,
                "error": self.error,
            }


def _default_pipeline_factory() -> SignRecognitionPipeline:
    return SignRecognitionPipeline(
        person_model=DEFAULT_MODEL_PATH,
        pose_model=DEFAULT_POSE_MODEL_PATH,
        backbone_model=DEFAULT_BACKBONE_PATH,
        templates_path=TEMPLATE_PATH,
    )


def _schedule_job_expiry(app: FastAPI, job_id: str, delay: float) -> None:
    timer = threading.Timer(max(0.1, delay), _expire_job, args=(app, job_id))
    timer.daemon = True
    with app.state.jobs_lock:
        previous = app.state.expiry_timers.get(job_id)
        app.state.expiry_timers[job_id] = timer
    if previous is not None:
        previous.cancel()
    timer.start()


def _expire_job(app: FastAPI, job_id: str) -> None:
    cleanup_dir: Path | None = None
    retry_after: float | None = None
    expiry_timer: threading.Timer | None = None
    now = time.time()
    with app.state.jobs_lock:
        expiry_timer = app.state.expiry_timers.pop(job_id, None)
        if expiry_timer is not None:
            expiry_timer.cancel()
        job: VideoJob | None = app.state.jobs.get(job_id)
        if job is None:
            return
        with job._lock:
            if job.status != "completed" or job.completed_at is None:
                return
            expires_at = job.completed_at + app.state.video_retention_seconds
            if now < expires_at:
                retry_after = expires_at - now
            elif job.active_video_requests > 0:
                retry_after = 60.0
            else:
                app.state.jobs.pop(job_id, None)
                cleanup_dir = job.temp_dir
    if cleanup_dir is not None:
        shutil.rmtree(cleanup_dir, ignore_errors=True)
    elif retry_after is not None:
        _schedule_job_expiry(app, job_id, retry_after)


def _release_video_request(job: VideoJob) -> None:
    with job._lock:
        job.active_video_requests = max(0, job.active_video_requests - 1)


def _annotated_filename(source_name: str) -> str:
    stem = Path(source_name).stem
    safe_stem = "".join(char for char in stem if char.isalnum() or char in " ._-").strip(" .")
    return f"{safe_stem or 'video'}-annotated.mp4"


def _run_job(app: FastAPI, job_id: str) -> None:
    job: VideoJob | None = app.state.jobs.get(job_id)
    if job is None:
        return
    job.set_status("processing")
    keep_artifact = False
    try:
        with app.state.pipeline_lock:
            if app.state.pipeline is None:
                app.state.pipeline = app.state.pipeline_factory()
            pipeline = app.state.pipeline
        result = pipeline.process_video(
            job.input_path,
            job.emit,
            job.cancel_event,
            annotated_video_path=job.annotated_video_path,
        )
        if result.get("cancelled") or job.cancel_event.is_set():
            with job._lock:
                job.status = "cancelled"
            job.emit({"type": "cancelled", "progress": job.progress})
        else:
            job.input_path.unlink(missing_ok=True)
            if not job.annotated_video_path.is_file() or job.annotated_video_path.stat().st_size == 0:
                raise RuntimeError("annotated video output was not created")
            result["video_url"] = f"/api/jobs/{job_id}/video"
            result["video_filename"] = _annotated_filename(job.filename)
            with job._lock:
                job.completed_at = time.time()
            job.finish(result)
            keep_artifact = True
            _schedule_job_expiry(app, job_id, app.state.video_retention_seconds)
    except Exception as exc:  # surfaced in the UI without a server traceback
        job.fail(f"{type(exc).__name__}: {exc}")
    finally:
        if not keep_artifact:
            shutil.rmtree(job.temp_dir, ignore_errors=True)
        with app.state.jobs_lock:
            if app.state.active_job_id == job_id:
                app.state.active_job_id = None


@asynccontextmanager
async def _app_lifespan(app: FastAPI):
    yield
    with app.state.jobs_lock:
        timers = list(app.state.expiry_timers.values())
        jobs = list(app.state.jobs.values())
        app.state.expiry_timers.clear()
    for timer in timers:
        timer.cancel()
    for job in jobs:
        if job.status in TERMINAL_STATES:
            shutil.rmtree(job.temp_dir, ignore_errors=True)


def create_app(
    *,
    pipeline_factory: Callable[[], Any] | None = None,
    max_upload_bytes: int = 512 * 1024 * 1024,
    video_retention_seconds: int = VIDEO_RETENTION_SECONDS,
) -> FastAPI:
    if video_retention_seconds <= 0:
        raise ValueError("video_retention_seconds must be positive")
    app = FastAPI(title="Sign Vision Lab", version="0.1.0", lifespan=_app_lifespan)
    app.state.jobs = {}
    app.state.jobs_lock = threading.Lock()
    app.state.expiry_timers = {}
    app.state.pipeline_lock = threading.Lock()
    app.state.pipeline_factory = pipeline_factory or _default_pipeline_factory
    app.state.pipeline = None
    app.state.active_job_id = None
    app.state.max_upload_bytes = max_upload_bytes
    app.state.video_retention_seconds = video_retention_seconds
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        assets = {
            "person_detector": DEFAULT_MODEL_PATH.is_file(),
            "pose_estimator": DEFAULT_POSE_MODEL_PATH.is_file(),
            "mobilenet_backbone": DEFAULT_BACKBONE_PATH.is_file(),
            "templates": TEMPLATE_PATH.is_file(),
        }
        if not all(assets.values()):
            status = "missing-model-assets"
        elif not hasattr(cv2, "dnn"):
            status = "opencv-dnn-unavailable"
        else:
            status = "assets-present"
        return {
            "status": status,
            "assets": assets,
            "opencv_version": cv2.__version__,
            "inference_loaded": app.state.pipeline is not None,
            "classification_mode": "single segmented clip; final result after clip processing",
            "domain_note": "current templates were built from cropped material; full-frame camera validation pending",
        }

    @app.post("/api/jobs")
    async def create_job(
        background_tasks: BackgroundTasks, file: UploadFile = File(...)
    ) -> dict[str, str]:
        filename = Path(file.filename or "").name
        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_SUFFIXES:
            raise HTTPException(415, "Upload an MP4, AVI, MOV or MKV video file.")

        with app.state.jobs_lock:
            active_id = app.state.active_job_id
            if active_id is not None:
                active_job = app.state.jobs.get(active_id)
                if active_id == "uploading" or active_job is None or active_job.status not in TERMINAL_STATES:
                    raise HTTPException(409, "A video is already being processed.")
            app.state.active_job_id = "uploading"

        temp_dir = Path(tempfile.mkdtemp(prefix="sign-vision-job-"))
        input_path = temp_dir / f"input{suffix}"
        total = 0
        try:
            with input_path.open("wb") as output:
                while chunk := await file.read(1024 * 1024):
                    total += len(chunk)
                    if total > app.state.max_upload_bytes:
                        raise HTTPException(413, "Video exceeds the configured upload limit.")
                    output.write(chunk)
            if total == 0:
                raise HTTPException(400, "Uploaded video is empty.")
        except Exception:
            shutil.rmtree(temp_dir, ignore_errors=True)
            with app.state.jobs_lock:
                if app.state.active_job_id == "uploading":
                    app.state.active_job_id = None
            raise
        finally:
            await file.close()

        job_id = uuid.uuid4().hex
        job = VideoJob(
            job_id=job_id,
            filename=filename,
            input_path=input_path,
            temp_dir=temp_dir,
            annotated_video_path=temp_dir / "annotated.mp4",
        )
        app.state.jobs[job_id] = job
        with app.state.jobs_lock:
            app.state.active_job_id = job_id
        background_tasks.add_task(_run_job, app, job_id)
        return {"job_id": job_id, "filename": filename, "status": "queued"}

    @app.get("/api/jobs/{job_id}")
    def get_job(job_id: str) -> dict[str, Any]:
        job = app.state.jobs.get(job_id)
        if job is None:
            raise HTTPException(404, "Job not found.")
        return job.snapshot()

    @app.get("/api/jobs/{job_id}/video")
    def get_annotated_video(job_id: str, download: bool = False) -> FileResponse:
        expired = False
        with app.state.jobs_lock:
            job: VideoJob | None = app.state.jobs.get(job_id)
            if job is None:
                raise HTTPException(404, "Job not found.")
            with job._lock:
                if job.status != "completed":
                    raise HTTPException(409, "Annotated video is not ready.")
                if job.completed_at is None or time.time() >= job.completed_at + app.state.video_retention_seconds:
                    expired = True
                elif not job.annotated_video_path.is_file():
                    raise HTTPException(410, "Annotated video is no longer available.")
                else:
                    job.active_video_requests += 1
        if expired:
            _expire_job(app, job_id)
            raise HTTPException(410, "Annotated video has expired.")
        filename = _annotated_filename(job.filename)
        return FileResponse(
            job.annotated_video_path,
            media_type="video/mp4",
            filename=filename,
            content_disposition_type="attachment" if download else "inline",
            background=BackgroundTask(_release_video_request, job),
        )

    @app.post("/api/jobs/{job_id}/cancel")
    def cancel_job(job_id: str) -> dict[str, str]:
        job = app.state.jobs.get(job_id)
        if job is None:
            raise HTTPException(404, "Job not found.")
        if job.status in TERMINAL_STATES:
            return {"job_id": job_id, "status": job.status}
        job.cancel()
        return {"job_id": job_id, "status": "cancelling"}

    @app.websocket("/ws/jobs/{job_id}")
    async def job_events(websocket: WebSocket, job_id: str) -> None:
        job = app.state.jobs.get(job_id)
        if job is None:
            await websocket.close(code=1008, reason="Unknown job")
            return
        await websocket.accept()
        await websocket.send_json({"type": "snapshot", **job.snapshot()})
        try:
            while True:
                try:
                    event = await asyncio.to_thread(job.events.get, True, 0.75)
                    await websocket.send_json(event)
                except queue.Empty:
                    await websocket.send_json({"type": "snapshot", **job.snapshot()})
                if job.status in TERMINAL_STATES and job.events.empty():
                    if job.status == "completed":
                        await websocket.send_json({"type": "completed", **job.snapshot()})
                    elif job.status == "error":
                        await websocket.send_json({"type": "error", **job.snapshot()})
                    else:
                        await websocket.send_json({"type": "cancelled", **job.snapshot()})
                    break
        except WebSocketDisconnect:
            return

    return app


app = create_app()
