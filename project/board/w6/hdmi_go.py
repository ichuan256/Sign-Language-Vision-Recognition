# hdmi_go.py - W6 HDMI out smoke, interrupt-free path
# Works around two pynq quirks of the output-only unified design:
#  1) HDMIWrapper doesn't match (no hdmi_in) -> VideoOut never gets its VDMA
#  2) HWH interrupt chain isn't parsed -> stock AxiVDMA ctor fails on mm2s_introut
# Solution: subclass AxiVDMA without interrupt, use setframe() (no blocking wait).
import time
from pynq import Overlay, DefaultIP
from pynq.lib.video import VideoMode
from pynq.lib.video.dma import AxiVDMA

LOG = '/home/xilinx/hdmi_go.log'
f = open(LOG, 'w')
def step(s):
    f.write('%s %s\n' % (time.strftime('%H:%M:%S'), s)); f.flush()
    print(s, flush=True)

step('G0 start')
ol = Overlay('/home/xilinx/kws_hdmi.bit', download=False)
step('G1 overlay attach ok')

class _VDMA(AxiVDMA):
    def __init__(self, description):
        DefaultIP.__init__(self, description)
        self.framecount = 4
        memory = description['device'].default_memory
        self.writechannel = AxiVDMA.MM2SChannel(self, None, memory)

hdmi = ol.video.hdmi_out
vdma = _VDMA(ol.ip_dict['video/axi_vdma'])
hdmi._vdma = vdma
step('G2 vdma wired manually')

mode = VideoMode(1280, 720, 24)
hdmi.configure(mode)
step('G3 configured 1280x720@24')

hdmi.start()          # VDMA writechannel start (circular, 4 slots)
step('G4 vdma started')
hdmi._hdmi.start()    # frontend: VTC generator + dynclk on
step('G5 frontend started')

frame = hdmi.newframe()
frame[:] = (16, 24, 48)          # dark blue background
frame[100:400, 200:600] = (255, 220, 0)   # yellow block
frame.flush()                    # cacheable buffer -> push to DDR
step('G6 frame drawn+flushed')

for i in range(vdma.framecount):  # point every VDMA slot at our frame
    vdma.writechannel._frames[i] = frame
    vdma.writechannel._frames.takeownership(i)
step('G7 frame live on all slots - LOOK AT SCREEN NOW')
time.sleep(30)
step('G8 done (pipeline left running)')
f.close()
