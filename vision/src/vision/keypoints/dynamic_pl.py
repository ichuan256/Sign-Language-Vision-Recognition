"""Paced moving video with cached PC ROI tracking and asynchronous actual PL pose.

The PC never executes the landmark network here. Cached PC points only define
the rotated ROI. Displayed finger pose comes from the persistent board graph.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import threading
import time
import cv2
import numpy as np
from .frame_server import LatestFrameServer
from .hdmi_link import HDMILink
from ..framesource import ReplaySource
from project.scripts.keypoints.prepare_hand_rois import canonical_roi
from project.scripts.keypoints.show_hand_result import EDGES

ROOT=next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())

class LatestSlot:
    def __init__(self):self.condition=threading.Condition();self.item=None;self.dropped=0
    def put(self,item):
        with self.condition:
            if self.item is not None:self.dropped+=1
            self.item=item;self.condition.notify()
    def take(self,timeout=.5):
        with self.condition:
            if self.item is None:self.condition.wait(timeout)
            result=self.item;self.item=None;return result

def skeleton(image,points,color=(0,220,0)):
    points=np.rint(points).astype(int)
    for i,j in EDGES:cv2.line(image,tuple(points[i]),tuple(points[j]),color,2)
    for point in points:cv2.circle(image,tuple(point),3,(0,180,255),-1)

def choose_probe(directory):
    report=json.loads((directory/'report.json').read_text(encoding='utf-8'))
    with np.load(directory/'rois.npz') as data:index=int(data['validation_indices'][0])
    record=report['records'][index]
    source=ROOT/record['source']
    if hashlib.sha256(source.read_bytes()).hexdigest()!=record['sha256']:raise RuntimeError('Source SHA mismatch')
    for file in (ROOT/'vision/data/cache/m1').glob('extract_part*/report.json'):
        for sample in json.loads(file.read_text(encoding='utf-8'))['samples']:
            if sample['source_sha256']==record['sha256']:return source,file.parent/sample['npz'],record
    raise RuntimeError('No SHA-matched cached ROI track')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--deployment',type=Path,required=True);p.add_argument('--probes',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--seconds',type=int,default=600)
    p.add_argument('--fps',type=int,default=15);p.add_argument('--board',default='xilinx@192.168.2.99')
    p.add_argument('--pc-port',type=int,default=18780);p.add_argument('--remote-port',type=int,default=18781)
    args=p.parse_args();out=args.output.resolve()
    if out.exists() or not out.is_relative_to(ROOT/'project/_tmp'):raise ValueError('New project/_tmp output required')
    if not 15<=args.seconds<=600 or not 1<=args.fps<=30:raise ValueError('Bounded seconds 15..600, FPS 1..30')
    out.mkdir(parents=True)
    release=json.loads((args.deployment/'deployment.json').read_text());work=release['board_workdir']
    args.release_manifest=args.deployment/'deployment.json'
    env=dict(os.environ);password=env.pop('KEYPOINT_BOARD_SUDO_PASSWORD')
    source,cache,record=choose_probe(args.probes)
    with np.load(cache) as data:hands=data['hands'];indices=data['frame_indices']
    q=shlex.quote;script=ROOT/'project/board/keypoints/stream_hand_board.py';remote=work+'/stream_hand_board.py'
    options=['-o','BatchMode=yes','-o','ConnectTimeout=8']
    exists=subprocess.run(['ssh',*options,args.board,'test -e '+q(remote)],env=env).returncode==0
    if not exists:subprocess.run(['scp',str(script),args.board+':'+remote],env=env,check=True,stdout=subprocess.DEVNULL)
    digest=subprocess.check_output(['ssh',*options,args.board,'sha256sum '+q(remote)],env=env,text=True).split()[0]
    if digest!=hashlib.sha256(script.read_bytes()).hexdigest():raise RuntimeError('Persistent worker differs; inspect instead of overwrite')
    command='sudo -S -p '+q('')+' env XILINX_XRT=/usr /usr/local/share/pynq-venv/bin/python -u '+q(remote)+' --work '+q(work)+' --seconds '+str(args.seconds+90)
    stop=threading.Event();ready=threading.Event();slot=LatestSlot();lock=threading.Lock()
    shared=dict(result=None,error=None);latencies=[];results=[];link_error=[];link_done=threading.Event()
    report=dict(scope='moving_video_PC_cached_ROI_actual_PL_landmarks',cpu_neural_fallback=False,
        cached_ROI_only=True,source=str(source.relative_to(ROOT)),source_sha256=record['sha256'],
        hand_index=record['hand_index'],requested_video_fps=args.fps,seconds=args.seconds,
        limitations=['PC cached ROI tracking on one SHA-matched clip; not autonomous arbitrary-video detection',
            'Left shows PC ROI box only; right shows actual PL input and pose, age/source ID shown',
            'Display FPS is independent of PL update rate; no camera exposure latency measurement'])
    with (out/'worker_stderr.log').open('wb') as stderr:
        process=subprocess.Popen(['ssh','-T',*options,args.board,command],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=stderr,env=env)
        process.stdin.write((password+'\n').encode());process.stdin.flush()
        def worker():
            try:
                message=json.loads(process.stdout.readline())
                if message.get('event')!='ready':raise RuntimeError('PL worker initialization failed')
                fraction=message['input_fraction'];shared['fraction']=fraction;ready.set()
                with (out/'pl_results.jsonl').open('w',encoding='utf-8') as log:
                    while not stop.is_set():
                        job=slot.take()
                        if job is None:continue
                        raw=job['codes'].astype('<i2',copy=False).tobytes();tick=time.monotonic()
                        header=dict(frame_id=job['frame_id'],source_timestamp_s=job['timestamp'])
                        process.stdin.write((json.dumps(header)+'\n').encode());process.stdin.write(raw);process.stdin.flush()
                        response=json.loads(process.stdout.readline())
                        if response.get('event')!='result' or response['frame_id']!=job['frame_id']:raise RuntimeError('PL stream response mismatch')
                        if response['input_sha256']!=hashlib.sha256(raw).hexdigest():raise RuntimeError('ROI transport SHA mismatch')
                        response['request_wall_s']=time.monotonic()-tick
                        log.write(json.dumps(response)+'\n');log.flush();results.append(response);latencies.append(response['board_forward_s'])
                        job['response']=response;job['received']=time.monotonic()
                        with lock:shared['result']=job
            except Exception as exc:
                shared['error']=str(exc);ready.set();stop.set()
            finally:
                if process.stdin:process.stdin.close()
        thread=threading.Thread(target=worker,daemon=True);thread.start()
        # Keep initialization out of the replay clock; no second bitstream download.
        if not ready.wait(60) or shared['error']:
            stop.set();process.terminate();thread.join(timeout=5)
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
            raise RuntimeError(shared['error'] or 'PL worker not ready in 60 seconds')
        started=time.monotonic();frames=0;roi_frames=0;link=None
        try:
            with LatestFrameServer(args.pc_port) as server,ReplaySource(source,max_fps=args.fps,loop=True) as replay:
                args.output=out/'hdmi'
                def run_link():
                    try:HDMILink(args,password).run()
                    except Exception as exc:link_error.append(str(exc));stop.set()
                    finally:link_done.set()
                while not stop.is_set() and time.monotonic()-started<args.seconds+60:
                    item=replay.read()
                    if item is None:break
                    frame,frame_id,timestamp=item;frames+=1;now=time.monotonic()
                    local_time=timestamp%replay._duration
                    near=int(np.argmin(np.abs(indices-local_time*replay.source._fps)))
                    hand=hands[near,record['hand_index']]
                    inverse=None
                    if np.isfinite(hand).all():
                        try:
                            rgb,inverse=canonical_roi(frame,hand)
                            codes=np.clip(np.rint(np.ldexp(rgb,shared['fraction'])),-32768,32767).astype(np.int16)
                            slot.put(dict(codes=codes,rgb=rgb,frame_id=frame_id,timestamp=timestamp,submitted=now))
                            roi_frames+=1
                        except ValueError:pass
                    with lock:latest=shared['result']
                    if inverse is not None:
                        corners=np.array([[0,0,1],[223,0,1],[223,223,1],[0,223,1]],np.float64)@inverse.T
                        cv2.polylines(frame,[np.rint(corners).astype(np.int32)],True,(0,220,220),2)
                    canvas=np.zeros((720,1280,3),np.uint8)
                    scale=min(880/frame.shape[1],570/frame.shape[0]);w,h=round(frame.shape[1]*scale),round(frame.shape[0]*scale)
                    canvas[120:120+h,10:10+w]=cv2.resize(frame,(w,h))
                    lines=[f'MOVING REPLAY | FRAME {frame_id} | SOURCE {timestamp:.2f}s',
                           f'VIDEO {frames/max(now-started,.001):.1f} FPS | PC CACHED ROI -> ACTUAL PL POSE',
                           'LEFT: PC ROI box | '+('ROI READY' if inverse is not None else 'NO NEW ROI')+' | RIGHT: actual PL input/pose']
                    if latest:
                        response=latest['response'];pose=np.array(response['outputs'][:63]).reshape(21,3)[:,:2]
                        roi=cv2.cvtColor(np.clip(latest['rgb']*255,0,255).astype(np.uint8),cv2.COLOR_RGB2BGR)
                        skeleton(roi,pose,(0,220,0) if response['outputs'][63]>.5 else (0,0,220))
                        canvas[160:496,930:1266]=cv2.resize(roi,(336,336))
                        lines += [f'PL result #{response["sequence"]} from FRAME {latest["frame_id"]} | pose age {now-latest["submitted"]:.2f}s',
                            f'PL forward {response["board_forward_s"]:.3f}s | presence {response["outputs"][63]:.3f}']
                        cv2.putText(canvas,'LAST PL INPUT / OUTPUT',(930,140),cv2.FONT_HERSHEY_SIMPLEX,.45,(240,240,240),1)
                    else:lines+=['Waiting for first actual PL result...']
                    for i,line in enumerate(lines):cv2.putText(canvas,line,(12,26+i*22),cv2.FONT_HERSHEY_SIMPLEX,.55,(240,240,240),1)
                    server.publish(canvas,frame_id,timestamp)
                    if frames%15==0:
                        live=dict(active=True,video_frames=frames,ROI_frames=roi_frames,elapsed_s=now-started,source_timestamp_s=timestamp,
                            pl_results=len(results),unique_PL_inputs=len({r['input_sha256'] for r in results}),
                            unique_PL_outputs=len({r['output_sha256'] for r in results}),
                            latest_PL_forward_s=results[-1]['board_forward_s'] if results else None,
                            pending_ROIs_replaced=slot.dropped,hdmi_state=server.state(),cpu_neural_fallback=False)
                        (out/'live.json').write_text(json.dumps(live,indent=2)+'\n')
                    if link is None:
                        link=threading.Thread(target=run_link,daemon=True);link.start()
                    if link_done.is_set():break
                report.update(video_frames=frames,ROI_frames=roi_frames,elapsed_s=time.monotonic()-started,hdmi_publish_state=server.state(),replay_loops=replay.loops)
        finally:
            stop.set();thread.join(timeout=40)
            if thread.is_alive():process.terminate()
            try:process.wait(timeout=10)
            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
            if link:link.join(timeout=20)
            report.update(pl_results=len(results),pending_ROIs_replaced=slot.dropped,
                unique_PL_inputs=len({r['input_sha256'] for r in results}),unique_PL_outputs=len({r['output_sha256'] for r in results}),
                pl_forward_s=latencies,error=shared['error'] or (link_error[0] if link_error else None),
                screen_visually_confirmed=False,worker_exit_code=process.returncode)
            report['valid_run']=frames>1 and len(results)>1 and report['unique_PL_inputs']>1 and report['unique_PL_outputs']>1 and not report['error']
            (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
            (out/'live.json').write_text(json.dumps(dict(active=False,video_frames=frames,
                pl_results=len(results),error=report['error'],final_report='report.json'),indent=2)+'\n')
        if report['error']:raise RuntimeError(report['error'])
if __name__=='__main__':main()
