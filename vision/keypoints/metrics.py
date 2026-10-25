"""Host-side timing and detection availability, not landmark accuracy."""
from dataclasses import dataclass, field
import math

import numpy as np


@dataclass
class Availability:
    detected: int = 0
    missing_runs: list = field(default_factory=list)
    _start: float | None = None
    _last: float | None = None
    _frames: int = 0

    def update(self, present, timestamp):
        self._last = timestamp
        if present:
            self.detected += 1
            if self._start is not None:
                self.missing_runs.append(dict(frames=self._frames,
                    observed_span_s=timestamp-self._start, recovered=True))
                self._start, self._frames = None, 0
        else:
            if self._start is None:
                self._start = timestamp
            self._frames += 1

    def summary(self, total):
        runs = list(self.missing_runs)
        if self._start is not None:
            runs.append(dict(frames=self._frames,
                observed_span_s=self._last-self._start, recovered=False))
        return dict(detected_frames=self.detected,
                    detected_rate=self.detected/total if total else None,
                    missing_runs=runs,
                    longest_missing_frames=max((r['frames'] for r in runs), default=0),
                    longest_observed_missing_span_s=max((r['observed_span_s'] for r in runs), default=0))


class KeypointMetrics:
    def __init__(self):
        self.frames = 0
        self.last_timestamp = None
        self.availability = {k: Availability() for k in ('pose', 'left_hand', 'right_hand', 'both_hands')}
        self.timings = {k: [] for k in ('read_ms', 'inference_ms', 'host_result_ms', 'host_preview_submit_ms')}

    def update(self, timestamp, *, pose, left_hand, right_hand,
               read_ms, inference_ms, host_result_ms, host_preview_submit_ms=None):
        if not math.isfinite(timestamp) or (self.last_timestamp is not None and timestamp <= self.last_timestamp):
            raise ValueError('Source timestamps must be finite and strictly increasing')
        values = dict(read_ms=read_ms, inference_ms=inference_ms,
                      host_result_ms=host_result_ms, host_preview_submit_ms=host_preview_submit_ms)
        if any(v is not None and (not math.isfinite(v) or v < 0) for v in values.values()):
            raise ValueError('Timings must be finite and non-negative')
        self.last_timestamp = timestamp
        self.frames += 1
        for key, present in dict(pose=pose, left_hand=left_hand, right_hand=right_hand,
                                 both_hands=left_hand and right_hand).items():
            self.availability[key].update(bool(present), timestamp)
        for key, value in values.items():
            if value is not None:
                self.timings[key].append(value)

    def summary(self, elapsed_s):
        if not math.isfinite(elapsed_s) or elapsed_s <= 0:
            raise ValueError('Elapsed time must be positive')
        timing = {k: (dict(p50=float(np.percentile(v, 50)), p95=float(np.percentile(v, 95)),
                          mean=float(np.mean(v)), first=v[0]) if v else None)
                  for k, v in self.timings.items()}
        return dict(frames=self.frames, loop_elapsed_s=elapsed_s,
                    processed_fps=self.frames/elapsed_s,
                    timing_ms=timing,
                    availability={k: v.summary(self.frames) for k, v in self.availability.items()})
