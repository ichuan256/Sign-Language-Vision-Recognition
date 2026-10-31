"""Bounded OV5640 -> PS RGB conversion -> HDMI preview; attach only, never download."""
import argparse
import json
import math
from pathlib import Path
import sys
import time

import capture as c
import continuous_capture as cc

UNSAFE_PREVIEWS = globals().get("UNSAFE_PREVIEWS", [])
HDMI_DESIGN = dict(hdmi_output=True, hdmi_width=1280, hdmi_height=720,
                   hdmi_pixel_format="RGB888", hdmi_hierarchy="video/hdmi_out",
                   hdmi_vdma="video/axi_vdma", hdmi_read_hp="HP2",
                   hdmi_axi_clock_hz=100000000)


def rgb565_to_bgr(raw, destination, width=c.WIDTH, height=c.HEIGHT):
    """Vectorized little-endian RGB565, exact bit replication, PYNQ PIXEL_BGR."""
    import numpy as np
    if len(raw) != width * height * 2 or destination.shape != (height, width, 3):
        raise ValueError("Only complete RGB565 frames of the configured size can be displayed")
    if destination.dtype != np.uint8:
        raise ValueError("HDMI destination must be uint8")
    pixels = np.frombuffer(raw, dtype="<u2", count=width * height).reshape(height, width)
    red, green, blue = (pixels >> 11) & 31, (pixels >> 5) & 63, pixels & 31
    destination[..., 0] = (blue << 3) | (blue >> 2)
    destination[..., 1] = (green << 2) | (green >> 4)
    destination[..., 2] = (red << 3) | (red >> 2)


def verify_hdmi_manifest(metadata):
    for key, expected in HDMI_DESIGN.items():
        if metadata.get("design", {}).get(key) != expected:
            raise c.CaptureError(f"Manifest design.{key}: expected {expected!r}")
    if metadata.get("firmware_name") != "ov5640_snapshot_hdmi":
        raise c.CaptureError("Expected ov5640_snapshot_hdmi firmware")


class BoundedDisplay:
    """Parked MM2S VDMA with owned buffers and bounded register polling.

    Register layout and park protocol match PYNQ v3.0.1 MM2SChannel. We keep
    every buffer until Halted rather than transfer ownership to a frame cache.
    No S2MM channel or interrupt is instantiated for this output-only pipeline.
    """
    def __init__(self, mmio, allocate, *, width=c.WIDTH, height=c.HEIGHT,
                 framecount=4, timeout=2, clock=time.monotonic, sleep=time.sleep,
                 stop_requested=lambda: False, frontend_stop=lambda: None):
        if not math.isfinite(timeout) or timeout <= 0 or not 2 <= framecount <= 16:
            raise ValueError("Positive finite HDMI timeout and 2..16 frame stores required")
        self.mmio, self.allocate = mmio, allocate
        self.width, self.height, self.framecount = width, height, framecount
        self.timeout, self.clock, self.sleep = timeout, clock, sleep
        self.stop_requested, self.frontend_stop = stop_requested, frontend_stop
        self.frames, self.started, self.safe = [], False, False
        self.result = dict(displayed_frames=0, skipped_partial=0, display_errors=0,
                           hdmi_shutdown_confirmed=False, unsafe_hdmi=False,
                           memory_pixel_format="BGR888", output_pixel_format="RGB888",
                           display_seconds=0.0, display_effective_fps=0.0)
        self.begin = None

    def _wait(self, predicate, label, *, cleanup=False):
        until = self.clock() + self.timeout
        while True:
            try:
                if not cleanup and self.stop_requested():
                    raise cc.Stopped()
                if predicate():
                    return
                if self.clock() >= until:
                    raise TimeoutError(label)
                self.sleep(0.001)
            except KeyboardInterrupt:
                if not cleanup:
                    raise cc.Stopped()

    def _status(self):
        status = self.mmio.read(4)
        if status & 0x70:
            raise RuntimeError("HDMI MM2S DMA error: " + hex(status))
        if status & 1:
            raise RuntimeError("HDMI MM2S unexpectedly Halted")
        return status

    def quiesce(self):
        # Never call PYNQ stop(): it spins indefinitely and releases its frames.
        self.safe = False
        while True:
            try:
                self.mmio.write(0, self.mmio.read(0) & ~1)
                break
            except KeyboardInterrupt:
                continue
        self._wait(lambda: bool(self.mmio.read(4) & 1), "HDMI MM2S Halted", cleanup=True)
        self.safe = True

    def start(self):
        self.begin = self.clock()
        self.quiesce()
        for _ in range(self.framecount):
            frame = self.allocate(shape=(self.height, self.width, 3), dtype="u1")
            self.frames.append(frame)
            address = int(frame.physical_address)
            if address % 8 or address < 0x100000 or address + frame.nbytes > 0x20000000:
                raise ValueError("Unsafe HDMI buffer address: " + hex(address))
            frame[:] = 0  # Explicit initial black, never presented as a camera frame.
            frame.flush()
        self.mmio.write(4, 0xFFFFFFFF)
        self.mmio.write(0x28, self.mmio.read(0x28) & ~0x1F)
        for index, frame in enumerate(self.frames):
            self.mmio.write(0x5C + 4 * index, int(frame.physical_address))
        self.mmio.write(0x54, self.width * 3)
        self.mmio.write(0x58, self.width * 3)
        self.safe, self.started = False, True  # Before issuing Run/Stop.
        self.mmio.write(0, 0x00011089)  # PYNQ MM2S parked, frame-count IRQ enabled.
        self.mmio.write(0x50, self.height)
        self._wait(lambda: not self.mmio.read(4) & 1, "HDMI MM2S running")
        self._status()
        self._wait(lambda: self._active() == 0, "HDMI initial park")

    def _active(self):
        self._status()
        return (self.mmio.read(0x28) >> 16) & 0x1F

    def on_frame(self, buffer, row):
        if row["received_bytes"] != c.FRAME_BYTES:
            self.result["skipped_partial"] += 1
            row["display"] = "skipped_partial"
            return
        try:
            desired = self.mmio.read(0x28) & 0x1F
            self._wait(lambda: self._active() == desired, "HDMI previous frame swap")
            slot = (desired + 1) % self.framecount
            # Parked DMA cannot move away from desired until we request a new slot.
            rgb565_to_bgr(buffer, self.frames[slot], self.width, self.height)
            self.frames[slot].flush()
            self.mmio.write(0x28, (self.mmio.read(0x28) & ~0x1F) | slot)
            self._wait(lambda: self._active() == slot, "HDMI frame swap")
            self.result["displayed_frames"] += 1
            row["display"], row["display_slot"] = "submitted_and_active", slot
        except (cc.Stopped, KeyboardInterrupt):
            raise
        except Exception:
            self.result["display_errors"] += 1
            raise

    def close(self):
        try:
            self.quiesce()
        except BaseException as exc:
            self.result.update(hdmi_shutdown_confirmed=False, unsafe_hdmi=True,
                               hdmi_cleanup_error=repr(exc))
            raise
        self.result.update(hdmi_shutdown_confirmed=True, unsafe_hdmi=False)
        # Only after the Halted bit is observed is DMA memory released.
        for frame in self.frames:
            frame.freebuffer()
        self.frames.clear()
        self.frontend_stop()
        duration = self.clock() - self.begin if self.begin is not None else 0.0
        self.result["display_seconds"] = duration
        self.result["display_effective_fps"] = self.result["displayed_frames"] / duration if duration > 0 else 0


