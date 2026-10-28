import unittest

from test_capture import c


class DmaLengthTests(unittest.TestCase):
    def test_loss_threshold_is_strict_and_rgb565_byte_counts_are_checked(self):
        self.assertTrue(c.pixel_loss_metrics(192, expected_bytes=200)["accepted"])
        at_limit = c.pixel_loss_metrics(190, expected_bytes=200)
        self.assertFalse(at_limit["accepted"])
        self.assertEqual(at_limit["loss_percent"], 5.0)
        malformed = c.pixel_loss_metrics(191, expected_bytes=200)
        self.assertFalse(malformed["accepted"])
        self.assertEqual(malformed["invalid_reason"], "incomplete_rgb565_pixel")

    def test_complete_frame_is_decided_from_dma_byte_count(self):
        metrics = c.pixel_loss_metrics(c.FRAME_BYTES)
        self.assertTrue(metrics["accepted"])
        self.assertEqual(metrics["received_bytes"], c.FRAME_BYTES)


if __name__ == "__main__":
    unittest.main()
