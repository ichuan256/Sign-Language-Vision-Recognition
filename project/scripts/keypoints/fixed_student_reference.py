"""R2 golden reference: W8/A8 integer forward of the hand student network.

Pure-numpy fixed-point re-implementation of the float student (BN folded into
convs), used to prove accumulator bit-widths and to validate RTL layer kernels
against an independent software oracle. Follows the R2 gate of
docs/方案/03_Zynq7020独立实时关键点方案.md.

Numeric contract (v2, after 2026-10-28 review):
- weights: int8, symmetric, per output channel
- activations: uint8 codes, zero_point=0 (post-ReLU ranges >= 0); clipping at
  the calibrated max implements the "clipped ReLU chosen by calibration" option
- requantization is INTEGER ONLY: per-output-channel multiplier M (signed
  int32) and shift F, y_q = sat(rne_shift(acc * M, F)); RNE = round half to
  even on the exact integer product, saturation AFTER rounding (same order as
  kp_gemm_tile). No float multiply/divide exists anywhere in the integer path.
- boundary quantizers use exact rational arithmetic (fractions.Fraction);
  float64 vectorized rounding is used for speed with an exactness guard that
  re-evaluates any value within 1e-12 of a rounding boundary via Fraction.
- coordinate head: int16 export, y16 = sat(rne_shift(acc*M, F), -32768,
  32767), per-channel scale head_scale recorded for the PC-side rescale.
- accumulator scope: int32 is proven ONLY for MAC+bias of THESE frozen W8/A8
  weights with the full 255 input-code range. It does NOT extend to the old
  W12/A16 network, to retrained/re-exported weights, or to the requant product
  acc*M (whose width is reported separately as acc_bits + M_bits).
- nothing here claims the student accuracy is deployable; this is the integer
  reference only, on a network whose precision gate is still unmet.
"""
import argparse
import hashlib
import json
import os
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------- exact integer arithmetic ----------------

def rne_frac(fr):
    """Round half to even of a Fraction, exact."""
    if fr < 0:
        return -rne_frac(-fr)
    q, r = divmod(fr.numerator, fr.denominator)
    c = 2 * r - fr.denominator
    if c > 0 or (c == 0 and q % 2 == 1):
        q += 1
    return q


def rne_shift(q, f):
    """RNE of q / 2**f for a signed Python int q."""
    if q < 0:
        return -rne_shift(-q, f)
    base = q >> f
    rem = q - (base << f)
    half = 1 << (f - 1)
    if rem > half or (rem == half and (base & 1)):
        base += 1
    return base


def rne_shift_arr(q, f):
    """Vectorized exact rne_shift for numpy integer arrays."""
    sign = np.where(q < 0, -1, 1)
    a = np.abs(q).astype(np.int64)
    base = a >> f
    rem = a & ((1 << f) - 1)
    half = 1 << (f - 1)
    up = (rem > half) | ((rem == half) & ((base & 1) == 1))
    return sign * (base + up)


def rne_array_exact(x, scale_fr, scale_f):
    """RNE of x / scale, bit-identical to the exact-rational reference.

    Scope and proof: x >= 0, scale > 0, both float64. t = fl64(x/scale) has
    |t - x/scale| <= 0.5 ulp(t). A rounding boundary sits at frac(t) = 0.5;
    any element whose quotient is more than 2 ulp away from the nearest
    boundary rounds identically in float64 and in exact arithmetic. Elements
    closer than 2 ulp are re-evaluated with Fraction. Therefore the result
    equals rne_frac(Fraction(x)/scale_fr) for every element.
    """
    x = np.asarray(x, np.float64)
    if x.size == 0:
        return np.zeros(x.shape, np.int64)
    if float(x.min()) < 0:
        raise ValueError("rne_array_exact is defined for x >= 0")
    t = x / scale_f
    r = np.rint(t).astype(np.int64)
    frac = t - np.floor(t)
    near = np.abs(frac - 0.5) < 2.0 * np.spacing(t)
    for idx in np.argwhere(near):
        r[tuple(idx)] = rne_frac(Fraction(float(x[tuple(idx)])) / scale_fr)
    return r


def sat_arr(q, lo, hi):
    return np.clip(q, lo, hi)


# ---------------- float folded model ----------------

