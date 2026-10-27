"""R2 golden reference: W8/A8 integer forward of the hand student network.

Pure-numpy fixed-point re-implementation of the float student (BN folded into
convs), used to prove accumulator bit-widths and to validate RTL layer kernels
against an independent software oracle. Follows the R2 gate of
docs/方案/03_Zynq7020独立实时关键点方案.md.

Quantization contract (hand_student_v1.json):
- weights: int8, symmetric, per output channel
- activations: uint8, asymmetric with zero_point=0 (all post-ReLU ranges >= 0);
  clipping at the calibrated max implements the "clipped ReLU chosen by
  calibration" option
- coordinate head output: unclipped int accumulator rescaled to float
- accumulators: int64 in this reference; the per-layer conservative bound
  (full 255 input-code range) is reported so the RTL width can be proven
- requantization rounding: round-half-to-even (np.rint), matching kp_gemm_tile

Nothing here claims the student accuracy is deployable; this is the integer
reference only.
"""
import argparse
import hashlib
import json
import os
import sys
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


# ---------------- float folded model ----------------

def fold_bn(conv_w, bn):
    """Fold BatchNormalization into a conv kernel. conv_w: (kh,kw,cin,cout|1)."""
    g = bn["gamma"].astype(np.float64)
    beta = bn["beta"].astype(np.float64)
    mean = bn["mean"].astype(np.float64)
    var = bn["var"].astype(np.float64)
    s = np.sqrt(var + bn["eps"])
    scale = g / s
    shift = beta - mean * scale
    w = conv_w.astype(np.float64).copy()
    if w.ndim == 4 and w.shape[3] == 1:          # depthwise: per input channel
        w *= scale.reshape(1, 1, -1, 1)
        b = shift
    else:                                        # pointwise/stem/dense: per out channel
        w *= scale.reshape(*([1] * (w.ndim - 1)), -1)
        b = shift
    return w, b


