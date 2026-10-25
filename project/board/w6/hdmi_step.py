# hdmi_step.py - fine-grained bisect: each step flushed to /home/xilinx/hdmi_step.log
import time

LOG = '/home/xilinx/hdmi_step.log'
f = open(LOG, 'w')
def step(s):
    f.write('%s %s\n' % (time.strftime('%H:%M:%S'), s))
    f.flush()
    print(s, flush=True)

step('S0 start')
from pynq import Overlay
step('S1 import ok')
ol = Overlay('/home/xilinx/kws_hdmi.bit', download=False)
step('S2 overlay attach ok (no download)')
ips = sorted(ol.ip_dict.keys())
step('S3 ip count=%d has_video=%s' % (len(ips), 'video' in ''.join(ips) or any('vdma' in k for k in ips)))

from pynq.lib.video import VideoMode
hdmi = ol.video.hdmi_out
# output-only design: no hdmi_in -> HDMIWrapper doesn't bind, so VideoOut never
# receives its VDMA reference. Wire it manually (pynq hierarchies.py).
if hdmi._vdma is None:
    hdmi._vdma = ol.video.axi_vdma
step('S4 driver bound')

mode = VideoMode(1280, 720, 24)
hdmi.configure(mode)
step('S5 configured 720p')

hdmi.start()
step('S5b hdmi started (before newframe; pynq needs start first)')

frame = hdmi.newframe()
step('S6 frame alloc %s' % (frame.shape,))
frame[:] = 40
frame[100:400, 200:600] = (255, 220, 0)
step('S7 frame filled')

hdmi.writeframe(frame)
step('S9 frame written - LOOK AT SCREEN NOW')

time.sleep(10)
hdmi.stop()
step('S10 stopped, ALL PASS')
f.close()
