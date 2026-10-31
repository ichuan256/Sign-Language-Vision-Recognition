"""Start the frozen teacher + 5-word sign head on USB, without a board."""
import argparse
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import build_opener,ProxyHandler

ROOT=Path(__file__).resolve().parents[2]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--camera',type=int,default=0)
    parser.add_argument('--seconds',type=int,default=86400)
    args=parser.parse_args()
    if not 0<=args.camera<=9 or not 30<=args.seconds<=86400:raise ValueError('Invalid camera index or duration')
    pointer=json.loads((ROOT/'vision/data/models/usb_sign_current.json').read_text(encoding='utf-8'))
    model=(ROOT/pointer['model']).resolve()
    if not model.is_relative_to(ROOT/'vision/data/models'):raise ValueError('Invalid model path')
    if hashlib.sha256(model.read_bytes()).hexdigest()!=pointer['sha256']:raise ValueError('Model SHA mismatch')
    for port in (18784,18785):
        with socket.socket() as probe:
            if probe.connect_ex(('127.0.0.1',port))==0:raise RuntimeError('USB sign demo already running or port occupied: '+str(port))
    out=ROOT/'project/_tmp'/('usb_sign_'+str(time.time_ns()));out.mkdir()
    command=[sys.executable,'-X','utf8','-m','vision.keypoints.recording_demo','--output',str(out/'run'),
        '--seconds',str(args.seconds),'--mode','pc','--no-pl','--camera',str(args.camera),
        '--control-port','18785','--frame-port','18784','--sign-model',str(model)]
    with (out/'stdout.log').open('ab') as stdout,(out/'stderr.log').open('ab') as stderr:
        child=subprocess.Popen(command,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,
            creationflags=subprocess.CREATE_NO_WINDOW|subprocess.CREATE_NEW_PROCESS_GROUP)
    report=dict(pid=child.pid,url='http://127.0.0.1:18785',output=str(out.relative_to(ROOT)),
        PC_inference=True,board_required=False,model_sha256=pointer['sha256'])
    (ROOT/'project/_tmp/usb_sign_launch.json').write_text(json.dumps(report,indent=2)+'\n')
    opener=build_opener(ProxyHandler({}));deadline=time.monotonic()+60
    while time.monotonic()<deadline:
        if child.poll() is not None:raise RuntimeError('USB detection failed; inspect '+str(out/'stderr.log'))
        try:
            with opener.open('http://127.0.0.1:18784/state',timeout=2) as response:state=json.load(response)
            if state['frames_published']>0:break
        except OSError:pass
        time.sleep(.5)
    else:raise RuntimeError('No first camera frame; inspect '+str(out/'stderr.log'))
    print(json.dumps(report),flush=True)


if __name__=='__main__':main()
