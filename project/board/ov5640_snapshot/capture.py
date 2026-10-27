"""Capture OV1 once; never load or reconfigure the FPGA."""
import argparse
import hashlib
import json
import math
import struct
import sys
import time
import xml.etree.ElementTree as ET
import zlib
from datetime import datetime, timezone
from pathlib import Path

WIDTH, HEIGHT = 1280, 720
FRAME_BYTES = WIDTH * HEIGHT * 2
DMA_BASE, CONTROL_BASE = 0x40400000, 0x41200000
CR, SR, ADDR, ADDR_MSB, LENGTH = 0x30, 0x34, 0x48, 0x4C, 0x58
RETAINED_BUFFERS = []

class CaptureError(RuntimeError):
    pass

def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()

def verify_manifest(path):
    path = Path(path).resolve()
    manifest = json.loads(path.read_text(encoding='utf-8'))
    if manifest.get('schema_version') != 1:
        raise CaptureError('Unsupported manifest schema')
    expected = dict(width=WIDTH, height=HEIGHT, pixel_format='RGB565_LE',
                    camera=1, dma='capture_dma', control='camera_control',
                    dma_base=DMA_BASE, control_base=CONTROL_BASE, sys_clk_hz=100000000)
    for key, value in expected.items():
        if manifest.get('design', {}).get(key) != value:
            raise CaptureError(f'Manifest design.{key}: expected {value!r}')
    files = {}
    for kind in ('bit', 'hwh'):
        item = manifest['files'][kind]
        relative = Path(item['path'])
        candidate = (path.parent / relative).resolve()
        if relative.is_absolute() or '..' in relative.parts or path.parent not in candidate.parents:
            raise CaptureError('Firmware path escapes release directory')
        if candidate.suffix != '.' + kind or sha256(candidate) != item['sha256']:
            raise CaptureError(f'{kind} SHA256 or file type mismatch')
        files[kind] = candidate
    if files['bit'].with_suffix('.hwh') != files['hwh']:
        raise CaptureError('bit/HWH must share basename and directory')
    root = ET.parse(files['hwh']).getroot()
    modules = {m.get('INSTANCE'): m for m in root.findall('.//MODULE')}
    checks = {'capture_dma': ('axi_dma', {'C_INCLUDE_SG': '0', 'C_INCLUDE_MM2S': '0',
              'C_INCLUDE_S2MM': '1', 'C_SG_LENGTH_WIDTH': '23',
              'C_M_AXI_S2MM_DATA_WIDTH': '64', 'C_S_AXIS_S2MM_TDATA_WIDTH': '32',
              'C_INCLUDE_S2MM_DRE': '0'}),
              'camera': ('ov5640_snapshot', {'CAMERA': '1', 'FRAME_WIDTH': '1280',
                         'FRAME_HEIGHT': '720', 'SYS_CLK_HZ': '100000000'}),
              'camera_control': ('axi_gpio', {'C_GPIO_WIDTH': '3', 'C_GPIO2_WIDTH': '32'})}
    for name, (kind, required) in checks.items():
        module = modules.get(name)
        if module is None or module.get('MODTYPE') != kind:
            raise CaptureError(f'Wrong HWH IP: {name}')
        params = {p.get('NAME'): p.get('VALUE') for p in module.findall('./PARAMETERS/PARAMETER')}
        if any(params.get(k) != v for k, v in required.items()):
            raise CaptureError(f'Incompatible HWH parameters: {name}')
    for name, base in (('capture_dma', DMA_BASE), ('camera_control', CONTROL_BASE)):
        ranges = [r for r in root.findall('.//MEMRANGE') if r.get('INSTANCE') == name
                  and r.get('MEMTYPE') == 'REGISTER']
        if len(ranges) != 1 or int(ranges[0].get('BASEVALUE', '-1'), 0) != base:
            raise CaptureError(f'Wrong HWH address: {name}')
    return manifest, files

