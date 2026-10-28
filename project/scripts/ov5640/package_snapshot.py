"""Package a successfully built snapshot candidate; no board operations."""
import argparse
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from snapshot_provenance import verify

ROOT = Path(__file__).resolve().parents[3]

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def hdmi_design_for_hwh(path):
    """Do not label a camera-only build as an HDMI candidate."""
    root = ET.parse(path).getroot()
    modules = {m.get('FULLNAME'): m for m in root.findall('.//MODULE')}
    required = {
        '/video/axi_vdma': 'axi_vdma',
        '/video/hdmi_out/pixel_unpack': 'pixel_unpack',
        '/video/hdmi_out/color_convert': 'color_convert',
        '/video/hdmi_out/frontend/axi_dynclk': 'axi_dynclk',
        '/video/hdmi_out/frontend/vtc_out': 'v_tc',
        '/video/hdmi_out/frontend/hdmi_out_hpd_video': 'axi_gpio',
        '/video/hdmi_out/frontend/rgb2dvi_0': 'rgb2dvi',
    }
    for name, kind in required.items():
        if name not in modules or modules[name].get('MODTYPE') != kind:
            raise ValueError('Missing HDMI HWH module: ' + name)
    for name, expected in {
        '/video/axi_vdma': {'C_INCLUDE_MM2S': '1', 'C_INCLUDE_S2MM': '0',
                            'C_NUM_FSTORES': '4', 'C_M_AXIS_MM2S_TUSER_BITS': '1'},
        '/ps7': {'C_USE_S_AXI_HP2': '1'},
    }.items():
        module = modules.get(name)
        if module is None:
            raise ValueError('Missing HWH module: ' + name)
        params = {p.get('NAME'): p.get('VALUE')
                  for p in module.findall('./PARAMETERS/PARAMETER')}
        if any(params.get(key) != value for key, value in expected.items()):
            raise ValueError('Incompatible HDMI HWH parameters: ' + name)
    return dict(hdmi_output=True, hdmi_width=1280, hdmi_height=720,
                hdmi_pixel_format='RGB888', hdmi_hierarchy='video/hdmi_out',
                hdmi_vdma='video/axi_vdma', hdmi_read_hp='HP2',
                hdmi_axi_clock_hz=100000000)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,required=True,help='Sealed build evidence directory')
    parser.add_argument('--output',type=Path,required=True,help='New release directory')
    parser.add_argument('--allow-unverified-io',action='store_true',help='Explicitly package a board-unverified engineering candidate')
    parser.add_argument('--hdmi-output',action='store_true',help='Require and describe the integrated HDMI output hardware')
    args=parser.parse_args()
    provenance = verify(ROOT, args.build)
    io_status = json.loads((args.build/'external_io_status.json').read_text())
    if not io_status['constrained'] and not args.allow_unverified_io:
        raise RuntimeError('External I/O timing incomplete; candidate requires --allow-unverified-io')
    result=(args.build/'build_result.tcl').read_text()
    if 'set snapshot_build_complete 1' not in result:
        raise RuntimeError('Build did not pass implementation gates')
    if 'set snapshot_sccb_structure_pass 1' not in result:
        raise RuntimeError('Build did not pass SCCB tristate/readback structural gate')
    hdmi_design = hdmi_design_for_hwh(args.build/'ov5640_snapshot.hwh') if args.hdmi_output else {}
    args.output.mkdir(parents=True,exist_ok=False)
    files={}
    for kind in ('bit','hwh'):
        source=args.build/('ov5640_snapshot.'+kind)
        target=args.output/source.name
        shutil.copy2(source,target)
        files[kind]=dict(path=target.name,sha256=digest(target),size_bytes=target.stat().st_size)
        if files[kind]['sha256'] != provenance['artifacts'][target.name]:
            raise RuntimeError('Artifact changed while packaging: ' + target.name)
    shutil.copy2(args.build/'build_provenance.json', args.output/'build_provenance.json')
    manifest=dict(schema_version=1,firmware_name='ov5640_snapshot_ov1_720p',
                  created_utc=datetime.now(timezone.utc).isoformat(),status='candidate_board_unverified',
                  files=files,design=dict(width=1280,height=720,pixel_format='RGB565_LE',camera=1,
                  dma='capture_dma',control='camera_control',dma_base=0x40400000,control_base=0x41200000,
                  sys_clk_hz=100000000,control_width=10,input_polarity_version=1,
                  pixel_loss_threshold_percent=5.0),
                  validation=dict(board_capture=False,external_io_timing=False,
                  external_io_constraints=io_status['constrained'],
                  notes='Constraints and physical-board validation are separate; external_io_timing remains false until board validation.'),
                  sources=provenance['sources'],
                  build_provenance=dict(path='build_provenance.json',sha256=digest(args.output/'build_provenance.json')))
    if args.hdmi_output:
        manifest['firmware_name'] = 'ov5640_snapshot_hdmi'
        manifest['design'].update(hdmi_design)
        manifest['validation']['board_hdmi'] = False
    path=args.output/'release_manifest.json'
    path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(path)

if __name__=='__main__':main()
