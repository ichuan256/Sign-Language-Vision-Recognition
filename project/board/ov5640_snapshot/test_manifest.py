import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from test_capture import c

ROOT=Path(__file__).resolve().parents[3]
HWH=Path(__file__).with_name('release')/'ov5640_snapshot.hwh'

class ManifestTests(unittest.TestCase):
    def fixture(self,d):
        p=Path(d);(p/'candidate.bit').write_bytes(b'test only')
        (p/'candidate.hwh').write_bytes(HWH.read_bytes())
        m=dict(schema_version=1,files={k:dict(path='candidate.'+k,sha256=c.sha256(p/('candidate.'+k))) for k in ('bit','hwh')},design=dict(width=1280,height=720,pixel_format='RGB565_LE',camera=1,dma='capture_dma',control='camera_control',dma_base=c.DMA_BASE,control_base=c.CONTROL_BASE,sys_clk_hz=100000000))
        path=p/'release_manifest.json';path.write_text(json.dumps(m));return path,m
    def test_hash_address_contract_rejections(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'project/analysis/ov5640_snapshot_20261027') as d:
            path,m=self.fixture(d);c.verify_manifest(path)
            (Path(d)/'candidate.bit').write_bytes(b'wrong')
            with self.assertRaisesRegex(c.CaptureError,'SHA256'):c.verify_manifest(path)
            path,m=self.fixture(d);hwh=Path(d)/'candidate.hwh'
            hwh.write_text(hwh.read_text(encoding='utf-8-sig').replace('0x40400000','0x40410000'))
            m['files']['hwh']['sha256']=c.sha256(hwh);path.write_text(json.dumps(m))
            with self.assertRaisesRegex(c.CaptureError,'address'):c.verify_manifest(path)
            path,m=self.fixture(d);m['design']['camera']=2;path.write_text(json.dumps(m))
            with self.assertRaisesRegex(c.CaptureError,'camera'):c.verify_manifest(path)
    def test_cli_ack_and_no_overwrite(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'project/analysis/ov5640_snapshot_20261027') as d:
            path,m=self.fixture(d);out=Path(d)/'output'
            self.assertEqual(c.main(['--manifest',str(path),'--output',str(out)]),1)
            self.assertFalse(out.exists());out.mkdir()
            with patch.object(c,'board_capture') as board:
                self.assertEqual(c.main(['--manifest',str(path),'--output',str(out),'--assume-cold-boot']),1)
                board.assert_not_called()
    def test_attach_no_download_clock_gate(self):
        overlay=SimpleNamespace(ip_dict={n:dict(phys_addr=b,type='xilinx.com:ip:'+i+':1.0') for n,b,i in [('capture_dma',c.DMA_BASE,'axi_dma'),('camera_control',c.CONTROL_BASE,'axi_gpio')]})
        calls=[]
        def attach(*a,**kw):calls.append(kw);return overlay
        fake=SimpleNamespace(Overlay=attach,MMIO=lambda *a:None,Clocks=SimpleNamespace(fclk0_mhz=100.),allocate=None)
        with patch.dict(sys.modules,{'pynq':fake}),patch.object(c,'capture_frame',return_value=(b'',{})) as capture:
            c.board_capture({'bit':Path('candidate.bit')},1,1)
            capture.assert_called_once();self.assertEqual(calls,[dict(download=False)])
            fake.Clocks.fclk0_mhz=125.
            with self.assertRaisesRegex(c.CaptureError,'100 MHz'):c.board_capture({'bit':Path('candidate.bit')},1,1)

if __name__=='__main__':unittest.main()
