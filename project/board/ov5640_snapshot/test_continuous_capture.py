"""Deterministic MMIO tests; no PYNQ import, board access, or FPGA download."""
import importlib.util
import json
from pathlib import Path
import signal
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import continuous_capture as cc


class Buffer(bytearray):
    physical_address = 0x01000000
    freed = False

    def flush(self):
        self.flushes = getattr(self, "flushes", 0) + 1

    def invalidate(self):
        self.invalidates = getattr(self, "invalidates", 0) + 1

    def freebuffer(self):
        self.freed = True


class Fake:
    def __init__(self, outcomes=("valid",), unsafe=False, slow=0.001):
        self.outcomes, self.unsafe, self.slow = list(outcomes), unsafe, slow
        self.now, self.control_value, self.cr, self.halted = 0.0, 0, 0, True
        self.frame, self.polls, self.mode, self.heartbeat = -1, 0, None, 0
        self.initialized, self.sticky, self.allocations = False, False, 0
        self.arm_values, self.events, self.buffer = [], [], None
        self.ctrl = SimpleNamespace(read=self.control_read, write=self.control_write)
        self.dma = SimpleNamespace(read=self.dma_read, write=self.dma_write)

    def clock(self):
        return self.now

    def sleep(self, duration):
        self.now += max(duration, self.slow)

    def allocate(self, **kwargs):
        self.allocations += 1
        self.buffer = Buffer(cc.c.FRAME_BYTES)
        return self.buffer

    def control_write(self, offset, value):
        self.events.append(("ctrl", offset, value))
        if offset:
            return
        previous = self.control_value
        self.control_value = value
        if value == 0:
            self.initialized, self.sticky, self.mode = False, False, None
        elif value & 3 == 3:
            self.initialized = True
        elif self.initialized and value & 3 == 1 and (value ^ previous) & 4:
            if self.sticky:
                raise AssertionError("Rearmed a sticky packet error without camera reset")
            self.frame += 1
            self.mode = self.outcomes[min(self.frame, len(self.outcomes) - 1)]
            self.polls = 0
            self.arm_values.append(value & 4)
            self.now += self.slow

    def control_read(self, offset):
        if offset == 0:
            return self.control_value
        if self.mode is None:
            self.heartbeat ^= 0x10000
            return 2 | self.heartbeat
        self.polls += 1
        if self.mode == "bad":
            self.sticky = True
            return 0x22
        if self.mode == "interrupt":
            raise KeyboardInterrupt()
        if self.mode in ("timeout", "dma_error"):
            return 10
        return 10 if self.polls == 1 else 18

    def dma_write(self, offset, value):
        self.events.append(("dma", offset, value))
        if offset == cc.c.CR:
            self.cr = value
            if value == 4:
                if self.unsafe and self.frame >= 0:
                    return
                self.cr, self.halted = 0, True
            elif value == 1:
                self.halted = False

    def dma_read(self, offset):
        if offset == cc.c.CR:
            return self.cr
        if offset == cc.c.SR:
            if self.halted:
                return 1
            if self.mode == "dma_error":
                return 0x40
            return 0x1002 if self.mode in ("valid", "short", "loss4", "loss5") and self.polls >= 2 else 0
        if offset == cc.c.LENGTH:
            lost = {"short": 2, "loss4": 4, "loss5": 5}.get(self.mode, 0)
            return cc.c.FRAME_BYTES - 2 * lost
        return 0


class ContinuousTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.output = Path(self.tmp.name)
        self.bytes_patch = patch.object(cc.c, "FRAME_BYTES", 16)
        self.bytes_patch.start()
        self.addCleanup(self.bytes_patch.stop)

    def run_session(self, fake=None, **kwargs):
        fake = fake or Fake()
        defaults = dict(seconds=0, max_attempts=3, max_errors=5, max_samples=2,
                        sample_every=1, frame_timeout=0.006, init_timeout=0.02,
                        cleanup_timeout=0.003, settle_seconds=0)
        defaults.update(kwargs)
        session = cc.CaptureSession(fake.ctrl, fake.dma, fake.allocate, self.output,
                                    clock=fake.clock, sleep=fake.sleep, **defaults)
        result = session.run()
        return fake, session, result

    def rows(self):
        return [json.loads(s) for s in (self.output / "attempts.jsonl").read_text().splitlines()]

    def test_single_init_buffer_reuse_toggle_and_no_png(self):
        with patch.object(cc.c, "png_bytes", side_effect=AssertionError("PNG in acquisition")):
            fake, _, r = self.run_session()
        self.assertEqual((r["attempts"], r["valid_frames"], r["initializations"]), (3, 3, 1))
        self.assertEqual(fake.allocations, 1)
        self.assertEqual(fake.arm_values, [4, 0, 4])
        self.assertEqual(fake.buffer.flushes, 3)
        self.assertEqual(fake.buffer.invalidates, 3)
        self.assertTrue(fake.buffer.freed)
        self.assertEqual(fake.control_value, 0)
        self.assertTrue(r["dma_shutdown_confirmed"])
        self.assertEqual(len(r["samples"]), 2)
        self.assertEqual(len(self.rows()), 3)
        self.assertFalse(list(self.output.glob("*.png")))
        # DMA length must precede every arm transition.
        starts = [i for i, e in enumerate(fake.events) if e == ("dma", cc.c.LENGTH, 16)]
        arms = [i for i, e in enumerate(fake.events) if e[0] == "ctrl" and e[1] == 0
                and e[2] in (0x205, 0x201) and i > starts[0]]
        self.assertTrue(all(start < arm for start, arm in zip(starts, arms)))

    def test_packet_error_reinitializes_before_rearming(self):
        fake, _, r = self.run_session(Fake(["bad", "valid"]), max_attempts=2)
        self.assertEqual((r["bad_frames"], r["valid_frames"], r["errors"]), (1, 1, 1))
        self.assertEqual((r["initializations"], r["recoveries"]), (2, 1))
        self.assertEqual(fake.arm_values, [4, 4])
        self.assertEqual(fake.allocations, 1)
        self.assertEqual(self.rows()[0]["diagnostics"]["camera_status"], "0x22")

    def test_timeout_classified_and_recovers(self):
        _, _, r = self.run_session(Fake(["timeout", "valid"]), max_attempts=2)
        self.assertEqual((r["timeouts"], r["bad_frames"], r["valid_frames"]), (1, 0, 1))
        self.assertEqual(r["recoveries"], 1)

    def test_dma_errors_and_large_partial_frame_are_distinct(self):
        for mode, key in (("dma_error", "dma_errors"), ("short", "bad_frames")):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temp:
                self.output = Path(temp)
                _, _, r = self.run_session(Fake([mode]), max_attempts=1)
                self.assertEqual(r[key], 1)
                self.assertEqual(r["valid_frames"], 0)
                self.assertEqual(r["recoveries"], 0)
                self.assertTrue(r["dma_shutdown_confirmed"])

    def test_under_five_percent_loss_is_counted_as_accepted_partial_frame(self):
        self.bytes_patch.stop()
        with patch.object(cc.c, "FRAME_BYTES", 200):
            fake, _, result = self.run_session(Fake(["loss4"]), max_attempts=1, max_samples=1)
            self.assertEqual((result["valid_frames"], result["bad_frames"], result["accepted_loss_frames"]),
                             (1, 0, 1))
            self.assertEqual(result["total_missing_pixels"], 4)
            self.assertEqual(self.rows()[0]["loss_percent"], 4.0)
            self.assertEqual(result["samples"][0]["bytes"], 192)
            self.assertFalse(result["samples"][0]["image_safe"])
            self.assertEqual(cc.convert_samples(self.output), [])

    def test_error_limit_stops_without_extra_recovery(self):
        _, _, r = self.run_session(Fake(["bad"]), max_attempts=100, max_errors=2)
        self.assertEqual((r["attempts"], r["errors"], r["recoveries"]), (2, 2, 1))
        self.assertEqual(r["stop_reason"], "max_errors")

    def test_valid_frame_resets_consecutive_error_limit(self):
        _, _, r = self.run_session(Fake(["bad", "valid", "bad", "valid"]), max_attempts=4, max_errors=2)
        self.assertEqual((r["attempts"], r["errors"], r["valid_frames"]), (4, 2, 2))
        self.assertEqual(r["stop_reason"], "max_attempts")
        self.assertEqual(r["max_consecutive_errors_observed"], 1)
        self.assertEqual(r["consecutive_errors"], 0)

    def test_process_scan_excludes_sudo_ancestors_but_finds_other_capture(self):
        proc = self.output / "proc"
        proc.mkdir()
        for pid, ppid, args in ((30, 20, b"python\0continuous_capture.py\0"),
                                (20, 10, b"sudo\0python\0continuous_capture.py\0"),
                                (10, 1, b"bash\0"), (1, 0, b"init\0"),
                                (40, 1, b"python\0capture.py\0")):
            item = proc / str(pid)
            item.mkdir()
            (item / "status").write_text("PPid:\t%d\n" % ppid)
            (item / "cmdline").write_bytes(args)
        with patch.object(cc.os, "getpid", return_value=30):
            self.assertEqual(cc.competing_processes(proc), [40])

    def test_duration_wins_over_frame_count_and_aborts_inflight(self):
        fake, _, r = self.run_session(Fake(["timeout"]), seconds=0.003, max_attempts=100)
        self.assertEqual(r["stop_reason"], "duration")
        self.assertEqual((r["attempts"], r["aborted_attempts"], r["timeouts"]), (1, 1, 0))
        self.assertTrue(fake.buffer.freed)
        self.assertTrue(r["dma_shutdown_confirmed"])
        self.assertLessEqual(r["capture_seconds"], 0.005)

    def test_count_limit_wins_over_duration(self):
        _, _, r = self.run_session(seconds=60, max_attempts=1)
        self.assertEqual(r["stop_reason"], "max_attempts")
        self.assertEqual(r["attempts"], 1)
        self.assertLess(r["capture_seconds"], 60)

    def test_ctrl_c_stops_and_halts_before_free(self):
        fake, _, r = self.run_session(Fake(["interrupt"]))
        self.assertEqual((r["stop_reason"], r["aborted_attempts"]), ("interrupted", 1))
        self.assertEqual(r["errors"], 0)
        self.assertTrue(fake.buffer.freed)
        self.assertTrue(r["dma_shutdown_confirmed"])

    def test_stop_before_initialize_does_not_allocate(self):
        fake, _, r = self.run_session(stop_requested=lambda: True)
        self.assertEqual(r["stop_reason"], "interrupted")
        self.assertEqual(fake.allocations, 0)
        self.assertTrue(r["dma_shutdown_confirmed"])

    def test_unconfirmed_halt_retains_buffer_and_stops(self):
        fake, session, r = self.run_session(Fake(["timeout"], unsafe=True))
        self.assertEqual(r["stop_reason"], "unsafe_dma")
        self.assertTrue(r["unsafe_dma"])
        self.assertFalse(fake.buffer.freed)
        self.assertIs(session.buffer, fake.buffer)
        self.assertEqual(r["attempts"], 1)
        self.assertEqual(r["recoveries"], 0)

    def test_repeat_interrupt_during_cleanup_does_not_skip_halt(self):
        fake = Fake()
        original, calls = fake.dma_read, [0]
        def interrupted_read(offset):
            if offset == cc.c.CR and calls[0] < 2:
                calls[0] += 1
                raise KeyboardInterrupt()
            return original(offset)
        fake.dma.read = interrupted_read
        _, _, r = self.run_session(fake, max_attempts=1)
        self.assertTrue(r["dma_shutdown_confirmed"])
        self.assertTrue(fake.buffer.freed)

    def test_invalid_limits_do_not_touch_hardware(self):
        for options in (dict(seconds=float("nan")), dict(max_attempts=0),
                        dict(max_errors=0), dict(max_samples=11), dict(frame_timeout=0)):
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.run_session(**options)

    def test_previous_unsafe_session_blocks_new_run(self):
        with patch.object(cc, "UNSAFE_SESSIONS", [object()]), self.assertRaisesRegex(RuntimeError, "Previous DMA"):
            cc.run_capture(self.output / "new", assume_cold_boot=True)

    def test_explicit_png_conversion_checks_hash_and_no_overwrite(self):
        self.run_session(max_attempts=1, max_samples=1)
        with patch.object(cc.c, "png_bytes", return_value=b"PNG"):
            paths = cc.convert_samples(self.output)
            self.assertEqual(paths[0].read_bytes(), b"PNG")
            with self.assertRaises(FileExistsError):
                cc.convert_samples(self.output)
        raw = next(self.output.glob("*.raw"))
        raw.write_bytes(b"bad")
        with self.assertRaisesRegex(ValueError, "SHA256"):
            cc.convert_samples(self.output)

    @unittest.skipIf(sys.platform == "win32", "fcntl is a board/Linux lock")
    def test_process_lock_exclusion_and_release(self):
        first = cc.ProcessLock(self.output / "camera.lock").acquire()
        try:
            with self.assertRaises(RuntimeError):
                cc.ProcessLock(self.output / "camera.lock").acquire()
        finally:
            first.release()
        second = cc.ProcessLock(self.output / "camera.lock").acquire()
        second.release()


if __name__ == "__main__":
    unittest.main()
