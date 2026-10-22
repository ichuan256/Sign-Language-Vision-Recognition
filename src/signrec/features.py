"""OpenCV-DNN MobileNetV2 features for complete video frames."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BACKBONE_PATH = (
    _REPO_ROOT
    / "models"
    / "image_classification_mobilenet"
    / "image_classification_mobilenetv2_2022apr_int8bq.onnx"
)
DEFAULT_FEATURE_LAYER = "onnx_node!GlobalAveragePool_97"
DEFAULT_INPUT_SIZE = 224
_RGB_MEAN = np.asarray([0.485, 0.456, 0.406], dtype=np.float32)
_RGB_STD = np.asarray([0.229, 0.224, 0.225], dtype=np.float32)


def preprocess_full_frame(
    frame: np.ndarray, input_size: int = DEFAULT_INPUT_SIZE
) -> np.ndarray:
    """Letterbox a complete BGR frame into a normalized NCHW RGB tensor.

    Padding is set to the ImageNet mean so it normalizes to zero. The frame is
    never center-cropped or geometrically stretched.
    """
    if not isinstance(frame, np.ndarray):
        raise TypeError("frame must be a NumPy array")
    if frame.ndim != 3 or frame.shape[2] != 3 or frame.dtype != np.uint8:
        raise ValueError("frame must be a uint8 three-channel BGR image")
    if frame.shape[0] <= 0 or frame.shape[1] <= 0:
        raise ValueError("frame must not be empty")
    if input_size <= 0:
        raise ValueError("input_size must be positive")

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    height, width = rgb.shape[:2]
    scale = min(input_size / width, input_size / height)
    resized_width = max(1, min(input_size, int(round(width * scale))))
    resized_height = max(1, min(input_size, int(round(height * scale))))
    interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
    resized = cv2.resize(rgb, (resized_width, resized_height), interpolation=interpolation)

    canvas = np.empty((input_size, input_size, 3), dtype=np.float32)
    canvas[:] = _RGB_MEAN
    left = (input_size - resized_width) // 2
    top = (input_size - resized_height) // 2
    canvas[top : top + resized_height, left : left + resized_width] = (
        resized.astype(np.float32) / 255.0
    )

    normalized = (canvas - _RGB_MEAN) / _RGB_STD
    return np.transpose(normalized, (2, 0, 1))[None, ...].astype(np.float32, copy=False)


class MobileNetV2Embedder:
    """Extract one normalized visual feature vector per complete frame."""

    def __init__(
        self,
        model_path: str | Path = DEFAULT_BACKBONE_PATH,
        feature_layer: str = DEFAULT_FEATURE_LAYER,
        input_size: int = DEFAULT_INPUT_SIZE,
    ) -> None:
        self.model_path = Path(model_path)
        if not self.model_path.is_file():
            raise FileNotFoundError(f"MobileNetV2 ONNX backbone not found: {self.model_path}")
        if not hasattr(cv2, "dnn"):
            raise RuntimeError("this OpenCV build has no DNN module")
        if input_size <= 0:
            raise ValueError("input_size must be positive")
        self.feature_layer = feature_layer
        self.input_size = input_size
        self._net = cv2.dnn.readNet(str(self.model_path))
        self._net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        self._net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
        if self._net.getLayerId(feature_layer) <= 0:
            raise ValueError(f"feature layer is not present in ONNX model: {feature_layer}")

    def embed_frame(self, frame: np.ndarray) -> np.ndarray:
        tensor = preprocess_full_frame(frame, self.input_size)
        self._net.setInput(tensor)
        feature = self._net.forward(self.feature_layer).reshape(-1).astype(np.float32)
        if feature.size == 0 or not np.isfinite(feature).all():
            raise RuntimeError("backbone produced an empty or non-finite feature vector")
        norm = float(np.linalg.norm(feature))
        if norm <= 1e-12:
            return np.zeros_like(feature)
        return feature / norm

    def embed_frames(self, frames: np.ndarray) -> np.ndarray:
        if not isinstance(frames, np.ndarray) or frames.ndim != 4 or frames.shape[-1] != 3:
            raise ValueError("frames must have shape (T, H, W, 3)")
        if frames.shape[0] == 0:
            raise ValueError("frames must contain at least one frame")
        return np.stack([self.embed_frame(frame) for frame in frames], axis=0)
