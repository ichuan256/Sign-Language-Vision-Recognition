"""Retrigger existing HDMI MMCM configuration, preserving the current owner/BO."""
import getpass
import json
from pathlib import Path
import shlex
import subprocess
import time

REMOTE=r'''
import hashlib,json,time
from pathlib import Path
from pynq import MMIO
root=Path('/home/xilinx/ov1_hdmi_20261031')
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
marker=json.loads(Path('/run/ov1_hdmi_boot.json').read_text())
m=json.loads((root/'release/release_manifest.json').read_text())
assert marker['boot_id']==boot and marker['bit_sha256']==m['files']['bit']['sha256']
assert m['design']['hdmi_hpd_input'] is True
for kind in ('bit','hwh'):
    item=m['files'][kind]
    assert hashlib.sha256((root/'release'/item['path']).read_bytes()).hexdigest()==item['sha256']
owner=json.loads((root/'color_probe.json').read_text())
assert owner['active'] and not owner['closing'] and owner['boot_id']==boot
proc=Path('/proc')/str(owner['pid'])
assert int((proc/'stat').read_text().rsplit(')',1)[1].split()[19])==owner['pid_start_ticks']
assert 'hdmi_color_probe.py' in (proc/'cmdline').read_bytes().decode()
assert not json.loads((root/'split_writer.json').read_text()).get('active')
assert MMIO(0x40400000,65536).read(0x34)&1
s=MMIO(0x41210000,65536);d=MMIO(0x44a10000,65536);v=MMIO(0x44a00000,65536)
assert not s.read(8)&64, 'Screen HPD is not asserted; do not relock'
assert not v.read(4)&1, 'Output owner is not scanning'
before={hex(o):hex(d.read(o)) for o in range(0,36,4)}
assert d.read(0)==1 and d.read(4)&1
print(json.dumps(dict(event='before',boot_id=boot,owner=owner,dynclk=before,flags=s.read(8))),flush=True)
try:
    d.write(0,0)
    deadline=time.monotonic()+2
    while d.read(4)&1 and time.monotonic()<deadline:time.sleep(.001)
    assert not d.read(4)&1, 'Clock state machine did not disable'
finally:
    d.write(0,1)
deadline=time.monotonic()+3
while not d.read(4)&1 and time.monotonic()<deadline:time.sleep(.001)
completed=bool(d.read(4)&1)
samples=[]
for _ in range(16):
    samples.append(dict(status=hex(s.read(0)),flags=s.read(8),vdma=hex(v.read(4))))
    time.sleep(.1)
after={hex(o):hex(d.read(o)) for o in range(0,36,4)}
print(json.dumps(dict(event='after',completed=completed,dynclk=after,samples=samples,
    configuration_unchanged=all(before[hex(o)]==after[hex(o)] for o in range(8,36,4)),
    owner_unchanged=json.loads((root/'color_probe.json').read_text())==owner,
    downloaded=False,rebooted=False,frame_address_preserved=True)),flush=True)
assert completed
'''


def main():
    out=Path(__file__).resolve().parents[2]/'project/analysis/hdmi_recovery_20261101'/('relock_'+str(time.time_ns()))
    out.mkdir(parents=True,exist_ok=False)
    password=getpass.getpass('Board sudo password (hidden): ')
    cmd="sudo -S -p '' env XILINX_XRT=/usr /usr/local/share/pynq-venv/bin/python -u -c "+shlex.quote(REMOTE)
    result=subprocess.run(['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=8','xilinx@192.168.2.99',cmd],
        input=password+'\n',capture_output=True,text=True,timeout=25)
    password=None
    (out/'result.jsonl').write_text(result.stdout,encoding='utf-8')
    (out/'stderr.log').write_text(result.stderr,encoding='utf-8')
    print(result.stdout);print(result.stderr)
    raise SystemExit(result.returncode)


if __name__=='__main__':main()
