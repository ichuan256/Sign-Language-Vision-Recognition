from pynq import MMIO
import time
g = MMIO(0x43C10000, 16)
seen = set()
for i in range(150):
    seen.add(g.read(0) & 0xF)
    time.sleep(0.2)
print('REG_VALUES_SEEN:', sorted(seen), flush=True)