def same_pad(h, k, stride):
    """TensorFlow/Keras 'same' padding: (before, after) per axis."""
    out = -(-h // stride)
    total = max((out - 1) * stride + k - h, 0)
    return total // 2, total - total // 2


def conv2d_float(x, w, b, stride):
    """x [N,H,W,Cin] float, w [kh,kw,Cin,Cout], TF 'same' padding."""
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
    """x [N,H,W,C], w [kh,kw,C,1], TF 'same' padding."""
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


# ---------------- integer forward ----------------

def rne(x):
    """Round half to even, matching the RTL requantizer."""
    return np.rint(x).astype(np.int64)


def conv2d_int(x_q, w_q, b_q, stride):
    """Integer TF-'same' conv by im2col; returns int64 [N,oh,ow,Cout]."""
    n, h, wid, cin = x_q.shape
    kh, kw, _, cout = w_q.shape
    pt, pb = same_pad(h, kh, stride)
    pl, pr = same_pad(wid, kw, stride)
    xp = np.pad(x_q, ((0, 0), (pt, pb), (pl, pr), (0, 0)))
    oh = (h + pt + pb - kh) // stride + 1
    ow = (wid + pl + pr - kw) // stride + 1
    cols = np.lib.stride_tricks.sliding_window_view(
        xp, (kh, kw), axis=(1, 2))[:, ::stride, ::stride]     # [N,oh,ow,Cin,kh,kw]
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
    """x [N,96,96,3] float in [0,1]. Returns (head_out, max_tracker_feed)."""
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


def build_quantizer(weights, calib_max):
    """Per-layer scales from calibration maxima; conservative accumulator bounds."""
    scheme = {}
    prev = "__input__"
    for name, kind, _s in GRAPH:
        w, b = weights[name]
        x_scale = max(calib_max[prev], 1e-12) / 255.0
        if kind == "depthwise":
            absmax = np.max(np.abs(w), axis=(0, 1, 3))
            w_scale = np.maximum(absmax / 127.0, 1e-12)
            w_q = np.rint(w / w_scale.reshape(1, 1, -1, 1)).astype(np.int64)
            sum_wq = np.sum(np.abs(w_q), axis=(0, 1, 3))
        else:
            absmax = np.max(np.abs(w), axis=(0, 1, 2))
            w_scale = np.maximum(absmax / 127.0, 1e-12)
            w_q = np.rint(w / w_scale.reshape(1, 1, 1, -1)).astype(np.int64)
            sum_wq = np.sum(np.abs(w_q), axis=(0, 1, 2))
        bias_q = rne(b / (x_scale * w_scale))
        out_scale = max(calib_max[name], 1e-12) / 255.0
        bound = 255 * sum_wq + np.abs(bias_q)
        scheme[name] = dict(kind=kind, x_scale=x_scale, w_scale=w_scale.tolist(),
                            bias_q=bias_q.tolist(), out_scale=out_scale,
                            acc_bound=int(bound.max()),
                            acc_bits=int(np.ceil(np.log2(int(bound.max()) + 1))) + 1,
                            _w_q=w_q)
        prev = name
    w, b = weights[HEAD]
    x_scale = max(calib_max[prev], 1e-12) / 255.0
    absmax = np.max(np.abs(w), axis=0)
    w_scale = np.maximum(absmax / 127.0, 1e-12)
    w_q = np.rint(w / w_scale.reshape(1, -1)).astype(np.int64)
    bias_q = rne(b / (x_scale * w_scale))
    bound = 255 * np.sum(np.abs(w_q), axis=0) + np.abs(bias_q)
    scheme[HEAD] = dict(kind="dense", x_scale=x_scale, w_scale=w_scale.tolist(),
                        bias_q=bias_q.tolist(), out_scale=None,
                        acc_bound=int(bound.max()),
                        acc_bits=int(np.ceil(np.log2(int(bound.max()) + 1))) + 1,
                        _w_q=w_q)
    return scheme


def quantize_acts(x, scale):
    return np.clip(rne(np.asarray(x, np.float64) / scale), 0, 255).astype(np.int64)


def int_forward(weights, scheme, x_float, collect_err=False):
    h_q = quantize_acts(x_float, scheme["stem"]["x_scale"])
    h_float = x_float
    errs = {}
    for name, kind, stride in GRAPH:
        s = scheme[name]
        w_q = s["_w_q"]
        acc = depthwise_int(h_q, w_q, np.asarray(s["bias_q"]), stride) \
            if kind == "depthwise" else conv2d_int(h_q, w_q, np.asarray(s["bias_q"]), stride)
        w_f, b_f = weights[name]
        ref = depthwise_float(h_float, w_f, b_f, stride) if kind == "depthwise" \
            else conv2d_float(h_float, w_f, b_f, stride)
        y_f = acc * (s["x_scale"] * np.asarray(s["w_scale"]))
        if collect_err:
            errs[name] = float(np.max(np.abs(y_f - ref) /
                                      np.maximum(np.abs(ref), 1e-6)))
        h_q = np.clip(rne(y_f / s["out_scale"]), 0, 255).astype(np.int64)
        h_float = np.maximum(ref, 0)
    s = scheme[HEAD]
    flat_q = h_q.reshape(h_q.shape[0], -1)
    acc = flat_q.astype(np.int64) @ s["_w_q"].astype(np.int64) + np.asarray(s["bias_q"])
    y = acc * (s["x_scale"] * np.asarray(s["w_scale"]))
    return y, errs


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--data", type=Path, required=True)
    p.add_argument("--reviews", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--batch", type=int, default=64)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("output must not exist")
    a.output.mkdir(parents=True)

    import tf_keras as keras
    from vision.keypoints.student_data import load_dataset, augment

    images, y, m, records, data_report = load_dataset(
        a.data, a.reviews, mask_outside_source=True)
    size = 96

    def build_split(split):
        idx = [i for i, r in enumerate(records)
               if r["split"] == split and m[i, :63].any()]
        x = np.stack([augment(images[i], y[i], m[i], size)[0] for i in idx])
        return x, y[idx], m[idx], [records[i] for i in idx]

    x_cal, _, _, _ = build_split("train")
    x_ev, y_ev, m_ev, _r = build_split("test")
    model = keras.models.load_model(a.model, compile=False)
    weights = extract_folded(model)

    # 1) folded-float sanity vs the original model
    probe = x_ev[:16]
    ref_orig = model.predict(probe, verbose=0)
    ref_fold, _ = float_forward(weights, probe)
    fold_err = float(np.max(np.abs(ref_orig - ref_fold)))
    if fold_err > 1e-3:
        raise ValueError(f"BN folding mismatch {fold_err}")

    # 2) calibration maxima on the train split (running max, low memory)
    calib_max = {}
    for i in range(0, len(x_cal), a.batch):
        _out, acts = float_forward(weights, x_cal[i:i + a.batch])
        for k, v in acts.items():
            calib_max[k] = max(calib_max.get(k, 0.0), float(v.max()))
    scheme = build_quantizer(weights, calib_max)

    # 3) integer forward on the eval split, batched, per-layer relative error
    preds_q, errs = [], {}
    for i in range(0, len(x_ev), a.batch):
        out, e = int_forward(weights, scheme, x_ev[i:i + a.batch], collect_err=True)
        preds_q.append(out)
        for k, v in e.items():
            errs.setdefault(k, []).append(v)
    preds_q = np.concatenate(preds_q)
    errs = {k: float(np.max(v)) for k, v in errs.items()}

    # 4) float reference predictions on the same inputs (folding proven above)
    preds_f, _ = float_forward(weights, x_ev)

    def pck_nme(pred, targets, mask):
        vals_p, vals_n = [], []
        for i in range(len(pred)):
            v = mask[i, :63].reshape(21, 3)[:, 0].astype(bool)
            if not v.any():
                continue
            pts = targets[i, :63].reshape(21, 3)[v, :2]
            diag = np.linalg.norm(pts.max(0) - pts.min(0)) + 1e-9
            err = np.linalg.norm(pred[i, :63].reshape(21, 3)[v, :2] - pts, axis=1) / diag
            vals_p.append(float((err <= 0.05).mean()))
            vals_n.append(float(err.mean()))
        return float(np.mean(vals_p)), float(np.mean(vals_n))

    pck_f, nme_f = pck_nme(preds_f, y_ev, m_ev)
    pck_q, nme_q = pck_nme(preds_q, y_ev, m_ev)

    report = {
        "purpose": "r2_w8a8_integer_golden_reference",
        "model": str(a.model), "model_sha256": sha256(a.model),
        "data": str(a.data),
        "data_sha256": sha256(a.data / "dataset.json"),
        "records_sha256": sha256(a.data / "records.jsonl"),
        "fold_vs_original_max_abs_err": fold_err,
        "calibration": {"split": "train", "n": int(len(x_cal)),
                        "maxima": calib_max},
        "eval": {"split": "test", "n": int(len(x_ev))},
        "float": {"pck05": pck_f, "nme": nme_f},
        "integer": {"pck05": pck_q, "nme": nme_q},
        "int_vs_float_max_rel_err_per_layer": errs,
        "quant_scheme": {k: {kk: vv for kk, vv in v.items() if not kk.startswith("_")}
                         for k, v in scheme.items()},
    }
    (a.output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    np.savez_compressed(a.output / "quantized_weights.npz",
                        **{f"{k}_wq": v["_w_q"] for k, v in scheme.items()},
                        **{f"{k}_bias_q": np.asarray(v["bias_q"]) for k, v in scheme.items()})
    print(json.dumps({"fold_err": fold_err, "float_pck": pck_f, "int_pck": pck_q,
                      "float_nme": nme_f, "int_nme": nme_q,
                      "max_acc_bits": max(v["acc_bits"] for v in scheme.values()),
                      "report": str(a.output / "report.json")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
