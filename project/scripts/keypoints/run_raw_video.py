"""Stage a short raw video once, then run board-local guarded HDMI replay; never change firmware."""
import argparse
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from vision.keypoints.hdmi_link import HDMILink
from vision.keypoints.student_data import digest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--deployment',type=Path,required=True);p.add_argument('--package',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--seconds',type=int,default=120)
    p.add_argument('--board',default='xilinx@192.168.2.99')
    a=p.parse_args();out=a.output.resolve()
    if out.exists() or not out.is_relative_to(ROOT/'project/_tmp') or not re.fullmatch(r'[A-Za-z0-9_]+',out.name):raise ValueError('New safe project/_tmp directory required')
    if not 10<=a.seconds<=120:raise ValueError('Bounded seconds 10..120 required')
    meta=json.loads((a.package/'manifest.json').read_text())
    if digest(a.package/'video.rgb')!=meta['raw_sha256']:raise ValueError('Raw package SHA mismatch')
    env=dict(os.environ);password=env.pop('KEYPOINT_BOARD_SUDO_PASSWORD')
    link=HDMILink(SimpleNamespace(board=a.board,release_manifest=a.deployment/'deployment.json'),password)
    prepared=link.prepare();release=json.loads((a.deployment/'deployment.json').read_text())
    script=ROOT/'project/board/keypoints/raw_frame_replay.py';sha=digest(script)
    remote_script='/home/xilinx/raw_frame_replay_'+sha[:12]+'.py';q=shlex.quote
    work=release['board_workdir']+'/raw_'+out.name
    options=['-o','BatchMode=yes','-o','ConnectTimeout=8']
    exists=link.ssh('test -e '+q(remote_script)+' && echo yes || true')=='yes'
    if not exists:subprocess.run(['scp',str(script),a.board+':'+remote_script],env=env,check=True,stdout=subprocess.DEVNULL)
    if link.ssh('sha256sum '+q(remote_script)).split()[0]!=sha:raise RuntimeError('Versioned script SHA mismatch')
    link.ssh('mkdir '+q(work));out.mkdir(parents=True)
    subprocess.run(['scp',str(a.package/'video.rgb'),str(a.package/'manifest.json'),a.board+':'+work+'/'],env=env,check=True,stdout=subprocess.DEVNULL)
    command='sudo -S -p '+q('')+' timeout --signal=TERM '+str(a.seconds+90)+' env XILINX_XRT=/usr '+q('/usr/local/share/pynq-venv/bin/python')+' -u '+q(remote_script)
    for key,value in [('manifest',work+'/manifest.json'),('raw',work+'/video.rgb'),('owner-pid',str(prepared['owner_pid'])),
        ('seconds',str(a.seconds)),('output',work+'/result'),('release',release['board_workdir']+'/manifest.json')]:
        command+=' --'+key+' '+q(value)
    print('RAW_PACKAGE_STAGED waiting for RAW_REPLAY_READY in console.log',flush=True)
    with (out/'console.log').open('w',encoding='utf-8') as log:
        result=subprocess.run(['ssh',*options,a.board,command],input=password+'\n',text=True,stdout=log,stderr=subprocess.STDOUT,env=env,timeout=a.seconds+120)
    if result.returncode:raise RuntimeError('Raw replay failed; inspect console.log')
    subprocess.run(['scp',a.board+':'+work+'/result/report.json',str(out/'report.json')],env=env,check=True,stdout=subprocess.DEVNULL)
    report=json.loads((out/'report.json').read_text());report['firmware_pair']=prepared
    report['framebuffer_write_gate_20fps_passed']=report['measured_framebuffer_writes_per_s']>=20 and report['unique_source_frames']>1
    report['screen_visually_confirmed']=False
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
