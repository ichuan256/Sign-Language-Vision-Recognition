# vdma_canary.py - exercise the 142M memory datapath using ONLY safe 100M-side
# register accesses. If VDMA MM2S (m_axi_mm2s_aclk = 142M) completes a frame,
# the 142M domain (FCLK1 + resets + mem interconnect) is alive in silicon.
# If it stalls with no error, the 142M datapath is dead.
# UART-streamed output survives a PS hang.
import time
import numpy as np
from pynq import Overlay, MMIO, allocate

print('CANARY_START', flush=True)
ol = Overlay('/home/xilinx/kws_hdmi.bit', download=False)
vinfo = ol.ip_dict['video/axi_vdma']
print('VDMA @0x%08x' % vinfo['phys_addr'], flush=True)
vdma = MMIO(vinfo['phys_addr'], vinfo['addr_range'])

W, H = 128, 64
buf = allocate((H, W, 3), dtype=np.uint8)
buf[:] = 0x33
buf.flush()
print('frame buf @0x%08x' % buf.physical_address, flush=True)

vdma.write(0x00, 0x00000004)          # MM2S reset
t = time.monotonic()
while vdma.read(0x00) & 0x4:
    if time.monotonic() - t > 2:
        print('RESET_TIMEOUT', flush=True)
        break
print('after reset: CR=0x%08x SR=0x%08x' % (vdma.read(0x00), vdma.read(0x04)), flush=True)

vdma.write(0x5C, buf.physical_address)  # frame 0 start address
vdma.write(0x54, W * 3)                 # HSIZE (bytes per line)
vdma.write(0x58, W * 3)                 # STRIDE
vdma.write(0x00, 0x00011089)            # run (pynq's MM2S start value)
vdma.write(0x50, H)                     # VSIZE kicks off the transfer
print('transfer started', flush=True)

for i in range(5):
    time.sleep(0.3)
    s = vdma.read(0x04)
    print('t+%dms SR=0x%08x | Idle=%d Halted=%d IntErr=%d SlvErr=%d DecErr=%d FrmCntIrq=%d'
          % ((i + 1) * 300, s, s & 1, (s >> 1) & 1, (s >> 4) & 1, (s >> 5) & 1,
             (s >> 6) & 1, (s >> 12) & 1), flush=True)

vdma.write(0x00, 0x00011080)            # stop
print('CANARY_DONE', flush=True)
