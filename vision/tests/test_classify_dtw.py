"""Tests for the mask-aware DTW baseline and dynamic segmentation."""
import numpy as np
import pytest

from vision.classify.dtw import frame_costs, dtw_distance, TemplateClassifier
from vision.classify.segment import wrist_energy, detect_segments


def make_features(n, motion_scale=1.0, seed=0, *, moving=slice(None)):
    """Synthetic [n, 392] sign_xy_v1 rows with controlled motion."""
    rng = np.random.default_rng(seed)
    feat = np.zeros((n, 392), np.float32)
    feat[:, :102] = 0.5
    feat[:, 288:339] = 1.0   # all points valid
    feat[:, 339:390] = 1.0   # all velocities valid
    feat[:, 390:392] = 1.0   # both hands' local shape valid
    vel = np.zeros((n, 102), np.float32)
    vel[list(range(n))[moving]] = motion_scale
    feat[:, 102:204] = vel
    feat[:, 204:288] = 0.3
    return feat


def test_identical_series_zero_distance():
    a = make_features(12, motion_scale=0.7, seed=1)
    dist, _ = dtw_distance(frame_costs(a, a))
    assert dist == pytest.approx(0.0, abs=1e-6)


def test_masked_dims_do_not_contribute():
    a = make_features(10, seed=2)
    b = a.copy()
    b[:, :2] += 5.0            # huge xy move on point 0 ...
    b[:, 288] = 0.0            # ... but mark point 0 invalid in b
    cost = frame_costs(a, b)
    dist, _ = dtw_distance(cost)
    assert dist == pytest.approx(0.0, abs=1e-6)


def test_more_motion_scores_higher_distance_than_less():
    still = make_features(10, motion_scale=0.05, seed=3)
    fast = make_features(10, motion_scale=0.9, seed=3)
    d_still, _ = dtw_distance(frame_costs(still, fast))
    d_fast, _ = dtw_distance(frame_costs(fast, fast))
    assert d_still > d_fast


def test_template_classifier_picks_right_label():
    train = [{"id": "a1", "label": "A", "group": "g1", "features": make_features(10, 0.9, seed=1)},
             {"id": "b1", "label": "B", "group": "g1", "features": make_features(10, 0.1, seed=1)}]
    clf = TemplateClassifier().fit(train)
    pred, dist, _ = clf.predict(make_features(10, 0.9, seed=1))
    assert pred == "A"
    pred, _, _ = clf.predict(make_features(10, 0.1, seed=1))
    assert pred == "B"


def test_wrist_energy_uses_valid_mask():
    vel = np.zeros((4, 51, 2), np.float32)
    vvalid = np.zeros((4, 51), bool)
    vel[:, 9, 0] = 2.0   # left wrist moving, but invalid
    assert wrist_energy(vel, vvalid).max() == 0.0
    vvalid[:, 9] = True
    assert wrist_energy(vel, vvalid).max() == pytest.approx(2.0)


def test_detect_segments_recovers_embedded_motion():
    n = 60
    rng = np.random.default_rng(0)
    times = np.arange(n) / 20.0
    energy = rng.normal(0.05, 0.01, n)
    energy[20:40] = 1.2      # 1 s of motion in the middle
    segments = detect_segments(energy, times, threshold=0.4)
    assert len(segments) == 1
    s, e = segments[0]
    assert s <= 20 and e >= 40          # covers the motion
    assert s >= 16 - 1                  # pre-pad ~0.2 s, not eating the run-up
    assert (times[min(e, n - 1)] - times[s]) <= 8.0


def test_detect_segments_drops_short_blips():
    n = 60
    times = np.arange(n) / 20.0
    energy = np.full(n, 0.05)
    energy[20:23] = 1.2      # 0.15 s blip, below min_duration even padded
    assert detect_segments(energy, times, threshold=0.4) == []
