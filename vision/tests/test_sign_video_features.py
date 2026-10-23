"""Video feature contract: geometry, missing detections and temporal boundaries."""
import numpy as np
import pytest

from vision.sign_video.features import build_features, feature_schema


def example(n=4):
    pose = np.zeros((n, 33, 4), np.float32)
    pose[..., :2] = [0.5, 0.5]
    pose[..., 3] = 1
    pose[:, 11, :2] = [0.4, 0.4]
    pose[:, 12, :2] = [0.6, 0.4]
    hands = np.zeros((n, 2, 21, 3), np.float32)
    hands[..., 0] = 0.4 + np.arange(21) * 0.005
    hands[..., 1] = 0.5 + np.arange(21) * 0.003
    return pose, hands, np.arange(n) * 0.1


def compute(pose, hands, times, **kwargs):
    return build_features(pose, hands, times, width=640, height=480, **kwargs)


def test_schema_and_translation_scale_invariance():
    pose, hands, times = example()
    result = compute(pose, hands, times)
    assert result["features"].shape == (4, 392)
    assert feature_schema()["dimension"] == 392
    moved_pose, moved_hands = pose.copy(), hands.copy()
    moved_pose[..., :2] = moved_pose[..., :2] * 0.7 + 0.1
    moved_hands[..., :2] = moved_hands[..., :2] * 0.7 + 0.1
    moved = compute(moved_pose, moved_hands, times)
    np.testing.assert_allclose(result["features"], moved["features"], atol=2e-5)


def test_velocity_uses_seconds_and_does_not_bridge_missing_hand():
    pose, hands, times = example()
    hands[1:, 0, :, 0] += 0.02
    expected = compute(pose, hands, times)
    # 0.02 image-width / 0.2 shoulder-width / 0.1 seconds = 1 / second.
    np.testing.assert_allclose(expected["velocity_xy"][1, 9:30, 0], 1, atol=1e-5)
    hands[1, 0] = np.nan
    result = compute(pose, hands, times)
    assert not result["point_valid"][1, 9:30].any()
    assert not result["velocity_valid"][1:3, 9:30].any()
    assert (result["velocity_xy"][1:3, 9:30] == 0).all()
    assert result["velocity_valid"][3, 9:30].all()
    assert np.isfinite(result["features"]).all()


def test_hidden_shoulders_disable_body_but_preserve_local_hand_shape():
    pose, hands, times = example()
    pose[1, 11, 3] = 0.1
    result = compute(pose, hands, times)
    assert not result["body_valid"][1]
    assert not result["point_valid"][1].any()
    assert result["local_hand_valid"][1].all()
    assert result["features"][1, -2:].all()
    hands[2] = np.nan
    result = compute(pose, hands, times)
    assert not result["local_hand_valid"][2].any()
    assert (result["local_hand_xy"][2] == 0).all()


def test_aspect_ratio_correction_and_single_frame():
    pose, hands, times = example(1)
    pose[0, 13, :2] = [0.5, 0.5]
    result = compute(pose, hands, times)
    # Elbow displacement: 0.1 y * 480/640 / 0.2 shoulder width.
    np.testing.assert_allclose(result["normalized_xy"][0, 3], [0, 0.375], atol=1e-6)
    assert not result["velocity_valid"].any()


@pytest.mark.parametrize("times", [[0, 0, 1, 2], [0, 2, 1, 3], [0, 1, 2, np.nan]])
def test_invalid_timestamps_rejected(times):
    pose, hands, _ = example()
    with pytest.raises(ValueError, match="strictly increasing"):
        compute(pose, hands, times)
