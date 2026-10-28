"""PS job parameters, independent integer oracle and attach-only MMIO control.

No FPGA download, clock change, DMA allocation, or implicit buffer release.
Callers own the input frame and the output DMA until BOTH engines are quiescent.
"""
from dataclasses import dataclass, fields
import math
import time

Q = 1 << 16
VERSION = 0x00010000
CTRL, STATUS, ERROR, OUTPUT_BYTES = 0x00, 0x04, 0x08, 0x0C
BUSY, DONE, FAILED, READ_IDLE = 1, 2, 4, 8
CONFIG_OFFSETS = tuple(range(0x10, 0x40, 4))


def q16(value):
    """Nearest Q16.16, ties toward +infinity, with explicit overflow rejection."""
    value = float(value)
    if not math.isfinite(value):
        raise ValueError('Affine coefficients must be finite')
    result = math.floor(value * Q + 0.5)
    if not -(1 << 31) <= result < (1 << 31):
        raise ValueError('Affine coefficient exceeds signed Q16.16')
    return result


@dataclass(frozen=True)
class AffineJob:
    src_base: int
    src_stride: int
    src_width: int
    src_height: int
    dst_width: int
    dst_height: int
    a: int = Q
    b: int = 0
    c: int = 0
    d: int = 0
    e: int = Q
    f: int = 0

    def __post_init__(self):
        for field in fields(self):
            value = getattr(self, field.name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(field.name + ' must be an integer')
        if not (1 <= self.src_width <= 4096 and 1 <= self.src_height <= 4096):
            raise ValueError('Source dimensions must be 1..4096')
        if not (1 <= self.dst_width <= 2048 and 1 <= self.dst_height <= 2048):
            raise ValueError('Destination dimensions must be 1..2048')
        if not 0 <= self.src_base < (1 << 32) or self.src_base % 4:
            raise ValueError('Source base must be an aligned uint32')
        minimum_stride = (self.src_width * 2 + 3) & ~3
        if not minimum_stride <= self.src_stride < (1 << 32) or self.src_stride % 4:
            raise ValueError('Source stride must contain each aligned RGB565 row')
        if self.src_base + self.source_bytes > (1 << 32):
            raise ValueError('Full source buffer crosses the 32-bit address space')
        if any(not -(1 << 31) <= value < (1 << 31) for value in self.coefficients):
            raise ValueError('Affine coefficients must be signed int32 Q16.16')

    @property
    def coefficients(self):
        return self.a, self.b, self.c, self.d, self.e, self.f

    @property
    def source_bytes(self):
        return self.src_stride * self.src_height

    @property
    def output_bytes(self):
        return self.dst_width * self.dst_height * 3

    @property
    def inverse_matrix(self):
        a, b, c, d, e, f = (value / Q for value in self.coefficients)
        return ((a, b, c), (d, e, f))

    def words(self):
        return tuple(getattr(self, field.name) & 0xFFFFFFFF for field in fields(self))


def affine_job(src_width, src_height, dst_width, dst_height, matrix,
               *, src_base=0, src_stride=None):
    """matrix maps integer output pixel positions to source pixel positions."""
    if len(matrix) != 2 or any(len(row) != 3 for row in matrix):
        raise ValueError('Expected a 2x3 inverse-affine matrix')
    stride = (src_width * 2 + 3) & ~3 if src_stride is None else src_stride
    return AffineJob(src_base, stride, src_width, src_height, dst_width, dst_height,
                     *(q16(value) for row in matrix for value in row))


def letterbox_job(src_width, src_height, size=192, *, src_base=0, src_stride=None):
    """Match the teacher's scale/black-border geometry (no half-pixel shift)."""
    if src_width <= 0 or src_height <= 0 or size <= 0:
        raise ValueError('Positive dimensions required')
    scale = min(size / src_width, size / src_height)
    dx, dy = (size - src_width * scale) / 2, (size - src_height * scale) / 2
    return affine_job(src_width, src_height, size, size,
                      ((1 / scale, 0, -dx / scale), (0, 1 / scale, -dy / scale)),
                      src_base=src_base, src_stride=src_stride)


def roi_job(src_width, src_height, roi, size=224, *, src_base=0, src_stride=None):
    """roi=(center_x,center_y,width,height,rotation_radians), normalized to frame.

    Rotation and crop-to-image mapping follow teacher_geometry.roi_matrix.
    ROI may extend outside the image; each outside bilinear neighbor is black.
    """
    if len(roi) != 5 or not all(math.isfinite(float(value)) for value in roi):
        raise ValueError('ROI must contain five finite values')
    cx, cy, width, height, angle = map(float, roi)
    if src_width <= 0 or src_height <= 0 or size <= 0 or width <= 0 or height <= 0:
        raise ValueError('Positive image, output and ROI dimensions required')
    cosine, sine = math.cos(angle), math.sin(angle)
    a, b = cosine * width * src_width / size, -sine * height * src_height / size
    d, e = sine * width * src_width / size, cosine * height * src_height / size
    c = cx * src_width - (a + b) * size / 2
    f = cy * src_height - (d + e) * size / 2
    return affine_job(src_width, src_height, size, size, ((a, b, c), (d, e, f)),
                      src_base=src_base, src_stride=src_stride)


def pack_rgb565_le(rgb, stride=None):
    """Test/input preparation only: RGB uint8 HWC -> padded RGB565_LE bytes."""
    import numpy as np
    rgb = np.asarray(rgb)
    if rgb.ndim != 3 or rgb.shape[2] != 3 or rgb.dtype != np.uint8:
        raise ValueError('Expected uint8 HWC RGB')
    height, width = rgb.shape[:2]
    minimum = (width * 2 + 3) & ~3
    stride = minimum if stride is None else stride
    if stride < minimum or stride % 4:
        raise ValueError('Invalid row stride')
    p = rgb.astype(np.uint16)
    words = ((p[..., 0] >> 3) << 11) | ((p[..., 1] >> 2) << 5) | (p[..., 2] >> 3)
    rows = np.zeros((height, stride // 2), dtype='<u2')
    rows[:, :width] = words
    return rows.tobytes(), stride


def expand_rgb565(raw, job):
    import numpy as np
    if memoryview(raw).nbytes != job.source_bytes:
        raise ValueError('Input must include every padded RGB565 source row')
    pixels = np.frombuffer(raw, dtype='<u2').reshape(job.src_height, job.src_stride // 2)
    pixels = pixels[:, :job.src_width]
    r, g, b = (pixels >> 11) & 31, (pixels >> 5) & 63, pixels & 31
    return np.stack(((r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2)),
                    axis=-1).astype(np.uint8)


def quantized_maps(job):
    """Signed Q5 source maps, with all arithmetic widened before multiplication."""
    import numpy as np
    y, x = np.indices((job.dst_height, job.dst_width), dtype=np.int64)
    qx = (job.a * x + job.b * y + job.c + 1024) // 2048
    qy = (job.d * x + job.e * y + job.f + 1024) // 2048
    return qx, qy


def reference_rgb888(raw, job):
    """Mathematical integer oracle, independent of the RTL memory/cache FSM."""
    import numpy as np
    source = expand_rgb565(raw, job)
    qx, qy = quantized_maps(job)
    x0, y0, fx, fy = qx // 32, qy // 32, qx & 31, qy & 31
    total = np.zeros((job.dst_height, job.dst_width, 3), dtype=np.int64)
    for dx, dy, weight in ((0, 0, (32 - fx) * (32 - fy)), (1, 0, fx * (32 - fy)),
                            (0, 1, (32 - fx) * fy), (1, 1, fx * fy)):
        x, y = x0 + dx, y0 + dy
        valid = (x >= 0) & (x < job.src_width) & (y >= 0) & (y < job.src_height)
        samples = source[np.clip(y, 0, job.src_height - 1),
                         np.clip(x, 0, job.src_width - 1)].astype(np.int64)
        total += samples * (weight * valid)[..., None]
    return ((total + 512) >> 10).astype(np.uint8)


def rgb888_to_model_tensor(raw, width, height):
    """Pure conversion; caller must first confirm both DMA and IP completion."""
    import numpy as np
    if memoryview(raw).nbytes != width * height * 3:
        raise ValueError('Expected complete tightly packed RGB888 output')
    image = np.frombuffer(raw, dtype=np.uint8).reshape(1, height, width, 3)
    return np.ascontiguousarray(image, dtype=np.float32) / np.float32(255)


class PreprocessError(RuntimeError):
    def __init__(self, message, snapshot):
        super().__init__(message)
        self.snapshot = snapshot


class Preprocessor:
    """Small MMIO driver. Does not own, stop, or free any DMA buffer.

    Configure the output S2MM DMA first. After wait(), also confirm DMA IOC/Idle
    and invalidate its buffer before reading it. An error rejects the ENTIRE
    tensor. A timeout requires hardware quiescence checks; never free on timeout.
    """
    def __init__(self, mmio, *, clock=time.monotonic, sleep=time.sleep):
        self.mmio, self.clock, self.sleep, self.job = mmio, clock, sleep, None
        self.source_buffer = None
        if self.mmio.read(0x40) != VERSION:
            raise RuntimeError('Unsupported vision_preprocess_axi register version')

    def snapshot(self):
        return dict(status=self.mmio.read(STATUS), error_code=self.mmio.read(ERROR),
                    output_bytes=self.mmio.read(OUTPUT_BYTES),
                    read_transactions=self.mmio.read(0x44), cycles=self.mmio.read(0x48))

    def start(self, job, *, source_buffer, received_bytes):
        if not isinstance(job, AffineJob):
            raise ValueError('Expected a validated AffineJob')
        if (int(getattr(source_buffer, 'physical_address', -1)) != job.src_base
                or int(getattr(source_buffer, 'nbytes', 0)) < job.source_bytes):
            raise ValueError('Job must refer to the retained complete source DMA buffer')
        if isinstance(received_bytes, bool) or not isinstance(received_bytes, int) or received_bytes != job.source_bytes:
            raise ValueError('Only a fully received source frame may be submitted')
        status = self.mmio.read(STATUS)
        if status & BUSY or not status & READ_IDLE:
            raise RuntimeError('Preprocessor/read adapter is not idle')
        for offset, word in zip(CONFIG_OFFSETS, job.words()):
            self.mmio.write(offset, word)
        self.job = job
        self.source_buffer = source_buffer  # Keep this reference on errors/timeouts too.
        self.mmio.write(CTRL, 3)  # START + CLEAR_STATUS; START takes precedence.

    def wait(self, timeout=5, poll_interval=0.001):
        if self.job is None:
            raise RuntimeError('No job was started')
        if not math.isfinite(timeout) or timeout <= 0 or not math.isfinite(poll_interval) or poll_interval <= 0:
            raise ValueError('Positive finite timeout and polling interval required')
        deadline = self.clock() + timeout
        while True:
            status = self.mmio.read(STATUS)
            if status & DONE and not status & BUSY:
                result = self.snapshot()
                if status & FAILED or result['error_code']:
                    raise PreprocessError('Preprocessor failed; reject entire output tensor', result)
                if not status & READ_IDLE or result['output_bytes'] != self.job.output_bytes:
                    raise PreprocessError('Incomplete preprocessor output or pending AXI read', result)
                return result
            if self.clock() >= deadline:
                raise PreprocessError('Preprocessor timeout; keep DMA buffers until quiescence is confirmed',
                                      self.snapshot())
            self.sleep(poll_interval)