def verify_overlay(overlay):
    for name, base, ip in (('capture_dma', DMA_BASE, 'axi_dma'),
                           ('camera_control', CONTROL_BASE, 'axi_gpio')):
        item = overlay.ip_dict.get(name, {})
        if item.get('phys_addr') != base or f':{ip}:' not in item.get('type', ''):
            raise CaptureError(f'Overlay metadata mismatch: {name}')

def rgb565_to_rgb(raw, width=WIDTH, height=HEIGHT):
    if width < 1 or height < 1 or len(raw) != width * height * 2:
        raise CaptureError('RGB565 byte count mismatch')
    rgb = bytearray(width * height * 3)
    for i in range(width * height):
        px = raw[2*i] | raw[2*i+1] << 8
        r, g, b = (px >> 11) & 31, (px >> 5) & 63, px & 31
        rgb[3*i:3*i+3] = bytes(((r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2)))
    return bytes(rgb)

def png_bytes(raw, width=WIDTH, height=HEIGHT):
    rgb = rgb565_to_rgb(raw, width, height)
    def chunk(name, data):
        return struct.pack('>I', len(data)) + name + data + struct.pack('>I', zlib.crc32(name + data))
    scan = b''.join(bytes([0]) + rgb[y*width*3:(y+1)*width*3] for y in range(height))
    return (bytes([137,80,78,71,13,10,26,10]) + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(scan)) + chunk(b'IEND', b''))

def wait_until(predicate, timeout, label, clock, sleep):
    deadline = clock() + timeout
    while True:
        if predicate():
            return
        if clock() >= deadline:
            raise CaptureError(f'Timeout: {label}')
        sleep(0.001)

def quiesce_dma(dma, timeout, clock, sleep):
    dma.write(CR, 4)
    wait_until(lambda: not (dma.read(CR) & 4) and bool(dma.read(SR) & 1),
               timeout, 'DMA reset complete and Halted', clock, sleep)

def capture_frame(control, dma, allocate, timeout=5.0, init_timeout=30.0,
                  cleanup_timeout=2.0, clock=time.monotonic, sleep=time.sleep):
    buffer, owned = None, False
    values = {}
    try:
        control.write(4, 0)
        control.write(12, 0xFFFFFFFF)
        control.write(0, 0)
        sleep(0.002)
        quiesce_dma(dma, cleanup_timeout, clock, sleep)
        control.write(0, 1)
        sleep(0.002)
        control.write(0, 3)
        sleep(0.001)
        control.write(0, 1)
        def initialized():
            status = control.read(8)
            if status & 4:
                raise CaptureError(f'SCCB initialization error: status=0x{status:08x}')
            return bool(status & 2) and not (status & 1)
        wait_until(initialized, init_timeout, 'camera initialization', clock, sleep)
        initial = control.read(8)
        wait_until(lambda: bool((control.read(8) ^ initial) & (1 << 16)),
                   min(timeout, 1.0), 'PCLK heartbeat', clock, sleep)
        buffer = allocate(shape=(FRAME_BYTES,), dtype='u1')
        address = int(buffer.physical_address)
        if address % 8 or address < 0x100000 or address + FRAME_BYTES > 0x20000000:
            raise CaptureError(f'Invalid aligned DDR buffer address: 0x{address:x}')
        buffer.flush()  # remove dirty CPU cache lines before device writes
        dma.write(SR, 0x7000)
        dma.write(CR, 1)
        wait_until(lambda: not (dma.read(SR) & 1), cleanup_timeout, 'DMA running', clock, sleep)
        dma.write(ADDR, address)
        dma.write(ADDR_MSB, 0)
        owned = True
        dma.write(LENGTH, FRAME_BYTES)
        control.write(0, 5)
        saw_busy = False
        def complete():
            nonlocal saw_busy
            status, dma_status = control.read(8), dma.read(SR)
            values.update(camera_status=status, dma_status=dma_status)
            if status & 0x64:
                raise CaptureError(f'Camera capture error/overflow: status=0x{status:08x}')
            if dma_status & 0x770:
                raise CaptureError(f'DMA error: DMASR=0x{dma_status:08x}')
            saw_busy |= bool(status & 8)
            return saw_busy and bool(status & 16) and bool(dma_status & 2) and bool(dma_status & 0x1000)
        wait_until(complete, timeout, 'complete frame and DMA IOC/Idle', clock, sleep)
        actual = dma.read(LENGTH)
        values.update(received_bytes=actual, physical_address=address)
        if actual != FRAME_BYTES:
            raise CaptureError(f'Wrong received bytes: {actual}; expected {FRAME_BYTES}')
        quiesce_dma(dma, cleanup_timeout, clock, sleep)
        owned = False
        buffer.invalidate()
        raw = memoryview(buffer).tobytes()
        if len(raw) != FRAME_BYTES:
            raise CaptureError('Buffer byte count mismatch')
        return raw, values
    finally:
        if buffer is not None:
            if owned:
                try:
                    quiesce_dma(dma, cleanup_timeout, clock, sleep)
                    owned = False
                except BaseException:
                    RETAINED_BUFFERS.append(buffer)
                    raise CaptureError('DMA shutdown unconfirmed; buffer retained. Power OFF before terminating this process.')
            if not owned:
                buffer.freebuffer()
        control.write(0, 0)