def fold_bn(conv_w, bn):
    g = bn["gamma"].astype(np.float64)
    beta = bn["beta"].astype(np.float64)
    mean = bn["mean"].astype(np.float64)
    var = bn["var"].astype(np.float64)
    s = np.sqrt(var + bn["eps"])
    scale = g / s
    shift = beta - mean * scale
    w = conv_w.astype(np.float64).copy()
    if w.ndim == 4 and w.shape[3] == 1:
        w *= scale.reshape(1, 1, -1, 1)
        b = shift
    else:
        w *= scale.reshape(*([1] * (w.ndim - 1)), -1)
        b = shift
    return w, b


def same_pad(h, k, stride):
    out = -(-h // stride)
    total = max((out - 1) * stride + k - h, 0)
    return total // 2, total - total // 2


def conv2d_float(x, w, b, stride):
    n, h, wid, cin = x.shape
    kh, kw, _, cout = w.shape
    pt, pb = same_pad(h, kh, stride)
    pl, pr = same_pad(wid, kw, stride)
    xp = np.pad(x, ((0, 0), (pt, pb), (pl, pr), (0, 0)))
    oh = (h + pt + pb - kh) // stride + 1
    ow = (wid + pl + pr - kw) // stride + 1
    cols = np.lib.stride_tricks.sliding_window_view(
        xp, (kh, kw), axis=(1, 2))[:, ::stride, ::stride]     # [N,oh,ow,Cin,kh,kw]
    return np.einsum("nxycuv,uvcj->nxyj", cols, w.astype(x.dtype)) + b


def depthwise_float(x, w, b, stride):
    kh = w.shape[0]
    h, wid = x.shape[1], x.shape[2]
    pt, pb = same_pad(h, kh, stride)
    pl, pr = same_pad(wid, kh, stride)
    xp = np.pad(x, ((0, 0), (pt, pb), (pl, pr), (0, 0)))
    n = x.shape[0]
    oh = (h + pt + pb - kh) // stride + 1
    ow = (wid + pl + pr - kh) // stride + 1
    y = np.zeros((n, oh, ow, x.shape[3]), dtype=x.dtype)
    for dy in range(kh):
        for dx in range(kh):
            y += xp[:, dy:dy + oh * stride:stride, dx:dx + ow * stride:stride, :] \
                * w[dy, dx, :, 0]
    return y + b


# ---------------- integer kernels ----------------

def conv2d_int(x_q, w_q, b_q, stride):
    n, h, wid, cin = x_q.shape
    kh, kw, _, cout = w_q.shape
    pt, pb = same_pad(h, kh, stride)
    pl, pr = same_pad(wid, kw, stride)
    xp = np.pad(x_q, ((0, 0), (pt, pb), (pl, pr), (0, 0)))
    oh = (h + pt + pb - kh) // stride + 1
    ow = (wid + pl + pr - kw) // stride + 1
    cols = np.lib.stride_tricks.sliding_window_view(
        xp, (kh, kw), axis=(1, 2))[:, ::stride, ::stride]
    m = cols.transpose(0, 1, 2, 4, 5, 3).reshape(n * oh * ow, kh * kw * cin)
    y = m.astype(np.int64) @ w_q.reshape(-1, cout).astype(np.int64) + b_q
    return y.reshape(n, oh, ow, cout)


def depthwise_int(x_q, w_q, b_q, stride):
    kh = w_q.shape[0]
    h, wid = x_q.shape[1], x_q.shape[2]
    pt, pb = same_pad(h, kh, stride)
    pl, pr = same_pad(wid, kh, stride)
    xp = np.pad(x_q, ((0, 0), (pt, pb), (pl, pr), (0, 0)))
    n, c = x_q.shape[0], x_q.shape[3]
    oh = (h + pt + pb - kh) // stride + 1
    ow = (wid + pl + pr - kh) // stride + 1
    y = np.zeros((n, oh, ow, c), np.int64)
    for dy in range(kh):
        for dx in range(kh):
            y += xp[:, dy:dy + oh * stride:stride, dx:dx + ow * stride:stride, :].astype(np.int64) \
                * w_q[dy, dx, :, 0].reshape(1, 1, 1, c)
    return y + b_q


# ---------------- model graph ----------------

GRAPH = [
    ("stem", "conv", 2),
    ("dw_0", "depthwise", 1), ("pw_0", "pointwise", 1),
    ("dw_1", "depthwise", 2), ("pw_1", "pointwise", 1),
    ("dw_2", "depthwise", 2), ("pw_2", "pointwise", 1),
    ("dw_3", "depthwise", 2), ("pw_3", "pointwise", 1),
    ("dw_4", "depthwise", 2), ("pw_4", "pointwise", 1),
]
HEAD = "coordinate_presence_handedness_head"
F_START = 30
M_LIMIT = 2**31 - 1


def extract_folded(model):
    weights = {}
    for name, kind, _stride in GRAPH:
        w = model.get_layer(name).get_weights()[0]
        bn = model.get_layer(name + "_bn")
        gamma, beta, mean, var = bn.get_weights()
        weights[name] = fold_bn(w, {"gamma": gamma, "beta": beta, "mean": mean,
                                    "var": var, "eps": bn.epsilon})
    dw, db = model.get_layer(HEAD).get_weights()
    weights[HEAD] = (dw.astype(np.float64), db.astype(np.float64))
    return weights


def float_forward(weights, x):
    acts = {"__input__": x}
    h = x
    for name, kind, stride in GRAPH:
        w, b = weights[name]
        h = depthwise_float(h, w, b, stride) if kind == "depthwise" \
            else conv2d_float(h, w, b, stride)
        h = np.maximum(h, 0)
        acts[name] = h
    flat = h.reshape(h.shape[0], -1)
    w, b = weights[HEAD]
    return flat @ w + b, acts


class LayerQ:
    """Exact-rational quantizer parameters for one layer."""

    def __init__(self, name, kind, w_f, b_f, x_max, out_max, head=False):
        self.name = name
        self.kind = kind
        self.x_scale = Fraction(float(x_max)) / 255 if not head else Fraction(float(x_max)) / 255
        if head:
            # int16 export: scale covers the calibration magnitude
            self.out_scale = Fraction(float(out_max)) / 32767 if out_max > 0 else Fraction(1, 2**20)
        else:
            self.out_scale = Fraction(float(out_max)) / 255 if out_max > 0 else Fraction(1, 2**20)
        if kind == "depthwise":
            absmax = np.max(np.abs(w_f), axis=(0, 1, 3))
            sum_wq_axes = (0, 1, 3)
        else:
            reduce_axes = (0, 1, 2) if w_f.ndim == 4 else (0,)
            absmax = np.max(np.abs(w_f), axis=reduce_axes)
            sum_wq_axes = reduce_axes
        # exact integer weights and biases
        def wscale(v):
            return Fraction(float(v)) / 127 if v > 0 else Fraction(1, 127)
        self.w_scale = [wscale(v) for v in absmax]
        # exact integer weights and biases
        w_scale_f = np.array([float(s) for s in self.w_scale])
        if kind == "depthwise":
            w_q = np.array([[rne_frac(Fraction(float(w_f[u, v, c, 0])) / self.w_scale[c])
                             for c in range(w_f.shape[2])]
                            for u in range(w_f.shape[0]) for v in range(w_f.shape[1])])
            w_q = w_q.reshape(w_f.shape[0], w_f.shape[1], w_f.shape[2], 1)
        else:
            flat = w_f.reshape(-1, w_f.shape[-1])
            w_q = np.array([[rne_frac(Fraction(float(flat[i, o])) / self.w_scale[o])
                             for o in range(flat.shape[1])] for i in range(flat.shape[0])])
            w_q = w_q.reshape(w_f.shape)
        self.w_q = w_q.astype(np.int64)
        self.bias_q = np.array([rne_frac(Fraction(float(b_f[o])) / (self.x_scale * self.w_scale[o]))
                                for o in range(len(b_f))], dtype=np.int64)
        # integer requant multiplier/shift, exact. Direction rules: F shrinks
        # when M overflows int32, F grows when a channel's M rounds to 0.
        # M==0 is only accepted for all-zero-weight, zero-bias channels (output
        # is then constantly 0); anything else needs per-channel F and raises.
        r = [(self.x_scale * self.w_scale[o]) / self.out_scale for o in range(len(self.w_scale))]
        f = F_START
        while True:
            m = [rne_frac(ro * 2**f) for ro in r]
            if max(abs(v) for v in m) <= M_LIMIT and min(abs(v) for v in m) >= 1:
                break
            f = f - 1 if max(abs(v) for v in m) > M_LIMIT else f + 1
            if f > 62 or f < 8:
                bad = [o for o, v in enumerate(m) if v == 0]
                zero_ok = all(not self.w_q[..., o].any() and self.bias_q[o] == 0
                              for o in bad)
                if f > 62 and zero_ok:
                    break
                raise ValueError(f"{name}: multiplier not representable at F={f}; "
                                 "needs per-channel shift")
        self.F = f
        self.M = np.array(m, dtype=np.int64)
        # conservative MAC+bias accumulator bound (full 255-code input range)
        sum_wq = np.sum(np.abs(self.w_q), axis=sum_wq_axes)
        bound = 255 * sum_wq + np.abs(self.bias_q)
        self.acc_bound = int(bound.max())
        self.acc_bits = int(np.ceil(np.log2(self.acc_bound + 1))) + 1
        self.m_bits = int(max(abs(v) for v in m).bit_length()) + 1
        self.product_bits = self.acc_bits + self.m_bits
        self.x_scale_f = float(self.x_scale)
        self.out_scale_f = float(self.out_scale)

    def quantize_input(self, x_float):
        return rne_array_exact(x_float, self.x_scale, self.x_scale_f).astype(np.int64)

    def requant(self, acc):
        prod = acc * self.M.reshape([1] * (acc.ndim - 1) + [-1])
        q = rne_shift_arr(prod, self.F)
        if self.kind == "dense":
            sat = sat_arr(q, -32768, 32767)
            pos_ovf = int(np.count_nonzero(q > 32767))
            neg_clip = int(np.count_nonzero(q < -32768))
        else:
            sat = sat_arr(q, 0, 255)
            pos_ovf = int(np.count_nonzero(q > 255))   # true calibration saturation
            neg_clip = int(np.count_nonzero(q < 0))    # ReLU zeros, expected
        return sat, {"positive_overflow": pos_ovf, "negative_relu": neg_clip}, \
            int(np.max(np.abs(prod)))


def build_scheme(weights, calib_max, head_calib_absmax):
    scheme = {}
    prev = "__input__"
    for name, kind, _s in GRAPH:
        w, b = weights[name]
        scheme[name] = LayerQ(name, kind, w, b, calib_max[prev], calib_max[name])
        prev = name
    w, b = weights[HEAD]
    scheme[HEAD] = LayerQ(HEAD, "dense", w, b, calib_max[prev], head_calib_absmax,
                          head=True)
    return scheme


def int_forward(weights, scheme, x_float):
    h_q = scheme["stem"].quantize_input(x_float)
    stats = {}
    for name, kind, stride in GRAPH:
        s = scheme[name]
        acc = depthwise_int(h_q, s.w_q, s.bias_q, stride) if kind == "depthwise" \
            else conv2d_int(h_q, s.w_q, s.bias_q, stride)
        h_q, ovf, prod_max = s.requant(acc)
        stats[name] = {"acc_max": int(np.max(np.abs(acc))), "clip": ovf,
                       "product_max": prod_max}
    s = scheme[HEAD]
    flat_q = h_q.reshape(h_q.shape[0], -1)
    acc = flat_q.astype(np.int64) @ s.w_q.astype(np.int64) + s.bias_q
    y16, ovf, prod_max = s.requant(acc)
    stats[HEAD] = {"acc_max": int(np.max(np.abs(acc))), "clip": ovf,
                   "product_max": prod_max}
    y_float = y16.astype(np.float64) * np.asarray(s.out_scale_f)
    return y_float, y16, stats, h_q


def self_test():
    """Boundary cases: RNE edges, negative accumulators, saturation order,
    and brute-force parity for every kernel kind (conv, depthwise,
    pointwise, dense head) including a full M/F requant chain."""
    assert rne_shift(24, 4) == 2      # 1.5 -> 2 (even)
    assert rne_shift(40, 4) == 2      # 2.5 -> 2 (even)
    assert rne_shift(8, 4) == 0       # 0.5 -> 0 (even)
    assert rne_shift(-24, 4) == -2    # symmetric
    assert rne_shift(-40, 4) == -2
    assert rne_shift(17, 4) == 1      # 1.0625 -> 1
    arr = rne_shift_arr(np.array([24, 40, 8, -24, -40, 300 << 4]), 4)
    assert arr.tolist() == [2, 2, 0, -2, -2, 300], arr.tolist()
    assert sat_arr(np.array([300, -5]), 0, 255).tolist() == [255, 0]
    rng = np.random.default_rng(7)
    xs = rng.uniform(0, 1, 50000)
    scale_fr = Fraction(3, 700)
    got = rne_array_exact(xs, scale_fr, float(scale_fr))
    for i in rng.integers(0, len(xs), 200):
        assert got[i] == rne_frac(Fraction(float(xs[i])) / scale_fr)

    # exactness guard: boundary-adjacent values go through Fraction
    tricky = np.array([3 * 0.5 * float(scale_fr) * 2,  # exactly 1.5 in quotient
                       (2 * 700 + 350) / 255 / 4.0])
    _ = rne_array_exact(np.abs(tricky), scale_fr, float(scale_fr))

    # ---- brute force parity, all kernel kinds, negative accumulators ----
    def brute_conv(x, w, b, stride):
        n, h, wid, cin = x.shape
        kh, kw, _, cout = w.shape
        oh = -(-h // stride)
        pt, pb = same_pad(h, kh, stride)
        pl, pr = same_pad(wid, kw, stride)
        xp = np.pad(x, ((0, 0), (pt, pb), (pl, pr), (0, 0)))
        y = np.zeros((n, oh, (wid + pl + pr - kw) // stride + 1, cout), np.int64)
        for i in range(y.shape[1]):
            for j in range(y.shape[2]):
                ii, jj = i * stride, j * stride
                patch = xp[:, ii:ii + kh, jj:jj + kw, :].astype(np.int64)
                y[:, i, j, :] = np.einsum("nuvc,uvco->no", patch, w.astype(np.int64)) + b
        return y

    xq = rng.integers(-4, 5, size=(2, 5, 5, 3)).astype(np.int64)
    w4 = rng.integers(-3, 4, size=(3, 3, 3, 4)).astype(np.int64)
    b4 = rng.integers(-20, 21, size=4).astype(np.int64)
    assert np.array_equal(conv2d_int(xq, w4, b4, 2), brute_conv(xq, w4, b4, 2))
    assert np.array_equal(conv2d_int(xq, w4, b4, 1), brute_conv(xq, w4, b4, 1))

    xd = rng.integers(-4, 5, size=(2, 4, 4, 3)).astype(np.int64)
    wd = rng.integers(-3, 4, size=(3, 3, 3, 1)).astype(np.int64)
    bd = rng.integers(-9, 10, size=3).astype(np.int64)
    y_dw = depthwise_int(xd, wd, bd, 2)
    brute_dw = np.zeros_like(y_dw)
    pt_d = same_pad(4, 3, 2)[0]
    for i in range(y_dw.shape[1]):
        for j in range(y_dw.shape[2]):
            for c in range(3):
                acc = int(bd[c])
                for u in range(3):
                    for v in range(3):
                        ii, jj = i * 2 + u, j * 2 + v
                        pad_i, pad_j = ii - pt_d, jj - pt_d
                        if 0 <= pad_i < 4 and 0 <= pad_j < 4:
                            acc += int(xd[0, pad_i, pad_j, c]) * int(wd[u, v, c, 0])
                brute_dw[0, i, j, c] = acc
    assert np.array_equal(y_dw[:1], brute_dw[:1])

    # pointwise = 1x1 conv; dense head = matmul; both feed an M/F requant
    xp_ = rng.integers(0, 6, size=(3, 2, 2, 5)).astype(np.int64)
    wp_ = rng.integers(-4, 5, size=(1, 1, 5, 7)).astype(np.int64)
    bp_ = rng.integers(-15, 16, size=7).astype(np.int64)
    acc_pw = conv2d_int(xp_, wp_, bp_, 1)
    brute_pw = xp_.astype(np.int64).reshape(-1, 5) @ wp_.reshape(5, 7) + bp_
    assert np.array_equal(acc_pw.reshape(-1, 7), brute_pw)

    xh = rng.integers(0, 6, size=(4, 9)).astype(np.int64)
    wh = rng.integers(-4, 5, size=(9, 5)).astype(np.int64)
    bh = rng.integers(-30, 31, size=5).astype(np.int64)
    acc_h = xh @ wh + bh
    # requant chain with half-integer products and negatives
    M = np.array([3, 5, 7, 11, 13], np.int64)
    F_ = 4
    prod = acc_h * M
    y16 = sat_arr(rne_shift_arr(prod, F_), -32768, 32767)
    for r_i in range(4):
        for c_i in range(5):
            want = rne_shift(int(prod[r_i, c_i]), F_)
            want = min(max(want, -32768), 32767)
            assert int(y16[r_i, c_i]) == want
    # explicit half-even cases through the chain: acc*M = 24 -> 1.5 -> 2 etc.
    acc_t = np.array([[8, -8, 1000000]], np.int64)   # 1.5, -1.5, saturate
    M_t = np.array([3, 3, 3], np.int64)
    got_t = sat_arr(rne_shift_arr(acc_t * M_t, 4), -32768, 32767)
    assert got_t.tolist() == [[2, -2, 32767]]
    print(json.dumps({"self_test": "PASS"}))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", type=Path)
    p.add_argument("--data", type=Path)
    p.add_argument("--reviews", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--batch", type=int, default=64)
    p.add_argument("--vectors", type=int, default=2)
    p.add_argument("--vectors-c", type=Path,
                   help="also dump raw little-endian vectors + manifest for the C testbench")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args()
    if a.self_test:
        self_test()
        return
    if not a.model or not a.data or not a.output:
        raise ValueError("--model, --data and --output are required "
                         "outside --self-test")
    if a.output.exists():
        raise ValueError("output must not exist")
    a.output.mkdir(parents=True)

    import tf_keras as keras
    from vision.keypoints.student_data import load_dataset, augment
    from project.scripts.keypoints.train_hand_student import evaluate

    images, y, m, records, _rep = load_dataset(
        a.data, a.reviews, mask_outside_source=True)
    size = 96

    def build_split(split):
        idx = [i for i, r in enumerate(records)
               if r["split"] == split and m[i, :63].any()]
        x = np.stack([augment(images[i], y[i], m[i], size)[0] for i in idx])
        return x, y[idx], m[idx], [records[i] for i in idx]

    x_cal, _, _, _ = build_split("train")
    x_ev, y_ev, m_ev, r_ev = build_split("test")
    model = keras.models.load_model(a.model, compile=False)
    weights = extract_folded(model)

    probe = x_ev[:16]
    ref_orig = model.predict(probe, verbose=0)
    ref_fold, _ = float_forward(weights, probe)
    fold_err = float(np.max(np.abs(ref_orig - ref_fold)))
    if fold_err > 1e-3:
        raise ValueError(f"BN folding mismatch {fold_err}")

    calib_max = {}
    head_max = 0.0
    for i in range(0, len(x_cal), a.batch):
        out, acts = float_forward(weights, x_cal[i:i + a.batch])
        for k, v in acts.items():
            calib_max[k] = max(calib_max.get(k, 0.0), float(v.max()))
        head_max = max(head_max, float(np.max(np.abs(out))))
    scheme = build_scheme(weights, calib_max, head_max)

    preds_q, y16_all, stats = [], [], {}
    for i in range(0, len(x_ev), a.batch):
        yf, y16, st, _ = int_forward(weights, scheme, x_ev[i:i + a.batch])
        preds_q.append(yf)
        y16_all.append(y16)
        for k, v in st.items():
            d = stats.setdefault(k, {"acc_max": 0, "product_max": 0,
                                     "clip": {"positive_overflow": 0,
                                              "negative_relu": 0}})
            d["acc_max"] = max(d["acc_max"], v["acc_max"])
            d["product_max"] = max(d["product_max"], v["product_max"])
            d["clip"]["positive_overflow"] += v["clip"]["positive_overflow"]
            d["clip"]["negative_relu"] += v["clip"]["negative_relu"]
    preds_q = np.concatenate(preds_q)
    y16_all = np.concatenate(y16_all).astype(np.int16)   # true int16 export

    preds_f = np.concatenate([float_forward(weights, x_ev[i:i + a.batch])[0]
                              for i in range(0, len(x_ev), a.batch)])

    metrics_f = evaluate(preds_f, y_ev, m_ev, r_ev)
    metrics_q = evaluate(preds_q, y_ev, m_ev, r_ev)

    # Per-layer integer test vectors for C/RTL testbenches: every layer gets
    # explicit input / output / accumulators, plus weights/bias/M and F in the
    # sidecar JSON. Head vectors use int16 outputs.
    vec = {}
    vec_meta = {}
    xv = x_ev[:a.vectors]
    h_q = scheme["stem"].quantize_input(xv)
    vec["stem_in"] = h_q.astype(np.uint8)
    for name, kind, stride in GRAPH:
        s = scheme[name]
        acc = depthwise_int(h_q, s.w_q, s.bias_q, stride) if kind == "depthwise" \
            else conv2d_int(h_q, s.w_q, s.bias_q, stride)
        out, _clip, _pm = s.requant(acc)
        vec[f"{name}_in"] = h_q.astype(np.uint8)
        vec[f"{name}_out"] = out.astype(np.uint8)
        vec[f"{name}_acc"] = acc.astype(np.int64)
        vec[f"{name}_w"] = s.w_q.astype(np.int8)
        vec_meta[name] = dict(kind=kind, stride=stride, F=s.F,
                              bias_q=s.bias_q.tolist(), M=s.M.tolist(),
                              in_shape=list(h_q.shape), out_shape=list(out.shape))
        h_q = out
    s = scheme[HEAD]
    flat_q = h_q.reshape(h_q.shape[0], -1)
    acc = flat_q.astype(np.int64) @ s.w_q.astype(np.int64) + s.bias_q
    y16v, _c, _p = s.requant(acc)
    vec["head_in"] = flat_q.astype(np.uint8)
    vec["head_out"] = y16v.astype(np.int16)
    vec["head_acc"] = acc.astype(np.int64)
    vec["head_w"] = s.w_q.astype(np.int8)
    vec_meta[HEAD] = dict(kind="dense", F=s.F, bias_q=s.bias_q.tolist(),
                          M=s.M.tolist(), in_shape=list(flat_q.shape),
                          out_shape=list(y16v.shape))
    np.savez_compressed(a.output / "layer_vectors.npz", **vec)
    (a.output / "vectors_meta.json").write_text(
        json.dumps(vec_meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # Raw binary dump for the C testbench (little-endian, x86/ARM LE shared).
    # Manifest line: name kind stride F k N H W C oN oH oW oC
    #   kind in {conv, depthwise, pointwise, dense}; k = kh (== kw);
    #   head is written as dense with H=W=1, C=576.
    # Per layer files: {name}_in.bin(u8) {name}_w.bin(i8) {name}_bias.bin(i64)
    #                  {name}_M.bin(i32) {name}_acc.bin(i64) {name}_out.bin
    #                  (u8, or i16 for dense)
    if a.vectors_c:
        cdir = a.vectors_c
        cdir.mkdir(parents=True, exist_ok=True)
        lines = []
        h_q = scheme["stem"].quantize_input(xv)
        (cdir / "stem_in.bin").write_bytes(np.ascontiguousarray(h_q, np.uint8).tobytes())
        lines.append(f"__stem_input__ input 1 {scheme['stem'].F} 1 "
                     f"{h_q.shape[0]} {h_q.shape[1]} {h_q.shape[2]} {h_q.shape[3]} "
                     f"{h_q.shape[0]} {h_q.shape[1]} {h_q.shape[2]} {h_q.shape[3]}")
        for name, kind, stride in GRAPH:
            s = scheme[name]
            acc = depthwise_int(h_q, s.w_q, s.bias_q, stride) if kind == "depthwise" \
                else conv2d_int(h_q, s.w_q, s.bias_q, stride)
            out, _c2, _p2 = s.requant(acc)
            k = s.w_q.shape[0]
            (cdir / f"{name}_in.bin").write_bytes(np.ascontiguousarray(h_q, np.uint8).tobytes())
            (cdir / f"{name}_w.bin").write_bytes(np.ascontiguousarray(s.w_q, np.int8).tobytes())
            (cdir / f"{name}_bias.bin").write_bytes(np.ascontiguousarray(s.bias_q, np.int64).tobytes())
            (cdir / f"{name}_M.bin").write_bytes(np.ascontiguousarray(s.M, np.int32).tobytes())
            (cdir / f"{name}_acc.bin").write_bytes(np.ascontiguousarray(acc, np.int64).tobytes())
            (cdir / f"{name}_out.bin").write_bytes(np.ascontiguousarray(out, np.uint8).tobytes())
            lines.append(f"{name} {kind} {stride} {s.F} {k} "
                         f"{h_q.shape[0]} {h_q.shape[1]} {h_q.shape[2]} {h_q.shape[3]} "
                         f"{out.shape[0]} {out.shape[1]} {out.shape[2]} {out.shape[3]}")
            h_q = out
        s = scheme[HEAD]
        flat_q = h_q.reshape(h_q.shape[0], -1)
        acc = flat_q.astype(np.int64) @ s.w_q.astype(np.int64) + s.bias_q
        y16v, _c3, _p3 = s.requant(acc)
        (cdir / "head_in.bin").write_bytes(np.ascontiguousarray(flat_q, np.uint8).tobytes())
        (cdir / "head_w.bin").write_bytes(np.ascontiguousarray(s.w_q, np.int8).tobytes())
        (cdir / "head_bias.bin").write_bytes(np.ascontiguousarray(s.bias_q, np.int64).tobytes())
        (cdir / "head_M.bin").write_bytes(np.ascontiguousarray(s.M, np.int32).tobytes())
        (cdir / "head_acc.bin").write_bytes(np.ascontiguousarray(acc, np.int64).tobytes())
        (cdir / "head_out.bin").write_bytes(np.ascontiguousarray(y16v, np.int16).tobytes())
        lines.append(f"head dense 1 {s.F} 1 "
                     f"{flat_q.shape[0]} 1 1 {flat_q.shape[1]} "
                     f"{y16v.shape[0]} 1 1 {y16v.shape[1]}")
        (cdir / "vectors_manifest.txt").write_text("\n".join(lines) + "\n",
                                                   encoding="utf-8")

    scheme_public = {}
    for name, s in scheme.items():
        scheme_public[name] = dict(
            kind=s.kind, F=s.F, M=s.M.tolist(), w_q_shape=list(s.w_q.shape),
            bias_q=s.bias_q.tolist(), x_scale=num_frac(s.x_scale),
            w_scale=[num_frac(v) for v in s.w_scale],
            out_scale=num_frac(s.out_scale),
            acc_bound=s.acc_bound, acc_bits=s.acc_bits, m_bits=s.m_bits,
            product_bits=s.product_bits)
    measured_product_bits = {k: int(np.ceil(np.log2(v["product_max"] + 1))) + 1
                             for k, v in stats.items()}
    report = {
        "purpose": "r2_w8a8_integer_golden_reference_v3",
        "numeric_contract": "integer-only requant y=sat(rne_shift(acc*M,F)); "
                            "RNE after product, saturation after rounding; "
                            "int16 coordinate export with a single per-head "
                            "scale (y in [-32768, 32767])",
        "model": str(a.model), "model_sha256": sha256(a.model),
        "data": str(a.data),
        "data_sha256": sha256(a.data / "dataset.json"),
        "records_sha256": sha256(a.data / "records.jsonl"),
        "reviews_sha256": sha256(a.reviews) if a.reviews else None,
        "script_sha256": sha256(Path(__file__)),
        "fold_vs_original_max_abs_err": fold_err,
        "calibration": {"split": "train", "n": int(len(x_cal)),
                        "maxima": calib_max, "head_absmax": head_max},
        "eval": {"split": "test", "n": int(len(x_ev))},
        "float_metrics": metrics_f,
        "integer_metrics": metrics_q,
        "run_stats": stats,
        "measured_product_bits": measured_product_bits,
        "quant_scheme": scheme_public,
        "int32_scope": "proven only for MAC+bias of these frozen W8/A8 weights "
                       "with full 255-code inputs; not for W12/A16, retrained "
                       "weights, or the acc*M product. product_bits is a "
                       "conservative bound (acc_bits + m_bits); "
                       "measured_product_bits is the observed maximum over "
                       "this eval run and is not a proven minimum either",
    }
    (a.output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    np.savez_compressed(a.output / "quantized_weights.npz",
                        **{f"{k}_wq": s.w_q for k, s in scheme.items()},
                        **{f"{k}_bias_q": s.bias_q for k, s in scheme.items()},
                        **{f"{k}_M": s.M for k, s in scheme.items()})
    np.savez_compressed(a.output / "head_outputs_int16.npz",
                        int16=y16_all, rescaled=preds_q)
    summary = {
        "fold_err": fold_err,
        "float_teacher_pck": metrics_f["teacher_agreement"]["PCK_at_005"],
        "int_teacher_pck": metrics_q["teacher_agreement"]["PCK_at_005"],
        "float_human_pck": (metrics_f["human_accuracy"] or {}).get("PCK_at_005"),
        "int_human_pck": (metrics_q["human_accuracy"] or {}).get("PCK_at_005"),
        "max_acc_bits": max(s.acc_bits for s in scheme.values()),
        "max_product_bits": max(s.product_bits for s in scheme.values()),
        "report": str(a.output / "report.json"),
    }
    print(json.dumps(summary, ensure_ascii=False))


def num_frac(fr):
    return {"num": fr.numerator, "den": fr.denominator}


if __name__ == "__main__":
    main()
