# -*- coding: utf-8 -*-
"""sherpa-ncnn 对比测试：ncnn 的 ARM32 NEON 优化远好于 onnxruntime，
模型同为 zipformer-zh-14M（ncnn 原版），目标是 RTF 压到 1 以下。"""
import sys, time
import numpy as np, wave
import sherpa_ncnn

M = "sherpa-ncnn-streaming-zipformer-zh-14M-2023-02-23"
print("加载 ncnn 模型...")
t0 = time.perf_counter()
rec = sherpa_ncnn.Recognizer(
    tokens=f"{M}/tokens.txt",
    encoder_param=f"{M}/encoder_jit_trace-pnnx.ncnn.param",
    encoder_bin=f"{M}/encoder_jit_trace-pnnx.ncnn.bin",
    decoder_param=f"{M}/decoder_jit_trace-pnnx.ncnn.param",
    decoder_bin=f"{M}/decoder_jit_trace-pnnx.ncnn.bin",
    joiner_param=f"{M}/joiner_jit_trace-pnnx.ncnn.param",
    joiner_bin=f"{M}/joiner_jit_trace-pnnx.ncnn.bin",
    num_threads=2,
)
print(f"模型就绪（{time.perf_counter()-t0:.1f}s）")

def read_wav(path):
    with wave.open(path, 'rb') as w:
        fr, nfr = w.getframerate(), w.getnframes()
        d = np.frombuffer(w.readframes(nfr), dtype=np.int16).astype(np.float32) / 2**15
    return d, fr

for path in sys.argv[1:]:
    d, fr = read_wav(path)
    d = np.concatenate([d, np.zeros(int(fr * 0.8), dtype=np.float32)])
    t0 = time.perf_counter()
    rec.accept_waveform(fr, d)
    rec.input_finished()
    dt = time.perf_counter() - t0
    print(f"{path.split('/')[-1]} -> {rec.text!r}  RTF={dt/(len(d)/fr):.2f}")
    rec.reset()
