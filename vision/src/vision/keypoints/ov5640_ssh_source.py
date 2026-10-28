"""Complete live OV5640 frames over SSH; never replace with video/USB input."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import threading
import time

import cv2
import numpy as np


class OV5640SSHSource:
    def __init__(self,password,output):
        self.password=password;self.output=Path(output);self.stop=threading.Event()
        self.condition=threading.Condition();self.latest=None;self.error=None;self.sequence=0
        self.pid=None;self.started=time.monotonic()
        work='/home/xilinx/jupyter_notebooks/ov5640_snapshot'
        command=('sudo -S -p '+shlex.quote('')+' env XILINX_XRT=/usr /usr/local/share/pynq-venv/bin/python -u '+
            work+'/demo_stream.py --manifest '+work+'/release/release_manifest.json --output '+
            work+'/captures/ui_'+str(time.time_ns())+' --assume-cold-boot')
        environment=dict(os.environ);environment.pop('KEYPOINT_BOARD_SUDO_PASSWORD',None)
        self.log=(self.output/'ov5640.stderr.log').open('ab')
        self.process=subprocess.Popen(['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=8',
            'xilinx@192.168.2.99',command],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.log,env=environment)
        self.process.stdin.write((password+'\n').encode());self.process.stdin.flush()
        self.process.stdin.close()
        self.thread=threading.Thread(target=self.receive,daemon=True);self.thread.start()

    @staticmethod
    def exact(stream,size):
        chunks=[]
        while size:
            chunk=stream.read(size)
            if not chunk:raise EOFError('OV5640 frame truncated')
            chunks.append(chunk);size-=len(chunk)
        return b''.join(chunks)

    def receive(self):
        try:
            ready=json.loads(self.process.stdout.readline())
            if ready.get('event')!='ready':raise RuntimeError('OV5640 worker did not initialize')
            self.pid=int(ready['pid'])
            while not self.stop.is_set():
                line=self.process.stdout.readline(8192)
                if not line:raise EOFError('OV5640 stream ended; inspect ov5640.stderr.log')
                header=json.loads(line)
                if header.get('event')!='frame':
                    raise RuntimeError('OV5640 capture stopped: '+json.dumps(header,ensure_ascii=False)[:1000])
                if (header.get('bytes'),header.get('width'),header.get('height'),header.get('format'),
                    header.get('dma_shutdown_confirmed'))!=(1280*720*2,1280,720,'RGB565_LE',True):
                    raise RuntimeError('Incomplete or unconfirmed OV5640 frame')
                raw=self.exact(self.process.stdout,header['bytes'])
                packed=np.frombuffer(raw,np.uint8).reshape(720,1280,2)
                bgr=cv2.cvtColor(packed,cv2.COLOR_BGR5652BGR)
                with self.condition:
                    self.latest=(bgr,header['frame'],time.monotonic()-self.started)
                    self.sequence+=1;self.condition.notify_all()
        except Exception as exc:
            with self.condition:self.error=str(exc);self.condition.notify_all()

    def read(self):
        with self.condition:
            self.condition.wait_for(lambda:self.latest is not None or self.error or self.stop.is_set(),timeout=45)
            if self.latest is not None:
                item=self.latest;self.latest=None;return item
            raise RuntimeError(self.error or 'OV5640 has not delivered a complete frame in 45 seconds')

    def release(self):
        if self.stop.is_set():return
        if self.pid is None and self.process.poll() is None:
            raise RuntimeError('OV5640 worker identity unknown; preserve process and inspect board')
        # Do not close the SSH stream or kill its tree while the board may own DMA.
        if self.pid is not None and self.process.poll() is None:
            command='sudo -S -p '+shlex.quote('')+' kill -INT '+str(self.pid)
            result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','xilinx@192.168.2.99',command],
                input=self.password+'\n',text=True,capture_output=True,timeout=15)
            if result.returncode:raise RuntimeError('OV5640 safe stop request failed; preserve process')
            try:self.process.wait(timeout=45)
            except subprocess.TimeoutExpired:raise RuntimeError('OV5640 DMA stop unconfirmed; preserve process and inspect board')
        self.stop.set();self.thread.join(timeout=5);self.log.close()

    def __enter__(self):return self
    def __exit__(self,*_):self.release()
