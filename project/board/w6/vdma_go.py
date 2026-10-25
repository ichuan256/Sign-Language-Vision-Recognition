# vdma_go.py - direct VDMA register programming for unified kws_hdmi design
# Pipeline: DDR frame -> VDMA MM2S (32bit XRGB) -> pixel_unpack -> color_convert -> vid_out -> rgb2dvi -> HDMI
import time
import numpy as np
from pynq import Overlay, MMIO, allocate

LOG = '/home/xilinx/vdma_go.log'
f = open(LOG, 'w')
def step(s):
    f.write('%s %s\n' % (time.strftime('%H:%M:%S'), s)); f.flush()
    print(s, flush=True)

VDMA = 0x44a00000
W, H = 1280, 720

step('V0 start')
ol = Overlay('/home/xilinx/kws_hdmi.bit', download=False)
step('V1 overlay attach ok')

# --- frontend: VTC timing + dynamic pixel clock (pynq frontend driver, proven OK) ---
from pynq.lib.video import VideoMode
hdmi = ol.video.hdmi_out
mode = VideoMode(W, H, 24)
hdmi.configure(mode)
hdmi.start()
step('V2 frontend running (VTC + dynclk)')

# --- frame buffer: 32-bit XRGB8888 ---
frame = allocate((H, W), dtype=np.uint32)
frame[:] = 0xFF102040                      # dark blue background (X R G B)
frame[100:400, 200:600] = 0xFFFFDC00       # yellow block
frame.flush()
step('V3 frame filled @phys=%#x' % frame.physical_address)

# --- VDMA direct programming (MM2S, circular, 4 framestores) ---
v = MMIO(VDMA, 0x10000)
v.write(0x00, 0x00011084)                  # reset
t0 = time.time()
while v.read(0x00) & 0x4:
    if time.time() - t0 > 2: raise RuntimeError('VDMA reset timeout')
    time.sleep(0.001)
step('V4 vdma reset done, SR=%#x' % v.read(0x04))

for i in range(4):
    v.write(0x5C + 4 * i, frame.physical_address)   # START_ADDRESS1..4
v.write(0x54, W * 4)                         # HSIZE: bytes per line (XRGB=4B/px)
v.write(0x58, W * 4)                         # STRIDE
v.write(0x00, 0x00010003)                    # RS=1 + Circular_Park=1, no IRQ
v.write(0x50, H)                             # VSIZE last: commits and starts
time.sleep(0.2)
sr = v.read(0x04)
step('V5 vdma started, CR=%#x SR=%#x' % (v.read(0x00), sr))
if sr & 0x1:
    step('V5 WARN: VDMA still halted!')

# --- verify frames advancing ---
a1 = v.read(0x28); time.sleep(1); a2 = v.read(0x28)
step('V6 park_ptr %#x -> %#x %s' % (a1, a2, 'ADVANCING' if a1 != a2 else 'STATIC'))
step('V7 done - LOOK AT SCREEN (dark blue bg + yellow block)')
f.close()
