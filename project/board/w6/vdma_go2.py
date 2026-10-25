# vdma_go2.py - agent's manual VDMA wiring + direct register start
import time
import numpy as np
from pynq import Overlay, MMIO, allocate, DefaultIP
from pynq.lib.video import VideoMode
from pynq.lib.video.dma import AxiVDMA

LOG = '/home/xilinx/vdma_go2.log'
f = open(LOG, 'w')
def step(s):
    f.write('%s %s\n' % (time.strftime('%H:%M:%S'), s)); f.flush()
    print(s, flush=True)

VDMA_ADDR = 0x44a00000
W, H = 1280, 720

step('W0 start')
ol = Overlay('/home/xilinx/kws_hdmi.bit', download=False)
step('W1 overlay attach ok')

class _VDMA(AxiVDMA):
    def __init__(self, description):
        DefaultIP.__init__(self, description)
        self.framecount = 4
        memory = description['device'].default_memory
        self.writechannel = AxiVDMA.MM2SChannel(self, None, memory)

hdmi = ol.video.hdmi_out
vdma = _VDMA(ol.ip_dict['video/axi_vdma'])
hdmi._vdma = vdma
step('W2 vdma wired')

mode = VideoMode(W, H, 24)
hdmi.configure(mode)
hdmi.start()
step('W3 frontend running')

frame = allocate((H, W), dtype=np.uint32)
frame[:] = 0xFF102040
frame[100:400, 200:600] = 0xFFFFDC00
frame.flush()
step('W4 frame filled phys=%#x' % frame.physical_address)

v = MMIO(VDMA_ADDR, 0x10000)
v.write(0x00, 0x00011084)          # reset
t0 = time.time()
while v.read(0x00) & 0x4:
    if time.time() - t0 > 2: raise RuntimeError('VDMA reset timeout')
    time.sleep(0.001)
for i in range(4):
    v.write(0x5C + 4 * i, frame.physical_address)
v.write(0x54, W * 4)               # HSIZE bytes per line
v.write(0x58, W * 4)               # STRIDE
v.write(0x00, 0x00010003)          # RS=1 + circular
v.write(0x50, H)                   # VSIZE last -> start
time.sleep(0.2)
step('W5 vdma CR=%#x SR=%#x' % (v.read(0x00), v.read(0x04)))

a1 = v.read(0x28); time.sleep(1); a2 = v.read(0x28)
step('W6 park_ptr %#x -> %#x %s' % (a1, a2, 'ADVANCING' if a1 != a2 else 'STATIC'))
step('W7 done - LOOK AT SCREEN (blue bg + yellow block)')
f.close()
