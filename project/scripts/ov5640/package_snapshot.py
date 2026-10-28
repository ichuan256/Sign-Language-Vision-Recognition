"""Package a successfully built snapshot candidate; no board operations."""
import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from snapshot_provenance import verify

ROOT = Path(__file__).resolve().parents[3]

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,required=True,help='Sealed build evidence directory')
    parser.add_argument('--output',type=Path,required=True,help='New release directory')
    parser.add_argument('--allow-unverified-io',action='store_true',help='Explicitly package a board-unverified engineering candidate')
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
    path=args.output/'release_manifest.json'
    path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(path)

if __name__=='__main__':main()
