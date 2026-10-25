"""Read-only HDMI register snapshot; does not instantiate video drivers."""
import hashlib
import json
import time

from pynq import MMIO


BLOCKS = {
    'vdma': (0x44A00000, 0x70),
    'color': (0x40010000, 0x70),
    'hpd': (0x40020000, 0x10),
    'dynclk': (0x44A10000, 0x20),
    'vtc': (0x44A20000, 0xA0),
}
result = {'time': time.time(), 'registers': {}}
for name, (address, length) in BLOCKS.items():
    block = MMIO(address, length)
    result['registers'][name] = {
        hex(offset): hex(block.read(offset)) for offset in range(0, length, 4)
    }
dma = MMIO(BLOCKS['vdma'][0], BLOCKS['vdma'][1])
addresses = [dma.read(0x5C + 4 * i) for i in range(4)]
if (len(set(addresses)) == 1 and addresses[0] and
        dma.read(0x50) == 720 and dma.read(0x54) == 3840 and
        dma.read(0x58) & 0xFFFFFF == 3840):
    pixels = MMIO(addresses[0], 1280 * 720 * 3).array.copy()
    result['frame'] = {'address': hex(addresses[0]),
                       'sha256': hashlib.sha256(pixels.tobytes()).hexdigest(),
                       'byte_mean': float(pixels.view('uint8').mean())}
print(json.dumps(result, indent=2))
