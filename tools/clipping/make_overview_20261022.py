# -*- coding: utf-8 -*-
"""按秒抽帧生成逐秒总览图（供对话/单人轮次人工重排边界用）。

仿 P08/P09 人工流程：1 fps 抽帧、640x360 单元、5列x3行=15帧/张，
左上角标秒数。输出到 _inspect_frames/P10/。

用法：python make_overview_20261022.py --lesson 10 --from 176 --to 224 --name dlg1
"""
import argparse
import io
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
FFMPEG = ROOT.parent / "_tools" / "ffmpeg.exe"
RAW_DIR = (ROOT / "raw" / "手语配套视频 《中国手语教程》（初级）倪兰"
           / "手语配套视频 《中国手语教程》（初级）倪兰")
INSPECT = ROOT / "_tmp" / "inspect_frames"
LESSON_PREFIX = {8: "P8-", 9: "P9-", 10: "P10-"}

COLS, ROWS = 5, 3
PER = COLS * ROWS
CW, CH = 640, 360


def grab(src, t):
    cmd = [str(FFMPEG), "-ss", f"{t:.3f}", "-i", str(src),
           "-frames:v", "1", "-vf", f"scale={CW}:{CH}",
           "-f", "image2pipe", "-vcodec", "mjpeg", "-"]
    buf = subprocess.run(cmd, capture_output=True).stdout
    img = Image.open(io.BytesIO(buf)).convert("RGB")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 130, 26], fill=(0, 0, 0))
    d.text((5, 5), f"{t:.0f}s", fill=(255, 255, 0))
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lesson", type=int, required=True, choices=[8, 9, 10])
    ap.add_argument("--from", dest="frm", type=float, required=True)
    ap.add_argument("--to", dest="to", type=float, required=True)
    ap.add_argument("--name", required=True)
    args = ap.parse_args()

    src = next(RAW_DIR.glob(LESSON_PREFIX[args.lesson] + "*.mp4"))
    out_dir = INSPECT / f"P{args.lesson:02d}"
    out_dir.mkdir(parents=True, exist_ok=True)

    times = []
    t = args.frm
    while t < args.to:
        times.append(t)
        t += 1.0
    for si in range(0, len(times), PER):
        chunk = times[si:si + PER]
        sheet = Image.new("RGB", (CW * COLS, CH * ROWS))
        for i, t in enumerate(chunk):
            sheet.paste(grab(src, t), (CW * (i % COLS), CH * (i // COLS)))
        suffix = chr(ord("a") + si // PER)
        out = out_dir / f"{args.name}{suffix}.jpg"
        sheet.save(out, quality=85)
        print(out.name, f"{chunk[0]:.0f}-{chunk[-1]:.0f}s")


if __name__ == "__main__":
    main()
