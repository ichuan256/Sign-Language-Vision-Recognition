"""Dynamic segmentation for continuous streams (no pre-cut clips).

Energy is the wrist-speed magnitude from sign_xy_v1 velocity (shoulder
widths/second): a hand moving fast is the defining trait of the target
high-dynamic gestures. Onset/offset hysteresis plus sustain counts avoid
chopping on single-frame jitter; short gaps are merged; segments outside
[min_duration_s, max_duration_s] are dropped. Frames with an invalid
wrist velocity contribute zero energy, so a dropped detection cannot
fake motion — it only fails to add energy.
"""
import numpy as np

from .dtw import LEFT_WRIST, RIGHT_WRIST


def wrist_energy(velocity_xy, velocity_valid):
    """[T,51,2]+[T,51] -> [T] max wrist speed in shoulder-widths/second."""
    velocity_xy = np.asarray(velocity_xy, np.float32)
    velocity_valid = np.asarray(velocity_valid, bool)
    if velocity_xy.ndim != 3 or velocity_xy.shape[1:] != (51, 2):
        raise ValueError("expected velocity_xy [T,51,2]")
    speed = np.linalg.norm(velocity_xy[:, (LEFT_WRIST, RIGHT_WRIST), :], axis=-1)
    valid = velocity_valid[:, (LEFT_WRIST, RIGHT_WRIST)]
    return np.where(valid, speed, 0.0).max(axis=1)


def detect_segments(energy, timestamps, *, threshold=None, abs_min=0.4,
                    mad_multiplier=3.0, onset_sustain_s=0.1, offset_sustain_s=0.25,
                    pre_pad_s=0.2, post_pad_s=0.3, merge_gap_s=0.4,
                    min_duration_s=0.4, max_duration_s=8.0):
    """Return [(start_idx, end_idx_exclusive)] sign-motion segments.

    threshold: absolute energy threshold; None -> adaptive
    max(abs_min, median + mad_multiplier * MAD) over the stream.
    Sustains, pads and duration limits are in seconds, converted via the
    timestamps of the *source* stream.
    """
    energy = np.asarray(energy, np.float64)
    times = np.asarray(timestamps, np.float64)
    if energy.shape != times.shape or energy.ndim != 1 or len(times) < 2:
        raise ValueError("expected 1-D energy and timestamps of equal length >= 2")
    dt = np.median(np.diff(times))
    if not np.isfinite(dt) or dt <= 0:
        raise ValueError("timestamps must be increasing")
    if threshold is None:
        med = np.median(energy)
        mad = np.median(np.abs(energy - med))
        threshold = max(abs_min, med + mad_multiplier * mad)
    if not np.isfinite(threshold) or threshold < 0:
        raise ValueError("invalid threshold")

    onset_k = max(1, int(round(onset_sustain_s / dt)))
    offset_k = max(1, int(round(offset_sustain_s / dt)))
    active = energy > threshold
    n = len(active)

    def sustained(mask, k, value):
        out = np.zeros_like(mask)
        run = 0
        for i, flag in enumerate(mask):
            run = run + 1 if flag else 0
            if run >= k:
                out[i - k + 1: i + 1] = value
        return out

    onset_zone = sustained(active, onset_k, True)
    # offset: sustained *inactive* marks the end; find runs of active bounded by them
    in_seg = False
    seg_start = 0
    segments = []
    pending_end = None  # index where active run ended, waiting for offset sustain
    for i in range(n):
        if active[i]:
            if not in_seg:
                if onset_zone[i]:
                    in_seg = True
                    seg_start = i
                else:
                    continue
            pending_end = None
        elif in_seg:
            if pending_end is None:
                pending_end = i
            if i - pending_end + 1 >= offset_k:
                segments.append((seg_start, pending_end))
                in_seg = False
                pending_end = None
    if in_seg:
        segments.append((seg_start, n))

    pre = int(round(pre_pad_s / dt))
    post = int(round(post_pad_s / dt))
    merge = int(round(merge_gap_s / dt))
    # duration limits apply to the detected active core, not the padded extent
    segments = [(s, e) for s, e in segments
                if min_duration_s <= (times[min(e, n - 1)] - times[s]) <= max_duration_s]
    merged = []
    for s, e in segments:
        s, e = max(0, s - pre), min(n, e + post)
        if merged and s - merged[-1][1] <= merge:
            merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))
    return merged
