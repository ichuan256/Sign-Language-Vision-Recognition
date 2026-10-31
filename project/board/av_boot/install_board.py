"""Install only the reviewed AV startup layer. Do not start/reboot/reload hardware."""
import argparse,hashlib,json,os,shutil,subprocess,time
from pathlib import Path

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--payload',type=Path,required=True);a=p.parse_args()
    if os.geteuid()!=0:raise RuntimeError('Root installation required')
    payload=a.payload.resolve();config=json.loads((payload/'config.json').read_text())
    original=Path('/home/xilinx/ov1_hdmi_20261031/release')
    manifest=json.loads((original/'release_manifest.json').read_text())
    before={kind:sha(original/manifest['files'][kind]['path']) for kind in ('bit','hwh')}
    boot_sha=sha(Path('/boot/boot.py'))
    assert before['bit']==config['bit_sha256'] and before['hwh']==config['hwh_sha256']
    native=Path('/home/xilinx/board_pcm_capture')
    assert sha(native)==config['files']['runtime/board_pcm_capture']
    for name,digest in config['files'].items():
        if name=='runtime/board_pcm_capture':continue
        assert not Path(name).is_absolute() and '..' not in Path(name).parts
        assert sha(payload/name)==digest,name
    code=Path('/usr/local/lib/sign-av');data=Path('/var/lib/sign-av')
    backup=payload.parent/('installed_backup_'+str(time.time_ns()));backup.mkdir()
    old=[]
    def put(source,target,mode=0o644):
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.is_symlink():raise RuntimeError('Refusing symlink target: '+str(target))
        if target.exists():
            saved=backup/str(target).lstrip('/');saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,saved)
            old.append(str(target))
        temp=target.with_name(target.name+'.install.tmp');shutil.copyfile(source,temp);os.chmod(temp,mode);temp.replace(target)
    for name in config['files']:
        put(native if name=='runtime/board_pcm_capture' else payload/name,code/name,
            0o755 if name=='runtime/board_pcm_capture' else 0o644)
    put(payload/'config.json',code/'config.json')
    put(payload/'board_gateway.py',Path('/usr/local/sbin/sign-av-ctl'),0o755)
    for path in (code,code/'runtime',code/'release',data,data/'captures'):path.mkdir(parents=True,exist_ok=True);os.chmod(path,0o755)
    # Exact action allowlist; stream's argument is additionally restricted to digits by argparse/regex.
    rules='xilinx ALL=(root) NOPASSWD: /usr/local/sbin/sign-av-ctl preflight, /usr/local/sbin/sign-av-ctl owner, /usr/local/sbin/sign-av-ctl audio, /usr/local/sbin/sign-av-ctl stop, /usr/local/sbin/sign-av-ctl stream ui_*, /usr/local/sbin/sign-av-ctl display ui_*\n'
    candidate=backup/'sign-av.sudoers';candidate.write_text(rules);os.chmod(candidate,0o440)
    subprocess.run(['/usr/sbin/visudo','-cf',str(candidate)],check=True,capture_output=True,text=True)
    put(candidate,Path('/etc/sudoers.d/sign-av'),0o440)
    subprocess.run(['/usr/sbin/visudo','-c'],check=True,capture_output=True,text=True)
    unit=Path('/etc/systemd/system/sign-av-owner.service');put(payload/'sign-av-owner.service',unit)
    subprocess.run(['systemd-analyze','verify',str(unit)],check=True,capture_output=True,text=True)
    subprocess.run(['systemctl','daemon-reload'],check=True)
    subprocess.run(['systemctl','enable','sign-av-owner.service'],check=True,capture_output=True,text=True)
    for kind in before:assert sha(original/manifest['files'][kind]['path'])==before[kind]
    assert sha(Path('/boot/boot.py'))==boot_sha
    for name,digest in config['files'].items():assert sha(code/name)==digest
    result=dict(installed=True,enabled=True,started=False,rebooted=False,bit_hwh_changed=False,
        boot_py_changed=False,boot_py_sha256=boot_sha,backup=str(backup),previous_files=old,
        code=str(code),data=str(data),service='sign-av-owner.service',
        password_saved=False,sudo_scope='fixed preflight/owner/audio/stop/stream/display only')
    (backup/'installation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)

if __name__=='__main__':main()
