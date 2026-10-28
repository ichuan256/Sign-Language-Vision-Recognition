"""Equivalence to the old exhaustive candidate loop, including threshold ties."""
import unittest
from unittest.mock import patch

import numpy as np
import teacher_geometry as geometry


def assert_detections_equal(actual, expected):
    if len(actual) != len(expected):
        raise AssertionError('Detection count changed')
    for a, b in zip(actual, expected):
        if a['score'] != b['score']:
            raise AssertionError('Score changed')
        for key in ('box', 'keypoints'):
            if a[key].dtype != b[key].dtype or not np.array_equal(a[key], b[key], equal_nan=True):
                raise AssertionError(key + ' changed')


class PalmEquivalence(unittest.TestCase):
    def check_case(self, scores, padding=(0., .21875, 0., .21875), threshold=.5):
        rng = np.random.default_rng(321)
        encoded = rng.normal(size=(1, 2016, 18)).astype(scores.dtype)
        encoded[..., 2:4] = 24.  # overlapping boxes exercise weighted NMS
        outputs = [encoded, scores.reshape(1, 2016, 1)]
        with np.errstate(over='ignore', invalid='ignore'):
            actual = geometry.decode_palms(outputs, padding, threshold)
            with patch.object(geometry, '_palm_candidate_indices',
                              lambda logits, unused: np.flatnonzero(logits > -100.)):
                expected = geometry.decode_palms(outputs, padding, threshold)
        assert_detections_equal(actual, expected)
        return actual

    def test_threshold_adjacent_and_nonfinite(self):
        for dtype in (np.float32, np.float64):
            scores = np.full(2016, -20., dtype)
            tiny = np.nextafter(dtype(0), dtype(1))
            scores[:18] = [-np.inf, -101., -100., -99.9, -1.001, -1.,
                          np.nextafter(dtype(-1), dtype(0)), -1e-6, -1e-9,
                          -tiny, -0., 0., tiny, 1e-9, 1., 100., np.inf, np.nan]
            with self.subTest(dtype=dtype):
                self.check_case(scores)

    def test_no_hands_and_many_tied_candidates(self):
        self.check_case(np.full(2016, -8., np.float32))
        scores = np.full(2016, -8., np.float32)
        scores[800:824] = .7
        self.check_case(scores)

    def test_seeded_mixed_inputs(self):
        for seed in range(8):
            rng = np.random.default_rng(seed)
            scores = rng.normal(-6., 1.5, 2016).astype(np.float32)
            scores[rng.choice(2016, 18, replace=False)] = rng.uniform(-1.1, 4., 18)
            with self.subTest(seed=seed):
                self.check_case(scores, padding=(.1, 0., .1, 0.))

    def test_other_thresholds_use_original_semantics(self):
        scores = np.full(2016, -100., np.float32)
        scores[:16] = np.linspace(-12, 5, 16)
        for threshold in (-1., 0., .1, .49, .50001, .9, 1., 2., np.nan):
            with self.subTest(threshold=threshold):
                self.check_case(scores, threshold=threshold)

    def test_float16_retains_original_scalar_behavior(self):
        scores = np.full(2016, -12., np.float16)
        scores[:8] = [-1., -.001, -.00001, -0., 0., .001, 1., 5.]
        self.check_case(scores)


if __name__ == '__main__':
    unittest.main()
