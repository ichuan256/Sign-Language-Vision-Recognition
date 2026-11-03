"""Install a fixed-digit UART gateway; no boot, service, FPGA or group changes."""
import argparse,hashlib,json,os,shutil,subprocess,time
from pathlib import Path

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--sha256',required=True);args=parser.parse_args()
    if os.geteuid()!=0:raise RuntimeError('Root installation required')
    if hashlib.sha256(args.source.read_bytes()).hexdigest()!=args.sha256:raise RuntimeError('UART helper hash mismatch')
    target=Path('/usr/local/sbin/sign-digit-say');rules=Path('/etc/sudoers.d/sign-digit-say')
    backup=args.source.parent/('backup_'+str(time.time_ns()));backup.mkdir()
    for path in (target,rules):
        if path.is_symlink():raise RuntimeError('Refusing symlink install target')
        if path.exists():shutil.copy2(path,backup/path.name)
    temp=target.with_suffix('.install.tmp');shutil.copyfile(args.source,temp);os.chmod(temp,0o755)
    assert hashlib.sha256(temp.read_bytes()).hexdigest()==args.sha256;temp.replace(target)
    policy=backup/'sudoers.new'
    policy.write_text('xilinx ALL=(root) NOPASSWD: '+', '.join(str(target)+' '+a for a in ('probe','1','2','3','4','5'))+'\n')
    os.chmod(policy,0o440)
    subprocess.run(['/usr/sbin/visudo','-cf',str(policy)],check=True,capture_output=True)
    stage=rules.with_suffix('.install.tmp');shutil.copyfile(policy,stage);os.chmod(stage,0o440);stage.replace(rules)
    subprocess.run(['/usr/sbin/visudo','-c'],check=True,capture_output=True)
    result=dict(installed=True,sha256=args.sha256,backup=str(backup),scope='SYN6288 probe and fixed digits only',
        bit_hwh_changed=False,boot_changed=False,services_changed=False,serial_permissions_changed=False)
    (backup/'installation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))

if __name__=='__main__':main()
