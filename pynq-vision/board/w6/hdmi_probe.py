# hdmi_probe.py - register-level bisect for W6 unified overlay
# Reads offset 0 of every IP one by one. Output goes to /dev/ttyPS0 (UART),
# so even if the PS hard-hangs on a dead-clock AXI slave, the PC log shows
# exactly which IP killed it.
# Run: sudo bash -c 'source /etc/profile.d/pynq_venv.sh; source /etc/profile.d/xrt_setup.sh; python3 -u hdmi_probe.py > /dev/ttyPS0 2>&1'
import time
from pynq import Overlay, MMIO

ol = Overlay('/home/xilinx/kws_hdmi.bit', download=False)
ips = ol.ip_dict

# probe order: 100M control-domain first; among 142M HLS IPs, pixel_unpack
# BEFORE color_convert to tell "shared path broken" vs "single IP broken"
order_hint = ['axi_dma', 'kws', 'audio', 'spi', 'gpio', 'hpd', 'vdma', 'vtc',
              'dynclk', 'axi4s', 'pixel', 'color', 'slice', 'rgb2dvi']
def rank(n):
    for i, k in enumerate(order_hint):
        if k in n.lower():
            return i
    return 50
names = sorted(n for n in ips.keys() if 'phys_addr' in ips[n])
names.sort(key=rank)

print('PROBE_START %d ips' % len(names), flush=True)
for n in names:
    print('  HAS_ADDR %-44s @0x%08x' % (n, ips[n]['phys_addr']), flush=True)
for n in names:
    info = ips[n]
    print('PROBE %-44s @0x%08x ...' % (n, info['phys_addr']), flush=True)
    time.sleep(0.4)  # let UART drain before risky access
    try:
        m = MMIO(info['phys_addr'], 4)
        v = m.read(0)
        print('  OK %s -> 0x%08x' % (n, v & 0xFFFFFFFF), flush=True)
    except Exception as e:
        print('  FAIL %s: %s' % (n, e), flush=True)
print('ALL_PROBE_DONE', flush=True)