def make_display(overlay, *, timeout, stop_requested):
    from pynq import DefaultIP, MMIO, allocate
    from pynq.lib.video import VideoMode, PIXEL_BGR
    from pynq.lib.video.dma import AxiVDMA

    class OutputVDMA(AxiVDMA):
        def __init__(self, description):
            DefaultIP.__init__(self, description)
            self.framecount = int(description["parameters"]["C_NUM_FSTORES"])
            self.writechannel = AxiVDMA.MM2SChannel(self, None, description["device"].default_memory)

    description = overlay.ip_dict.get("video/axi_vdma", {})
    params = description.get("parameters", {})
    if (":axi_vdma:" not in description.get("type", "") or params.get("C_INCLUDE_MM2S") != "1"
            or params.get("C_INCLUDE_S2MM") != "0"
            or params.get("C_M_AXI_MM2S_ADDR_WIDTH") != "32"):
        raise c.CaptureError("HDMI requires a 32-bit-address, MM2S-only video/axi_vdma")
    hdmi, vdma = overlay.video.hdmi_out, OutputVDMA(description)
    hdmi._vdma = vdma
    display = BoundedDisplay(vdma.mmio,
        lambda **kw: allocate(target=description["device"].default_memory, **kw),
        framecount=vdma.framecount, timeout=timeout, stop_requested=stop_requested,
        frontend_stop=hdmi._hdmi.stop)
    # The caller must retain display even if configure/start raises.
    return display, lambda: _configure_output(overlay, hdmi, display, MMIO, VideoMode, PIXEL_BGR)


def _configure_output(overlay, hdmi, display, MMIO, VideoMode, PIXEL_BGR):
    display.quiesce()  # configure/mode setter can otherwise invoke PYNQ's unbounded stop.
    hdmi.configure(VideoMode(c.WIDTH, c.HEIGHT, 24), PIXEL_BGR)
    gpio = overlay.ip_dict["video/hdmi_out/frontend/hdmi_out_hpd_video"]
    MMIO(gpio["phys_addr"], 32).write(0, 1)
    clock = overlay.ip_dict["video/hdmi_out/frontend/axi_dynclk"]
    if not MMIO(clock["phys_addr"], 32).read(4) & 1:
        raise RuntimeError("HDMI pixel clock is not locked")
    display.start()


