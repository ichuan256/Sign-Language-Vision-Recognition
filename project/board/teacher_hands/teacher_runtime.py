"""Small ctypes binding to the unmodified TFLite ARMv7 runtime."""
import ctypes as C
from pathlib import Path
import time
import numpy as np

_FLOAT = np.dtype(np.float32)

class TFLiteModel:
    def __init__(self, library, model, threads=2):
        self.lib = C.CDLL(str(Path(library).resolve()))
        self.lib.hands_tflite_create.argtypes = [C.c_char_p, C.c_int]
        self.lib.hands_tflite_create.restype = C.c_void_p
        self.lib.hands_tflite_destroy.argtypes = [C.c_void_p]
        self.lib.hands_tflite_input_count.argtypes = [C.c_void_p]
        self.lib.hands_tflite_output_count.argtypes = [C.c_void_p, C.c_int]
        self.lib.hands_tflite_input_dims.argtypes = [C.c_void_p, C.POINTER(C.c_int), C.c_int]
        self.lib.hands_tflite_output_dims.argtypes = [C.c_void_p, C.c_int, C.POINTER(C.c_int), C.c_int]
        self.lib.hands_tflite_invoke.argtypes = [C.c_void_p, C.POINTER(C.c_float), C.c_size_t,
            C.POINTER(C.c_float), C.c_size_t, C.c_int]
        self.lib.hands_tflite_read_output.argtypes = [C.c_void_p, C.POINTER(C.c_float), C.c_size_t, C.c_int]
        self.handle = self.lib.hands_tflite_create(str(Path(model)).encode(), threads)
        if not self.handle:
            raise RuntimeError(f"TFLite model could not be loaded: {model}")
        self.input_shape = self._dims(self.lib.hands_tflite_input_dims, None)
        self.input_count = self.lib.hands_tflite_input_count(self.handle)
        self.output_counts = [self.lib.hands_tflite_output_count(self.handle, i) for i in range(4)]
        self.output_shapes = [self._dims(self.lib.hands_tflite_output_dims, i) if n > 0 else []
                              for i, n in enumerate(self.output_counts)]
        if self.input_count <= 0 or self.output_counts[0] <= 0:
            self.close()
            raise RuntimeError("Unexpected TFLite input/output contract")

    def _dims(self, function, output_index):
        dims = (C.c_int * 4)()
        args = (self.handle,) if output_index is None else (self.handle, output_index)
        rank = function(*args, dims, 4)
        if rank < 0:
            raise RuntimeError("Cannot query TFLite tensor shape")
        return list(dims[:rank])

    def invoke(self, image):
        image = np.ascontiguousarray(image, dtype=_FLOAT)
        if image.size != self.input_count:
            raise ValueError(f"Expected {self.input_count} floats, got {image.size}")
        scratch = np.empty(self.output_counts[0], dtype=_FLOAT)
        code = self.lib.hands_tflite_invoke(self.handle,
            image.ctypes.data_as(C.POINTER(C.c_float)), image.size,
            scratch.ctypes.data_as(C.POINTER(C.c_float)), scratch.size, 0)
        if code:
            raise RuntimeError(f"TFLite invoke failed: {code}")
        outputs = [scratch.reshape(self.output_shapes[0])]
        for index in range(1, len(self.output_counts)):
            count = self.output_counts[index]
            if count <= 0:
                break
            output = np.empty(count, dtype=_FLOAT)
            code = self.lib.hands_tflite_read_output(self.handle,
                output.ctypes.data_as(C.POINTER(C.c_float)), count, index)
            if code:
                raise RuntimeError(f"TFLite output read failed: {code}")
            outputs.append(output.reshape(self.output_shapes[index]))
        return outputs

    def benchmark(self, repeat=5):
        image = np.zeros(self.input_shape, dtype=_FLOAT)
        start = time.perf_counter()
        outputs = self.invoke(image)
        setup_s = time.perf_counter() - start
        durations = []
        for _ in range(repeat):
            start = time.perf_counter()
            outputs = self.invoke(image)
            durations.append(time.perf_counter() - start)
        return outputs, dict(first_invoke_s=setup_s, invoke_s=durations,
            input_shape=self.input_shape, output_shapes=self.output_shapes)

    def close(self):
        handle = getattr(self, "handle", None)
        if handle:
            self.lib.hands_tflite_destroy(handle)
            self.handle = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
