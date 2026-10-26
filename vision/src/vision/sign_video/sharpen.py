"""Bit-exact CPU reference for a small candidate FPGA sharpening kernel.

out = clip(floor((4*C + q*(4*C-N-S-E-W) + 2) / 4), 0, 255)
q=0/1/2 gives strength 0/0.25/0.5. Border pixels pass through unchanged.
Independent 8-bit channels; signed int16 intermediates (range -2040..3060
before rounding for supported q). No resize, denoise or colour conversion.
"""
import numpy as np


def sharpen_u8(image, quarter_strength=1):
    if quarter_strength not in (0, 1, 2):
        raise ValueError("quarter_strength must be 0, 1 or 2")
    image = np.asarray(image)
    if image.dtype != np.uint8 or image.ndim not in (2, 3):
        raise ValueError("expected uint8 grayscale or multichannel image")
    out = image.copy()
    if quarter_strength == 0 or min(image.shape[:2]) < 3:
        return out
    src = image.astype(np.int16)
    center = src[1:-1, 1:-1]
    neighbours = src[:-2, 1:-1] + src[2:, 1:-1] + src[1:-1, :-2] + src[1:-1, 2:]
    value = (4 * center + quarter_strength * (4 * center - neighbours) + 2) // 4
    out[1:-1, 1:-1] = np.clip(value, 0, 255).astype(np.uint8)
    return out
