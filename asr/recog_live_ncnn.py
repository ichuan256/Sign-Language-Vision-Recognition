# -*- coding: utf-8 -*-
"""板端实时整句识别（ncnn 内核 · 定案版 2026-10-15）
LINE IN 录音 → sherpa-ncnn zipformer-zh-14M → 打印文字 + RTF
用法（PYNQ ssh / Jupyter Terminal，在 ~/asr_offline 下）：
    python3 recog_live_ncnn.py [录音秒数，默认 4]
实测 RTF：ncnn 双线程 ≈1.05~1.15（onnx 1.9~2.1，fp32 2.5 已淘汰）
关键：录音结束后补 0.8s 静音再 flush（PC 实测不补会吞尾词）。
"""
import sys, time
import numpy as np
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

# ---- 录音（base overlay 的 ADAU1761，48kHz/24bit 立体声）----
secs = float(sys.argv[1]) if len(sys.argv) > 1 else 4.0
from pynq.overlays.base import BaseOverlay
base = BaseOverlay("base.bit")
base.audio.select_line_in()
print(f"开始录音 {secs}s，请对着麦克风说话...")
base.audio.record(secs)
base.audio.save("_live.wav")
print("录音完成")

# ---- wav → float32 单声道（24bit 解析，MAX9814 接左声道）----
import wave
with wave.open("_live.wav", "rb") as w:
    nch, sw, fr, nfr = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
    raw = w.readframes(nfr)
a = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
b = np.zeros((a.shape[0], 4), dtype=np.uint8)
b[:, 1:] = a
d = (b.view("<i4").reshape(-1) >> 8).astype(np.float32) / 2**23
if nch == 2:
    d = d[0::2]

# ---- 识别（尾部补静音，见头部注释）----
d = np.concatenate([d, np.zeros(int(fr * 0.8), dtype=np.float32)])
t0 = time.perf_counter()
rec.accept_waveform(fr, d)
rec.input_finished()
dt = time.perf_counter() - t0
dur = len(d) / fr
print(f"识别结果: {rec.text!r}")
print(f"音频 {dur:.2f}s / 解码 {dt:.2f}s → RTF={dt/dur:.2f}")
