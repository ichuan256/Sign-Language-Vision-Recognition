"""Wait for a different boot and verified HDMI owner; read-only on the board."""
import json,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OLD='8eb07956-cc57-43f6-a252-cb0c4e106eb5'
def main():
    out=ROOT/'project/analysis/av_console_20261101';out.mkdir(exist_ok=True)
    started=time.monotonic();deadline=started+300
    while time.monotonic()<deadline:
        cmd="cat /proc/sys/kernel/random/boot_id; systemctl is-active sign-av-owner.service; test -f /var/lib/sign-av/color_probe.json && cat /var/lib/sign-av/color_probe.json"
        r=subprocess.run(['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=3','xilinx@192.168.2.99',cmd],capture_output=True,text=True,encoding='utf-8',timeout=10)
        lines=r.stdout.splitlines();status=dict(waited_s=round(time.monotonic()-started,1),boot=lines[0] if lines else None,service=lines[1] if len(lines)>1 else None)
        print(json.dumps(status),flush=True)
        if len(lines)>2 and lines[0]!=OLD and lines[1]=='active':
            owner=json.loads(lines[2])
            if owner.get('active') and owner['boot_id']==lines[0]:
                r=subprocess.run(['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=5','xilinx@192.168.2.99','sudo -n /usr/local/sbin/sign-av-ctl preflight'],capture_output=True,text=True,encoding='utf-8',timeout=65)
                if r.returncode==0:
                    result=json.loads(r.stdout)
                    (out/('boot_ready_'+str(time.time_ns())+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
                    print(json.dumps(result),flush=True);return
                print(r.stderr.splitlines()[-1] if r.stderr else 'Preflight not ready',flush=True)
        time.sleep(8)
    raise RuntimeError('New boot/HDMI owner not ready within 300 seconds')
if __name__=='__main__':main()
