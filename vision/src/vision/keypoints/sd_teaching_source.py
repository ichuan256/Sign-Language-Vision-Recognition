"""Latest live replay pixels from the board's SD card, with exact-frame metadata."""
import json,os,subprocess,threading
from pathlib import Path
import cv2
import numpy as np

EXPECTED='f9b444cf3c46854b0ace7cc662ae3267adbe577e0362845b6b15d055275be1b2'

class SDTeachingSSHSource:
    def __init__(self,output):
        self.condition=threading.Condition();self.latest=None;self.error=None;self.closed=False
        self.last_metadata={}
        self.log=(Path(output)/'sd_video.stderr.log').open('ab')
        environment=dict(os.environ)
        for key in ('KEYPOINT_BOARD_SUDO_PASSWORD','AUDIO_BOARD_SUDO_PASSWORD','DEMO_CONTROL_SUDO_PASSWORD'):environment.pop(key,None)
        self.process=subprocess.Popen(['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=8',
            '-o','ServerAliveInterval=5','-o','ServerAliveCountMax=2','xilinx@192.168.2.99',
            '/usr/local/share/pynq-venv/bin/python -I -u /usr/local/lib/sign-av/runtime/sd_video_stream.py'],
            stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=self.log,env=environment)
        self.thread=threading.Thread(target=self.receive,daemon=True);self.thread.start()

    @staticmethod
    def exact(stream,size):
        chunks=[]
        while size:
            chunk=stream.read(size)
            if not chunk:raise EOFError('SD JPEG truncated')
            chunks.append(chunk);size-=len(chunk)
        return b''.join(chunks)

    def receive(self):
        try:
            stream=self.process.stdout;ready=json.loads(stream.readline(8192))
            if (ready.get('event'),ready.get('raw_sha256'),ready.get('width'),ready.get('height'))!=('ready',EXPECTED,960,540):
                raise RuntimeError('SD video identity mismatch')
            while not self.closed:
                header=json.loads(stream.readline(8192))
                size=header['bytes']
                if (header.get('event'),header.get('format'),header.get('width'),header.get('height'))!=('frame','JPEG',960,540) or not 0<size<=4*1024*1024:
                    raise RuntimeError('Invalid SD frame header')
                image=cv2.imdecode(np.frombuffer(self.exact(stream,size),np.uint8),cv2.IMREAD_COLOR)
                if image is None or image.shape!=(540,960,3):raise RuntimeError('Invalid SD frame image')
                with self.condition:
                    self.latest=(image,header['frame'],header['board_monotonic_s'],header)
                    self.condition.notify_all()
        except Exception as exc:
            with self.condition:self.error=str(exc);self.condition.notify_all()

    def read(self,timeout=45):
        with self.condition:
            self.condition.wait_for(lambda:self.latest is not None or self.error or self.closed,timeout)
            if self.latest is None:raise RuntimeError(self.error or 'SD video has not delivered a frame')
            image,number,stamp,metadata=self.latest;self.latest=None
            self.last_metadata=dict(metadata)
            return image,number,stamp

    def release(self):
        self.closed=True
        # Read-only SD publisher owns no DMA or model buffers.
        if self.process.poll() is None:self.process.terminate()
        self.process.wait(timeout=12);self.thread.join(timeout=3);self.log.close()

    def __enter__(self):return self
    def __exit__(self,*_):self.release()
