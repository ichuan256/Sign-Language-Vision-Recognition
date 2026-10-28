"""Color, buffer ownership, failure cleanup and attach-only preview tests."""
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

try:
    import numpy as np
except ImportError:
    np = None

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hdmi_preview as hp
from test_continuous_capture import Fake


class Frame(np.ndarray if np is not None else object):
    def __new__(cls, shape, owner, index):
        value = np.zeros(shape, dtype=np.uint8).view(cls)
        value.physical_address = 0x2000000 + index * 0x10000
        value.owner, value.index, value.freed = owner, index, False
        return value

    def __array_finalize__(self, value):
        if value is not None:
            self.owner = getattr(value, 'owner', None)
            self.index = getattr(value, 'index', -1)

    def flush(self):
        if not self.owner.halted and self.index == self.owner.active:
            raise AssertionError('Writing to the active display buffer')
        self.owner.events.append(('flush', self.index))

    def freebuffer(self):
        if not self.owner.halted:
            raise AssertionError('Free before HDMI DMA Halted')
        self.freed = True
        self.owner.events.append(('free', self.index))


class DisplayHardware:
    def __init__(self):
        self.now, self.halted = 0.0, True
        self.registers, self.events, self.frames = {}, [], []
        self.active, self.desired, self.park_reads = 0, 0, 0
        self.stuck_swap, self.stuck_halt, self.error = False, False, 0

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds

    def allocate(self, shape, dtype):
        frame = Frame(shape, self, len(self.frames))
        self.frames.append(frame)
        return frame

    def read(self, offset):
        if offset == 4:
            return int(self.halted) | self.error
        if offset == 0x28:
            self.park_reads += 1
            if not self.stuck_swap and self.park_reads >= 2:
                self.active = self.desired
            return self.desired | (self.active << 16)
        return self.registers.get(offset, 0)

    def write(self, offset, value):
        self.events.append(('write', offset, value))
        self.registers[offset] = value
        if offset == 0:
            if value & 1:
                self.halted = False
            elif not self.stuck_halt:
                self.halted = True
        elif offset == 0x28:
            self.desired, self.park_reads = value & 0x1f, 0

    def display(self, **kwargs):
        return hp.BoundedDisplay(self, self.allocate, width=4, height=2,
                                 timeout=0.003, clock=self.clock, sleep=self.sleep,
                                 **kwargs)


@unittest.skipIf(np is None, 'Preview colors require NumPy; use board or bundled Python')
class ColorTests(unittest.TestCase):
    def test_every_rgb565_value_matches_existing_reference(self):
        raw = np.arange(65536, dtype='<u2').tobytes()
        destination = np.zeros((256, 256, 3), dtype=np.uint8)
        hp.rgb565_to_bgr(raw, destination, 256, 256)
        reference = np.frombuffer(hp.c.rgb565_to_rgb(raw, 256, 256), dtype=np.uint8)
        np.testing.assert_array_equal(destination, reference.reshape(256, 256, 3)[..., ::-1])
        np.testing.assert_array_equal(destination.reshape(-1, 3)[[0xf800, 0x07e0, 0x001f]],
                                      [[0, 0, 255], [0, 255, 0], [255, 0, 0]])

    def test_partial_input_and_wrong_destination_are_rejected(self):
        for raw, destination in ((b'\0', np.zeros((2, 4, 3), dtype='u1')),
                                 (bytes(16), np.zeros((2, 4, 3), dtype='u2')),
                                 (bytes(16), np.zeros((4, 2, 3), dtype='u1'))):
            with self.subTest(size=len(raw)), self.assertRaises(ValueError):
                hp.rgb565_to_bgr(raw, destination, 4, 2)

    def test_camera_only_manifest_is_rejected(self):
        good = dict(firmware_name='ov5640_snapshot_hdmi', design=dict(hp.HDMI_DESIGN))
        hp.verify_hdmi_manifest(good)
        for key in hp.HDMI_DESIGN:
            bad = dict(good, design={k: v for k, v in good['design'].items() if k != key})
            with self.subTest(key=key), self.assertRaises(hp.c.CaptureError):
                hp.verify_hdmi_manifest(bad)


