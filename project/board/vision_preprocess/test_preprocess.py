"""Pixel math, inverse geometry, tensor layout and guarded MMIO API tests."""
from dataclasses import replace
import math
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import preprocess as p


class GeometryTests(unittest.TestCase):
    def test_rgb565_expansion_matches_existing_capture_decoder_for_all_values(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ov5640_snapshot'))
        import capture
        raw = np.arange(65536, dtype='<u2').tobytes()
        job = p.AffineJob(0, 512, 256, 256, 1, 1)
        expected = np.frombuffer(capture.rgb565_to_rgb(raw, 256, 256), dtype=np.uint8).reshape(256, 256, 3)
        np.testing.assert_array_equal(p.expand_rgb565(raw, job), expected)

    def test_letterbox_preserves_aspect_center_and_black_padding(self):
        job = p.letterbox_job(1280, 720)
        self.assertEqual((job.dst_width, job.dst_height), (192, 192))
        self.assertEqual((job.b, job.c, job.d, job.f), (0, 0, 0, -280 * p.Q))
        sx = (job.a * 96 + job.c) / p.Q
        sy = (job.e * 96 + job.f) / p.Q
        self.assertAlmostEqual(sx, 640, places=2)
        self.assertAlmostEqual(sy, 360, places=2)
        raw, stride = p.pack_rgb565_le(np.full((2, 4, 3), 255, dtype=np.uint8))
        out = p.reference_rgb888(raw, p.letterbox_job(4, 2, 4, src_stride=stride))
        self.assertTrue(np.all(out[0] == 0))
        self.assertTrue(np.all(out[1:3, :3] == 255))
        self.assertTrue(np.all(out[3] == 0))

    def test_rotated_roi_inverse_mapping_and_no_half_pixel_shift(self):
        job = p.roi_job(8, 8, (.5, .5, .5, .5, math.pi / 2), 4)
        self.assertEqual(job.coefficients, (0, -p.Q, 6 * p.Q, p.Q, 0, 2 * p.Q))
        full = p.roi_job(224, 224, (.5, .5, 1, 1, 0))
        self.assertEqual(full.coefficients, (p.Q, 0, 0, 0, p.Q, 0))

    def test_bilinear_four_colors_and_individual_black_neighbors(self):
        image = np.array([[[255, 0, 0], [0, 255, 0]], [[0, 0, 255], [255, 255, 255]]], dtype='u1')
        raw, stride = p.pack_rgb565_le(image)
        job = p.affine_job(2, 2, 1, 1, ((1, 0, .5), (0, 1, .5)), src_stride=stride)
        np.testing.assert_array_equal(p.reference_rgb888(raw, job)[0, 0], [128, 128, 128])
        white = np.array([[[255, 255, 255]]], dtype='u1')
        raw, stride = p.pack_rgb565_le(white)
        for coordinate, expected in ((-.5, 64), (-1, 0), (-1 / 64, 255), (-1025 / p.Q, 247)):
            with self.subTest(coordinate=coordinate):
                f = coordinate if coordinate == -.5 else 0
                job = p.affine_job(1, 1, 1, 1, ((0, 0, coordinate), (0, 0, f)), src_stride=stride)
                np.testing.assert_array_equal(p.reference_rgb888(raw, job)[0, 0], [expected] * 3)

    def test_source_padding_is_not_an_image_neighbor(self):
        raw = bytes.fromhex('0000ffff')
        job = p.affine_job(1, 1, 1, 1, ((0, 0, .5), (0, 0, 0)))
        np.testing.assert_array_equal(p.reference_rgb888(raw, job), np.zeros((1, 1, 3), dtype='u1'))

    def test_coordinate_accumulation_does_not_wrap_int32(self):
        raw, stride = p.pack_rgb565_le(np.full((1, 1, 3), 255, dtype='u1'))
        for coefficient in (0x7fffffff, -0x80000000):
            job = p.AffineJob(0, stride, 1, 1, 4, 4, coefficient, coefficient, 0, 0, 0, 0)
            actual = p.reference_rgb888(raw, job)
            self.assertTrue(np.all(actual[0, 0] == 255))
            self.assertTrue(np.all(actual[1:] == 0))
            self.assertTrue(np.all(actual[0, 1:] == 0))

    def test_configuration_validation_and_32bit_end_boundary(self):
        base = p.AffineJob(0, 4, 1, 1, 1, 1)
        self.assertEqual(replace(base, src_base=0xfffffffc).source_bytes, 4)
        for changes in (dict(src_base=1), dict(src_stride=2), dict(src_stride=0),
                        dict(src_width=4097), dict(src_height=0), dict(dst_width=2049),
                        dict(dst_height=0), dict(a=1 << 31), dict(src_width=True),
                        dict(src_base=0xfffffffc, src_height=2)):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(base, **changes)
        for number in (float('nan'), float('inf'), 32768, -32769):
            with self.assertRaises(ValueError):
                p.q16(number)
        for roi in ((.5, .5, 0, 1, 0), (.5, .5, 1, 1, float('nan'))):
            with self.assertRaises(ValueError):
                p.roi_job(720, 1280, roi)

    def test_model_tensor_is_rgb_nhwc_float32_zero_to_one(self):
        raw = bytes([255, 0, 128, 0, 255, 64])
        tensor = p.rgb888_to_model_tensor(raw, 2, 1)
        self.assertEqual(tensor.shape, (1, 1, 2, 3))
        self.assertEqual(tensor.dtype, np.float32)
        self.assertTrue(tensor.flags.c_contiguous)
        np.testing.assert_allclose(tensor[0, 0, 0], [1, 0, 128 / 255], atol=1e-7)
        with self.assertRaises(ValueError):
            p.rgb888_to_model_tensor(raw[:-1], 2, 1)


class MMIO:
    def __init__(self, *, error=0, bytes_out=3, stuck=False):
        self.words = {0x40: p.VERSION, p.STATUS: p.READ_IDLE, p.ERROR: error,
                      p.OUTPUT_BYTES: bytes_out, 0x44: 1, 0x48: 100}
        self.writes, self.now, self.started, self.stuck = [], 0.0, False, stuck

    def read(self, offset):
        if offset == p.STATUS and self.started:
            if self.now >= .002 and not self.stuck:
                self.words[p.STATUS] = p.DONE | p.READ_IDLE | (p.FAILED if self.words[p.ERROR] else 0)
        return self.words.get(offset, 0)

    def write(self, offset, value):
        self.writes.append((offset, value))
        if offset == p.CTRL:
            self.words[p.STATUS], self.started = p.BUSY | p.READ_IDLE, True

    def clock(self):
        return self.now

    def sleep(self, delay):
        self.now += delay


class DriverTests(unittest.TestCase):
    def driver(self, **kwargs):
        mmio = MMIO(**kwargs)
        return mmio, p.Preprocessor(mmio, clock=mmio.clock, sleep=mmio.sleep)

    def start(self, driver, job):
        buffer = SimpleNamespace(physical_address=job.src_base, nbytes=job.source_bytes)
        driver.start(job, source_buffer=buffer, received_bytes=job.source_bytes)
        return buffer

    def test_register_order_signed_coefficients_and_final_byte_count(self):
        mmio, driver = self.driver()
        job = p.affine_job(1, 1, 1, 1, ((0, 0, -.5), (0, 0, 0)), src_base=0x100000)
        self.start(driver, job)
        self.assertEqual([x[0] for x in mmio.writes], list(p.CONFIG_OFFSETS) + [p.CTRL])
        self.assertEqual(mmio.writes[8], (0x30, 0xffff8000))
        self.assertEqual(mmio.writes[-1], (p.CTRL, 3))
        self.assertEqual(driver.wait()['output_bytes'], 3)

    def test_busy_or_outstanding_read_refuses_start_without_writes(self):
        for status in (p.BUSY | p.READ_IDLE, 0):
            mmio, driver = self.driver()
            mmio.words[p.STATUS] = status
            with self.assertRaises(RuntimeError):
                self.start(driver, p.AffineJob(0, 4, 1, 1, 1, 1))
            self.assertEqual(mmio.writes, [])

    def test_error_and_short_byte_count_reject_entire_tensor(self):
        for options in (dict(error=4), dict(bytes_out=2)):
            mmio, driver = self.driver(**options)
            self.start(driver, p.AffineJob(0, 4, 1, 1, 1, 1))
            with self.assertRaises(p.PreprocessError) as context:
                driver.wait()
            self.assertEqual(context.exception.snapshot['output_bytes'], options.get('bytes_out', 3))

    def test_timeout_exposes_state_and_does_not_write_reset_or_free(self):
        mmio, driver = self.driver(stuck=True)
        source = self.start(driver, p.AffineJob(0, 4, 1, 1, 1, 1))
        before = list(mmio.writes)
        with self.assertRaisesRegex(p.PreprocessError, 'keep DMA buffers') as context:
            driver.wait(.003)
        self.assertTrue(context.exception.snapshot['status'] & p.BUSY)
        self.assertEqual(mmio.writes, before)
        self.assertIs(driver.source_buffer, source)

    def test_version_and_wait_arguments_are_guarded(self):
        mmio = MMIO()
        mmio.words[0x40] = 0
        with self.assertRaises(RuntimeError):
            p.Preprocessor(mmio)
        _, driver = self.driver()
        with self.assertRaises(RuntimeError):
            driver.wait()
        self.start(driver, p.AffineJob(0, 4, 1, 1, 1, 1))
        with self.assertRaises(ValueError):
            driver.wait(float('nan'))

    def test_partial_frame_wrong_pointer_or_short_allocation_is_rejected(self):
        mmio, driver = self.driver()
        job = p.AffineJob(0x100000, 4, 1, 1, 1, 1)
        for address, allocated, received in ((job.src_base, 4, 2), (0, 4, 4), (job.src_base, 2, 4)):
            with self.subTest(address=address, received=received), self.assertRaises(ValueError):
                driver.start(job, source_buffer=SimpleNamespace(physical_address=address, nbytes=allocated),
                             received_bytes=received)
        self.assertEqual(mmio.writes, [])


if __name__ == '__main__':
    unittest.main()
