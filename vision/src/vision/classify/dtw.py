"""Mask-aware DTW baseline over sign_xy_v1 features.

Distance model: per-frame cost is the mask-intersection-weighted mean
squared difference over three blocks of the 392-dim vector —
body/hand normalized xy, xy velocity, and per-hand local shape. Dims
invalid in either frame are excluded (both numerator and denominator),
so missing detections cost nothing instead of being imputed. DTW uses a
The band is on *normalized time* — frame i of the shorter sequence may
pair with frames j where ``|i/T1 - j/T2| <= band_ratio`` — so strongly
different clip lengths stay reachable, which a fixed-diagonal window
forbids. DTW distance is the mean per-frame cost along the optimal
path, keeping comparisons length-fair.
"""
import numpy as np

# sign_xy_v1 layout (see vision/src/vision/sign_video/features.py feature_schema)
N_POINTS = 51
XY_SLICE = slice(0, 102)              # 51 points x (x, y), shoulder-normalized
VEL_SLICE = slice(102, 204)           # d(xy)/dt, shoulder-widths / second
LOCAL_SLICE = slice(204, 288)         # per-hand shape, wrist-origin, own scale
VALID_SLICE = slice(288, 339)         # point valid mask
VEL_VALID_SLICE = slice(339, 390)     # velocity valid mask
LOCAL_VALID_SLICE = slice(390, 392)   # per-hand local shape valid mask

# wrist landmarks inside POINT_NAMES (pose 0-8, then left_hand 0-20, right_hand 0-20)
LEFT_WRIST = 9
RIGHT_WRIST = 30


def frame_costs(feat_a, feat_b, *, xy_weight=1.0, velocity_weight=0.5,
                local_weight=1.0, min_dims=4):
    """Per-frame squared costs between every frame of a and every frame of b.

    feat: [T, 392] sign_xy_v1 rows. Returns [T_a, T_b] costs.
    """
    fa, fb = np.asarray(feat_a, np.float32), np.asarray(feat_b, np.float32)
    if fa.ndim != 2 or fb.ndim != 2 or fa.shape[1] != 392 or fb.shape[1] != 392:
        raise ValueError("expected [T, 392] feature rows")
    valid_a, valid_b = fa[:, VALID_SLICE] > 0.5, fb[:, VALID_SLICE] > 0.5
    vvalid_a, vvalid_b = fa[:, VEL_VALID_SLICE] > 0.5, fb[:, VEL_VALID_SLICE] > 0.5
    lvalid_a, lvalid_b = fa[:, LOCAL_VALID_SLICE] > 0.5, fb[:, LOCAL_VALID_SLICE] > 0.5
    valid_a = np.repeat(valid_a, 2, axis=1)    # per-point -> per-axis (102)
    valid_b = np.repeat(valid_b, 2, axis=1)
    vvalid_a = np.repeat(vvalid_a, 2, axis=1)
    vvalid_b = np.repeat(vvalid_b, 2, axis=1)
    lvalid_a = np.repeat(lvalid_a, 42, axis=1)  # per-hand -> 42 dims each
    lvalid_b = np.repeat(lvalid_b, 42, axis=1)

    def block(a, b, mask_a, mask_b, weight):
        both = mask_a[:, None, :] & mask_b[None, :, :]
        diff = (a[:, None, :] - b[None, :, :]) ** 2
        num = (diff * both).sum(axis=-1)
        den = both.sum(axis=-1)
        return np.where(den >= min_dims, num / np.maximum(den, 1), 0.0) * weight

    cost = block(fa[:, XY_SLICE], fb[:, XY_SLICE], valid_a, valid_b, xy_weight)
    cost += block(fa[:, VEL_SLICE], fb[:, VEL_SLICE], vvalid_a, vvalid_b, velocity_weight)
    cost += block(fa[:, LOCAL_SLICE], fb[:, LOCAL_SLICE], lvalid_a, lvalid_b, local_weight)
    return cost / (xy_weight + velocity_weight + local_weight)


def dtw_distance(cost, *, band_ratio=0.2):
    """Mean per-frame cost of the banded DTW optimal path.

    The band is on *normalized time* — frame i of the shorter sequence may
    pair with frames j where |i/T1 - j/T2| <= band_ratio — so strongly
    different clip lengths (common here: 0.5 s vs 3 s) stay reachable,
    which a fixed-diagonal Sakoe-Chiba window forbids. Endpoints are
    always reachable; band_ratio is a phase-alignment tolerance.
    """
    cost = np.asarray(cost, np.float64)
    t1, t2 = cost.shape
    if t1 == 0 or t2 == 0:
        raise ValueError("empty sequence")
    if not 0 < band_ratio <= 0.5:
        raise ValueError("band_ratio must be in (0, 0.5]")
    inf = np.inf
    dp = np.full((t1 + 1, t2 + 1), inf)      # accumulated cost
    ln = np.zeros((t1 + 1, t2 + 1), np.int32)  # steps on the best-cost path
    dp[0, 0] = 0.0
    for i in range(1, t1 + 1):
        # 1-based i maps to normalized time i/t1; j window in 1-based coords
        j_lo = max(1, int(np.ceil(t2 * (i / t1 - band_ratio))))
        j_hi = min(t2, int(np.floor(t2 * (i / t1 + band_ratio))))
        if i == t1:
            j_hi = t2  # exact endpoint
        for j in range(j_lo, j_hi + 1):
            cands = ((dp[i - 1, j], ln[i - 1, j]),      # insertion
                     (dp[i, j - 1], ln[i, j - 1]),      # deletion
                     (dp[i - 1, j - 1], ln[i - 1, j - 1]))  # match
            prev_cost, prev_len = min(cands, key=lambda c: c[0])
            dp[i, j] = cost[i - 1, j - 1] + prev_cost
            ln[i, j] = prev_len + 1
    path_cost = dp[t1, t2]
    if not np.isfinite(path_cost) or ln[t1, t2] == 0:
        raise ValueError("no path within band; sequences too dissimilar in length")
    return path_cost / ln[t1, t2], path_cost


class TemplateClassifier:
    """1-NN over per-label DTW template sets.

    Each training clip is its own template; the label score is the minimum
    distance among its templates. This is a baseline, not a learned model.
    """

    def __init__(self, *, band_ratio=0.2, xy_weight=1.0, velocity_weight=0.5,
                 local_weight=1.0):
        self.band_ratio = band_ratio
        self.weights = dict(xy_weight=xy_weight, velocity_weight=velocity_weight,
                            local_weight=local_weight)
        self.templates_ = []  # (label, group, sample_id, features)

    def fit(self, samples):
        """samples: iterable of dicts with keys label, group, id, features."""
        self.templates_ = [(s["label"], s["group"], s["id"],
                            np.asarray(s["features"], np.float32)) for s in samples]
        if not self.templates_:
            raise ValueError("no templates")
        labels = {t[0] for t in self.templates_}
        if len(labels) < 2:
            raise ValueError("need at least two distinct labels")
        return self

    def predict(self, features):
        """Return (label, distance, margins) where margins is a label->distance dict."""
        feat = np.asarray(features, np.float32)
        best_by_label = {}
        for label, _group, _sid, tmpl in self.templates_:
            cost = frame_costs(feat, tmpl, **self.weights)
            dist, _ = dtw_distance(cost, band_ratio=self.band_ratio)
            if label not in best_by_label or dist < best_by_label[label]:
                best_by_label[label] = dist
        label = min(best_by_label, key=best_by_label.get)
        return label, best_by_label[label], best_by_label