def board_capture(files, timeout, init_timeout):
    from pynq import Overlay, MMIO, Clocks, allocate
    overlay = Overlay(str(files['bit']), download=False)
    verify_overlay(overlay)
    frequency = float(Clocks.fclk0_mhz)
    if not math.isfinite(frequency) or abs(frequency - 100.0) > 1.0:
        raise CaptureError(f'FCLK0 must already be 100 MHz; current {frequency}. Arrange a cold boot.')
    return capture_frame(MMIO(CONTROL_BASE, 0x10000), MMIO(DMA_BASE, 0x10000),
                         allocate, timeout=timeout, init_timeout=init_timeout)

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path, help='New directory; never overwrite')
    parser.add_argument('--assume-cold-boot', action='store_true')
    parser.add_argument('--verify-only', action='store_true', help='Host-only SHA256/HWH checks')
    parser.add_argument('--timeout', type=float, default=5.0)
    parser.add_argument('--init-timeout', type=float, default=30.0)
    args = parser.parse_args(argv)
    try:
        manifest, files = verify_manifest(args.manifest)
        if args.verify_only:
            print('PASS: paired hashes, HWH IP configuration and addresses')
            return 0
        if not args.assume_cold_boot:
            raise CaptureError('Require --assume-cold-boot; file hashes and PL cache cannot identify running hardware')
        if not all(math.isfinite(v) and v > 0 for v in (args.timeout, args.init_timeout)):
            raise CaptureError('Timeouts must be finite positive seconds')
        args.output.mkdir(parents=True, exist_ok=False)
        raw, values = board_capture(files, args.timeout, args.init_timeout)
        (args.output / 'frame.raw').write_bytes(raw)
        (args.output / 'frame.png').write_bytes(png_bytes(raw))
        values.update(schema_version=1, created_utc=datetime.now(timezone.utc).isoformat(),
                      firmware_manifest=manifest, frame_sha256=hashlib.sha256(raw).hexdigest())
        (args.output / 'capture.json').write_text(json.dumps(values, indent=2), encoding='utf-8')
        print('Captured: ' + str(args.output / 'frame.png'))
        return 0
    except (CaptureError, OSError, ValueError, KeyError, ET.ParseError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        if RETAINED_BUFFERS:
            print('Keeping process and DMA buffer alive. Power OFF the board before terminating.', file=sys.stderr, flush=True)
            while True:
                try:
                    time.sleep(1)
                except KeyboardInterrupt:
                    print('Power OFF before terminating.', file=sys.stderr, flush=True)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
