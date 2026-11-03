"""Archive only this session's unused SYN6288 helper/rule; never open serial."""
import hashlib,json,os,shutil,time
from pathlib import Path

def main():
    if os.geteuid()!=0:raise RuntimeError('Root required to withdraw installed sudo rule')
    helper=Path('/usr/local/sbin/sign-digit-say');rule=Path('/etc/sudoers.d/sign-digit-say')
    expected='30a16726689daa31302ee63ed68af21406294590f32290de255b947fbb83e0f5'
    if helper.is_symlink() or rule.is_symlink():raise RuntimeError('Refusing changed installation')
    if helper.exists() and hashlib.sha256(helper.read_bytes()).hexdigest()!=expected:
        raise RuntimeError('Installed helper changed; preserve it')
    if rule.exists() and rule.read_text()!='xilinx ALL=(root) NOPASSWD: '+', '.join(str(helper)+' '+a for a in ('probe','1','2','3','4','5'))+'\n':
        raise RuntimeError('Installed rule changed; preserve it')
    archive=Path('/root')/('sign-digit-disabled_'+str(time.time_ns()));archive.mkdir(mode=0o700)
    moved=[]
    for path in (rule,helper):
        if path.exists():shutil.move(str(path),str(archive/path.name));moved.append(str(path))
    result=dict(disabled=True,archive=str(archive),moved=moved,serial_opened=False,
        serial_bytes_sent=0,files_deleted=False,firmware_changed=False,startup_changed=False)
    (archive/'disabled.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))

if __name__=='__main__':main()
