"""Mirror audio-loop JPEG frames into a retained HDMI frame. Never reconfigure video.

Requires the already visible hdmi_display.py owner to remain alive. Run as root
with XILINX_XRT=/usr, and stop this receiver before restarting that owner.
"""
import argparse
import io
import time
from pathlib import Path
from urllib.request import build_opener, ProxyHandler

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pynq import MMIO


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True, help='http://computer-address:8765/frame.jpg')
    parser.add_argument('--owner-pid', required=True, type=int)
    parser.add_argument('--fps', default=10, type=float)
    args = parser.parse_args()
    if not 0 < args.fps <= 30:
        parser.error('--fps must be in (0, 30]')
    owner = Path('/proc') / str(args.owner_pid)
    identity = (owner / 'stat').read_text().rsplit(')', 1)[1].split()[19]
    dma = MMIO(0x44A00000, 65536)
    addresses = [dma.read(0x5C + 4 * i) for i in range(4)]
    if not addresses[0] or len(set(addresses)) != 1:
        raise RuntimeError('Expected one retained frame in all four slots')
    frame = MMIO(addresses[0], 1280 * 720 * 3)

    def check():
        if b'hdmi_display.py' not in (owner / 'cmdline').read_bytes():
            raise RuntimeError('The original display owner is not running')
        if (owner / 'stat').read_text().rsplit(')', 1)[1].split()[19] != identity:
            raise RuntimeError('Display owner identity changed')
        if addresses != [dma.read(0x5C + 4 * i) for i in range(4)]:
            raise RuntimeError('Frame addresses changed')
        if (dma.read(4) & 0x71 or dma.read(0x50) != 720 or
                dma.read(0x54) != 3840 or dma.read(0x58) & 0xFFFFFF != 3840):
            raise RuntimeError('Display mode or DMA state changed')

    check()
    color = MMIO(0x40010000, 65536)
    for index, value in enumerate([0, 0, 256, 0, 256, 0, 256, 0, 0, 0, 0, 0]):
        color.write(0x10 + index * 8, value)
    count = 0
    polls = 0
    previous_payload = None
    disconnected = False
    while True:
        start = time.monotonic()
        check()
        try:
            with build_opener(ProxyHandler({})).open(args.url, timeout=3) as response:
                payload = response.read(4 * 1024 * 1024 + 1)
        except OSError as error:
            if not disconnected:
                image = Image.new('RGB', (1280, 720), (13, 22, 39))
                font = ImageFont.truetype(
                    '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf', 38)
                ImageDraw.Draw(image).text((90, 310), '显示连接已断开，正在恢复…',
                                          font=font, fill='white')
                check()
                frame.array[:] = np.frombuffer(image.tobytes(), dtype='<u4')
                print('AUDIO_HDMI_DISCONNECTED:', error, flush=True)
            previous_payload = None
            disconnected = True
            time.sleep(1)
            continue
        if disconnected:
            print('AUDIO_HDMI_RECOVERED', flush=True)
            disconnected = False
        if len(payload) > 4 * 1024 * 1024:
            raise ValueError('Frame too large')
        polls += 1
        if payload == previous_payload:
            if polls % 100 == 0:
                print('AUDIO_HDMI updates=%d polls=%d unchanged' % (count, polls), flush=True)
            time.sleep(max(0, 1 / args.fps - (time.monotonic() - start)))
            continue
        image = Image.open(io.BytesIO(payload))
        if image.size != (1280, 720):
            raise ValueError('Expected a 1280x720 frame')
        words = np.frombuffer(image.convert('RGB').tobytes(), dtype='<u4')
        check()
        frame.array[:] = words
        previous_payload = payload
        count += 1
        if count == 1 or count % 100 == 0:
            print('AUDIO_HDMI frames=%d address=%#x' % (count, addresses[0]), flush=True)
        time.sleep(max(0, 1 / args.fps - (time.monotonic() - start)))


if __name__ == '__main__':
    main()
