"""Stereo calibration and range estimation from synchronized image pairs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np


@dataclass(frozen=True)
class StereoCalibration:
    """Calibration parameters; all translations use square_size_mm units."""

    image_size: tuple[int, int]  # width, height
    camera_matrix_left: np.ndarray
    distortion_left: np.ndarray
    camera_matrix_right: np.ndarray
    distortion_right: np.ndarray
    rotation: np.ndarray
    translation: np.ndarray
    rectification_left: np.ndarray
    rectification_right: np.ndarray
    projection_left: np.ndarray
    projection_right: np.ndarray
    reprojection_matrix: np.ndarray
    square_size_mm: float
    rms_error: float
    pairs_used: int

    @property
    def baseline_mm(self) -> float:
        return float(np.linalg.norm(self.translation))

    def __post_init__(self) -> None:
        width, height = self.image_size
        if width <= 0 or height <= 0:
            raise ValueError("calibration image size must be positive")
        if not np.isfinite(self.square_size_mm) or self.square_size_mm <= 0:
            raise ValueError("square_size_mm must be finite and positive")
        if self.pairs_used < 1:
            raise ValueError("pairs_used must be positive")
        arrays = (
            self.camera_matrix_left,
            self.distortion_left,
            self.camera_matrix_right,
            self.distortion_right,
            self.rotation,
            self.translation,
            self.rectification_left,
            self.rectification_right,
            self.projection_left,
            self.projection_right,
            self.reprojection_matrix,
        )
        if any(not np.isfinite(np.asarray(value)).all() for value in arrays):
            raise ValueError("calibration contains non-finite values")
        if self.baseline_mm <= 0:
            raise ValueError("stereo baseline must be positive")

    def save(self, path: str | Path) -> None:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            destination,
            image_size=np.asarray(self.image_size, dtype=np.int32),
            camera_matrix_left=np.asarray(self.camera_matrix_left, dtype=np.float64),
            distortion_left=np.asarray(self.distortion_left, dtype=np.float64),
            camera_matrix_right=np.asarray(self.camera_matrix_right, dtype=np.float64),
            distortion_right=np.asarray(self.distortion_right, dtype=np.float64),
            rotation=np.asarray(self.rotation, dtype=np.float64),
            translation=np.asarray(self.translation, dtype=np.float64),
            rectification_left=np.asarray(self.rectification_left, dtype=np.float64),
            rectification_right=np.asarray(self.rectification_right, dtype=np.float64),
            projection_left=np.asarray(self.projection_left, dtype=np.float64),
            projection_right=np.asarray(self.projection_right, dtype=np.float64),
            reprojection_matrix=np.asarray(self.reprojection_matrix, dtype=np.float64),
            square_size_mm=np.asarray(self.square_size_mm, dtype=np.float64),
            rms_error=np.asarray(self.rms_error, dtype=np.float64),
            pairs_used=np.asarray(self.pairs_used, dtype=np.int32),
        )

    @classmethod
    def load(cls, path: str | Path) -> "StereoCalibration":
        source = Path(path)
        if not source.is_file():
            raise FileNotFoundError(f"stereo calibration not found: {source}")
        with np.load(source, allow_pickle=False) as archive:
            return cls(
                image_size=tuple(int(v) for v in archive["image_size"]),
                camera_matrix_left=archive["camera_matrix_left"].copy(),
                distortion_left=archive["distortion_left"].copy(),
                camera_matrix_right=archive["camera_matrix_right"].copy(),
                distortion_right=archive["distortion_right"].copy(),
                rotation=archive["rotation"].copy(),
                translation=archive["translation"].copy(),
                rectification_left=archive["rectification_left"].copy(),
                rectification_right=archive["rectification_right"].copy(),
                projection_left=archive["projection_left"].copy(),
                projection_right=archive["projection_right"].copy(),
                reprojection_matrix=archive["reprojection_matrix"].copy(),
                square_size_mm=float(archive["square_size_mm"]),
                rms_error=float(archive["rms_error"]),
                pairs_used=int(archive["pairs_used"]),
            )


def pair_image_files(
    left_dir: str | Path, right_dir: str | Path
) -> tuple[list[tuple[Path, Path]], list[str]]:
    """Pair stereo calibration images by basename; report unmatched files."""
    extensions = {".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}
    left_root, right_root = Path(left_dir), Path(right_dir)
    if not left_root.is_dir() or not right_root.is_dir():
        raise FileNotFoundError("both left and right calibration directories must exist")
    left = {p.stem: p for p in left_root.iterdir() if p.is_file() and p.suffix.lower() in extensions}
    right = {p.stem: p for p in right_root.iterdir() if p.is_file() and p.suffix.lower() in extensions}
    names = sorted(set(left) & set(right))
    unmatched = sorted(set(left) ^ set(right))
    return [(left[name], right[name]) for name in names], unmatched


def _read_color_image(path: Path) -> np.ndarray:
    raw = np.fromfile(path, dtype=np.uint8)
    image = cv2.imdecode(raw, cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"cannot decode calibration image: {path}")
    return image


def calibrate_stereo_pairs(
    pairs: Iterable[tuple[str | Path, str | Path]],
    *,
    pattern_size: tuple[int, int] = (9, 6),
    square_size_mm: float,
    min_pairs: int = 8,
) -> StereoCalibration:
    """Calibrate synchronized, same-time chessboard image pairs.

    pattern_size is the number of inner corners as (columns, rows). Pairs with
    an undetected chessboard are skipped; at least min_pairs must succeed.
    """
    columns, rows = pattern_size
    if columns < 2 or rows < 2:
        raise ValueError("pattern_size must have at least 2 inner corners per dimension")
    if not np.isfinite(square_size_mm) or square_size_mm <= 0:
        raise ValueError("square_size_mm must be finite and positive")
    if min_pairs < 3:
        raise ValueError("min_pairs must be at least 3")

    object_grid = np.zeros((rows * columns, 3), dtype=np.float32)
    object_grid[:, :2] = np.mgrid[0:columns, 0:rows].T.reshape(-1, 2)
    object_grid *= float(square_size_mm)
    object_points: list[np.ndarray] = []
    left_points: list[np.ndarray] = []
    right_points: list[np.ndarray] = []
    image_size: tuple[int, int] | None = None
    criteria = (
        cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
        100,
        1e-5,
    )
    flags = cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE

    for left_path, right_path in pairs:
        left_image = _read_color_image(Path(left_path))
        right_image = _read_color_image(Path(right_path))
        if left_image.shape != right_image.shape:
            raise ValueError(f"stereo pair dimensions differ: {left_path}, {right_path}")
        height, width = left_image.shape[:2]
        current_size = (width, height)
        if image_size is None:
            image_size = current_size
        elif current_size != image_size:
            raise ValueError("all calibration images must use the same resolution")

        found_left, corners_left = cv2.findChessboardCorners(
            cv2.cvtColor(left_image, cv2.COLOR_BGR2GRAY), pattern_size, flags
        )
        found_right, corners_right = cv2.findChessboardCorners(
            cv2.cvtColor(right_image, cv2.COLOR_BGR2GRAY), pattern_size, flags
        )
        if not found_left or not found_right:
            continue
        corners_left = cv2.cornerSubPix(
            cv2.cvtColor(left_image, cv2.COLOR_BGR2GRAY), corners_left, (11, 11), (-1, -1), criteria
        )
        corners_right = cv2.cornerSubPix(
            cv2.cvtColor(right_image, cv2.COLOR_BGR2GRAY), corners_right, (11, 11), (-1, -1), criteria
        )
        object_points.append(object_grid.copy())
        left_points.append(corners_left)
        right_points.append(corners_right)

    if image_size is None or len(object_points) < min_pairs:
        raise ValueError(
            f"need at least {min_pairs} synchronized pairs with detected chessboards; got {len(object_points)}"
        )

    rms_left, camera_left, dist_left, _, _ = cv2.calibrateCamera(
        object_points, left_points, image_size, None, None
    )
    rms_right, camera_right, dist_right, _, _ = cv2.calibrateCamera(
        object_points, right_points, image_size, None, None
    )
    stereo_criteria = (
        cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
        100,
        1e-5,
    )
    rms_stereo, camera_left, dist_left, camera_right, dist_right, rotation, translation, _, _ = cv2.stereoCalibrate(
        object_points,
        left_points,
        right_points,
        camera_left,
        dist_left,
        camera_right,
        dist_right,
        image_size,
        criteria=stereo_criteria,
        flags=cv2.CALIB_FIX_INTRINSIC,
    )
    rect_left, rect_right, proj_left, proj_right, reprojection, _, _ = cv2.stereoRectify(
        camera_left,
        dist_left,
        camera_right,
        dist_right,
        image_size,
        rotation,
        translation,
        flags=cv2.CALIB_ZERO_DISPARITY,
        alpha=0,
    )
    return StereoCalibration(
        image_size=image_size,
        camera_matrix_left=camera_left,
        distortion_left=dist_left,
        camera_matrix_right=camera_right,
        distortion_right=dist_right,
        rotation=rotation,
        translation=translation,
        rectification_left=rect_left,
        rectification_right=rect_right,
        projection_left=proj_left,
        projection_right=proj_right,
        reprojection_matrix=reprojection,
        square_size_mm=float(square_size_mm),
        rms_error=float(rms_stereo),
        pairs_used=len(object_points),
    )


def depth_from_disparity(
    disparity_px: np.ndarray, focal_length_px: float, baseline_mm: float
) -> np.ndarray:
    """Convert rectified horizontal disparity to depth in mm."""
    if not np.isfinite(focal_length_px) or focal_length_px <= 0:
        raise ValueError("focal_length_px must be finite and positive")
    if not np.isfinite(baseline_mm) or baseline_mm <= 0:
        raise ValueError("baseline_mm must be finite and positive")
    disparity = np.asarray(disparity_px, dtype=np.float32)
    depth = np.full(disparity.shape, np.nan, dtype=np.float32)
    valid = np.isfinite(disparity) & (disparity > 0)
    depth[valid] = (float(focal_length_px) * float(baseline_mm)) / disparity[valid]
    return depth


def median_depth_mm(
    depth_map_mm: np.ndarray, roi: tuple[int, int, int, int] | None = None, min_pixels: int = 16
) -> float | None:
    """Return a robust median over the whole map or an (x,y,w,h) ROI."""
    if min_pixels <= 0:
        raise ValueError("min_pixels must be positive")
    depth = np.asarray(depth_map_mm, dtype=np.float32)
    if depth.ndim != 2 or depth.size == 0:
        raise ValueError("depth_map_mm must be a non-empty 2-D array")
    if roi is not None:
        x, y, width, height = roi
        if width <= 0 or height <= 0:
            raise ValueError("ROI width and height must be positive")
        x1 = max(0, int(x))
        y1 = max(0, int(y))
        x2 = min(depth.shape[1], int(x + width))
        y2 = min(depth.shape[0], int(y + height))
        if x2 <= x1 or y2 <= y1:
            return None
        depth = depth[y1:y2, x1:x2]
    valid = depth[np.isfinite(depth) & (depth > 0)]
    if valid.size < min_pixels:
        return None
    return float(np.median(valid))


class StereoRangeEstimator:
    """Rectify synchronized stereo frames and estimate a robust range."""

    def __init__(
        self,
        calibration: StereoCalibration,
        *,
        num_disparities: int = 64,
        block_size: int = 5,
    ) -> None:
        width, height = calibration.image_size
        if num_disparities <= 0 or num_disparities % 16 != 0:
            raise ValueError("num_disparities must be a positive multiple of 16")
        if num_disparities >= width:
            raise ValueError("num_disparities must be smaller than calibrated image width")
        if block_size < 3 or block_size % 2 == 0:
            raise ValueError("block_size must be an odd integer >= 3")
        self.calibration = calibration
        self._map_left_x, self._map_left_y = cv2.initUndistortRectifyMap(
            calibration.camera_matrix_left,
            calibration.distortion_left,
            calibration.rectification_left,
            calibration.projection_left,
            (width, height),
            cv2.CV_32FC1,
        )
        self._map_right_x, self._map_right_y = cv2.initUndistortRectifyMap(
            calibration.camera_matrix_right,
            calibration.distortion_right,
            calibration.rectification_right,
            calibration.projection_right,
            (width, height),
            cv2.CV_32FC1,
        )
        self._matcher = cv2.StereoSGBM_create(
            minDisparity=0,
            numDisparities=num_disparities,
            blockSize=block_size,
            P1=8 * block_size * block_size,
            P2=32 * block_size * block_size,
            disp12MaxDiff=1,
            uniquenessRatio=10,
            speckleWindowSize=100,
            speckleRange=2,
            mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY,
        )

    def compute_depth(
        self, left_frame: np.ndarray, right_frame: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        if not isinstance(left_frame, np.ndarray) or not isinstance(right_frame, np.ndarray):
            raise TypeError("stereo frames must be NumPy arrays")
        if left_frame.ndim not in (2, 3) or right_frame.ndim not in (2, 3):
            raise ValueError("stereo frames must be grayscale or color images")
        if (left_frame.ndim == 3 and left_frame.shape[2] != 3) or (
            right_frame.ndim == 3 and right_frame.shape[2] != 3
        ):
            raise ValueError("color stereo frames must have three channels")
        if left_frame.dtype != np.uint8 or right_frame.dtype != np.uint8:
            raise ValueError("stereo frames must be uint8")
        width, height = self.calibration.image_size
        if left_frame.shape[:2] != (height, width) or right_frame.shape[:2] != (height, width):
            raise ValueError(f"stereo frames must both have calibrated size {(width, height)}")

        left = cv2.remap(left_frame, self._map_left_x, self._map_left_y, cv2.INTER_LINEAR)
        right = cv2.remap(right_frame, self._map_right_x, self._map_right_y, cv2.INTER_LINEAR)
        if left.ndim == 3:
            left = cv2.cvtColor(left, cv2.COLOR_BGR2GRAY)
        if right.ndim == 3:
            right = cv2.cvtColor(right, cv2.COLOR_BGR2GRAY)
        disparity = self._matcher.compute(left, right).astype(np.float32) / 16.0
        focal_length_px = float(self.calibration.projection_left[0, 0])
        depth = depth_from_disparity(
            disparity, focal_length_px, self.calibration.baseline_mm
        )
        return depth, disparity

    def measure_range_mm(
        self,
        left_frame: np.ndarray,
        right_frame: np.ndarray,
        roi: tuple[int, int, int, int] | None = None,
        min_pixels: int = 16,
    ) -> float | None:
        depth, _ = self.compute_depth(left_frame, right_frame)
        return median_depth_mm(depth, roi=roi, min_pixels=min_pixels)
