"""Board demo: teacher palm detection + STUDENT keypoint net -> HDMI.

Pipeline per frame: palm detection (teacher TFLite) -> ROI tracking ->
student 96x96 TFLite (converted from hand_student_96_FLOAT_PILOT.keras v6)
-> 21 keypoints drawn over the video on the 720p HDMI screen.

Numeric contract (must match training): input RGB/255 in [0,1], 96x96;
output 65 = 21*(x,y,z normalized ROI) + presence logit + handedness logit.
"""
import argparse
import hashlib
import json
import time
from pathlib import Path

import cv2
import numpy as np

from teacher_runtime import TFLiteModel
from teacher_geometry import (decode_palms, letterbox_rgb, roi_from_palm,
                              associate, roi_from_landmarks, roi_matrix, draw_hands)


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run_student(model, rgb, roi):
    """Crop ROI at 96x96, run the student, return hand dict in image-normalized coords."""
    matrix = roi_matrix(roi, rgb.shape, size=96)
    crop = cv2.warpAffine(rgb, matrix, (96, 96), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    outputs = model.invoke(np.asarray(crop, np.float32) / 255.0)
    out = outputs[0].reshape(-1)          # (65,)
    landmarks = out[:63].reshape(21, 3).copy()
    # student xy is [0,1] over the ROI crop ((size-1) grid, same as augment)
    xy = np.c_[landmarks[:, :2] * 95.0, np.ones(21)]
    projected = xy @ matrix.T
    height, width = rgb.shape[:2]
    projected[:, 0] /= width
    projected[:, 1] /= height
    landmarks[:, :2] = projected
    landmarks[:, 2] *= float(roi[2])
    presence = 1.0 / (1.0 + np.exp(-float(out[63])))   # sigmoid on raw logit
    handedness = 1.0 / (1.0 + np.exp(-float(out[64])))
    return dict(points=landmarks, presence=presence, right_score=handedness,
                roi=roi, accepted=presence > 0.5)


class HdmiWriter:
    """Write 720p frames into the retained framebuffer owned by hdmi_display.py.

    kws_hdmi.bit swaps R/B between framebuffer and TMDS (quadrant-tested
    2026-10-28): compensate by swapping channels before writing.
    """

    def __init__(self, owner_pid):
        from pynq import MMIO
        self.owner = Path("/proc") / str(owner_pid)
        if b"hdmi_display.py" not in (self.owner / "cmdline").read_bytes():
            raise RuntimeError("Existing HDMI owner is not alive")
        self.identity = (self.owner / "stat").read_text().rsplit(")", 1)[1].split()[19]
        self.dma = MMIO(0x44A00000, 65536)
        self.addresses = [self.dma.read(0x5C + 4 * i) for i in range(4)]
        if not self.addresses[0] or len(set(self.addresses)) != 1:
            raise RuntimeError("Expected one retained framebuffer")
        self.check()
        self.frame = MMIO(self.addresses[0], 1280 * 720 * 3)

    def check(self):
        if b"hdmi_display.py" not in (self.owner / "cmdline").read_bytes() or \
                (self.owner / "stat").read_text().rsplit(")", 1)[1].split()[19] != self.identity:
            raise RuntimeError("HDMI owner changed")
        if self.addresses != [self.dma.read(0x5C + 4 * i) for i in range(4)] or self.dma.read(4) & 0x71:
            raise RuntimeError("VDMA state changed")
        if self.dma.read(0x50) != 720 or self.dma.read(0x54) != 3840 or self.dma.read(0x58) & 0xFFFFFF != 3840:
            raise RuntimeError("Expected 720p RGB888 mode")

    def write(self, rgb):
        self.check()
        if rgb.shape[:2] != (720, 1280):
            rgb = cv2.resize(rgb, (1280, 720), interpolation=cv2.INTER_LINEAR)
        rgb = rgb[..., ::-1]  # R/B swap compensation (PL wiring defect, M0b fix pending)
        self.frame.array[:] = np.ascontiguousarray(rgb, dtype=np.uint8).reshape(-1).view("<u4")


class StudentPipeline:
    def __init__(self, work, threads=2):
        self.palm = TFLiteModel(work / "libhands_tflite.so", work / "palm_detection_full.tflite", threads)
        self.student = TFLiteModel(work / "libhands_tflite.so", work / "student96_v6.tflite", threads)
        self.rois = []

    def close(self):
        self.palm.close()
        self.student.close()

    def process(self, rgb):
        metrics = dict(palm_ms=0.0, student_ms=[], detections=0)
        rois = self.rois
        if len(rois) != 2:
            tensor, padding = letterbox_rgb(rgb)
            start = time.perf_counter()
            outputs = self.palm.invoke(tensor)
            metrics["palm_ms"] = (time.perf_counter() - start) * 1000
            detections = decode_palms(outputs, padding)
            metrics["detections"] = len(detections)
            detected = [roi_from_palm(d, rgb.shape) for d in detections[:2]]
            rois = associate(detected, self.rois)
        metrics["presence_scores"] = []
        hands, next_rois = [], []
        for roi in rois[:2]:
            start = time.perf_counter()
            hand = run_student(self.student, rgb, roi)
            metrics["student_ms"].append((time.perf_counter() - start) * 1000)
            metrics["presence_scores"].append(round(hand["presence"], 3))
            if hand["accepted"]:
                hands.append(hand)
                next_rois.append(roi_from_landmarks(hand["points"], rgb.shape))
        self.rois = next_rois
        return hands, metrics


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--video", type=Path, required=True)
    p.add_argument("--frames", type=int, default=200)
    p.add_argument("--threads", type=int, default=2, choices=(1, 2))
    p.add_argument("--loop", action="store_true")
    p.add_argument("--display-owner-pid", type=int)
    p.add_argument("--record", action="store_true")
    a = p.parse_args()
    if a.output.exists() or not 1 <= a.frames <= 10000:
        raise ValueError("New bounded output required")
    a.output.mkdir(parents=True)
    report = dict(scope="board_student_keypoints_hdmi", completed=False,
                  student_model="student96_v6.tflite (from hand_student_96_FLOAT_PILOT.keras v6)",
                  student_sha256=sha256(a.work / "student96_v6.tflite"),
                  palm_sha256=sha256(a.work / "palm_detection_full.tflite"),
                  threads=a.threads, pc_inference=False)
    pipeline = StudentPipeline(a.work, a.threads)
    records, writer, capture, recorder = [], None, None, None
    try:
        capture = cv2.VideoCapture(str(a.video))
        if not capture.isOpened():
            raise RuntimeError("Board-local video cannot decode")
        if a.display_owner_pid:
            writer = HdmiWriter(a.display_owner_pid)
        if a.record:
            recorder = cv2.VideoWriter(str(a.output / "annotated.mp4"), cv2.VideoWriter_fourcc(*"mp4v"),
                                       10, (1280, 720))
        start_all = time.perf_counter()
        for frame_id in range(a.frames):
            frame_start = time.perf_counter()
            ok, bgr = capture.read()
            if not ok:
                if not a.loop:
                    break
                capture.release()
                capture = cv2.VideoCapture(str(a.video))
                ok, bgr = capture.read()
                if not ok:
                    break
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            hands, metrics = pipeline.process(rgb)
            annotated = draw_hands(rgb, hands)
            fps = (frame_id + 1) / (time.perf_counter() - start_all)
            if writer:
                display = cv2.resize(annotated, (1280, 720)) if annotated.shape[:2] != (720, 1280) else annotated
                cv2.rectangle(display, (0, 0), (1280, 65), (0, 0, 0), -1)
                cv2.putText(display, "STUDENT 96 KEYPOINTS v6 | %.2f FPS | %d HANDS" % (fps, len(hands)),
                            (14, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 220, 255), 2, cv2.LINE_AA)
                cv2.putText(display, "PALM(Teacher) + ROI + STUDENT 21pts | presence %.2f" %
                            (max(metrics["presence_scores"]) if metrics["presence_scores"] else 0.0),
                            (14, 54), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
                writer.write(display)
            if recorder:
                frame = cv2.resize(annotated, (1280, 720))
                recorder.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            records.append(dict(frame_id=frame_id, hands=len(hands),
                                end_to_end_ms=(time.perf_counter() - frame_start) * 1000, **metrics))
            print("STUDENT_FRAME", frame_id, "hands", len(hands),
                  "ms", round(records[-1]["end_to_end_ms"], 1), flush=True)
        elapsed = time.perf_counter() - start_all
        report.update(completed=len(records) == a.frames, frames=len(records), elapsed_s=elapsed,
                      end_to_end_fps=len(records) / elapsed if elapsed else 0,
                      tracked_frames=sum(1 for r in records if r["palm_ms"] == 0),
                      display_enabled=bool(writer), screen_visually_confirmed=False)
    finally:
        if recorder:
            recorder.release()
        if capture:
            capture.release()
        pipeline.close()
        (a.output / "frames.json").write_text(json.dumps(records) + "\n")
        (a.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print("STUDENT_REPORT " + json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