@unittest.skipIf(np is None, 'Preview buffers require NumPy; use board or bundled Python')
class DisplayTests(unittest.TestCase):
    def test_swaps_use_inactive_buffers_and_short_frame_keeps_previous(self):
        hardware, raw = DisplayHardware(), bytes.fromhex('00f8') * 8
        display = hardware.display()
        with patch.object(hp.c, 'FRAME_BYTES', 16):
            display.start()
            row = dict(received_bytes=16)
            display.on_frame(raw, row)
            self.assertEqual((row['display_slot'], hardware.active), (1, 1))
            np.testing.assert_array_equal(display.frames[1][0, 0], [0, 0, 255])
            before = len(hardware.events)
            display.on_frame(raw, dict(received_bytes=14))
            self.assertEqual(len(hardware.events), before)
            self.assertEqual(display.result['skipped_partial'], 1)
            display.on_frame(raw, dict(received_bytes=16))
            self.assertEqual(hardware.active, 2)
            self.assertEqual(display.result['displayed_frames'], 2)
            display.close()
        self.assertTrue(display.safe)
        self.assertTrue(all(frame.freed for frame in hardware.frames))
        self.assertTrue(display.result['hdmi_shutdown_confirmed'])

    def test_swap_timeout_is_bounded_and_can_cleanly_halt(self):
        hardware = DisplayHardware()
        display = hardware.display()
        display.start()
        hardware.stuck_swap = True
        with patch.object(hp.c, 'FRAME_BYTES', 16), self.assertRaises(TimeoutError):
            display.on_frame(bytes(16), dict(received_bytes=16))
        self.assertLess(hardware.now, 0.01)
        self.assertEqual(display.result['display_errors'], 1)
        display.close()
        self.assertTrue(all(frame.freed for frame in hardware.frames))

    def test_halt_timeout_retains_every_frame(self):
        hardware = DisplayHardware()
        display = hardware.display()
        display.start()
        hardware.stuck_halt = True
        with self.assertRaises(TimeoutError):
            display.close()
        self.assertFalse(display.safe)
        self.assertTrue(display.result['unsafe_hdmi'])
        self.assertFalse(any(frame.freed for frame in hardware.frames))
        self.assertEqual(len(display.frames), 4)

    def test_interrupt_is_a_stop_and_dma_error_is_a_display_error(self):
        for interrupt in (True, False):
            with self.subTest(interrupt=interrupt):
                hardware, stop = DisplayHardware(), [False]
                display = hardware.display(stop_requested=lambda: stop[0])
                display.start()
                stop[0] = interrupt
                hardware.error = 0 if interrupt else 0x40
                with patch.object(hp.c, 'FRAME_BYTES', 16), self.assertRaises(hp.cc.Stopped if interrupt else RuntimeError):
                    display.on_frame(bytes(16), dict(received_bytes=16))
                self.assertEqual(display.result['display_errors'], int(not interrupt))
                display.close()