def run_preview(output, manifest="release_hdmi/release_manifest.json", *, assume_cold_boot=False,
                lock_path="/run/lock/ov5640_continuous_capture.lock", hdmi_timeout=2, **options):
    if UNSAFE_PREVIEWS or cc.UNSAFE_SESSIONS or c.RETAINED_BUFFERS:
        raise RuntimeError("Previous DMA shutdown unconfirmed; power OFF before another run")
    if not assume_cold_boot:
        raise RuntimeError("Require assume_cold_boot=True for the paired HDMI firmware")
    metadata, files = c.verify_manifest(manifest)
    verify_hdmi_manifest(metadata)
    boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    if not boot or Path("/run/ov5640_snapshot_download_attempted").read_text().strip() != boot:
        raise RuntimeError("Current boot/download marker mismatch")
    lock = cc.ProcessLock(lock_path).acquire()
    display, session, overlay, result = None, None, None, None
    output = Path(output).resolve()
    try:
        active = cc.competing_processes()
        if active:
            raise RuntimeError("Another camera/HDMI owner is active; PIDs=" + repr(active))
        from pynq import Overlay, MMIO, Clocks, allocate
        overlay = Overlay(str(files["bit"]), download=False)
        c.verify_overlay(overlay)
        frequency = float(Clocks.fclk0_mhz)
        if not math.isfinite(frequency) or abs(frequency - 100) > 1:
            raise RuntimeError("FCLK0 must already be 100 MHz")
        output.mkdir(parents=True, exist_ok=False)
        with cc.interrupt_flag() as requested:
            try:
                display, configure = make_display(overlay, timeout=hdmi_timeout, stop_requested=requested)
                configure()
                session = cc.CaptureSession(MMIO(c.CONTROL_BASE, 65536), MMIO(c.DMA_BASE, 65536),
                    allocate, output, c.polarity_for_manifest(metadata),
                    on_frame=display.on_frame, stop_requested=requested, **options)
                session.result.update(boot_id=boot, firmware=metadata["files"], fclk0_mhz=frequency,
                    helper_sha256=c.sha256(__file__), capture_sha256=c.sha256(c.__file__),
                    continuous_capture_sha256=c.sha256(cc.__file__), downloaded=False)
                result = session.run()
            except (cc.Stopped, KeyboardInterrupt):
                result = dict(stop_reason="interrupted", error=None, downloaded=False)
            except BaseException as exc:
                result = dict(stop_reason="startup_error", error=repr(exc), downloaded=False)
                raise
            finally:
                if display is not None:
                    try:
                        display.close()
                    except BaseException as exc:
                        if result is None:
                            result = dict(stop_reason="hdmi_cleanup_error", error=repr(exc))
                        else:
                            result.update(stop_reason="hdmi_cleanup_error", error=repr(exc))
                    if result is None:
                        result = dict(stop_reason="startup_error", error="HDMI/capture startup failed")
                    result["display"] = dict(display.result)
                    result["physical_fps_measured"] = False
                    result["preview_completed_without_errors"] = bool(
                        result.get("completed_without_errors") and display.safe
                        and result.get("stop_reason") in ("duration", "max_attempts")
                        and result.get("error") is None
                        and not display.result["display_errors"] and display.result["displayed_frames"] > 0)
                    (output / "preview_results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result
    finally:
        camera_unsafe = session is not None and session.hardware_started and not session.dma_safe
        hdmi_unsafe = display is not None and not display.safe
        if camera_unsafe or hdmi_unsafe:
            UNSAFE_PREVIEWS.append((session, display, overlay, lock))
            print("DMA停机未确认：已保留相机/HDMI buffer、overlay和锁；先断电，禁止杀进程。", flush=True)
        else:
            lock.release()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="release_hdmi/release_manifest.json")
    parser.add_argument("--output", required=True)
    parser.add_argument("--assume-cold-boot", action="store_true")
    parser.add_argument("--seconds", type=float, default=60)
    parser.add_argument("--max-attempts", type=int, default=1000)
    parser.add_argument("--max-errors", type=int, default=5)
    parser.add_argument("--frame-timeout", type=float, default=5)
    parser.add_argument("--init-timeout", type=float, default=30)
    parser.add_argument("--hdmi-timeout", type=float, default=2)
    args = vars(parser.parse_args(argv))
    result = None
    try:
        result = run_preview(**args)
        print(json.dumps(result, indent=2), flush=True)
    except BaseException as exc:
        print("ERROR: " + repr(exc), file=sys.stderr, flush=True)
        if not UNSAFE_PREVIEWS:
            raise
    if UNSAFE_PREVIEWS:
        while True:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                print("DMA停机未确认：先断电，再结束本进程。", flush=True)
    if result["stop_reason"] == "interrupted":
        return 130
    return 0 if result.get("preview_completed_without_errors") else 1


if __name__ == "__main__":
    raise SystemExit(main())
