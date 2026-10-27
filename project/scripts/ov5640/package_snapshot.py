"""Package a successfully built snapshot candidate; no board operations."""
import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,default=ROOT/'project/analysis/ov5640_snapshot_20261027/build')
    parser.add_argument('--output',type=Path,required=True,help='New release directory')
    args=parser.parse_args()
    result=(args.build/'build_result.tcl').read_text()
    if 'set snapshot_build_complete 1' not in result:
        raise RuntimeError('Build did not pass implementation gates')
    args.output.mkdir(parents=True,exist_ok=False)
    files={}
    for kind in ('bit','hwh'):
        source=args.build/('ov5640_snapshot.'+kind)
        target=args.output/source.name
        shutil.copy2(source,target)
        files[kind]=dict(path=target.name,sha256=digest(target),size_bytes=target.stat().st_size)
    source_files=[]
    for pattern in ('project/fpga/rtl/ov5640_snapshot/*.v','project/fpga/rtl/ov5640_stereo/*.v',
                    'project/fpga/scripts/ov5640_snapshot*.tcl','project/fpga/scripts/load_ov5640_pins.tcl',
                    'project/fpga/xdc/ov5640_stereo_pins.xdc','project/analysis/ov5640_snapshot_20261027/ps_config.tcl'):
        source_files.extend(ROOT.glob(pattern))
    manifest=dict(schema_version=1,firmware_name='ov5640_snapshot_ov1_720p',
                  created_utc=datetime.now(timezone.utc).isoformat(),status='candidate_board_unverified',
                  files=files,design=dict(width=1280,height=720,pixel_format='RGB565_LE',camera=1,
                  dma='capture_dma',control='camera_control',dma_base=0x40400000,control_base=0x41200000,
                  sys_clk_hz=100000000),validation=dict(board_capture=False,external_io_timing=False,
                  notes='Sensor data/control I/O delays require specification or measurement; internal timing is separate.'),
                  sources={str(p.relative_to(ROOT)).replace(chr(92),'/'):digest(p) for p in sorted(set(source_files))})
    path=args.output/'release_manifest.json'
    path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(path)

if __name__=='__main__':main()
