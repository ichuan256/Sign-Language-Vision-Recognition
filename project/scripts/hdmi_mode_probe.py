"""Safely switch the existing cold-loaded candidate to a 640x480 color probe."""
import ast
import base64
import getpass
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import time

REMOTE=r'''
import base64,hashlib,json,os,signal,subprocess,time
from pathlib import Path
from pynq import MMIO
root=Path('/home/xilinx/ov1_hdmi_20261031')
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
marker=json.loads(Path('/run/ov1_hdmi_boot.json').read_text())
m=json.loads((root/'release/release_manifest.json').read_text())
assert marker['boot_id']==boot and marker['bit_sha256']==m['files']['bit']['sha256']
assert m['design']['hdmi_hpd_input'] is True
for k in ('bit','hwh'):
    item=m['files'][k];assert hashlib.sha256((root/'release'/item['path']).read_bytes()).hexdigest()==item['sha256']
assert not json.loads((root/'split_writer.json').read_text()).get('active')
assert MMIO(0x40400000,65536).read(0x34)&1
status=MMIO(0x41210000,65536);vdma=MMIO(0x44a00000,65536)
assert not status.read(8)&64, 'Screen is not detected'
file=root/'color_probe.json';owner=json.loads(file.read_text());proc=Path('/proc')/str(owner['pid'])
assert owner['active'] and not owner['closing'] and owner['boot_id']==boot
assert int((proc/'stat').read_text().rsplit(')',1)[1].split()[19])==owner['pid_start_ticks']
assert 'hdmi_color_probe.py' in (proc/'cmdline').read_bytes().decode()
assert owner['width']==1280 and owner['height']==720
assert vdma.read(0x5c)==owner['frame_address']
mem=MMIO(owner['frame_address'],owner['frame_bytes']).array.view('uint8')
colors=[]
for x in (160,480,800,1120):
    i=(360*1280+x)*3;colors.append([int(v) for v in mem[i:i+3]])
before=dict(event='before',boot_id=boot,owner=owner,BGR_pixels=colors,
    pixel_unpack={hex(o):hex(MMIO(0x40030000,65536).read(o)) for o in (0,0x10)},
    color_control=hex(MMIO(0x40010000,65536).read(0)))
print(json.dumps(before),flush=True)
del mem
folder=root/PROBE_NAME;folder.mkdir(exist_ok=False)
helper=folder/'hdmi_color_probe.py';data=base64.b64decode(HELPER_B64)
assert hashlib.sha256(data).hexdigest()==HELPER_SHA
helper.write_bytes(data)
(folder/'before.json').write_text(json.dumps(before,indent=2))
os.kill(owner['pid'],signal.SIGINT)
deadline=time.monotonic()+12
while time.monotonic()<deadline:
    state=json.loads(file.read_text())
    if state.get('Halted') and not proc.exists():break
    time.sleep(.1)
else:raise RuntimeError('Prior output shutdown not confirmed; no reconfiguration attempted')
assert vdma.read(4)&1
print(json.dumps(dict(event='old_owner_stopped',Halted=True,pid=owner['pid'])),flush=True)
with (folder/'stdout.log').open('ab') as out,(folder/'stderr.log').open('ab') as err:
    child=subprocess.Popen(['/usr/local/share/pynq-venv/bin/python','-u',str(helper)],
        stdin=subprocess.DEVNULL,stdout=out,stderr=err,start_new_session=True)
deadline=time.monotonic()+30
while time.monotonic()<deadline:
    state=json.loads(file.read_text())
    if state.get('active') and state['pid']==child.pid:break
    assert child.poll() is None, 'VGA output failed; inspect '+str(folder/'stderr.log')
    time.sleep(.2)
else:raise RuntimeError('VGA owner did not become ready')
assert state['width']==640 and state['height']==480
samples=[]
for _ in range(16):
    samples.append(dict(status=hex(status.read(0)),flags=status.read(8),vdma=hex(vdma.read(4))))
    time.sleep(.1)
result=dict(event='vga_started',owner=state,samples=samples,downloaded=False,rebooted=False,
    prior_owner_halted=True,probe_directory=str(folder))
(folder/'started.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result),flush=True)
'''


def main():
    root=Path(__file__).resolve().parents[2]
    stamp=str(time.time_ns())
    out=root/'project/analysis/hdmi_recovery_20261101'/('vga_'+stamp)
    out.mkdir(parents=True,exist_ok=False)
    source=(root/'project/board/ov5640_snapshot/hdmi_color_probe.py').read_text(encoding='utf-8')
    for old,new in [('from pathlib import Path','from pathlib import Path\nimport sys\nsys.path.insert(0,str(Path(__file__).resolve().parents[1]))'),
        ('VideoMode(1280,720,24)','VideoMode(640,480,24)'),
        ('index*320:(index+1)*320','index*160:(index+1)*160'),
        ('1280*720*3,width=1280,height=720','640*480*3,width=640,height=480')]:
        assert source.count(old)==1, old
        source=source.replace(old,new)
    ast.parse(source)
    assert "if not manifest['design'].get('hdmi_hpd_input'):" in source
    data=source.encode('utf-8')
    (out/'hdmi_color_probe.py').write_bytes(data)
    remote=REMOTE.replace('PROBE_NAME',repr('vga_recovery_'+stamp)).replace('HELPER_B64',repr(base64.b64encode(data).decode())).replace('HELPER_SHA',repr(hashlib.sha256(data).hexdigest()))
    ast.parse(remote)
    password=getpass.getpass('Board sudo password (hidden): ')
    cmd="sudo -S -p '' env XILINX_XRT=/usr /usr/local/share/pynq-venv/bin/python -u -c "+shlex.quote(remote)
    result=subprocess.run(['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=8','xilinx@192.168.2.99',cmd],
        input=password+'\n',capture_output=True,text=True,timeout=55)
    password=None
    (out/'result.jsonl').write_text(result.stdout,encoding='utf-8')
    (out/'stderr.log').write_text(result.stderr,encoding='utf-8')
    print(result.stdout);print(result.stderr)
    raise SystemExit(result.returncode)


if __name__=='__main__':main()