class CallbackTests(unittest.TestCase):
    def test_notebook_hash_matches_current_helper(self):
        path = Path(hp.cc.__file__).with_suffix('.ipynb')
        notebook = json.loads(path.read_text(encoding='utf-8'))
        expected = hp.c.sha256(hp.cc.__file__)
        self.assertEqual(notebook['metadata']['ov5640_helper_sha256'], expected)
        code = ''.join(line for cell in notebook['cells'] for line in cell.get('source', []))
        self.assertIn(f"EXPECTED_HELPER_SHA256 = '{expected}'", code)

    def session(self, directory, fake, callback, **kwargs):
        return hp.cc.CaptureSession(fake.ctrl, fake.dma, fake.allocate, Path(directory),
            seconds=0, max_attempts=kwargs.pop('max_attempts', 1), max_samples=0,
            frame_timeout=0.006, init_timeout=0.02, cleanup_timeout=0.003,
            settle_seconds=0, clock=fake.clock, sleep=fake.sleep, on_frame=callback, **kwargs)

    def test_callback_only_after_halt_and_invalidate(self):
        fake, calls = Fake(), []
        def callback(buffer, row):
            self.assertTrue(fake.halted)
            self.assertEqual(buffer.invalidates, 1)
            self.assertFalse(buffer.freed)
            calls.append(row['received_bytes'])
        with tempfile.TemporaryDirectory() as directory, patch.object(hp.c, 'FRAME_BYTES', 16):
            result = self.session(directory, fake, callback).run()
        self.assertEqual(calls, [16])
        self.assertTrue(result['dma_shutdown_confirmed'])
        self.assertTrue(fake.buffer.freed)

    def test_callback_failure_does_not_misreport_unsafe_camera_dma(self):
        fake = Fake()
        def failed(*_):
            raise RuntimeError('display failed')
        with tempfile.TemporaryDirectory() as directory, patch.object(hp.c, 'FRAME_BYTES', 16):
            result = self.session(directory, fake, failed).run()
            row = json.loads((Path(directory) / 'attempts.jsonl').read_text())
        self.assertEqual(result['stop_reason'], 'display_error')
        self.assertEqual(result['display_errors'], 1)
        self.assertTrue(row['dma_shutdown_confirmed'])
        self.assertIn('display failed', row['display_error'])
        self.assertFalse(result['unsafe_dma'])
        self.assertTrue(fake.buffer.freed)

    def test_rejected_or_unsafe_frames_never_reach_callback(self):
        for fake in (Fake(['short']), Fake(['timeout'], unsafe=True)):
            with self.subTest(mode=fake.outcomes), tempfile.TemporaryDirectory() as directory:
                calls = []
                with patch.object(hp.c, 'FRAME_BYTES', 16):
                    result = self.session(directory, fake, lambda *_: calls.append(True)).run()
                self.assertEqual(calls, [])
                self.assertEqual(fake.buffer.freed, not result['unsafe_dma'])

    def test_partial_acceptance_policy_is_preserved_and_callback_sees_length(self):
        fake, calls = Fake(['loss4']), []
        with tempfile.TemporaryDirectory() as directory, patch.object(hp.c, 'FRAME_BYTES', 200):
            result = self.session(directory, fake, lambda buffer, row: calls.append(row['received_bytes'])).run()
        self.assertEqual(result['accepted_loss_frames'], 1)
        self.assertEqual(calls, [192])


