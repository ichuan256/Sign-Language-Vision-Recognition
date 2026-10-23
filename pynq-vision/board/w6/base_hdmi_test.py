# base_hdmi_test.py - A/B reference test with OFFICIAL PYNQ base overlay
# Run on a FRESH boot where no bitstream has been loaded yet.
# (second load of any bitstream hard-resets this board, so this must be the first)
import time, sys
from pynq import Overlay

print('[1] loading base.bit (official reference)...', flush=True)
ol = Overlay('base.bit')   # resolves to pynq package's bundled base overlay
print('[2] base.bit loaded', flush=True)

ips = sorted(ol.ip_dict.keys())
cc = [k for k in ips if 'color_convert' in k]
print('[3] color_convert instances:', cc, flush=True)

if cc:
    from pynq import MMIO
    info = ol.ip_dict[cc[0]]
    print('[4] reading %s @0x%08x ...' % (cc[0], info['phys_addr']), flush=True)
    m = MMIO(info['phys_addr'], 4)
    print('[5] color_convert reg0 = 0x%08x  <-- READ OK, no hang' % m.read(0), flush=True)

from pynq.lib.video import VideoMode
from pynq import MMIO
hdmi = ol.video.hdmi_out
mode = VideoMode(1280, 720, 24)
hdmi.configure(mode)
hdmi.start()   # must precede newframe (frame cache created in start)
# drive HPD high explicitly (portable panel needs it)
gpio = MMIO(ol.ip_dict['video/hdmi_out/frontend/hdmi_out_hpd_video']['phys_addr'], 32)
gpio.write(0, 1)
frame = hdmi.newframe()
frame[:, :] = (0, 64, 128)
frame[:, : frame.shape[1]//3] = (255, 64, 0)
print('[6] hdmi_out configured, writing frame - LOOK AT SCREEN', flush=True)
hdmi.writeframe(frame)
time.sleep(30)
print('[7] DONE: base HDMI out works' , flush=True)
