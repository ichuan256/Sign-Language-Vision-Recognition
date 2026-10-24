# -*- coding: utf-8 -*-
"""R3.1 历史基线复跑（QKeras W4/A6 小 CNN，旧实验名 w4a4）。

输入契约（对应 hls4ml 友好的结构）：64×64 灰度帧 × 8 帧均匀抽样，
8 帧作为输入通道（64×64×8）——纯 Conv2D 结构，无时序层。
词表：清单中片段数 >= 4 的类别；按类别分层 75/25 划分训练/测试。
缓存：_tmp/r3/tensors.npz（帧张量与标签，重跑不重复解码视频）。

用法（仓库根）：
  F:\\PLD\\.venv-r3\\Scripts\\python.exe -X utf8 scripts/r3/r3_baseline_20261024.py [--epochs 30]
"""
import argparse
import json
import os
import time
from pathlib import Path

os.environ.setdefault("TF_USE_LEGACY_KERAS", "1")  # QKeras 0.9 依赖 Keras 2（tf-keras）

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "_tmp" / "r3"
MANIFEST = ROOT / "data" / "manifests" / "manifest_fullframe_20261024.csv"


def build_tensors(min_per_class: int = 4, sample_count: int = 8, size: int = 64):
    """精剪片段 → (N, 64, 64, 8) uint8 张量 + 标签。"""
    import csv
    import cv2  # 延迟导入，便于先看缓存

    sys_path_sep = ";"
    rows = list(csv.DictReader(open(MANIFEST, encoding="utf-8-sig")))
    by_label = {}
    for r in rows:
        by_label.setdefault(r["类别"], []).append(r["输出路径"])
    labels = sorted(l for l, v in by_label.items() if len(v) >= min_per_class)
    print(f"类别数（>={min_per_class}条）: {len(labels)}")
    label_idx = {l: i for i, l in enumerate(labels)}

    X, y, meta = [], [], []
    for label in labels:
        for rel in by_label[label]:
            path = ROOT / rel
            if not path.is_file():
                print("缺:", rel)
                continue
            cap = cv2.VideoCapture(str(path))
            total = int(round(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
            idxs = [int(round(i * (total - 1) / (sample_count - 1))) for i in range(sample_count)]
            frames = []
            fi = 0
            want = set(idxs)
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                if fi in want:
                    g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    frames.append(cv2.resize(g, (size, size), interpolation=cv2.INTER_AREA))
                fi += 1
            cap.release()
            if len(frames) < sample_count:
                while len(frames) < sample_count:
                    frames.append(frames[-1])
            X.append(np.stack(frames, axis=-1))  # 64×64×8
            y.append(label_idx[label])
            meta.append({"label": label, "path": rel})
    X = np.stack(X)
    y = np.asarray(y, dtype=np.int64)
    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE / "tensors.npz", X=X, y=y,
                        labels=np.asarray(labels), meta=json.dumps(meta, ensure_ascii=False))
    return X, y, labels, meta


def make_model(num_classes: int, size: int = 64, frames: int = 8, mode: str = "quant"):
    from tensorflow.keras import Input, Model
    from tensorflow.keras.layers import BatchNormalization, Conv2D, Dense, GlobalAveragePooling2D, MaxPooling2D, ReLU
    from qkeras import QActivation, QConv2D, QDense

    quant = mode == "quant"
    Conv = QConv2D if quant else Conv2D
    kw = dict(kernel_quantizer="quantized_bits(4,0)", bias_quantizer="quantized_bits(4,0)") if quant else {}
    Act = (lambda name: QActivation("quantized_relu(6,2)", name=name)) if quant else (lambda name: ReLU(name=name))

    inp = Input((size, size, frames))
    x = Conv(16, 3, padding="same", name="conv1", **kw)(inp)
    x = BatchNormalization()(x)
    x = Act("act1")(x)
    x = MaxPooling2D()(x)
    x = Conv(32, 3, padding="same", name="conv2", **kw)(x)
    x = BatchNormalization()(x)
    x = Act("act2")(x)
    x = MaxPooling2D()(x)
    x = Conv(64, 3, padding="same", name="conv3", **kw)(x)
    x = BatchNormalization()(x)
    x = Act("act3")(x)
    x = MaxPooling2D()(x)
    x = Conv(64, 3, padding="same", name="conv4", **kw)(x)
    x = BatchNormalization()(x)
    x = Act("act4")(x)
    x = GlobalAveragePooling2D()(x)
    if quant:
        out = QDense(num_classes, kernel_quantizer="quantized_bits(4,0)",
                     bias_quantizer="quantized_bits(4,0)", name="qdense")(x)
    else:
        out = Dense(num_classes, name="dense")(x)
    return Model(inp, out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--mode", choices=["quant", "float"], default="quant")
    ap.add_argument("--rebuild", action="store_true", help="忽略缓存重新解码视频")
    args = ap.parse_args()

    import tensorflow as tf
    tf.get_logger().setLevel("ERROR")

    if not args.rebuild and (CACHE / "tensors.npz").is_file():
        d = np.load(CACHE / "tensors.npz", allow_pickle=False)
        X, y, labels = d["X"], d["y"], list(d["labels"])
        print(f"缓存命中: {X.shape}, {len(labels)} 类")
    else:
        X, y, labels, _ = build_tensors()
        print(f"张量: {X.shape}, {len(labels)} 类")

    # 分层划分：每类最后 25% 做测试（≥1 条）
    rng = np.random.default_rng(20261024)
    train_idx, test_idx = [], []
    for c in np.unique(y):
        idx = np.where(y == c)[0]
        rng.shuffle(idx)
        n_test = max(1, len(idx) // 4)
        test_idx.extend(idx[:n_test])
        train_idx.extend(idx[n_test:])
    Xtr, Xte = X[train_idx].astype(np.float32) / 255.0, X[test_idx].astype(np.float32) / 255.0
    ytr, yte = y[train_idx], y[test_idx]
    print(f"训练 {len(Xtr)} / 测试 {len(Xte)}")

    model = make_model(len(labels), mode=args.mode)
    model.compile(optimizer="adam", loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True), metrics=["accuracy"])
    t0 = time.time()
    model.fit(Xtr, ytr, validation_data=(Xte, yte), epochs=args.epochs,
              batch_size=32, verbose=2)
    loss, acc = model.evaluate(Xte, yte, verbose=0)
    tr_loss, tr_acc = model.evaluate(Xtr, ytr, verbose=0)
    print(f"\n=== R3.1 基线（{args.mode} 小 CNN, {len(labels)} 类）===")
    print(f"测试 top-1 准确率: {acc:.4f}  训练: {tr_acc:.4f}  用时 {time.time()-t0:.0f}s")
    CACHE.mkdir(exist_ok=True)
    model.save(CACHE / f"r3_model_{args.mode}.keras")
    (CACHE / f"r3_baseline_{args.mode}.json").write_text(json.dumps({
        "classes": len(labels), "train": len(Xtr), "test": len(Xte),
        "test_top1": round(float(acc), 4), "train_top1": round(float(tr_acc), 4),
        "epochs": args.epochs, "mode": args.mode, "seconds": round(time.time() - t0),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("模型与结果存于 _tmp/r3/")


if __name__ == "__main__":
    main()
