"""Persistent PL graph over SSH stdin/stdout. Only one request is in flight."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import numpy as np
try:
    from .hand_runtime import HandGraph
    from .hand_layer_runtime import LayerHardwareBackend
except ImportError:
    from hand_runtime import HandGraph
    from hand_layer_runtime import LayerHardwareBackend

def read_exact(stream,n):
    parts=[]
    while n:
        data=stream.read(n)
        if not data:raise EOFError('Truncated ROI packet')
        parts.append(data);n-=len(data)
    return b''.join(parts)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True)
    p.add_argument('--seconds',type=float,default=660);a=p.parse_args();work=a.work
    release=json.loads((work/'manifest.json').read_text());bit=Path('/home/xilinx/kws_hdmi.bit')
    for suffix in ('bit','hwh'):
        if hashlib.sha256(bit.with_suffix('.'+suffix).read_bytes()).hexdigest()!=release['artifacts'][suffix]['sha256']:
            raise RuntimeError('Pair mismatch; no MMIO allowed')
    if Path('/proc/sys/kernel/random/boot_id').read_text().strip()==release['board_boot_id_before_deployment']:
        raise RuntimeError('Cold boot missing')
    if subprocess.check_output(['systemctl','show','-p','SubState','--value','bootpy.service'],text=True).strip()!='exited':
        raise RuntimeError('Cold initialization pending')
    backend=LayerHardwareBackend(bit,work/'registers.json')
    try:
        graph=HandGraph(work/'model',backend)
        fraction=next(s['fraction'] for s in graph.graph if s['kind']=='InputLayer')
        print(json.dumps(dict(event='ready',input_fraction=fraction,backend=backend.name)),flush=True)
        start=time.monotonic();count=0
        while time.monotonic()-start<a.seconds:
            line=sys.stdin.buffer.readline(4097)
            if not line:break
            if len(line)>4096:raise ValueError('Oversized request header')
            header=json.loads(line)
            raw=read_exact(sys.stdin.buffer,224*224*3*2)
            roi=np.frombuffer(raw,dtype='<i2').reshape(224,224,3)
            backend.mac_calls=backend.vector_calls=0
            coordinates,metrics=graph.run(roi,verbose=False);count+=1
            print(json.dumps(dict(event='result',frame_id=header['frame_id'],source_timestamp_s=header['source_timestamp_s'],
                sequence=count,outputs=coordinates.tolist(),board_forward_s=metrics['elapsed_s'],
                mac_calls=metrics['mac_calls'],vector_calls=metrics['vector_calls'],
                input_sha256=hashlib.sha256(raw).hexdigest(),output_sha256=hashlib.sha256(coordinates.tobytes()).hexdigest(),
                cpu_neural_fallback=False)),flush=True)
    finally:backend.close()
if __name__=='__main__':main()
