"""Launch the current AV console detached with logs; replace legacy idle UI only on request."""
import argparse,json,os,socket,subprocess,time
from pathlib import Path
from urllib.request import build_opener,ProxyHandler
ROOT=Path(__file__).resolve().parents[2]
OPENER=build_opener(ProxyHandler({}))

def state():
    try:return json.loads(OPENER.open('http://127.0.0.1:18790/api/state',timeout=3).read())
    except OSError:return None

def main():
    p=argparse.ArgumentParser();p.add_argument('--replace-idle',action='store_true');a=p.parse_args()
    current=state()
    if current is not None:
        if current.get('console_profile')=='av_current_firmware_v1' and not a.replace_idle:print('CONTROL_URL=http://127.0.0.1:18790 (AV ready)');return
        if not a.replace_idle:print('原控制台仍在运行。更新时先停止演示，再使用 --replace-idle。');return
        if current.get('mode')!='idle' or current.get('busy'):raise RuntimeError('当前演示尚未安全停止，不替换控制服务')
        script=r'''
$avCheck=Invoke-RestMethod -Uri 'http://127.0.0.1:18790/api/state' -TimeoutSec 3
if ($avCheck.mode -ne 'idle' -or $avCheck.busy) { throw 'Console is no longer idle' }
$avConnections=@(Get-NetTCPConnection -LocalPort 18790 -State Listen)
$avOwners=@($avConnections.OwningProcess | Select-Object -Unique)
if ($avOwners.Count -ne 1) { throw 'Expected a single local control owner' }
$avProcess=Get-CimInstance Win32_Process -Filter ('ProcessId='+$avOwners[0])
if ($avProcess.CommandLine -notmatch '(demo_control|av_autostart)[.]py') { throw 'Unrecognized control process' }
Stop-Process -Id $avOwners[0]
'''
        r=subprocess.run(['powershell.exe','-NoProfile','-Command',script],capture_output=True,text=True)
        if r.returncode:raise RuntimeError(r.stderr)
        deadline=time.monotonic()+8
        while state() is not None and time.monotonic()<deadline:time.sleep(.2)
        if state() is not None:raise RuntimeError('旧控制服务未退出')
    out=ROOT/'project/_tmp/av_console';out.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,PYTHONUTF8='1')
    for key in ('DEMO_CONTROL_SUDO_PASSWORD','AUDIO_BOARD_SUDO_PASSWORD','KEYPOINT_BOARD_SUDO_PASSWORD'):env.pop(key,None)
    with (out/'stdout.log').open('ab') as stdout,(out/'stderr.log').open('ab') as stderr:
        child=subprocess.Popen(['F:/PLD/.venv-vision/Scripts/python.exe','-X','utf8',str(ROOT/'project/scripts/av_autostart.py')],
            cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,
            creationflags=subprocess.CREATE_NO_WINDOW|subprocess.CREATE_NEW_PROCESS_GROUP)
    deadline=time.monotonic()+30
    while time.monotonic()<deadline:
        current=state()
        if current and current.get('console_profile')=='av_current_firmware_v1':
            (out/'launch.json').write_text(json.dumps(dict(child_pid=child.pid,service_pid=current.get('service_pid'),url='http://127.0.0.1:18790'),indent=2))
            print('CONTROL_URL=http://127.0.0.1:18790');return
        if child.poll() is not None:raise RuntimeError('控制台启动失败，请查看 project/_tmp/av_console/stderr.log')
        time.sleep(.5)
    raise RuntimeError('控制台尚未就绪，请查看日志')

if __name__=='__main__':main()
