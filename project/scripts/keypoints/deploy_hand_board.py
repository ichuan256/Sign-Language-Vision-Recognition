"""Stage a checked hand+HDMI pair, back up the current pair, and cold reboot.

No Overlay download, boot.py edit, or service/startup edit is performed.
Run only after routed timing gates pass. Password is consumed from an ephemeral
environment variable; it is never saved, printed, or passed as an argument.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[3]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True)
    p.add_argument('--model',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--host',default='xilinx@192.168.2.99')
    p.add_argument('--apply',action='store_true',help='Replace backed-up pair and reboot once')
    a=p.parse_args()
    out=a.output.resolve()
    if not out.is_relative_to(ROOT/'project/_tmp') or out.exists():
        raise ValueError('Use a new workspace project/_tmp directory')
    build=a.build.resolve()
    for name in ('timing_routed.rpt','methodology_routed.rpt','route_status.rpt'):
        if not (build/name).is_file():raise FileNotFoundError(build/name)
    release=build/'release'
    if not all((release/('hand_hdmi.'+s)).is_file() for s in ('bit','hwh')):
        raise RuntimeError('Successful routed release gate required')
    env=dict(os.environ)
    password=env.pop('KEYPOINT_BOARD_SUDO_PASSWORD',None)
    if a.apply and password is None:raise RuntimeError('Missing ephemeral sudo password')
    def ssh(command,**kwargs):
        return subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8',a.host,command],
            capture_output=True,text=True,env=env,check=True,**kwargs).stdout.strip()
    boot=ssh('cat /proc/sys/kernel/random/boot_id')
    if ssh('systemctl show -p SubState --value bootpy.service')!='exited':
        raise RuntimeError('Board cold initialization not complete')
    current=ssh('sha256sum /home/xilinx/kws_hdmi.bit /home/xilinx/kws_hdmi.hwh')
    stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    work='/home/xilinx/hand_pl_'+stamp
    backup='/home/xilinx/hand_pl_backup_'+stamp
    out.mkdir(parents=True)
    payload=out/'payload';payload.mkdir()
    (payload/'model').mkdir()
    for suffix in ('bit','hwh'):
        shutil.copy2(release/('hand_hdmi.'+suffix),payload/('hand_hdmi.'+suffix))
    for name in ('graph.json','weights.npz'):
        shutil.copy2(a.model/name,payload/'model'/name)
    for name in ('roi0.npy','registers.json'):
        shutil.copy2(a.model/name,payload/name)
    for name in ('hand_runtime.py','run_hand_board.py'):
        shutil.copy2(ROOT/'project/board/keypoints'/name,payload/name)
    architecture=json.loads((a.model/'registers.json').read_text()).get('architecture','tile_v1')
    if architecture=='whole_layer_v2':
        shutil.copy2(ROOT/'project/board/keypoints/hand_layer_runtime.py',payload/'hand_layer_runtime.py')
    manifest=dict(scope='single_hand_PC_ROI_PL_neural_graph',
        architecture=architecture,board_boot_id_before_deployment=boot,previous_pair_sha256=current,
        board_workdir=work,board_backup=backup,
        artifacts={s:dict(sha256=digest(payload/('hand_hdmi.'+s))) for s in ('bit','hwh')})
    (payload/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    checks=[]
    for path in sorted(payload.rglob('*')):
        if path.is_file():checks.append(digest(path)+'  '+path.relative_to(payload).as_posix())
    (payload/'SHA256SUMS').write_bytes(('\n'.join(checks)+'\n').encode('utf-8'))
    (out/'deployment.json').write_text(json.dumps(manifest,indent=2)+'\n')
    if not a.apply:
        print('Prepared only:',out)
        return
    ssh('mkdir '+shlex.quote(work))
    subprocess.run(['scp','-r',str(payload)+'/.' ,a.host+':'+work+'/'],check=True,env=env,
                   stdout=subprocess.DEVNULL)
    ssh('cd '+shlex.quote(work)+' && sha256sum -c SHA256SUMS')
    # Stop if the running pair changed since preflight. Backup precedes replacement.
    quoted=shlex.quote
    old=[line.split()[0] for line in current.splitlines()]
    command='set -eu; '+ 'mkdir '+quoted(backup)+'; '
    for suffix,expected in zip(('bit','hwh'),old):
        target='/home/xilinx/kws_hdmi.'+suffix
        command+='test "$(sha256sum '+quoted(target)+' | cut -d " " -f 1)" = '+quoted(expected)+'; '
        command+='cp -p '+quoted(target)+' '+quoted(backup+'/kws_hdmi.'+suffix)+'; '
    for suffix in ('bit','hwh'):
        target='/home/xilinx/kws_hdmi.'+suffix
        command+='cp '+quoted(work+'/hand_hdmi.'+suffix)+' '+quoted(target+'.new')+'; '
    for suffix in ('bit','hwh'):
        target='/home/xilinx/kws_hdmi.'+suffix
        command+='mv '+quoted(target+'.new')+' '+quoted(target)+'; '
    command+='sync; reboot'
    result=subprocess.run(['ssh','-o','BatchMode=yes',a.host,
        'sudo -S -p '+quoted('')+' sh -c '+quoted(command)],input=password+'\n',
        capture_output=True,text=True,env=env)
    # Reboot can close the connection before ssh receives a successful status.
    (out/'reboot_status.json').write_text(json.dumps(dict(returncode=result.returncode,
        reboot_requested=True,cold_boot_confirmation_pending=True))+'\n')
    # Windows OpenSSH may report UINT32_MAX when reboot tears down its socket.
    # None of these exit codes confirms deployment: a NEW boot ID and both
    # candidate hashes still have to be verified before any MMIO access.
    if result.returncode not in (0,255,-1,0xffffffff):
        raise RuntimeError('Deployment/reboot failed; inspect board pair before continuing')
    print('Candidate staged, pair backed up, cold reboot requested:',work)

if __name__=='__main__':main()
