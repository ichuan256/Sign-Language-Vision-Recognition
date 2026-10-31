"""Stage/apply the reviewed startup layer without interrupting the running demo."""
import argparse,getpass,hashlib,json,os,shlex,shutil,subprocess,time,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HOST='xilinx@192.168.2.99'

def run(args,timeout=50,input=None):
    result=subprocess.run(args,input=input,capture_output=True,text=True,encoding='utf-8',timeout=timeout)
    if result.returncode:raise RuntimeError(result.stderr or result.stdout)
    return result

def windows_startup(out):
    appdata=Path(os.environ['APPDATA']).resolve()
    startup=(appdata/'Microsoft/Windows/Start Menu/Programs/Startup').resolve()
    assert startup.is_relative_to(appdata) and startup.is_dir()
    target=startup/'SignAV三栏自启.lnk';old=startup/'audio_resident_autostart.bat'
    backup=(appdata/'SignAVAutostartBackup'/str(time.time_ns())).resolve();backup.mkdir(parents=True)
    moved=[]
    for path in (old,target):
        if path.exists():
            assert path.resolve().parent==startup
            destination=(backup/path.name).resolve();assert destination.parent==backup
            # Same-volume rename preserves any pre-existing private contents; never print/copy them.
            os.replace(path,destination);moved.append(dict(source=str(path),backup=str(destination)))
    python=Path('F:/PLD/.venv-vision/Scripts/pythonw.exe');script=ROOT/'project/scripts/start_av_console.py'
    def quote(value):return "'"+str(value).replace("'","''")+"'"
    ps=("$avShell=New-Object -ComObject WScript.Shell\n"
        "$avLink=$avShell.CreateShortcut("+quote(target)+")\n"
        "$avLink.TargetPath="+quote(python)+"\n"
        "$avLink.Arguments="+quote('-X utf8 "'+str(script)+'"')+"\n"
        "$avLink.WorkingDirectory="+quote(ROOT)+"\n"
        "$avLink.WindowStyle=7\n$avLink.Save()\n"
        "if ($avLink.TargetPath -ne "+quote(python)+") { throw 'Shortcut target mismatch' }\n")
    psfile=out/'install_shortcut.ps1';psfile.write_text(ps,encoding='utf-8-sig')
    run(['powershell.exe','-NoProfile','-Command',ps])
    if not target.is_file():raise RuntimeError('Startup shortcut was not created')
    return dict(installed=True,trigger='Windows user logon',shortcut=str(target),
        legacy_startup_backups=moved,password_saved=False,started_now=False)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');parser.add_argument('--board-only',action='store_true');a=parser.parse_args()
    info=json.loads((ROOT/'project/_tmp/av_autostart_package.json').read_text());package=Path(info['path']);out=Path(info['evidence'])
    stage='/home/xilinx/av_autostart_20261101/'+out.name
    archive=ROOT/'project/_tmp'/('av_autostart_'+out.name+'.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for path in package.rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts:z.write(path,str(path.relative_to(package)).replace('\\','/'))
    run(['ssh','-T','-o','BatchMode=yes',HOST,'mkdir -p '+stage])
    installer=ROOT/'project/board/av_boot/install_board.py'
    run(['scp','-o','BatchMode=yes',str(archive),str(installer),HOST+':'+stage+'/'])
    code="import zipfile;zipfile.ZipFile("+repr(stage+'/'+archive.name)+").extractall("+repr(stage+'/payload')+")"
    run(['ssh','-T','-o','BatchMode=yes',HOST,'/usr/bin/python3 -c '+shlex.quote(code)])
    plan=dict(date='2026-11-01',package=str(package),board_stage=stage,
        service='sign-av-owner.service',enable_only_no_start=True,
        sudo_actions=['preflight','owner','audio','stop','stream ui_<digits>'],
        windows_trigger='user logon, hidden pythonw',models_changed=False,bit_hwh_changed=False,
        startup_entry='SignAV三栏自启.lnk',old_W6_startup='backup outside Startup before replacement',
        running_demo_preserved=True,password_saved=False)
    (out/'install_plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    if not a.apply:print(json.dumps(plan,ensure_ascii=False));return
    password=getpass.getpass('Board sudo password (hidden): ')
    cmd="sudo -S -p '' env XILINX_XRT=/usr /usr/local/share/pynq-venv/bin/python -I "+shlex.quote(stage+'/install_board.py')+' --payload '+shlex.quote(stage+'/payload')
    result=run(['ssh','-T','-o','BatchMode=yes',HOST,cmd],timeout=120,input=password+'\n');password=None
    board=json.loads(result.stdout);(out/'board_install.json').write_text(json.dumps(board,ensure_ascii=False,indent=2),encoding='utf-8')
    windows=dict(changed=False) if a.board_only else windows_startup(out)
    (out/'windows_install.json').write_text(json.dumps(windows,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(board=board,windows=windows),ensure_ascii=False))

if __name__=='__main__':main()
