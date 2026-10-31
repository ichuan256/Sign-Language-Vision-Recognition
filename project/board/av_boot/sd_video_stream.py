"""Read the historical SD RGB video, paced at source FPS. No neural/PL calls."""
import hashlib,json,sys,time
from pathlib import Path
import cv2
import numpy as np

SOURCE=Path('/home/xilinx/independent_video_20261028')
EXPECTED='f9b444cf3c46854b0ace7cc662ae3267adbe577e0362845b6b15d055275be1b2'

def main():
    manifest=json.loads((SOURCE/'video.json').read_text())
    shape=(manifest['frames'],manifest['height'],manifest['width'],manifest['channels'])
    raw=SOURCE/'frames.rgb'
    if shape!=(63,540,960,3) or manifest['fps']!=10 or raw.stat().st_size!=97977600:
        raise RuntimeError('Unexpected SD teaching video contract')
    digest=hashlib.sha256()
    with raw.open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):digest.update(block)
    if digest.hexdigest()!=EXPECTED or manifest['raw_sha256']!=EXPECTED:
        raise RuntimeError('SD video SHA mismatch')
    frames=np.memmap(raw,dtype=np.uint8,mode='r',shape=shape)
    pipe=sys.stdout.buffer
    pipe.write((json.dumps(dict(event='ready',width=960,height=540,fps=10,frames=63,raw_sha256=EXPECTED))+'\n').encode());pipe.flush()
    start=time.monotonic();previous=-1
    try:
        while True:
            number=int((time.monotonic()-start)*10)
            if number==previous:time.sleep(.005);continue
            previous=number;index=number%63
            clip=next(c for c in manifest['clips'] if c['first_frame']<=index<c['end_frame'])
            ok,jpeg=cv2.imencode('.jpg',cv2.cvtColor(frames[index],cv2.COLOR_RGB2BGR),[cv2.IMWRITE_JPEG_QUALITY,90])
            if not ok:raise RuntimeError('SD JPEG encoding failed')
            header=dict(event='frame',bytes=len(jpeg),format='JPEG',width=960,height=540,
                frame=number,source_frame=index,clip=clip.get('label',clip.get('word',clip.get('name'))),
                source_sha256=clip['source_sha256'],board_monotonic_s=time.monotonic())
            pipe.write((json.dumps(header,ensure_ascii=False)+'\n').encode());pipe.write(jpeg.tobytes());pipe.flush()
    except BrokenPipeError:pass

if __name__=='__main__':main()
