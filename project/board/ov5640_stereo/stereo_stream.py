"""Independent left/right capture over SSH; not exposure-synchronized stereo."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import sys
import threading
import time
import xml.etree.ElementTree as ET


def verify(path):
    path=Path(path).resolve();manifest=json.loads(path.read_text())
    if manifest.get('schema')!='ov5640-dual-v1':raise RuntimeError('Not a dual capture manifest')
    if [c['id'] for c in manifest['channels']]!=[1,2]:raise RuntimeError('Exactly two different physical cameras required')
    files={}
    for kind in ('bit','hwh'):
        record=manifest['files'][kind];target=(path.parent/record['path']).resolve()
        if target.parent!=path.parent or hashlib.sha256(target.read_bytes()).hexdigest()!=record['sha256']:
            raise RuntimeError('Dual firmware pair mismatch')
        files[kind]=target
    if files['bit'].with_suffix('.hwh')!=files['hwh']:raise RuntimeError('Pair basename mismatch')
    modules={m.get('INSTANCE'):m for m in ET.parse(files['hwh']).getroot().findall('.//MODULE')}
    for channel in manifest['channels']:
        camera=modules[channel['camera_ip']]
        params={p.get('NAME'):p.get('VALUE') for p in camera.findall('./PARAMETERS/PARAMETER')}
        if (params.get('CAMERA'),params.get('FRAME_WIDTH'),params.get('FRAME_HEIGHT'))!=(str(channel['id']),'1280','720'):
            raise RuntimeError('Physical camera selection/dimensions mismatch')
        for field,base in (('dma_ip','dma_base'),('control_ip','control_base')):
            # MEMRANGE is canonical across the AXI GPIO/DMA parameter spellings.
            ranges=[r for r in ET.parse(files['hwh']).getroot().findall('.//MEMRANGE') if r.get('INSTANCE')==channel[field] and r.get('MEMTYPE')=='REGISTER']
            if len(ranges)!=1 or int(ranges[0].get('BASEVALUE'),0)!=channel[base]:raise RuntimeError('Camera register map mismatch')
    return manifest,files


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--seconds',type=int,default=3600)
    parser.add_argument('--assume-cold-boot',action='store_true')
    a=parser.parse_args();manifest,files=verify(a.manifest)
    if not a.assume_cold_boot:raise RuntimeError('Explicit cold-boot confirmation required')
    if not 10<=a.seconds<=86400:raise ValueError('Bounded capture required')
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    marker=json.loads(Path('/run/ov5640_stereo_boot.json').read_text())
    if marker.get('boot_id')!=boot or marker.get('bit_sha256')!=manifest['files']['bit']['sha256']:
        raise RuntimeError('Dual candidate cold-boot marker absent; no hardware access')
    import continuous_capture as cc
    from pynq import PL,Overlay,MMIO,Clocks,allocate
    if PL.bitfile_name and Path(PL.bitfile_name).resolve()!=files['bit']:raise RuntimeError('Loaded metadata does not name the dual candidate')
    if cc.UNSAFE_SESSIONS:raise RuntimeError('An unsafe DMA session is retained')
    lock=cc.ProcessLock('/run/lock/ov5640_continuous_capture.lock').acquire()
    if cc.competing_processes():raise RuntimeError('An old camera capture is active')
    overlay=Overlay(str(files['bit']),download=False)
    if not math.isfinite(float(Clocks.fclk0_mhz)) or abs(float(Clocks.fclk0_mhz)-100)>1:raise RuntimeError('Unexpected existing FCLK')
    for channel in manifest['channels']:
        for field,base in (('dma_ip','dma_base'),('control_ip','control_base')):
            if overlay.ip_dict[channel[field]]['phys_addr']!=channel[base]:raise RuntimeError('Live register map mismatch')
    a.output.mkdir(parents=True,exist_ok=False)
    stop=threading.Event();write_lock=threading.Lock();sessions=[]
    for signum in (signal.SIGINT,signal.SIGTERM):signal.signal(signum,lambda *_:stop.set())
    def emit(header,raw=b''):
        try:
            with write_lock:
                sys.stdout.buffer.write((json.dumps(header)+'\n').encode());sys.stdout.buffer.write(raw);sys.stdout.buffer.flush()
        except BrokenPipeError:stop.set()
    class Session(cc.CaptureSession):
        pending=None;sequence=0
        def _capture_one(self):
            self.pending=None;result=super()._capture_one();self.pending=result;return result
        def _halt(self):
            super()._halt();pending=self.pending;self.pending=None
            if pending is None or not pending['image_safe'] or self.buffer is None:return
            self.buffer.invalidate();raw=memoryview(self.buffer)[:pending['received_bytes']].tobytes()
            self.sequence+=1
            emit(dict(event='frame',camera=self.channel,frame=self.sequence,bytes=len(raw),width=1280,height=720,
                format='RGB565_LE',capture_completed_monotonic_s=time.monotonic(),dma_shutdown_confirmed=True),raw)
    def work(channel):
        output=a.output/('camera_'+str(channel['id']));output.mkdir()
        session=Session(MMIO(channel['control_base'],65536),MMIO(channel['dma_base'],65536),allocate,output,
            0x200,seconds=a.seconds,max_attempts=1000000,max_errors=5,max_samples=0,stop_requested=stop.is_set)
        session.channel=channel['id'];sessions.append(session)
        try:
            result=session.run()
            emit(dict(event='channel_finished',camera=channel['id'],result=result))
        finally:stop.set()
    emit(dict(event='ready',pid=os.getpid(),cameras=[1,2],exposure_synchronized=False))
    threads=[threading.Thread(target=work,args=(ch,)) for ch in manifest['channels']]
    try:
        for thread in threads:thread.start()
        for thread in threads:thread.join()
    finally:
        if any(s.hardware_started and not s.dma_safe for s in sessions):
            print('Dual DMA stop unconfirmed. Preserve this process and power OFF before retry.',file=sys.stderr,flush=True)
            while True:time.sleep(60)
        lock.release()
    emit(dict(event='finished',safe=True))


if __name__=='__main__':main()
