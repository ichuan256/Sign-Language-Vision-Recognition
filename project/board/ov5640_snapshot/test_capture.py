import importlib.util
import struct
import unittest
import zlib
from pathlib import Path
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location('capture', Path(__file__).with_name('capture.py'))
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

class Buffer(bytearray):
    physical_address = 0x1000000
    def flush(self): self.flushed = True
    def invalidate(self): self.invalidated = True
    def freebuffer(self): self.freed = True

class Fake:
    def __init__(self, mode='ok'):
        self.mode, self.now, self.events = mode, 0, []
        self.armed, self.polls, self.beat = False, 0, 0
        self.cr, self.sr, self.resets, self.buffer = 0, 1, 0, None
    def clock(self): return self.now
    def sleep(self, n): self.now += n
    def allocate(self, **kwargs):
        self.buffer = Buffer(c.FRAME_BYTES)
        self.buffer.freed = self.buffer.invalidated = False
        if self.mode == 'bad_address': self.buffer.physical_address = 3
        return self.buffer
    def control_write(self, address, value):
        self.events.append(('control', address, value))
        if address == 0 and value == 5: self.armed = True
    def control_read(self, address):
        if self.mode == 'init_error': return 4
        if not self.armed:
            if self.mode == 'no_pclk': return 2
            self.beat ^= 0x10000
            return 2 | self.beat
        self.polls += 1
        if self.mode == 'camera_error': return 0x62
        if self.mode == 'stale_done': return 18
        if self.mode in ('timeout', 'unsafe_reset'): return 10
        return 10 if self.polls == 1 else 18
    def dma_write(self, address, value):
        self.events.append(('dma', address, value))
        if address == c.CR:
            self.cr = value
            if value == 4:
                self.resets += 1
                if not (self.mode == 'unsafe_reset' and self.armed): self.cr, self.sr = 0, 1
            elif value == 1: self.sr = 0
    def dma_read(self, address):
        if address == c.CR: return self.cr
        if address == c.LENGTH: return c.FRAME_BYTES - (4 if self.mode == 'short' else 0)
        if address == c.SR:
            if self.armed and self.sr != 1 and self.mode == 'dma_error': return 0x40
            if self.sr == 1: return 1
            return 0x1002 if self.armed and self.polls > 1 else 0
        return 0
    def run(self):
        control = SimpleNamespace(write=self.control_write, read=self.control_read)
        dma = SimpleNamespace(write=self.dma_write, read=self.dma_read)
        return c.capture_frame(control, dma, self.allocate, timeout=.02, init_timeout=.02,
                               cleanup_timeout=.01, clock=self.clock, sleep=self.sleep)

class CaptureTests(unittest.TestCase):
    def test_success_order_and_cleanup(self):
        f = Fake(); raw, result = f.run()
        self.assertEqual(len(raw), c.FRAME_BYTES)
        self.assertEqual(result['received_bytes'], c.FRAME_BYTES)
        self.assertLess(f.events.index(('dma', c.LENGTH, c.FRAME_BYTES)), f.events.index(('control', 0, 5)))
        self.assertTrue(f.buffer.flushed and f.buffer.invalidated and f.buffer.freed)
        self.assertEqual(f.resets, 2)
    def test_capture_failures_reset_before_free(self):
        for mode in ('timeout', 'short', 'camera_error', 'dma_error', 'stale_done'):
            with self.subTest(mode=mode):
                f = Fake(mode)
                with self.assertRaises(c.CaptureError): f.run()
                self.assertTrue(f.buffer.freed)
                self.assertFalse(f.buffer.invalidated)
                self.assertEqual(f.resets, 2)
    def test_init_or_stopped_pclk_never_allocate(self):
        for mode in ('init_error', 'no_pclk'):
            f = Fake(mode)
            with self.assertRaises(c.CaptureError): f.run()
            self.assertIsNone(f.buffer)
    def test_bad_address_never_starts_dma(self):
        f = Fake('bad_address')
        with self.assertRaises(c.CaptureError): f.run()
        self.assertTrue(f.buffer.freed)
        self.assertFalse(any(e[0]=='dma' and e[1]==c.LENGTH for e in f.events))
    def test_unconfirmed_shutdown_retains_buffer(self):
        f = Fake('unsafe_reset')
        with self.assertRaisesRegex(c.CaptureError, 'retained'): f.run()
        self.assertFalse(f.buffer.freed)
        self.assertIs(c.RETAINED_BUFFERS[-1], f.buffer)
        c.RETAINED_BUFFERS.clear()
    def test_rgb565_and_png_crc_pixels(self):
        raw = bytes([0,248,224,7,31,0,255,255,0,0])
        rgb = bytes([255,0,0,0,255,0,0,0,255,255,255,255,0,0,0])
        self.assertEqual(c.rgb565_to_rgb(raw,5,1),rgb)
        data = c.png_bytes(raw,5,1)
        self.assertEqual(data[:8],bytes([137,80,78,71,13,10,26,10]))
        position, payload = 8, b''
        while position < len(data):
            size=struct.unpack('>I',data[position:position+4])[0]
            kind=data[position+4:position+8]; body=data[position+8:position+8+size]
            self.assertEqual(struct.unpack('>I',data[position+8+size:position+12+size])[0],zlib.crc32(kind+body))
            if kind==b'IDAT': payload+=body
            position+=size+12
        self.assertEqual(zlib.decompress(payload),bytes([0])+rgb)
        with self.assertRaises(c.CaptureError): c.png_bytes(raw[:-1],5,1)

if __name__=='__main__': unittest.main()