@unittest.skipIf(np is None, 'Preview integration mocks require NumPy; use board or bundled Python')
class PreviewTests(unittest.TestCase):
    def run_mock(self, root, *, unsafe=False, startup_error=False, frequency=100,
                 frontend_error=False, startup_interrupt=False):
        fake, hardware = Fake(), DisplayHardware()
        display = hardware.display()
        if frontend_error:
            def failed_stop():
                raise RuntimeError('frontend stop failed')
            display.frontend_stop = failed_stop
        lock = SimpleNamespace(acquire=lambda: lock, release=lambda: setattr(lock, 'released', True), released=False)
        overlay = SimpleNamespace(ip_dict={
            name: dict(phys_addr=address, type='xilinx.com:ip:' + kind + ':1.0')
            for name, address, kind in [('capture_dma', hp.c.DMA_BASE, 'axi_dma'),
                                        ('camera_control', hp.c.CONTROL_BASE, 'axi_gpio')]})
        attached = []
        def attach(*args, **kwargs):
            attached.append(kwargs)
            return overlay
        pynq = SimpleNamespace(Overlay=attach, Clocks=SimpleNamespace(fclk0_mhz=frequency),
            MMIO=lambda address, _: fake.ctrl if address == hp.c.CONTROL_BASE else fake.dma,
            allocate=fake.allocate)
        metadata = dict(firmware_name='ov5640_snapshot_hdmi', design=dict(hp.HDMI_DESIGN), files={})
        saved_read = Path.read_text
        def read(path, *args, **kwargs):
            if path.as_posix() in ('/proc/sys/kernel/random/boot_id', '/run/ov5640_snapshot_download_attempted'):
                return 'this-boot'
            return saved_read(path, *args, **kwargs)
        def configure():
            display.start()
            hardware.stuck_halt = unsafe
            if startup_error:
                raise RuntimeError('configuration failed')
            if startup_interrupt:
                raise hp.cc.Stopped()
        with patch.object(hp.c, 'FRAME_BYTES', 16), patch.object(hp.c, 'verify_manifest', return_value=(metadata, {'bit': Path('test.bit')})), \
             patch.object(hp.cc, 'ProcessLock', return_value=lock), patch.object(hp.cc, 'competing_processes', return_value=[]), \
             patch.object(hp, 'make_display', return_value=(display, configure)), patch.object(Path, 'read_text', read), \
             patch.dict(sys.modules, {'pynq': pynq}):
            result = hp.run_preview(root / 'run', assume_cold_boot=True, seconds=0, max_attempts=1,
                max_samples=0, settle_seconds=0, clock=fake.clock, sleep=fake.sleep,
                frame_timeout=0.006, init_timeout=0.02, cleanup_timeout=0.003)
        return result, lock, hardware, attached

    def tearDown(self):
        # Unsafe mocks contain no real DMA; release references only in tests.
        hp.UNSAFE_PREVIEWS.clear()

    def test_attach_only_complete_preview_and_safe_release(self):
        with tempfile.TemporaryDirectory() as directory:
            result, lock, hardware, attached = self.run_mock(Path(directory))
            artifact = json.loads((Path(directory) / 'run/preview_results.json').read_text())
        self.assertEqual(attached, [dict(download=False)])
        self.assertTrue(result['preview_completed_without_errors'])
        self.assertEqual(artifact['display']['displayed_frames'], 1)
        self.assertFalse(result['physical_fps_measured'])
        self.assertTrue(lock.released)
        self.assertTrue(all(frame.freed for frame in hardware.frames))

    def test_unsafe_hdmi_retains_process_lock_and_buffers(self):
        with tempfile.TemporaryDirectory() as directory:
            result, lock, hardware, _ = self.run_mock(Path(directory), unsafe=True)
        self.assertEqual(result['stop_reason'], 'hdmi_cleanup_error')
        self.assertFalse(lock.released)
        self.assertFalse(any(frame.freed for frame in hardware.frames))
        self.assertEqual(len(hp.UNSAFE_PREVIEWS), 1)
        self.assertFalse(result['preview_completed_without_errors'])

    def test_bad_startup_records_error_and_releases_halted_display(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, 'configuration failed'):
                self.run_mock(Path(directory), startup_error=True)
            result = json.loads((Path(directory) / 'run/preview_results.json').read_text())
        self.assertEqual(result['stop_reason'], 'startup_error')
        self.assertIn('configuration failed', result['error'])
        self.assertTrue(result['display']['hdmi_shutdown_confirmed'])

    def test_confirmation_and_previous_unsafe_session_gate_before_hardware(self):
        with self.assertRaisesRegex(RuntimeError, 'assume_cold_boot'):
            hp.run_preview('unused')
        with patch.object(hp, 'UNSAFE_PREVIEWS', [object()]), self.assertRaisesRegex(RuntimeError, 'Previous DMA'):
            hp.run_preview('unused', assume_cold_boot=True)

    def test_frontend_cleanup_failure_cannot_report_success(self):
        with tempfile.TemporaryDirectory() as directory:
            result, lock, hardware, _ = self.run_mock(Path(directory), frontend_error=True)
        self.assertEqual(result['stop_reason'], 'hdmi_cleanup_error')
        self.assertIn('frontend stop failed', result['error'])
        self.assertFalse(result['preview_completed_without_errors'])
        self.assertTrue(result['display']['hdmi_shutdown_confirmed'])
        self.assertTrue(lock.released)
        self.assertTrue(all(frame.freed for frame in hardware.frames))

    def test_interrupt_during_startup_returns_clean_interrupted_result(self):
        with tempfile.TemporaryDirectory() as directory:
            result, lock, hardware, _ = self.run_mock(Path(directory), startup_interrupt=True)
        self.assertEqual(result['stop_reason'], 'interrupted')
        self.assertIsNone(result['error'])
        self.assertTrue(lock.released)
        self.assertTrue(all(frame.freed for frame in hardware.frames))


if __name__ == '__main__':
    unittest.main()
