"""Versioned 2-D temporal features with explicit missing-data masks.

Coordinates use image-width units for both axes, avoiding aspect-ratio distortion.
No mirroring, rotation alignment, interpolation or hand-identity swapping is done.
"""
import numpy as np

VERSION = "sign_xy_v1"
POSE_IDS = (0, 11, 12, 13, 14, 15, 16, 23, 24)
POINT_NAMES = tuple(f"pose_{i}" for i in POSE_IDS) + tuple(
    f"{hand}_{i}" for hand in ("left_hand", "right_hand") for i in range(21)
)
N_POINTS = len(POINT_NAMES)


def feature_schema():
    names = [f"{p}_{axis}" for p in POINT_NAMES for axis in ("x", "y")]
    names += [f"{p}_velocity_{axis}" for p in POINT_NAMES for axis in ("x", "y")]
    names += [f"{hand}_{i}_local_{axis}" for hand in ("left_hand", "right_hand")
              for i in range(21) for axis in ("x", "y")]
    names += [f"{p}_valid" for p in POINT_NAMES]
    names += [f"{p}_velocity_valid" for p in POINT_NAMES]
    names += ["left_hand_local_valid", "right_hand_local_valid"]
    return {"version": VERSION, "dimension": len(names), "names": names,
            "point_names": list(POINT_NAMES), "coordinates": "2D, image y points down"}


def build_features(pose, hands, timestamps, *, width, height, visibility=0.5):
    """pose[T,33,4]=x,y,z,visibility; hands[T,2,21,3]=x,y,z.

    Missing landmarks must be NaN. Body coordinates need both visible shoulders.
    Local hand shape uses its own wrist and wrist-to-middle-MCP scale, and can
    remain valid when shoulders are missing. Velocity never crosses a missing frame.
    """
    pose = np.asarray(pose, dtype=np.float32)
    hands = np.asarray(hands, dtype=np.float32)
    times = np.asarray(timestamps, dtype=np.float64)
    n = len(times)
    if pose.shape != (n, 33, 4) or hands.shape != (n, 2, 21, 3) or n == 0:
        raise ValueError("nonempty aligned pose[T,33,4], hands[T,2,21,3] required")
    if not np.isfinite(times).all() or np.any(np.diff(times) <= 0):
        raise ValueError("timestamps must be finite and strictly increasing")
    if not np.isfinite([width, height]).all() or width <= 0 or height <= 0 or not 0 <= visibility <= 1:
        raise ValueError("invalid image dimensions or visibility threshold")
    xy = np.concatenate((pose[:, POSE_IDS, :2], hands[..., :2].reshape(n, 42, 2)), axis=1)
    xy[..., 1] *= height / width
    valid = np.isfinite(xy).all(axis=-1)
    valid[:, :len(POSE_IDS)] &= pose[:, POSE_IDS, 3] >= visibility
    shoulders = pose[:, (11, 12), :2].copy()
    shoulders[..., 1] *= height / width
    scale = np.linalg.norm(shoulders[:, 0] - shoulders[:, 1], axis=-1)
    body_valid = (np.isfinite(shoulders).all(axis=(1, 2)) &
                  (pose[:, (11, 12), 3] >= visibility).all(axis=1) & (scale > 1e-4))
    origin = shoulders.mean(axis=1)
    safe_scale = np.where(body_valid, scale, 1)
    normalized = (xy - origin[:, None, :]) / safe_scale[:, None, None]
    valid &= body_valid[:, None]
    normalized = np.where(valid[..., None], normalized, 0).astype(np.float32)
    velocity = np.zeros_like(normalized)
    velocity_valid = np.zeros_like(valid)
    if n > 1:
        velocity_valid[1:] = valid[1:] & valid[:-1]
        delta = np.diff(normalized, axis=0) / np.diff(times)[:, None, None]
        velocity[1:] = np.where(velocity_valid[1:, :, None], delta, 0)
    local = hands[..., :2].copy()
    local[..., 1] *= height / width
    local_scale = np.linalg.norm(local[:, :, 9] - local[:, :, 0], axis=-1)
    hand_valid = np.isfinite(local).all(axis=(2, 3)) & (local_scale > 1e-4)
    local = (local - local[:, :, :1]) / np.where(hand_valid, local_scale, 1)[:, :, None, None]
    local = np.where(hand_valid[:, :, None, None], local, 0).astype(np.float32)
    # Failed local hand shapes have explicit masks in the feature vector too.
    features = np.concatenate((normalized.reshape(n, -1), velocity.reshape(n, -1),
                               local.reshape(n, -1), valid, velocity_valid, hand_valid), axis=1).astype(np.float32)
    return {"features": features, "normalized_xy": normalized, "velocity_xy": velocity,
            "point_valid": valid, "velocity_valid": velocity_valid,
            "local_hand_xy": local, "local_hand_valid": hand_valid,
            "body_valid": body_valid, "body_origin": origin,
            "body_scale": scale}
