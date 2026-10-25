# hdmi_smoke.py - kws_hdmi.bit board smoke test (run on PYNQ, sudo -E with PYTHONPATH)
# 1) load unified overlay 2) check IP list 3) HDMI 720p out with text frames
import sys, time
import numpy as np
from pynq import Overlay

BIT = '/home/xilinx/kws_hdmi.bit'
# 合一设计在开机时由 boot.py 加载一次；此处仅接管，不重编程（重配置会硬复位）
ol = Overlay(BIT, download=False)
print('[1] overlay loaded')
ips = sorted(ol.ip_dict.keys())
print('[2] IPs:', ips)
assert 'video' in ips or any('axi_vdma' in k for k in ips), 'video pipeline missing!'

from pynq.lib.video import VideoMode
hdmi = ol.video.hdmi_out
# output-only design: HDMIWrapper doesn't match (no hdmi_in), so VideoOut._vdma
# is never wired by pynq — do it manually
if hdmi._vdma is None:
    hdmi._vdma = ol.video.axi_vdma
mode = VideoMode(1280, 720, 24)
hdmi.configure(mode)
print('[3] hdmi_out configured 1280x720@24bit')

hdmi.start()   # must start before newframe: _FrameCache is created in start()
W, H = mode.width, mode.height
frame = hdmi.newframe()
print('[4] frame buffer:', frame.shape, frame.dtype)

# try PIL text; fallback to color bars
try:
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new('RGB', (W, H), (16, 24, 48))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 72)
        font2 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 36)
    except Exception:
        font = font2 = ImageFont.load_default()
    d.text((60, 200), 'KWS HDMI OK', fill=(255, 220, 60), font=font)
    d.text((60, 320), 'unified bitstream: audio + kws + hdmi', fill=(200, 200, 200), font=font2)
    frame[:] = np.asarray(img)
    print('[5] PIL text frame drawn')
except Exception as e:
    print('[5] PIL failed, fallback color bars:', e)
    thirds = W // 3
    frame[:, :thirds] = (255, 0, 0)
    frame[:, thirds:2*thirds] = (0, 255, 0)
    frame[:, 2*thirds:] = (0, 0, 255)


hdmi.writeframe(frame)
print('[6] hdmi_out started, frame written')
time.sleep(2)
f2 = hdmi.readframe()
print('[7] readback frame mean=%.1f (expect ~50-130, nonzero means path alive)' % f2.mean())
hdmi.stop()
print('[DONE] HDMI smoke test passed')
