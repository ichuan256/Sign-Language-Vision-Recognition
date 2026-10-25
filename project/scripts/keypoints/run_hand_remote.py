"""Run the cold-loaded PL graph and fetch numeric/latency evidence."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import time

import numpy as np

ROOT=Path(__file__).resolve().parents[3]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--deployment',type=Path,required=True)
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--host',default='xilinx@192.168.2.99')
    a=p.parse_args()
    out=a.output.resolve()
    if out.exists() or not out.is_relative_to(ROOT/'project/_tmp'):
        raise ValueError('Use a new project/_tmp evidence directory')
    release=json.loads((a.deployment/'deployment.json').read_text())
    work=release['board_workdir']
    result=work+'/result_'+out.name
    env=dict(os.environ)
    password=env.pop('KEYPOINT_BOARD_SUDO_PASSWORD')
    q=shlex.quote
    command='env XILINX_XRT=/usr /usr/local/share/pynq-venv/bin/python -u '+q(work+'/run_hand_board.py')
    for key,value in [('bit','/home/xilinx/kws_hdmi.bit'),('manifest',work+'/manifest.json'),
        ('registers',work+'/registers.json'),('model',work+'/model'),('input',work+'/roi0.npy'),('output',result)]:
        command+=' --'+key+' '+q(value)
    command='sudo -S -p '+q('')+' '+command
    out.mkdir(parents=True)
    start=time.perf_counter()
    with (out/'console.log').open('w',encoding='utf-8') as log:
        status=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8',a.host,command],
            input=password+'\n',text=True,stdout=log,stderr=subprocess.STDOUT,env=env,timeout=600)
    elapsed=time.perf_counter()-start
    for name in ('report.json','output.npy'):
        subprocess.run(['scp',a.host+':'+result+'/'+name,str(out/name)],env=env,check=True,
                       stdout=subprocess.DEVNULL)
    if status.returncode:raise RuntimeError('Board inference failed; inspect console/report')
    report=json.loads((out/'report.json').read_text())
    output=np.load(out/'output.npy',allow_pickle=False)
    with np.load(a.reference,allow_pickle=False) as data:
        expected=data['reference'][0]
    if output.shape!=expected.shape or not np.isfinite(output).all():
        raise RuntimeError('Invalid board output')
    difference=float(np.max(np.abs(output-expected)))
    evidence=dict(scope='actual_PL_single_PC_ROI',exact_match=bool(np.array_equal(output,expected)),
        max_abs_difference=difference,output_count=int(output.size),
        board_forward_s=report['elapsed_s'],board_with_setup_s=report['wall_with_setup_s'],
        ssh_request_wall_s=elapsed,mac_calls=report['mac_calls'],vector_calls=report['vector_calls'],
        hand_presence=report['hand_presence'],input_sha256=report['input_sha256'],
        bit_sha256=release['artifacts']['bit']['sha256'],hwh_sha256=release['artifacts']['hwh']['sha256'],
        boot_id=report['boot_id'],cpu_neural_fallback=report['cpu_neural_fallback'],
        output_sha256=hashlib.sha256((out/'output.npy').read_bytes()).hexdigest())
    (out/'alignment.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(evidence,indent=2))
    if not evidence['exact_match']:raise RuntimeError('Actual PL/reference mismatch')

if __name__=='__main__':main()
