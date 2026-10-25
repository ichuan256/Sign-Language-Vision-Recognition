"""Loopback-only latest-JPEG sink compatible with the existing W6 HDMI receiver."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
import time

import cv2
import numpy as np


def hdmi_jpeg(bgr):
    if bgr.dtype != np.uint8 or bgr.ndim != 3 or bgr.shape[2] != 3 or min(bgr.shape[:2]) <= 0:
        raise ValueError('Expected a nonempty uint8 BGR frame')
    height, width = bgr.shape[:2]
    scale = min(1280/width, 720/height)
    w, h = max(1, round(width*scale)), max(1, round(height*scale))
    canvas = np.zeros((720, 1280, 3), np.uint8)
    x, y = (1280-w)//2, (720-h)//2
    canvas[y:y+h, x:x+w] = cv2.resize(bgr, (w, h))
    ok, data = cv2.imencode('.jpg', canvas, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not ok:
        raise RuntimeError('JPEG encoder failed')
    return data.tobytes()


class LatestFrameServer:
    def __init__(self, port=18780):
        self.port = port
        self._lock = threading.Lock()
        self._jpeg = None
        self._state = dict(frames_published=0, frame_requests=0, frame_id=None,
                           source_timestamp_s=None, size=[1280, 720], published_monotonic_s=None)
        self.server = self.thread = None

    def publish(self, frame, frame_id, timestamp):
        jpeg = hdmi_jpeg(frame)
        with self._lock:
            self._jpeg = jpeg  # exactly one frame retained, no per-client frame queue
            self._state.update(frames_published=self._state['frames_published']+1,
                               frame_id=frame_id, source_timestamp_s=timestamp,
                               published_monotonic_s=time.monotonic())

    def state(self):
        with self._lock:
            return dict(self._state)

    def __enter__(self):
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                with owner._lock:
                    if self.path == '/frame.jpg':
                        payload = owner._jpeg
                        status = 200 if payload is not None else 503
                        content_type = 'image/jpeg' if payload is not None else 'text/plain'
                        payload = payload if payload is not None else b'No frame published yet'
                        if status == 200:
                            owner._state['frame_requests'] += 1
                    elif self.path == '/state':
                        payload = json.dumps(owner._state).encode()
                        status, content_type = 200, 'application/json'
                    else:
                        payload, status, content_type = b'Not found', 404, 'text/plain'
                self.send_response(status)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(len(payload)))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                try:
                    self.wfile.write(payload)
                except (BrokenPipeError, ConnectionResetError):
                    pass
            def log_message(self, *args):
                pass
        self.server = ThreadingHTTPServer(('127.0.0.1', self.port), Handler)
        self.server.daemon_threads = True
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever,
                                       kwargs=dict(poll_interval=.1), daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *args):
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
        if self.thread is not None:
            self.thread.join(timeout=3)
