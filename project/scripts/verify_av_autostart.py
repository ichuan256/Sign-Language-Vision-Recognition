"""Read-only verification of installed startup configuration; never starts AV."""
import json,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CODE=r'''
import importlib.util,json,subprocess
from pathlib import Path
code=Path('/usr/local/lib/sign-av');count=0
for p in code.rglob('*.py'):compile(p.read_text(),str(p),'exec');count+=1
spec=importlib.util.spec_from_file_location('gateway',code/'board_gateway.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
config,boot=module.verify()
from capture import verify_manifest
verify_manifest(code/'release/release_manifest.json')
def run(args):
 r=subprocess.run(args,capture_output=True,text=True)
 return dict(exit_code=r.returncode,stdout=r.stdout.strip(),stderr=r.stderr.strip())
print(json.dumps(dict(date='2026-11-01',python_sources_compiled=count,runtime_hashes_verified=len(config['files']),
 boot_id=boot,protected_HWH_contract_verified=True,
 service_enabled=run(['systemctl','is-enabled','sign-av-owner.service']),
 service_state=run(['systemctl','show','sign-av-owner.service','-p','ActiveState','-p','SubState']),
 limited_sudo=run(['sudo','-n','-l','/usr/local/sbin/sign-av-ctl','preflight']),
 hardware_started=False,registers_touched=False,models_loaded=False)))
'''
def main():
 info=json.loads((ROOT/'project/_tmp/av_autostart_package.json').read_text());out=Path(info['evidence'])
 r=subprocess.run(['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=8','xilinx@192.168.2.99',
  '/usr/local/share/pynq-venv/bin/python -I -'],input=CODE,capture_output=True,text=True,encoding='utf-8',timeout=50)
 if r.returncode:raise RuntimeError(r.stderr)
 record=json.loads(r.stdout)
 (out/('verified_'+str(time.time_ns())+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
 assert record['service_enabled']['exit_code']==0 and record['limited_sudo']['exit_code']==0
 print(json.dumps(record,ensure_ascii=False))
if __name__=='__main__':main()
