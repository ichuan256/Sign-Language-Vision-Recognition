from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import cv2
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from signrec.stereo import (  # noqa: E402
    StereoCalibration,
    StereoRangeEstimator,
    calibrate_stereo_pairs,
    depth_from_disparity,
    median_depth_mm,
    pair_image_files,
)


def calibration(width: int = 128, height: int = 96) -> StereoCalibration:
    camera = np.asarray(
        [[100.0, 0.0, width / 2], [0.0, 100.0, height / 2], [0.0, 0.0, 1.0]],
        dtype=np.float64,
    )
    projection_left = np.hstack((camera, np.zeros((3, 1), dtype=np.float64)))
    projection_right = projection_left.copy()
    projection_right[0, 3] = -6000.0
    return StereoCalibration(
        image_size=(width, height),
        camera_matrix_left=camera,
        distortion_left=np.zeros((1, 5), dtype=np.float64),
        camera_matrix_right=camera.copy(),
        distortion_right=np.zeros((1, 5), dtype=np.float64),
        rotation=np.eye(3, dtype=np.float64),
        translation=np.asarray([[-60.0], [0.0], [0.0]], dtype=np.float64),
        rectification_left=np.eye(3, dtype=np.float64),
        rectification_right=np.eye(3, dtype=np.float64),
        projection_left=projection_left,
        projection_right=projection_right,
        reprojection_matrix=np.eye(4, dtype=np.float64),
        square_size_mm=20.0,
        rms_error=0.2,
        pairs_used=10,
    )


def _render_synthetic_board(
    board: np.ndarray,
    object_corners: np.ndarray,
    camera: np.ndarray,
    distortion: np.ndarray,
    rvec: np.ndarray,
    tvec: np.ndarray,
    image_size: tuple[int, int],
) -> np.ndarray:
    board_height, board_width = board.shape[:2]
    source_corners = np.asarray(
        [[0, 0], [board_width - 1, 0], [board_width - 1, board_height - 1], [0, board_height - 1]],
        dtype=np.float32,
    )
    projected, _ = cv2.projectPoints(object_corners, rvec, tvec, camera, distortion)
    transform = cv2.getPerspectiveTransform(source_corners, projected.reshape(4, 2).astype(np.float32))
    warped = cv2.warpPerspective(
        board, transform, image_size, borderMode=cv2.BORDER_CONSTANT, borderValue=127
    )
    return cv2.cvtColor(warped, cv2.COLOR_GRAY2BGR)


def test_calibrate_synthetic_stereo_pairs_recovers_baseline(tmp_path: Path) -> None:
    width, height = 640, 480
    inner_columns, inner_rows = 7, 5
    square_px, square_mm, baseline_mm = 64, 20.0, 60.0
    board = np.zeros(((inner_rows + 1) * square_px, (inner_columns + 1) * square_px), dtype=np.uint8)
    for row in range(inner_rows + 1):
        for column in range(inner_columns + 1):
            value = 255 if (row + column) % 2 else 0
            board[row * square_px : (row + 1) * square_px, column * square_px : (column + 1) * square_px] = value

    outer_corners = np.asarray(
        [
            [-square_mm, -square_mm, 0.0],
            [inner_columns * square_mm, -square_mm, 0.0],
            [inner_columns * square_mm, inner_rows * square_mm, 0.0],
            [-square_mm, inner_rows * square_mm, 0.0],
        ],
        dtype=np.float32,
    )
    camera = np.asarray(
        [[800.0, 0.0, width / 2], [0.0, 800.0, height / 2], [0.0, 0.0, 1.0]],
        dtype=np.float64,
    )
    distortion = np.zeros((1, 5), dtype=np.float64)
    left_dir, right_dir = tmp_path / "left", tmp_path / "right"
    left_dir.mkdir()
    right_dir.mkdir()
    pairs = []
    poses = [
        (0.00, 0.00, 0.00, -80.0, -60.0, 600.0),
        (0.25, 0.10, 0.05, -70.0, -50.0, 620.0),
        (-0.20, 0.25, -0.05, -90.0, -60.0, 650.0),
        (0.15, -0.25, 0.08, -75.0, -70.0, 580.0),
        (-0.25, -0.20, 0.10, -80.0, -40.0, 640.0),
        (0.20, -0.15, -0.12, -85.0, -55.0, 680.0),
        (-0.12, 0.18, 0.14, -65.0, -70.0, 610.0),
        (0.28, 0.22, -0.08, -95.0, -65.0, 700.0),
        (-0.18, -0.28, 0.06, -70.0, -45.0, 590.0),
        (0.10, 0.30, -0.15, -88.0, -50.0, 660.0),
    ]
    for index, (rx, ry, rz, tx, ty, tz) in enumerate(poses):
        rvec = np.asarray([rx, ry, rz], dtype=np.float64)
        tvec_left = np.asarray([tx, ty, tz], dtype=np.float64)
        tvec_right = tvec_left + np.asarray([-baseline_mm, 0.0, 0.0])
        left_image = _render_synthetic_board(
            board, outer_corners, camera, distortion, rvec, tvec_left, (width, height)
        )
        right_image = _render_synthetic_board(
            board, outer_corners, camera, distortion, rvec, tvec_right, (width, height)
        )
        left_path, right_path = left_dir / f"{index:02d}.png", right_dir / f"{index:02d}.png"
        assert cv2.imwrite(str(left_path), left_image)
        assert cv2.imwrite(str(right_path), right_image)
        pairs.append((left_path, right_path))

    result = calibrate_stereo_pairs(
        pairs,
        pattern_size=(inner_columns, inner_rows),
        square_size_mm=square_mm,
        min_pairs=8,
    )

    assert result.pairs_used >= 8
    assert result.baseline_mm == pytest.approx(baseline_mm, abs=4.0)


