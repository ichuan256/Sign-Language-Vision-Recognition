"""Board-only PL inference entry. Attach to cold-loaded overlay; never download."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

import numpy as np
from hand_runtime import HardwareBackend,HandGraph

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bit',type=Path,required=True)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--registers',type=Path,required=True)
    parser.add_argument('--model',type=Path,required=True)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    release=json.loads(args.manifest.read_text())
    for suffix in ('bit','hwh'):
        path=args.bit.with_suffix('.'+suffix)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=release['artifacts'][suffix]['sha256']:
            raise RuntimeError('bit/hwh candidate pair hash mismatch')
    before=release['board_boot_id_before_deployment']
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    if boot==before:raise RuntimeError('Cold reboot gate missing; never download on a running board')
    state=subprocess.check_output(['systemctl','show','-p','SubState','--value','bootpy.service'],universal_newlines=True).strip()
    if state!='exited':raise RuntimeError('Cold initialization has not completed')
    inputs=np.load(args.input,allow_pickle=False)
    if inputs.dtype!=np.int16 or inputs.shape!=(224,224,3):raise ValueError('Expected integer normalized ROI codes')
    args.output.mkdir(parents=True)
    report=dict(backend='PL_gemm_and_vector',cpu_neural_fallback=False,bitstream_downloaded=False,
                boot_id=boot,scope='single_hand_landmarks_PC_supplied_ROI',input_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest())
    backend=None
    try:
        start=time.perf_counter()
        backend=HardwareBackend(args.bit,args.registers)
        graph=HandGraph(args.model,backend)
        report['input_fraction']=next(s['fraction'] for s in graph.graph if s['kind']=='InputLayer')
        coordinates,metrics=graph.run(inputs)
        report.update(metrics)
        report['wall_with_setup_s']=time.perf_counter()-start
        report['coordinates_roi_units']=coordinates[:63].reshape(21,3).tolist()
        report['hand_presence']=float(coordinates[63])
        report['hand_accepted']=bool(coordinates[63]>.5)
        report['completed']=True
        np.save(args.output/'output.npy',coordinates)
    except Exception as exc:
        report.update(completed=False,error=str(exc))
        raise
    finally:
        if backend is not None:backend.close()
        (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('trace','coordinates_roi_units')},indent=2))

if __name__=='__main__':main()
