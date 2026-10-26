"""Board-only bounded raw replay into a guarded existing framebuffer. Never load an overlay."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def main():
    from pynq import MMIO
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True);p.add_argument('--raw',type=Path,required=True)
    p.add_argument('--owner-pid',type=int,required=True);p.add_argument('--seconds',type=int,default=120)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--release',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists() or not 10<=a.seconds<=120:raise ValueError('New bounded output required')
    release=json.loads(a.release.read_text());meta=json.loads(a.manifest.read_text())
    if Path('/proc/sys/kernel/random/boot_id').read_text().strip()==release['board_boot_id_before_deployment']:
        raise RuntimeError('Cold deployment gate missing')
    for suffix in ('bit','hwh'):
        if digest('/home/xilinx/kws_hdmi.'+suffix)!=release['artifacts'][suffix]['sha256']:raise RuntimeError('Firmware pair changed')
    if digest(a.raw)!=meta['raw_sha256'] or a.raw.stat().st_size!=meta['frames']*1280*720*3:raise ValueError('Raw input SHA/size mismatch')
    available=int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))*1024
    if available<a.raw.stat().st_size+32*1024*1024:raise RuntimeError('Insufficient memory headroom for bounded raw page cache')
    owner=Path('/proc')/str(a.owner_pid);identity=(owner/'stat').read_text().rsplit(')',1)[1].split()[19]
    dma=MMIO(0x44A00000,65536);addresses=[dma.read(0x5c+4*i) for i in range(4)]
    if not addresses[0] or len(set(addresses))!=1:raise RuntimeError('Expected one retained frame')
    frame=MMIO(addresses[0],1280*720*3)
    def check():
        if b'hdmi_display.py' not in (owner/'cmdline').read_bytes() or (owner/'stat').read_text().rsplit(')',1)[1].split()[19]!=identity:
            raise RuntimeError('Display owner changed')
        if addresses!=[dma.read(0x5c+4*i) for i in range(4)] or dma.read(4)&0x71:
            raise RuntimeError('Framebuffer/VDMA changed')
        if dma.read(0x50)!=720 or dma.read(0x54)!=3840 or dma.read(0x58)&0xffffff!=3840:
            raise RuntimeError('Expected retained 720p RGB888 mode')
    check();words=1280*720*3//4
    source=np.memmap(a.raw,mode='r',dtype='<u4',shape=(meta['frames'],words))
    tick=time.monotonic();checksum=int(source.sum(dtype=np.uint64));prefault=time.monotonic()-tick
    fps=min(float(meta['source_fps']),30.);period=1/fps;durations=[];seen=set();missed=0;last=-1
    print('RAW_REPLAY_READY fps=%.3f seconds=%d'%(fps,a.seconds),flush=True)
    start=time.monotonic()
    while time.monotonic()-start<a.seconds:
        now=time.monotonic();index=int((now-start)*fps)
        if index<=last:time.sleep(max(0,start+(last+1)*period-now));continue
        missed+=max(0,index-last-1);check();t=time.monotonic()
        frame.array[:]=source[index%meta['frames']]
        durations.append((time.monotonic()-t)*1000);seen.add(index%meta['frames']);last=index
        if len(durations)%100==0:print('RAW_FRAMES',len(durations),'dropped',missed,flush=True)
    elapsed=time.monotonic()-start;check()
    report=dict(scope='board_local_raw_loop_framebuffer_write_throughput',completed=True,
        source_fps=meta['source_fps'],requested_fps=fps,frames_written=len(durations),elapsed_s=elapsed,
        measured_framebuffer_writes_per_s=len(durations)/elapsed,missed_slots=missed,unique_source_frames=len(seen),
        copy_ms_P50=float(np.percentile(durations,50)),copy_ms_P95=float(np.percentile(durations,95)),
        raw_sha256=meta['raw_sha256'],source_sha256=meta['source_sha256'],prefault_s=prefault,
        input_read_checksum=checksum,bitstream_downloaded=False,owner_left_alive=True,screen_visually_confirmed=False,
        limitations=['Single retained framebuffer written in place: tearing/vsync and physical display latency not measured',
            'Predecoded short loop in board page cache; no PC frame transport, no landmark inference, no sustained SD decode'])
    a.output.mkdir(parents=True);(a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':main()
