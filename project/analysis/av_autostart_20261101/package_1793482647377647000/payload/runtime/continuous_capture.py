"""Bounded OV5640 capture on an already loaded FPGA; never download a bitstream."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import sys
import time

import capture as c

SOURCE_SHA256 = c.sha256(__file__)
UNSAFE_SESSIONS = globals().get("UNSAFE_SESSIONS", [])  # Survive accidental module reload.


class Stopped(Exception):
    pass


class DurationReached(Exception):
    pass


class FrameIssue(Exception):
    def __init__(self, kind, message, diagnostics=None):
        super().__init__(message)
        self.kind, self.diagnostics = kind, diagnostics


def validate_limits(seconds, max_attempts, max_errors, max_samples, sample_every,
                    frame_timeout, init_timeout, cleanup_timeout, settle_seconds):
    for name, value in (("seconds", seconds), ("settle_seconds", settle_seconds)):
        if not math.isfinite(value) or value < 0:
            raise ValueError(name + " must be finite and nonnegative")
    for name, value in (("frame_timeout", frame_timeout), ("init_timeout", init_timeout),
                        ("cleanup_timeout", cleanup_timeout)):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(name + " must be finite and positive")
    for name, value in (("max_attempts", max_attempts), ("max_errors", max_errors),
                        ("sample_every", sample_every)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(name + " must be a positive integer")
    if isinstance(max_samples, bool) or not isinstance(max_samples, int) or not 0 <= max_samples <= 10:
        raise ValueError("max_samples must be an integer from 0 to 10")


@contextmanager
def interrupt_flag():
    """SIGINT requests a stop; cleanup cannot be interrupted by another SIGINT."""
    stop = [False]
    previous = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, lambda *_: stop.__setitem__(0, True))
    try:
        yield lambda: stop[0]
    finally:
        signal.signal(signal.SIGINT, previous)


class ProcessLock:
    def __init__(self, path):
        self.path, self.file = Path(path), None

    def acquire(self):
        import fcntl  # Board Linux only; algorithm tests also run on Windows.
        self.file = self.path.open("a+")
        try:
            fcntl.flock(self.file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BaseException:
            self.file.close()
            self.file = None
            raise RuntimeError("Another continuous capture owns " + str(self.path))
        return self

    def release(self):
        if self.file is not None:
            self.file.close()
            self.file = None


def competing_processes(proc=Path("/proc")):
    """Best effort guard for old scripts which do not honor our flock."""
    ancestors, ancestor = set(), os.getpid()
    while ancestor > 0 and ancestor not in ancestors:
        ancestors.add(ancestor)
        try:
            status = (proc / str(ancestor) / "status").read_text()
            ancestor = int(next(s.split(":", 1)[1] for s in status.splitlines() if s.startswith("PPid:")))
        except (OSError, StopIteration, ValueError):
            break
    found = []
    for item in proc.iterdir():
        if not item.name.isdigit() or int(item.name) in ancestors:
            continue
        try:
            args = (item / "cmdline").read_bytes().split(b"\0")
        except (OSError, PermissionError):
            continue
        names = [Path(a.decode(errors="replace")).name for a in args if a]
        if any(n in ("capture.py", "sensor_probe.py", "continuous_capture.py", "hdmi_preview.py",
                     "hdmi_display.py", "hdmi_go.py", "hdmi_probe.py", "vdma_canary.py",
                     "stream_hand_board.py", "show_hand_result.py", "raw_video_board.py",
                     "raw_frame_replay.py", "hdmi_audio_receiver.py", "hdmi_paint_live.py")
               or (n.startswith("ov5640_ps_debug_") and n.endswith(".py")) for n in names):
            found.append(int(item.name))
    return found


class CaptureSession:
    """Testable loop. The caller owns a process lock and existing overlay metadata."""
    def __init__(self, control, dma, allocate, output, flags=0x200, *, seconds=60,
                 max_attempts=1000, max_errors=5, max_samples=3, sample_every=100,
                 frame_timeout=5, init_timeout=30, cleanup_timeout=2,
                 settle_seconds=0.5,
                 pixel_loss_threshold_percent=c.DEFAULT_PIXEL_LOSS_THRESHOLD_PERCENT,
                 clock=time.monotonic, sleep=time.sleep,
                 stop_requested=lambda: False, on_frame=None):
        validate_limits(seconds, max_attempts, max_errors, max_samples, sample_every,
                        frame_timeout, init_timeout, cleanup_timeout, settle_seconds)
        if flags not in (0, 0x100, 0x200, 0x300):
            raise ValueError("Invalid input polarity")
        if not math.isfinite(pixel_loss_threshold_percent) or not 0 <= pixel_loss_threshold_percent <= 100:
            raise ValueError("pixel_loss_threshold_percent must be finite and between 0 and 100")
        self.ctrl, self.dma, self.allocate = control, dma, allocate
        self.output, self.flags = Path(output), flags
        self.limit, self.max_attempts, self.max_errors = seconds, max_attempts, max_errors
        self.max_samples, self.sample_every = max_samples, sample_every
        self.frame_timeout, self.init_timeout = frame_timeout, init_timeout
        self.cleanup_timeout, self.settle_seconds = cleanup_timeout, settle_seconds
        self.pixel_loss_threshold_percent = float(pixel_loss_threshold_percent)
        self.clock, self.sleep, self.stop_requested = clock, sleep, stop_requested
        self.on_frame = on_frame
        self.buffer, self.arm, self.deadline = None, 0, None
        self.samples, self.dma_safe, self.hardware_started = [], False, False
        self.result = dict(schema_version=1, attempts=0, valid_frames=0, bad_frames=0,
                           accepted_loss_frames=0,
                           total_missing_pixels=0, max_loss_percent=0.0,
                           pixel_loss_threshold_percent=self.pixel_loss_threshold_percent,
                           timeouts=0, dma_errors=0, errors=0, other_errors=0, display_errors=0,
                           consecutive_errors=0, max_consecutive_errors_observed=0,
                           aborted_attempts=0, recovery_attempts=0, recoveries=0,
                           initializations=0, initialization_failures=0,
                           downloaded=False, input_polarity=hex(flags),
                           max_seconds=seconds, max_attempts=max_attempts,
                           max_consecutive_errors=max_errors, max_samples=max_samples,
                           sample_every=sample_every, frame_timeout=frame_timeout,
                           init_timeout=init_timeout, cleanup_timeout=cleanup_timeout,
                           settle_seconds=settle_seconds)

    def _wait(self, predicate, timeout, label, *, cleanup=False):
        until = self.clock() + timeout
        while True:
            try:
                now = self.clock()
                if not cleanup:
                    if self.stop_requested():
                        raise Stopped()
                    if self.deadline is not None and now >= self.deadline:
                        raise DurationReached()
                if predicate():
                    return
                if now >= until:
                    raise TimeoutError(label)
                self.sleep(0.001)
            except KeyboardInterrupt:
                if not cleanup:
                    raise Stopped()
                # A second interrupt must not skip confirmation of DMA Halted.

    def _halt(self):
        self.dma_safe = False
        # Reset write and polling are both protected from notebook interrupts.
        while True:
            try:
                self.dma.write(c.CR, 4)
                break
            except KeyboardInterrupt:
                continue
        self._wait(lambda: not self.dma.read(c.CR) & 4 and bool(self.dma.read(c.SR) & 1),
                   self.cleanup_timeout, "DMA reset/Halted", cleanup=True)
        self.dma_safe = True

    def _initialize(self):
        self.hardware_started = True
        self.ctrl.write(4, 0)
        self.ctrl.write(12, 0xFFFFFFFF)
        self.ctrl.write(0, 0)
        self.sleep(0.002)
        self._halt()
        self.arm = 0
        self.result["initializations"] += 1
        self.ctrl.write(0, 1 | self.flags)
        self.sleep(0.002)
        self.ctrl.write(0, 3 | self.flags)
        self.sleep(0.001)
        self.ctrl.write(0, 1 | self.flags)

        def initialized():
            status = self.ctrl.read(8)
            if status & 4:
                raise FrameIssue("initialization", "SCCB initialization error " + hex(status),
                                 {"camera_status": hex(status)})
            return bool(status & 2) and not status & 1
        try:
            self._wait(initialized, self.init_timeout, "Camera initialization")
            initial = self.ctrl.read(8)
            self._wait(lambda: bool((self.ctrl.read(8) ^ initial) & 0x10000),
                       1, "PCLK heartbeat")
            # Bounded settling; it also gives the FIFO reset handshake time to settle.
            until = self.clock() + self.settle_seconds
            self._wait(lambda: self.clock() >= until, self.settle_seconds + 0.1, "Settling")
        except (FrameIssue, TimeoutError):
            self.result["initialization_failures"] += 1
            raise

    def _capture_one(self):
        self.buffer.flush()
        self.dma.write(c.SR, 0x7000)
        self.dma.write(c.CR, 1)
        self._wait(lambda: not self.dma.read(c.SR) & 1, self.cleanup_timeout, "DMA running")
        self.dma.write(c.ADDR, int(self.buffer.physical_address))
        self.dma.write(c.ADDR_MSB, 0)
        self.dma_safe = False  # Before LENGTH: an interrupt must still halt safely.
        self.dma.write(c.LENGTH, c.FRAME_BYTES)
        self.arm ^= 4
        self.ctrl.write(0, 1 | self.flags | self.arm)
        seen = False
        states = {}

        def complete():
            nonlocal seen
            status, ds = self.ctrl.read(8), self.dma.read(c.SR)
            states.update(camera_status=hex(status), dma_status=hex(ds))
            if ds & 0x770:
                raise FrameIssue("dma", "DMA error " + hex(ds), dict(states))
            if status & 0x64:
                raise FrameIssue("bad_frame", "Camera error/overflow " + hex(status),
                                 dict(states))
            seen |= bool(status & 8)
            return seen and status & 16 and ds & 2 and ds & 0x1000
        self._wait(complete, self.frame_timeout, "Complete frame + DMA IOC/Idle")
        length = self.dma.read(c.LENGTH)
        states["received_bytes"] = length
        metrics = c.pixel_loss_metrics(length, threshold_percent=self.pixel_loss_threshold_percent)
        metrics["image_safe"] = length == c.FRAME_BYTES
        states.update(metrics)
        if not metrics["accepted"]:
            raise FrameIssue("bad_frame", f"Pixel loss {metrics['loss_percent']:.6f}% is at or above "
                             f"the {metrics['threshold_percent']:.3f}% acceptance limit", states)
        return states

    def _limit_reason(self):
        if self.stop_requested():
            return "interrupted"
        if self.deadline is not None and self.clock() >= self.deadline:
            return "duration"
        if self.result["consecutive_errors"] >= self.max_errors:
            return "max_errors"
        if self.result["attempts"] >= self.max_attempts:
            return "max_attempts"
        return None

    def run(self):
        begin, capture_start, capture_end = self.clock(), None, None
        reason, fatal = None, None
        try:
            with (self.output / "attempts.jsonl").open("x", encoding="utf-8") as log:
                self._initialize()
                self.buffer = self.allocate(shape=(c.FRAME_BYTES,), dtype="u1")
                address = int(self.buffer.physical_address)
                if address % 8 or address < 0x100000 or address + c.FRAME_BYTES > 0x20000000:
                    raise ValueError("Unsafe aligned DDR buffer address: " + hex(address))
                self.result["physical_address"] = address
                capture_start = self.clock()
                self.deadline = capture_start + self.limit if self.limit else None
                while not (reason := self._limit_reason()):
                    index, started = self.result["attempts"], self.clock()
                    self.result["attempts"] += 1
                    row = dict(index=index, elapsed=started - capture_start, outcome="unknown")
                    issue = None
                    try:
                        row.update(self._capture_one())
                        row["dma_seconds"] = self.clock() - started
                        if row["lost_pixels"]:
                            row["outcome"] = "accepted_loss"
                        else:
                            row["outcome"] = "valid"
                    except FrameIssue as exc:
                        issue = exc
                        key = "dma_errors" if exc.kind == "dma" else "bad_frames"
                        self.result[key] += 1
                        self.result["errors"] += 1
                        self.result["consecutive_errors"] += 1
                        row.update(outcome=exc.kind, error=str(exc), diagnostics=exc.diagnostics)
                    except TimeoutError as exc:
                        issue = exc
                        self.result["timeouts"] += 1
                        self.result["errors"] += 1
                        self.result["consecutive_errors"] += 1
                        row.update(outcome="timeout", error=str(exc))
                    except (Stopped, KeyboardInterrupt):
                        self.result["aborted_attempts"] += 1
                        row["outcome"], reason = "interrupted", "interrupted"
                    except DurationReached:
                        self.result["aborted_attempts"] += 1
                        row["outcome"], reason = "duration", "duration"
                    except Exception as exc:
                        self.result["other_errors"] += 1
                        self.result["errors"] += 1
                        row.update(outcome="fatal", error=repr(exc))
                        fatal = repr(exc)
                        reason = "fatal"
                    finally:
                        try:
                            self._halt()
                            row["dma_shutdown_confirmed"] = True
                            if row["outcome"] in ("valid", "accepted_loss"):
                                self.buffer.invalidate()
                                self.result["valid_frames"] += 1
                                self.result["consecutive_errors"] = 0
                                self.result["total_missing_pixels"] += row["lost_pixels"]
                                self.result["max_loss_percent"] = max(
                                    self.result["max_loss_percent"], row["loss_percent"])
                                if row["outcome"] == "accepted_loss":
                                    self.result["accepted_loss_frames"] += 1
                                if len(self.samples) < self.max_samples and index % self.sample_every == 0:
                                    sample = memoryview(self.buffer)[:row["received_bytes"]].tobytes()
                                    self.samples.append((index, sample, dict(
                                        received_bytes=row["received_bytes"],
                                        received_pixels=row["received_pixels"],
                                        lost_pixels=row["lost_pixels"],
                                        loss_percent=row["loss_percent"],
                                        image_safe=row["image_safe"])))
                        except Exception as exc:
                            row.update(cleanup_error=repr(exc), dma_shutdown_confirmed=False)
                            reason, fatal = "unsafe_dma", repr(exc)
                        # A display failure cannot turn an already halted capture DMA unsafe.
                        # The callback borrows this invalidated buffer only until it returns.
                        if (self.dma_safe and row.get("dma_shutdown_confirmed")
                                and row["outcome"] in ("valid", "accepted_loss")
                                and self.on_frame is not None):
                            try:
                                self.on_frame(self.buffer, row)
                            except (Stopped, KeyboardInterrupt):
                                reason = "interrupted"
                            except Exception as exc:
                                row["display_error"] = repr(exc)
                                self.result["display_errors"] += 1
                                self.result["errors"] += 1
                                reason, fatal = "display_error", repr(exc)
                        row["attempt_seconds"] = self.clock() - started
                        self.result["max_consecutive_errors_observed"] = max(
                            self.result["max_consecutive_errors_observed"], self.result["consecutive_errors"])
                        row["consecutive_errors"] = self.result["consecutive_errors"]
                        log.write(json.dumps(row) + "\n")
                        log.flush()
                    if reason:
                        break
                    if issue is not None:
                        reason = self._limit_reason()
                        if reason:
                            break
                        # Conservative known path: reset camera/packet/FIFO and initialize again.
                        # DMA-only reset cannot clear the packet's sticky error.
                        self.result["recovery_attempts"] += 1
                        self._initialize()
                        self.result["recoveries"] += 1
                capture_end = self.clock()
        except (Stopped, KeyboardInterrupt):
            reason = "interrupted"
        except DurationReached:
            reason = "duration"
        except Exception as exc:
            fatal = repr(exc)
            reason = "fatal"
            self.result["fatal_diagnostics"] = getattr(exc, "diagnostics", None)
        finally:
            if capture_start is not None and capture_end is None:
                capture_end = self.clock()
            if self.hardware_started:
                # No recovery attempt here after an already unconfirmed shutdown.
                if reason != "unsafe_dma":
                    try:
                        self._halt()
                    except Exception as exc:
                        reason, fatal = "unsafe_dma", repr(exc)
                if self.dma_safe:
                    # SIGINT uses a flag; direct notebook KeyboardInterrupt cannot free early.
                    try:
                        self.ctrl.write(0, 0)
                        if self.buffer is not None:
                            self.buffer.freebuffer()
                        self.result["camera_reset_after_capture"] = True
                    except BaseException as exc:
                        reason, fatal = "cleanup_error", repr(exc)
            self.result.update(stop_reason=reason, error=fatal,
                               dma_shutdown_confirmed=self.dma_safe,
                               unsafe_dma=not self.dma_safe and self.hardware_started,
                               capture_seconds=(capture_end - capture_start) if capture_start is not None else 0,
                               total_seconds=self.clock() - begin,
                               created_utc=datetime.now(timezone.utc).isoformat())
            duration = self.result["capture_seconds"]
            self.result["effective_fps"] = self.result["valid_frames"] / duration if duration > 0 else 0
            self.result["completed_without_errors"] = (reason in ("duration", "max_attempts")
                                                        and self.result["errors"] == 0 and fatal is None)
        # Disk samples and all PNG conversion are outside capture_seconds.
        self.result["samples"] = []
        try:
            for index, raw, metadata in self.samples:
                path = self.output / ("sample_%06d.raw" % index)
                path.write_bytes(raw)
                self.result["samples"].append(dict(path=path.name, frame_index=index,
                                                   bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                                                   **metadata))
            self.result["artifact_seconds"] = self.clock() - begin - self.result["total_seconds"]
            (self.output / "results.json").write_text(json.dumps(self.result, indent=2), encoding="utf-8")
        except BaseException:
            # The public wrapper must retain this session even if artifact writing fails.
            raise
        return self.result


def run_capture(output, manifest="release/release_manifest.json", *, assume_cold_boot=False,
                lock_path="/run/lock/ov5640_continuous_capture.lock", **options):
    """Notebook/CLI API. Does not load firmware. Unsafe sessions remain globally retained."""
    if UNSAFE_SESSIONS or c.RETAINED_BUFFERS:
        raise RuntimeError("Previous DMA shutdown unconfirmed. Do not rerun or restart kernel; power OFF first.")
    if not assume_cold_boot:
        raise RuntimeError("Confirm this paired firmware was loaded once at cold boot: assume_cold_boot=True")
    metadata, files = c.verify_manifest(manifest)
    boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    marker = Path("/run/ov5640_snapshot_download_attempted").read_text().strip()
    if not boot or marker != boot:
        raise RuntimeError("Current boot/download marker mismatch")
    lock = ProcessLock(lock_path).acquire()
    session = None
    try:
        active = competing_processes()
        if active:
            raise RuntimeError("Another camera process is active; PIDs=" + repr(active))
        from pynq import Overlay, MMIO, Clocks, allocate
        overlay = Overlay(str(files["bit"]), download=False)
        c.verify_overlay(overlay)
        frequency = float(Clocks.fclk0_mhz)
        if not math.isfinite(frequency) or abs(frequency - 100) > 1:
            raise RuntimeError("FCLK0 must already be 100 MHz; got " + repr(frequency))
        output = Path(output).resolve()
        output.mkdir(parents=True, exist_ok=False)
        with interrupt_flag() as requested:
            session = CaptureSession(MMIO(c.CONTROL_BASE, 65536), MMIO(c.DMA_BASE, 65536),
                                     allocate, output, c.polarity_for_manifest(metadata),
                                     stop_requested=requested, **options)
            session.result.update(boot_id=boot, firmware=metadata["files"], fclk0_mhz=frequency,
                                  helper_sha256=c.sha256(__file__), capture_sha256=c.sha256(c.__file__))
            return session.run()
    finally:
        if session is not None and session.hardware_started and not session.dma_safe:
            UNSAFE_SESSIONS.append((session, lock))
            print("DMA停机未确认：已保留buffer和锁。禁止重跑/重启kernel/杀进程；先断电。", flush=True)
        else:
            lock.release()


def convert_samples(output):
    """Explicit post-run step; never called in the acquisition loop."""
    if UNSAFE_SESSIONS or c.RETAINED_BUFFERS:
        raise RuntimeError("DMA unsafe: keep kernel/process alive and power OFF first")
    output = Path(output)
    result = json.loads((output / "results.json").read_text(encoding="utf-8"))
    if not result.get("dma_shutdown_confirmed"):
        raise RuntimeError("DMA shutdown unconfirmed in results.json")
    converted = []
    for sample in result["samples"]:
        relative = Path(sample["path"])
        if relative.name != str(relative) or relative.suffix != ".raw":
            raise ValueError("Unsafe sample path")
        raw = (output / relative).read_bytes()
        if len(raw) != sample["bytes"] or hashlib.sha256(raw).hexdigest() != sample["sha256"]:
            raise ValueError("Sample byte count/SHA256 mismatch")
        if not sample.get("image_safe") or len(raw) != c.FRAME_BYTES:
            continue
        path = (output / relative).with_suffix(".png")
        with path.open("xb") as handle:
            handle.write(c.png_bytes(raw))
        converted.append(path)
    return converted


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="release/release_manifest.json")
    parser.add_argument("--output", required=True)
    parser.add_argument("--assume-cold-boot", action="store_true")
    parser.add_argument("--seconds", type=float, default=60)
    parser.add_argument("--max-attempts", type=int, default=1000)
    parser.add_argument("--max-errors", type=int, default=5, help="Stop after this many consecutive failed attempts")
    parser.add_argument("--max-samples", type=int, default=3)
    parser.add_argument("--sample-every", type=int, default=100)
    parser.add_argument("--max-pixel-loss-percent", type=float,
                        default=c.DEFAULT_PIXEL_LOSS_THRESHOLD_PERCENT,
                        help="Strictly reject frames with this much pixel loss or more")
    parser.add_argument("--frame-timeout", type=float, default=5)
    parser.add_argument("--init-timeout", type=float, default=30)
    parser.add_argument("--convert-only", action="store_true", help="Convert saved RAW samples, no hardware access")
    args = vars(parser.parse_args(argv))
    convert_only = args.pop("convert_only")
    if convert_only:
        print("\n".join(str(p) for p in convert_samples(args["output"])))
        return 0
    result = None
    try:
        result = run_capture(**args)
        print(json.dumps(result, indent=2), flush=True)
    except BaseException as exc:
        print("ERROR: " + repr(exc), file=sys.stderr, flush=True)
        if not UNSAFE_SESSIONS:
            raise
    if UNSAFE_SESSIONS:
        # Do not return to a shell which would discard the retained physical buffer.
        while True:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                print("DMA停机未确认：先断电，再结束本进程。", flush=True)
    if result["stop_reason"] == "interrupted":
        return 130
    return 0 if result["stop_reason"] in ("duration", "max_attempts") and not result["error"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
