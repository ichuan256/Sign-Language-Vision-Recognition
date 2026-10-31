#!/usr/local/share/pynq-venv/bin/python -I
"""Fixed AV operations for unattended PC control. Never load a bitstream."""
import argparse,hashlib,json,os,re,runpy,signal,subprocess,sys,time
from pathlib import Path

CODE=Path('/usr/local/lib/sign-av');DATA=Path('/var/lib/sign-av')
PYTHON='/usr/local/share/pynq-venv/bin/python'

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):h.update(block)
    return h.hexdigest()

def atomic(path,value):
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(value));temp.replace(path)

def verify():
    config=json.loads((CODE/'config.json').read_text())
    for name,digest in config['files'].items():
        relative=Path(name)
        if relative.is_absolute() or '..' in relative.parts:raise RuntimeError('Unsafe runtime path')
        if sha(CODE/relative)!=digest:raise RuntimeError('Runtime hash mismatch: '+name)
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    marker=json.loads(Path('/run/ov1_hdmi_boot.json').read_text())
    if marker['boot_id']!=boot or marker['bit_sha256']!=config['bit_sha256']:
        raise RuntimeError('Expected AV firmware was not cold-loaded this boot')
    if sha(Path(config['loaded_bit_path']))!=config['bit_sha256'] or sha(Path(config['loaded_hwh_path']))!=config['hwh_sha256']:
        raise RuntimeError('Cold-loaded firmware pair changed on disk')
    sys.path.insert(0,str(CODE/'runtime'));os.chdir(CODE/'runtime')
    os.environ['XILINX_XRT']='/usr'
    return config,boot

def identity(pid,boot):
    return dict(pid=pid,boot_id=boot,pid_start_ticks=int((Path('/proc')/str(pid)/'stat').read_text().rsplit(')',1)[1].split()[19]))

def live(value,boot):
    path=Path('/proc')/str(value['pid'])/'stat'
    return value.get('boot_id')==boot and path.exists() and int(path.read_text().rsplit(')',1)[1].split()[19])==value['pid_start_ticks']

def owner(boot):
    from pynq import MMIO
    value=json.loads((DATA/'color_probe.json').read_text())
    if not live(value,boot) or not value.get('active') or value.get('closing'):raise RuntimeError('Boot HDMI owner not ready')
    video=MMIO(0x44a00000,65536);flags=MMIO(0x41210000,65536).read(8)
    if video.read(4)&0x71 or any(video.read(0x5c+4*i)!=value['frame_address'] for i in range(4)):
        raise RuntimeError('HDMI DMA mode/address changed')
    if flags&3!=3:raise RuntimeError('HDMI timing not locked; preserve owner and inspect, no reconfiguration')
    return value

def stop_stream(boot):
    path=DATA/'stream.json'
    if path.exists():
        value=json.loads(path.read_text())
        if live(value,boot):
            args=(Path('/proc')/str(value['pid'])/'cmdline').read_bytes().split(bytes([0]))
            if b'/usr/local/sbin/sign-av-ctl' not in args or b'stream' not in args:raise RuntimeError('Unowned capture process')
            os.kill(value['pid'],signal.SIGINT);deadline=time.monotonic()+90
            while live(value,boot) and time.monotonic()<deadline:time.sleep(.1)
            if live(value,boot):raise RuntimeError('Capture stop unconfirmed; no force kill')
    from pynq import MMIO
    if not MMIO(0x40400000,65536).read(0x34)&1:raise RuntimeError('Camera DMA not Halted')
    return dict(stopped=True,camera_dma_halted=True)

def start_audio(boot):
    path=DATA/'audio.json'
    if path.exists():
        value=json.loads(path.read_text())
        if live(value,boot):return value
    env=dict(os.environ,XILINX_XRT='/usr',PYTHONNOUSERSITE='1',PYTHONPATH='')
    with (DATA/'audio.stdout.log').open('ab') as out,(DATA/'audio.stderr.log').open('ab') as err:
        child=subprocess.Popen([PYTHON,'-I','-u',str(CODE/'runner.py'),'board_audio_stream.py',
            '--av-manifest',str(CODE/'release/release_manifest.json')],env=env,cwd='/',
            stdin=subprocess.DEVNULL,stdout=out,stderr=err,start_new_session=True)
    value=identity(child.pid,boot);atomic(path,value);return value

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('preflight','owner','audio','stop','stream','owner-foreground'))
    p.add_argument('run',nargs='?');a=p.parse_args()
    if a.action=='stream':
        if not a.run or not re.fullmatch(r'ui_[0-9]{12,24}',a.run):p.error('Invalid capture run name')
    elif a.run is not None:p.error('Unexpected argument')
    if os.geteuid()!=0:raise RuntimeError('Use the installed fixed sudo entry')
    config,boot=verify()
    if a.action=='owner-foreground':
        sys.argv=[str(CODE/'runtime/hdmi_owner.py')]
        runpy.run_path(sys.argv[0],run_name='__main__');return
    if a.action=='stop':result=stop_stream(boot)
    else:
        value=owner(boot)
        if a.action=='preflight':result=dict(ready=True,boot_id=boot,bit_sha256=config['bit_sha256'],owner=value)
        elif a.action=='owner':result=dict(owner_pid=value['pid'],frame_address=value['frame_address'],reused=True,downloaded=False)
        elif a.action=='audio':result=start_audio(boot)
        else:
            # Root-owned data tree, fixed program and parameters; no arbitrary code/paths.
            from continuous_capture import ProcessLock
            stream_lock=ProcessLock('/run/lock/sign_av_gateway.lock').acquire()
            target=DATA/'captures'/a.run
            if target.exists() or target.is_symlink():raise RuntimeError('Capture run already exists')
            from pynq import MMIO
            if not MMIO(0x40400000,65536).read(0x34)&1:raise RuntimeError('Capture DMA already active')
            atomic(DATA/'stream.json',identity(os.getpid(),boot))
            sys.argv=[str(CODE/'runtime/split_hdmi_stream.py'),'--manifest',str(CODE/'release/release_manifest.json'),
                '--output',str(target),'--assume-cold-boot','--triple','--seconds','0']
            runpy.run_path(sys.argv[0],run_name='__main__');return
    print(json.dumps(result),flush=True)

if __name__=='__main__':main()
