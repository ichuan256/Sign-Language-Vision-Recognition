"""Prepare a short, bounded 720p raw RGB loop for board-only display throughput validation."""
import argparse
import csv
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
import cv2
import numpy as np
from vision.keypoints.student_data import digest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--frames',type=int,default=24)
    a=p.parse_args();out=a.output.resolve();source=a.source.resolve()
    if out.exists() or not out.is_relative_to(ROOT/'project/_tmp') or not 2<=a.frames<=48:raise ValueError('New bounded project/_tmp output required')
    current=json.loads((ROOT/'vision/data/manifests/current_available_fullframe.json').read_text())
    manifest=ROOT/current['manifest']
    if digest(manifest)!=current['sha256']:raise ValueError('Approved manifest SHA changed')
    with manifest.open(encoding='utf-8-sig',newline='') as stream:rows=list(csv.DictReader(stream))
    if source not in {(ROOT/r['输出路径']).resolve() for r in rows}:raise ValueError('Choose source from approved subset')
    sha=digest(source);audit=json.loads((ROOT/'vision/analysis/dataset/label_source_audit_20261025.json').read_text(encoding='utf-8'))
    if sha not in {r['sha256'] for r in audit['records']}:raise ValueError('Source not SHA verified')
    cap=cv2.VideoCapture(str(source));fps=cap.get(cv2.CAP_PROP_FPS)
    if not cap.isOpened() or not 0<fps<=60:raise ValueError('Invalid source FPS')
    out.mkdir(parents=True);raw=out/'video.rgb';frame_hashes=[]
    import hashlib
    try:
        with raw.open('wb') as stream:
            for index in range(a.frames):
                ok,bgr=cap.read()
                if not ok:break
                h,w=bgr.shape[:2];scale=min(1280/w,720/h);image=cv2.resize(bgr,(round(w*scale),round(h*scale)))
                canvas=np.zeros((720,1280,3),np.uint8);yy=(720-image.shape[0])//2;xx=(1280-image.shape[1])//2
                canvas[yy:yy+image.shape[0],xx:xx+image.shape[1]]=image
                cv2.rectangle(canvas,(0,0),(1280,80),(0,0,0),-1)
                cv2.putText(canvas,'BOARD RAW VIDEO ONLY / NO LANDMARKS',(16,28),cv2.FONT_HERSHEY_SIMPLEX,.7,(0,220,255),2)
                cv2.putText(canvas,f'SOURCE FRAME {index} | {index/fps:.3f}s | short loop',(16,60),cv2.FONT_HERSHEY_SIMPLEX,.7,(255,255,255),2)
                payload=cv2.cvtColor(canvas,cv2.COLOR_BGR2RGB).tobytes();stream.write(payload)
                frame_hashes.append(hashlib.sha256(payload).hexdigest())
    finally:cap.release()
    if len(set(frame_hashes))<2:raise ValueError('Need distinct decoded source frames')
    report=dict(scope='board_local_raw_video_display_no_network_inference',width=1280,height=720,
        channels=3,frames=len(frame_hashes),source_fps=fps,source_sha256=sha,raw_sha256=digest(raw),
        raw_bytes=raw.stat().st_size,frame_sha256=frame_hashes,layout='RGB888 contiguous little-endian uint32 copy',
        limitations=['Short predecoded loop; no sustained SD decode test, no camera, no keypoints or vsync synchronization'])
    (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('frames','source_fps','raw_bytes')},indent=2))


if __name__=='__main__':main()
