"""Bounded HDMI display of one verified PL output. This is a static ROI test."""
import argparse
import json
from pathlib import Path
import threading
import time
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))

import cv2
import numpy as np
from vision.keypoints.frame_server import LatestFrameServer
from vision.keypoints.hdmi_link import HDMILink

EDGES=[(0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),
       (5,9),(9,10),(10,11),(11,12),(9,13),(13,14),(14,15),(15,16),
       (13,17),(0,17),(17,18),(18,19),(19,20)]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--result',type=Path,required=True)
    p.add_argument('--release-manifest',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--seconds',type=int,default=60)
    p.add_argument('--board',default='xilinx@192.168.2.99')
    p.add_argument('--pc-port',type=int,default=18780)
    p.add_argument('--remote-port',type=int,default=18781)
    p.add_argument('--fps',type=int,default=5)
    a=p.parse_args()
    if not 1<=a.seconds<=600:raise ValueError('Bounded display requires 1..600 seconds')
    report=json.loads((a.result/'report.json').read_text())
    if not report['completed'] or report['cpu_neural_fallback']:
        raise RuntimeError('Successful actual PL report required')
    import hashlib,os
    if hashlib.sha256(a.input.read_bytes()).hexdigest()!=report['input_sha256']:
        raise RuntimeError('Result and input mismatch')
    roi=np.load(a.input,allow_pickle=False)
    # Decode the recorded integer RGB scale; no new model invocation.
    image=cv2.cvtColor(np.clip(np.ldexp(roi.astype(np.float32),-report['input_fraction'])*255,0,255).astype(np.uint8),cv2.COLOR_RGB2BGR)
    coordinates=np.load(a.result/'output.npy',allow_pickle=False)
    points=coordinates[:63].reshape(21,3)[:,:2]
    canvas=np.zeros((720,1280,3),np.uint8)
    image=cv2.resize(image,(560,560))
    pts=np.rint(points*560/224).astype(int)
    for i,j in EDGES:cv2.line(image,tuple(pts[i]),tuple(pts[j]),(0,220,0),2)
    for point in pts:cv2.circle(image,tuple(point),4,(0,180,255),-1)
    canvas[110:670,40:600]=image
    lines=['STATIC ROI / ACTUAL PL RESULT','Single hand: 21 points',
        'PC supplied normalized ROI',f'PL graph + PS schedule: {report["elapsed_s"]:.3f} s',
        f'Presence: {coordinates[63]:.4f}', 'No CPU neural fallback',
        'Not live video / not camera FPS']
    for i,line in enumerate(lines):
        cv2.putText(canvas,line,(620 if i else 30,160+i*58 if i else 52),
            cv2.FONT_HERSHEY_SIMPLEX,.65 if i else .95,(230,230,230),2)
    stop=threading.Event()
    server=LatestFrameServer(a.pc_port)
    server.__enter__()
    def publish():
        frame=0
        while not stop.is_set():
            server.publish(canvas,frame,frame/a.fps)
            frame+=1
            stop.wait(1/a.fps)
    worker=threading.Thread(target=publish,daemon=True);worker.start()
    try:
        time.sleep(.25)
        password=os.environ['KEYPOINT_BOARD_SUDO_PASSWORD']
        HDMILink(a,password).run()
    finally:
        stop.set();worker.join();server.__exit__()

if __name__=='__main__':main()
