"""Collect current HDMI state without downloading/configuring hardware.

Run in a local terminal. The sudo password is read without echo and sent only
through SSH stdin. Evidence contains register values and process identity.
"""
import argparse
import getpass
import json
from pathlib import Path
import shlex
import subprocess
import time


REMOTE = r'''
import hashlib,json,time
from pathlib import Path
root=Path('/home/xilinx/ov1_hdmi_20261031')
manifest=json.loads((root/'release/release_manifest.json').read_text())
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
marker=json.loads(Path('/run/ov1_hdmi_boot.json').read_text())
assert marker['boot_id']==boot
assert marker['bit_sha256']==manifest['files']['bit']['sha256']
assert manifest['design']['hdmi_hpd_input'] is True
hashes={}
for kind in ('bit','hwh'):
    item=manifest['files'][kind]; path=(root/'release'/item['path']).resolve()
    assert path.parent==root/'release' and path.suffix=='.'+kind
    hashes[kind]=hashlib.sha256(path.read_bytes()).hexdigest()
    assert hashes[kind]==item['sha256']
from pynq import MMIO
status=MMIO(0x41210000,65536)
vdma=MMIO(0x44a00000,65536)
capture=MMIO(0x40400000,65536)
vtc=MMIO(0x44a20000,65536)
dynclk=MMIO(0x44a10000,65536)
flags_names=manifest['design']['video_status']['flags']
def owner():
    value=json.loads((root/'color_probe.json').read_text())
    p=Path('/proc')/str(value['pid'])
    value['identity_matches']=False
    if p.exists():
        stat=(p/'stat').read_text().rsplit(')',1)[1].split()
        value['identity_matches']=(int(stat[19])==value['pid_start_ticks'] and value['boot_id']==boot)
        value['process_state']=stat[0]
    return value
def registers(mmio,offsets):return {hex(o):hex(mmio.read(o)) for o in offsets}
def emit(value):print(json.dumps(value),flush=True)
emit(dict(event='initial',boot_id=boot,hashes=hashes,owner=owner(),
    boot_py_sha256=hashlib.sha256(Path('/boot/boot.py').read_bytes()).hexdigest(),
    vdma=registers(vdma,[0,4,0x28,0x2c,0x50,0x54,0x58,0x5c,0x60,0x64]),
    capture=registers(capture,[0x30,0x34]),
    vtc=registers(vtc,list(range(0,0x30,4))+list(range(0x60,0xa0,4))),
    dynclk=registers(dynclk,list(range(0,0x24,4))),
    downloaded=False,register_writes=False))
for index in range(90):
    raw=status.read(0);flags=status.read(8)&255
    emit(dict(event='sample',index=index,monotonic_s=time.monotonic(),
        status=hex(raw),VTG_lag=raw>>16,flags=flags,
        **{n:bool(flags&(1<<i)) for i,n in enumerate(flags_names)},
        vdma_status=hex(vdma.read(4)),capture_status=hex(capture.read(0x34))))
    time.sleep(2)
emit(dict(event='final',owner=owner(),downloaded=False,register_writes=False))
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board',default='xilinx@192.168.2.99')
    parser.add_argument('--samples',type=int,default=90)
    args=parser.parse_args()
    if not 2<=args.samples<=300:parser.error('--samples must be between 2 and 300')
    root=Path(__file__).resolve().parents[2]
    out=root/'project/analysis/hdmi_recovery_20261101'/('probe_'+str(time.time_ns()))
    out.mkdir(parents=True,exist_ok=False)
    print('READ ONLY: no bit download, no register writes, no restart.',flush=True)
    print('Evidence: '+str(out),flush=True)
    password=getpass.getpass('Board sudo password (hidden): ')
    source=REMOTE.replace('range(90)', 'range('+str(args.samples)+')')
    command="sudo -S -p '' env XILINX_XRT=/usr /usr/local/share/pynq-venv/bin/python -u -c "+shlex.quote(source)
    with (out/'stderr.log').open('w',encoding='utf-8') as err:
        child=subprocess.Popen(['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=8',args.board,command],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,encoding='utf-8')
        child.stdin.write(password+'\n');child.stdin.flush();child.stdin.close()
        password=None
        with (out/'samples.jsonl').open('w',encoding='utf-8') as evidence:
            for line in child.stdout:
                value=json.loads(line)
                evidence.write(line);evidence.flush()
                if value['event']=='sample':
                    print('Sample %02d: HPD_n=%s MMCM=%s video=%s underflow=%s overflow=%s VDMA=%s' %
                        (value['index'],value['HPD_n'],value['MMCM_locked'],value['video_locked'],
                         value['underflow'],value['overflow'],value['vdma_status']),flush=True)
                else:print(json.dumps(value,ensure_ascii=False),flush=True)
        code=child.wait()
    print('Finished, exit='+str(code),flush=True)
    if code:print((out/'stderr.log').read_text(encoding='utf-8'),flush=True)
    input('Press Enter to close. ')


if __name__=='__main__':main()
