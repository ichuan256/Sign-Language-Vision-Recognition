"""Preflight/normal reboot of the same verified AV firmware. Never redownload."""
import argparse,getpass,json,shlex,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CODE=r'''
import hashlib,importlib.util,json,os,signal,subprocess,time
from pathlib import Path
spec=importlib.util.spec_from_file_location('av_gateway','/usr/local/lib/sign-av/board_gateway.py')
gateway=importlib.util.module_from_spec(spec);spec.loader.exec_module(gateway)
config,boot=gateway.verify()
from pynq import MMIO
capture=MMIO(0x40400000,65536);vdma=MMIO(0x44a00000,65536);status=MMIO(0x41210000,65536)
assert capture.read(0x34)&1,'Camera DMA not Halted; stop the current task first'
owners=[]
for root in (Path('/home/xilinx/ov1_hdmi_20261031'),Path('/var/lib/sign-av')):
 p=root/'split_writer.json'
 if p.exists():
  writer=json.loads(p.read_text())
  if writer.get('active'):
   proc=Path('/proc')/str(writer['pid'])/'stat'
   assert not (proc.exists() and int(proc.read_text().rsplit(')',1)[1].split()[19])==writer['pid_start_ticks']),'A live painter still owns DMA'
 p=root/'color_probe.json'
 if p.exists():
  owner=json.loads(p.read_text());proc=Path('/proc')/str(owner['pid'])
  if owner.get('active') and owner.get('boot_id')==boot and proc.exists():
   assert int((proc/'stat').read_text().rsplit(')',1)[1].split()[19])==owner['pid_start_ticks']
   names=[Path(x.decode(errors='replace')).name for x in (proc/'cmdline').read_bytes().split(bytes([0])) if x]
   assert any(n in names for n in ('hdmi_owner.py','hdmi_color_probe.py','sign-av-ctl')),'Unknown HDMI owner'
   owners.append(owner)
assert len(owners)<=1,'Ambiguous output ownership'
enabled=subprocess.check_output(['systemctl','is-enabled','sign-av-owner.service'],text=True).strip()
assert enabled=='enabled'
record=dict(action=ACTION,boot_id=boot,bit_sha256=config['bit_sha256'],hwh_sha256=config['hwh_sha256'],
 boot_py_sha256=hashlib.sha256(Path('/boot/boot.py').read_bytes()).hexdigest(),owners=owners,
 capture_dma_halted=True,flags=status.read(8),video_status=hex(status.read(0)),vdma_status=hex(vdma.read(4)),
 startup_enabled=True,bit_hwh_changed=False,downloaded=False)
if ACTION=='reboot':
 for owner in owners:
  proc=Path('/proc')/str(owner['pid'])/'stat'
  os.kill(owner['pid'],signal.SIGTERM);deadline=time.monotonic()+15
  while proc.exists() and time.monotonic()<deadline:time.sleep(.1)
  assert not proc.exists(),'Owner has not quiesced; no force kill or reboot performed'
 assert vdma.read(4)&1 and capture.read(0x34)&1,'DMA not Halted; reboot not requested'
 record.update(output_dma_halted=True,reboot_requested=True)
print(json.dumps(record),flush=True)
if ACTION=='reboot':subprocess.run(['systemctl','reboot'],check=True)
'''

def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=('check','reboot'));a=p.parse_args()
 out=ROOT/'project/analysis/av_console_20261101';out.mkdir(parents=True,exist_ok=True)
 password=getpass.getpass('Board sudo password (hidden): ')
 cmd="sudo -S -p '' env XILINX_XRT=/usr /usr/local/share/pynq-venv/bin/python -u -c "+shlex.quote(CODE.replace('ACTION',repr(a.action)))
 r=subprocess.run(['ssh','-T','-o','BatchMode=yes','xilinx@192.168.2.99',cmd],input=password+'\n',capture_output=True,text=True,encoding='utf-8',timeout=75)
 password=None;stamp=str(time.time_ns())
 (out/(a.action+'_'+stamp+'.json')).write_text(r.stdout,encoding='utf-8')
 (out/(a.action+'_'+stamp+'.stderr')).write_text(r.stderr,encoding='utf-8')
 print(r.stdout);print(r.stderr)
 if r.returncode and not(a.action=='reboot' and '"reboot_requested": true' in r.stdout and 'closed' in r.stderr.lower()):raise SystemExit(r.returncode)

if __name__=='__main__':main()
