"""Package an implemented dual candidate, never program hardware."""
import argparse,hashlib,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'project/board/ov5640_stereo'))
from stereo_stream import verify


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    output=a.output.resolve()
    if not output.is_relative_to(ROOT/'project/board/ov5640_stereo') or output.exists():raise ValueError('New stereo release path required')
    result=(a.build/'build_result.tcl').read_text()
    if 'set snapshot_build_complete 1' not in result:raise RuntimeError('Implemented bitstream gate incomplete')
    output.mkdir(parents=True)
    for kind in ('bit','hwh'):shutil.copyfile(a.build/('ov5640_snapshot.'+kind),output/('ov5640_stereo.'+kind))
    manifest=dict(schema='ov5640-dual-v1',status='candidate_board_unverified',width=1280,height=720,format='RGB565_LE',
        files={kind:dict(path='ov5640_stereo.'+kind,sha256=sha(output/('ov5640_stereo.'+kind))) for kind in ('bit','hwh')},
        channels=[dict(id=1,camera_ip='camera',control_ip='camera_control',dma_ip='capture_dma',control_base=0x41200000,dma_base=0x40400000),
            dict(id=2,camera_ip='camera_right',control_ip='camera_control_right',dma_ip='capture_dma_right',control_base=0x41210000,dma_base=0x40410000)],
        exposure_synchronized=False,external_io_timing_verified=False,HDMI=False,neural_inference='PC teacher; none in this bitstream',
        build_directory=a.build.resolve().relative_to(ROOT).as_posix(),timing_gate=result,
        software={name:sha(ROOT/relative) for name,relative in {
            'capture.py':'project/board/ov5640_snapshot/capture.py',
            'continuous_capture.py':'project/board/ov5640_snapshot/continuous_capture.py',
            'stereo_stream.py':'project/board/ov5640_stereo/stereo_stream.py'}.items()})
    path=output/'release_manifest.json';path.write_text(json.dumps(manifest,indent=2)+'\n')
    verify(path)
    for name in ('timing_routed.rpt','utilization.rpt','sccb_structure.txt','external_io_status.json'):
        shutil.copyfile(a.build/name,output/name)
    print(json.dumps(dict(packaged=True,manifest=str(path.relative_to(ROOT)),files=manifest['files'])),flush=True)


if __name__=='__main__':main()
