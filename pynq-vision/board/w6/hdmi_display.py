"""Persistent 720p display. Run as root with XILINX_XRT=/usr.

Use --program only when explicitly loading the FPGA; otherwise attach.
Keep the process alive so the frame buffer stays allocated.
"""
import argparse
import time
from pynq import Overlay, DefaultIP, MMIO
from pynq.lib.video import VideoMode
from pynq.lib.video.dma import AxiVDMA

parser = argparse.ArgumentParser()
parser.add_argument('--program', action='store_true')
args = parser.parse_args()
print('Loading FPGA' if args.program else 'Attaching overlay', flush=True)
ol = Overlay('/home/xilinx/kws_hdmi.bit', download=args.program)
print('Overlay ready', flush=True)


class OutputVDMA(AxiVDMA):
    def __init__(self, description):
        DefaultIP.__init__(self, description)
        self.framecount = 4
        self.writechannel = AxiVDMA.MM2SChannel(
            self, None, description['device'].default_memory)


hdmi = ol.video.hdmi_out
vdma = OutputVDMA(ol.ip_dict['video/axi_vdma'])
hdmi._vdma = vdma
hdmi.configure(VideoMode(1280, 720, 24))
print('Configured 720p', flush=True)
hdmi.start()
hdmi._hdmi.start()
gpio = ol.ip_dict['video/hdmi_out/frontend/hdmi_out_hpd_video']
MMIO(gpio['phys_addr'], 32).write(0, 1)
frame = hdmi.newframe()
frame[:] = (16, 24, 48)
frame[100:400, 200:600] = (255, 220, 0)
frame.flush()
for index in range(vdma.framecount):
    vdma.writechannel._frames[index] = frame
    vdma.writechannel._frames.takeownership(index)
print('DISPLAY_RUNNING: 1280x720 dark blue background + yellow rectangle', flush=True)
print('VDMA control=%#x status=%#x' % (vdma.read(0), vdma.read(4)), flush=True)
clock_info = ol.ip_dict['video/hdmi_out/frontend/axi_dynclk']
clock_status = MMIO(clock_info['phys_addr'], 32).read(4)
print('Dynamic pixel clock status=%#x' % clock_status, flush=True)
if not clock_status & 1 or vdma.read(4) & 0x70:
    raise RuntimeError('Pixel clock unlocked or VDMA transfer error')
while True:
    time.sleep(10)
