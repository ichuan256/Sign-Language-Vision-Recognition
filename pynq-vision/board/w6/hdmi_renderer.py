"""Paint into the retained frame owned by hdmi_display.py. No video reconfigure.

Keep hdmi_display.py running while using this diagnostic. It must be the sole
owner and must not modify/release its frame while this script is active.
"""
import argparse
import time

import numpy as np
from pynq import MMIO
from hdmi_ui import Renderer, read_state
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--state', default='/home/xilinx/hdmi_state.json')
parser.add_argument('--once', action='store_true')
parser.add_argument('--owner-pid', type=int, required=True)
args = parser.parse_args()
owner = Path('/proc') / str(args.owner_pid) / 'cmdline'
assert owner.exists() and b'hdmi_display.py' in owner.read_bytes(), 'Output owner is not alive' 
vdma = MMIO(0x44A00000, 65536)
assert vdma.read(0x54) == 1280 * 3
assert vdma.read(0x58) & 0xFFFFFF == 1280 * 3
assert vdma.read(0x50) == 720
assert not vdma.read(4) & 0x71
addresses = [vdma.read(0x5C + 4 * i) for i in range(4)]
assert addresses[0] and len(set(addresses)) == 1, addresses
frame_address = addresses[0]
frame_bytes = 1280 * 720 * 3
frame = MMIO(frame_address, frame_bytes)
color = MMIO(0x40010000, 65536)
for i, value in enumerate([0, 0, 256, 0, 256, 0, 256, 0, 0, 0, 0, 0]):
    color.write(0x10 + i * 8, value)
print('LIVE_PAINT frame=%#x bytes=%d; VDMA mode and pointers unchanged' %
      (frame_address, frame_bytes), flush=True)
renderer = Renderer()
state = {'page': 'calibration'}
ticks = 0
last_state = None
while True:
    assert owner.exists() and b'hdmi_display.py' in owner.read_bytes(), 'Output owner exited'
    # Abort before accessing the old physical allocation if its owner changes.
    assert addresses == [vdma.read(0x5C + 4 * i) for i in range(4)]
    assert not vdma.read(4) & 0x71
    state = read_state(Path(args.state), state)
    if state == last_state:
        time.sleep(0.5)
        continue
    pixels = np.asarray(renderer.render(state, ticks))
    words = np.frombuffer(pixels.tobytes(), dtype='<u4')
    frame.array[:] = words
    print('DISPLAY_UPDATE count=%d mean=%.2f page=%s text=%s' %
          (ticks, pixels.mean(), state.get('page'), state.get('text', '')), flush=True)
    last_state = dict(state)
    ticks += 1
    if args.once:
        break
    time.sleep(1)