def test_printable_stereo_checkerboard_matches_calibration_defaults() -> None:
    svg_path = ROOT / "models" / "stereo_checkerboard_9x6_20mm.svg"
    root = ET.parse(svg_path).getroot()
    assert root.attrib["width"] == "230mm"
    assert root.attrib["height"] == "180mm"
    black_squares = [
        node for node in root.iter()
        if node.tag.endswith("rect") and node.attrib.get("fill") == "#000"
    ]
    assert len(black_squares) == 35
    assert all(square.attrib["width"] == "20" and square.attrib["height"] == "20" for square in black_squares)


def test_depth_from_disparity_returns_millimeters_and_masks_invalid() -> None:
    disparity = np.asarray([[30.0, 0.0, -1.0, np.nan]], dtype=np.float32)

    depth = depth_from_disparity(disparity, focal_length_px=500.0, baseline_mm=60.0)

    assert depth[0, 0] == pytest.approx(1000.0)
    assert np.isnan(depth[0, 1:]).all()


def test_median_depth_mm_uses_roi_and_minimum_valid_count() -> None:
    depth = np.asarray([[1000, 4000, np.nan], [1200, 5000, np.nan]], dtype=np.float32)

    assert median_depth_mm(depth, roi=(0, 0, 1, 2), min_pixels=2) == pytest.approx(1100.0)
    assert median_depth_mm(depth, roi=(2, 0, 1, 2), min_pixels=1) is None


def test_calibration_round_trips_without_pickle(tmp_path: Path) -> None:
    original = calibration()
    path = tmp_path / "calibration.npz"

    original.save(path)
    restored = StereoCalibration.load(path)

    assert restored.image_size == original.image_size
    assert restored.baseline_mm == pytest.approx(60.0)
    assert restored.pairs_used == 10
    assert np.allclose(restored.projection_left, original.projection_left)


def test_pair_image_files_matches_names_and_reports_unmatched(tmp_path: Path) -> None:
    left = tmp_path / "left"
    right = tmp_path / "right"
    left.mkdir()
    right.mkdir()
    (left / "0001.png").write_bytes(b"left")
    (left / "0002.png").write_bytes(b"left")
    (right / "0001.png").write_bytes(b"right")
    (right / "0003.png").write_bytes(b"right")

    pairs, unmatched = pair_image_files(left, right)

    assert len(pairs) == 1
    assert pairs[0][0].name == pairs[0][1].name == "0001.png"
    assert unmatched == ["0002", "0003"]


def test_calibrate_requires_enough_detected_chessboard_pairs(tmp_path: Path) -> None:
    left = tmp_path / "left.png"
    right = tmp_path / "right.png"
    blank = np.zeros((120, 160, 3), dtype=np.uint8)
    assert cv2.imwrite(str(left), blank)
    assert cv2.imwrite(str(right), blank)

    with pytest.raises(ValueError, match="need at least"):
        calibrate_stereo_pairs([(left, right)], square_size_mm=20.0, min_pairs=3)


def test_sgbm_depth_recovers_known_synthetic_disparity() -> None:
    width, height, disparity_px = 320, 240, 12
    estimator = StereoRangeEstimator(calibration(width, height), num_disparities=64, block_size=5)
    rng = np.random.default_rng(7)
    left = rng.integers(0, 256, (height, width, 3), dtype=np.uint8)
    right = np.zeros_like(left)
    right[:, :-disparity_px] = left[:, disparity_px:]

    depth, disparity = estimator.compute_depth(left, right)
    roi = (80, 40, 160, 160)

    assert np.nanmedian(disparity[40:200, 80:240]) == pytest.approx(disparity_px, abs=1.0)
    assert median_depth_mm(depth, roi=roi, min_pixels=100) == pytest.approx(500.0, abs=60.0)


def test_stereo_range_estimator_rejects_non_image_frames() -> None:
    estimator = StereoRangeEstimator(calibration(), num_disparities=16, block_size=3)
    valid = np.zeros((96, 128, 3), dtype=np.uint8)
    with pytest.raises(TypeError, match="NumPy arrays"):
        estimator.compute_depth(None, valid)
    with pytest.raises(ValueError, match="three channels"):
        estimator.compute_depth(np.zeros((96, 128, 4), dtype=np.uint8), valid)


def test_stereo_range_estimator_checks_calibrated_resolution() -> None:
    estimator = StereoRangeEstimator(calibration(), num_disparities=16, block_size=3)
    wrong = np.zeros((48, 64, 3), dtype=np.uint8)

    with pytest.raises(ValueError, match="calibrated size"):
        estimator.compute_depth(wrong, wrong)
