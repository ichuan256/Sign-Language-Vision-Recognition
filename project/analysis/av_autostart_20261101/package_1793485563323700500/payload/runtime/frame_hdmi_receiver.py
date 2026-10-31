"""Write PC teacher frames to the existing boot owner's BGR buffer only."""
import argparse,base64,json,mmap,os,signal,sys,time
from pathlib import Path
from urllib.request import build_opener,ProxyHandler
import cv2
import numpy as np
from retained_mmio import Registers

DATA=Path('/var/lib/sign-av')

def atomic(path,value):
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(value));temp.replace(path)

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    output=a.output;output.mkdir(parents=True)
    owner=json.loads((DATA/'color_probe.json').read_text())
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    owner_stat=Path('/proc')/str(owner['pid'])/'stat'
    def check():
        if (owner['boot_id']!=boot or not owner_stat.exists() or
            int(owner_stat.read_text().rsplit(')',1)[1].split()[19])!=owner['pid_start_ticks']):
            raise RuntimeError('HDMI owner identity changed')
        video=Registers(0x44a00000)
        if video.read(4)&0x71 or any(video.read(0x5c+4*i)!=owner['frame_address'] for i in range(4)):
            raise RuntimeError('HDMI DMA changed; refusing buffer write')
        if Registers(0x41210000).read(8)&3!=3:raise RuntimeError('HDMI timing lost')
    check()
    address=owner['frame_address'];page=address//mmap.PAGESIZE*mmap.PAGESIZE;delta=address-page
    fd=os.open('/dev/mem',os.O_RDWR|os.O_SYNC)
    mapped=mmap.mmap(fd,delta+1280*720*3,flags=mmap.MAP_SHARED,prot=mmap.PROT_READ|mmap.PROT_WRITE,offset=page)
    os.close(fd);frame=np.ndarray((720,1280,3),np.uint8,buffer=mapped,offset=delta)
    stop=[False]
    def stopping(*_):stop[0]=True
    signal.signal(signal.SIGINT,stopping);signal.signal(signal.SIGTERM,stopping)
    state=dict(active=True,pid=os.getpid(),boot_id=boot,owner_pid=owner['pid'],frame_address=address,
               hdmi_frames=0,raw_updates=0,source='PC teacher',error=None)
    writer=dict(active=True,pid=os.getpid(),boot_id=boot,
        pid_start_ticks=int(Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19]))
    atomic(DATA/'split_writer.json',writer)
    opener=build_opener(ProxyHandler({}));previous=None;last_save=0;started=time.monotonic()
    try:
        while not stop[0]:
            tick=time.monotonic()
            try:
                with opener.open('http://127.0.0.1:18781/frame.jpg',timeout=3) as response:
                    header=response.headers.get('X-Frame-Metadata','')
                    if len(header)>16384:raise ValueError('Oversized frame metadata')
                    metadata=json.loads(base64.b64decode(header,validate=True))
                    raw=response.read(4*1024*1024+1)
                if len(raw)>4*1024*1024:raise ValueError('Oversized JPEG')
                identity=(metadata['frame_id'],metadata['source_timestamp_s'])
                if identity!=previous:
                    image=cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_COLOR)
                    if image is None or image.shape!=(720,1280,3):raise ValueError('Invalid HDMI image shape')
                    check()
                    if stop[0]:break
                    frame[:]=image;previous=identity
                    state.update(hdmi_frames=state['hdmi_frames']+1,source_frame=metadata.get('source_frame'),
                        raw_source_frame=metadata.get('source_frame'),metadata=metadata,error=None,
                        hdmi_write_hz=(state['hdmi_frames']+1)/max(time.monotonic()-started,.001))
                    if tick-last_save>=1:
                        temp=output/'latest.tmp';temp.write_bytes(raw);temp.replace(output/'latest.jpg');last_save=tick
            except (OSError,ValueError,KeyError) as exc:state['error']=str(exc)
            atomic(output/'live.json',state)
            time.sleep(max(0,.1-(time.monotonic()-tick)))
    finally:
        # Only this view is unmapped; the boot owner retains allocation and DMA.
        del frame;mapped.close()
        state['active']=False;atomic(output/'live.json',state)
        writer['active']=False;atomic(DATA/'split_writer.json',writer)

if __name__=='__main__':main()
