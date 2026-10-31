"""Live PC teacher and actual existing PL graph, selectable on one HDMI feed."""
import argparse
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import shlex
import subprocess
import threading
import time

import cv2
import mediapipe as mp
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .dynamic_pl import LatestSlot, skeleton
from .frame_server import LatestFrameServer
from ..framesource import ReplaySource, USBCamSource
from project.scripts.keypoints.prepare_hand_rois import canonical_roi

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'AGENTS.md').is_file())


class PLStream:
    def __init__(self, work, password, output, seconds):
        self.slot=LatestSlot();self.stop=threading.Event();self.ready=threading.Event()
        self.lock=threading.Lock();self.latest=None;self.error=None;self.results=[]
        self.inputs=set();self.outputs=set();self.started=None
        self.log=(output/'pl_results.jsonl').open('x',encoding='utf-8')
        self.stderr=(output/'pl_worker_stderr.log').open('xb')
        q=shlex.quote
        command=('sudo -S -p '+q('')+' env XILINX_XRT=/usr /usr/local/share/pynq-venv/bin/python -u '+
                 q(work+'/stream_hand_board.py')+' --work '+q(work)+' --seconds '+str(seconds+120))
        env=dict(os.environ);env.pop('KEYPOINT_BOARD_SUDO_PASSWORD',None)
        self.process=subprocess.Popen(['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=8',
            '-o','ServerAliveInterval=5','-o','ServerAliveCountMax=2','xilinx@192.168.2.99',command],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.stderr,env=env)
        self.process.stdin.write((password+'\n').encode());self.process.stdin.flush()
        self.thread=threading.Thread(target=self.run,daemon=True);self.thread.start()

    def run(self):
        try:
            response=json.loads(self.process.stdout.readline())
            if response.get('event')!='ready' or 'PL_' not in response.get('backend',''):
                raise RuntimeError('Actual PL backend did not initialize')
            self.fraction=response['input_fraction'];self.started=time.monotonic();self.ready.set()
            while not self.stop.is_set():
                job=self.slot.take()
                if job is None:continue
                codes=np.clip(np.rint(np.ldexp(job['rgb'],self.fraction)),-32768,32767).astype('<i2')
                raw=codes.tobytes();tick=time.monotonic()
                header=dict(frame_id=job['frame_id'],source_timestamp_s=job['timestamp'])
                self.process.stdin.write((json.dumps(header)+'\n').encode());self.process.stdin.write(raw);self.process.stdin.flush()
                response=json.loads(self.process.stdout.readline())
                if response.get('event')!='result' or response['frame_id']!=job['frame_id']:
                    raise RuntimeError('Actual PL response identity mismatch')
                if response['input_sha256']!=hashlib.sha256(raw).hexdigest():raise RuntimeError('PL input SHA mismatch')
                if response.get('cpu_neural_fallback') is not False or response['mac_calls']!=49 or response['vector_calls']!=13:
                    raise RuntimeError('Unexpected PL graph call counts')
                if len(response['outputs'])!=64 or not np.isfinite(response['outputs']).all():
                    raise RuntimeError('Invalid hardware output')
                response.update(clip=job['clip'],request_wall_s=time.monotonic()-tick)
                self.log.write(json.dumps(response,ensure_ascii=False)+'\n');self.log.flush()
                job.update(response=response,received=time.monotonic())
                with self.lock:
                    self.latest=job;self.results.append(response)
                    self.inputs.add(response['input_sha256']);self.outputs.add(response['output_sha256'])
        except Exception as error:
            self.error=str(error);self.ready.set()
        finally:
            if self.process.stdin:self.process.stdin.close()

    def snapshot(self):
        with self.lock:
            now=time.monotonic();latest=self.latest
            state=dict(pl_results=len(self.results),unique_PL_inputs=len(self.inputs),unique_PL_outputs=len(self.outputs),
                pl_result_hz=len(self.results)/max(now-(self.started or now),.001),pl_error=self.error,
                pending_ROIs_replaced=self.slot.dropped)
            if latest:
                state.update(pl_forward_ms=latest['response']['board_forward_s']*1000,
                             pl_source_frame=latest['frame_id'],pl_result_age_s=now-latest['submitted'])
            return latest,state

    def close(self):
        self.stop.set();self.thread.join(timeout=40)
        if self.thread.is_alive():
            # Do not terminate a process that could still own active DMA buffers.
            return
        self.process.wait(timeout=15);self.log.close();self.stderr.close()


def playlist():
    report=json.loads((ROOT/'project/_tmp/kp_rois_v1/report.json').read_text(encoding='utf-8'))
    records=[]
    for word,group in [('没关系','NL_lesson_09'),('服务','NL_lesson_09'),('可以。','NL_lesson_10')]:
        record=next(r for r in report['records'] if r['source_group']==group and ('/'+word+'/') in r['source'])
        path=ROOT/record['source']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=record['sha256']:raise RuntimeError('Source video SHA mismatch')
        records.append(dict(record,label=word))
    return records


def fit(canvas,image,box):
    x,y,w,h=box;s=min(w/image.shape[1],h/image.shape[0])
    ww,hh=round(image.shape[1]*s),round(image.shape[0]*s)
    canvas[y+(h-hh)//2:y+(h-hh)//2+hh,x+(w-ww)//2:x+(w-ww)//2+ww]=cv2.resize(image,(ww,hh))


class NoPL:
    """Teacher-only view must not allocate or execute the PL graph."""
    error=None
    class Sink:
        def put(self,item):pass
    slot=Sink()
    def snapshot(self):
        return None,dict(pl_results=0,pl_result_hz=0,pl_error=None,PL_enabled=False)
    def close(self):pass


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--seconds',type=int,default=600)
    p.add_argument('--mode',choices=('pc','pl'),default='pc')
    p.add_argument('--control-port',type=int,default=18782)
    p.add_argument('--frame-port',type=int,default=18780)
    p.add_argument('--camera',type=int,help='Computer USB camera index; no file fallback')
    p.add_argument('--ov5640',action='store_true',help='Board OV5640 over SSH; PC preview only, no HDMI in snapshot firmware')
    p.add_argument('--no-pl',action='store_true',help='Teacher-only processing, no PL graph')
    p.add_argument('--sign-model',type=Path,help='Optional temporal sign head over the same frozen teacher landmarks')
    p.add_argument('--video',type=Path,help='Single workspace video for explicit replay verification')
    a=p.parse_args();out=a.output.resolve()
    if out.exists() or not out.is_relative_to(ROOT/'project/_tmp') or not 30<=a.seconds<=86400:
        raise ValueError('New bounded workspace output required')
    if not 1024<=a.control_port<=65535 or (a.camera is not None and not 0<=a.camera<=9):
        raise ValueError('Invalid control port or camera index')
    if a.no_pl and a.mode=='pl':raise ValueError('PL view requires PL execution')
    if a.ov5640 and (a.camera is not None or not a.no_pl):raise ValueError('OV5640 requires exclusive input and teacher-only processing')
    out.mkdir(parents=True)
    password=os.environ.pop('KEYPOINT_BOARD_SUDO_PASSWORD',None)
    deployment=None if a.no_pl else json.loads((ROOT/'project/_tmp/kp_stream_deploy_v2/deployment.json').read_text())
    live_camera=a.camera is not None or a.ov5640
    sources=[dict(label='OV5640实时输入' if a.ov5640 else 'USB摄像头实时输入',hand_index=0)] if live_camera else playlist()
    if a.video:
        video=a.video.resolve()
        if live_camera or not video.is_relative_to(ROOT) or not video.is_file():raise ValueError('Exclusive existing workspace video required')
        sources=[dict(source=str(video.relative_to(ROOT)),label=video.stem,hand_index=0)]
    (out/'playlist.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    pl=NoPL() if a.no_pl else PLStream(deployment['board_workdir'],password,out,a.seconds)
    sign=None
    if a.sign_model:
        if not a.no_pl:raise ValueError('First sign-recognition head runs with the PC teacher only')
        from ..classify.teacher_sign import LiveSignHead
        sign=LiveSignHead(a.sign_model)
    token=secrets.token_urlsafe(24);lock=threading.Lock();stop=threading.Event()
    state=dict(mode=a.mode,active=True,video_frames=0,teacher_frames=0,teacher_hand_frames=0,
        PC_neural_backend='MediaPipe Holistic',PL_neural_backend='W12/A16 lite graph on PL',
        ROI_locator='live PC Holistic; no cached ROI tracks',new_full_teacher_PL_migration=False,
        input_source='board OV5640' if a.ov5640 else 'USB camera' if a.camera is not None else 'recorded video',camera_index=a.camera)
    html='''<!doctype html><meta charset="utf-8"><title>关键点录制控制</title>
<style>body{font:20px sans-serif;background:#101b2c;color:white;margin:24px}button{font-size:22px;margin:10px;padding:16px}img{max-width:100%}</style>
<h1>关键点演示模式</h1><button onclick="mode('pc')">1 PC教师识别 → HDMI</button>
<button onclick="mode('pl')">2 实际PL关键点 → HDMI</button><p>视频来自文件回放。第二模式由PC定位ROI，PL计算单手21点。</p><pre id="s"></pre>
<img id="f"><script>function mode(m){fetch('/mode/'+m,{method:'POST',headers:{'X-Session':'TOKEN'}})}
setInterval(async()=>{let s=await(await fetch('/state')).json();document.getElementById('s').textContent=JSON.stringify(s,null,2);document.getElementById('f').src='http://127.0.0.1:18780/frame.jpg?t='+Date.now()},700)</script>'''.replace('TOKEN',token)
    if sign:
        html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>USB手语识别实验</title>
<style>body{font:18px 'Microsoft YaHei',sans-serif;background:#101b2c;color:white;max-width:1150px;margin:24px auto;padding:16px}img{width:100%;border-radius:12px}#word{font-size:38px;color:#6fe1c4}p{line-height:1.7}button{padding:12px 22px;border-radius:10px;cursor:pointer}pre{white-space:pre-wrap;max-height:180px;overflow:auto}</style>
<h1>USB摄像头 · 手语识别实验</h1><p>教师关键点 + 时序模板模型，在电脑执行。词表：谢谢、再见、没关系、可以、早上。</p>
<div id="word">等待动作</div><p id="candidate"></p><p>请完整做一个动作，停顿后再做下一个。词表外动作可能混淆；候选分数不是准确率或概率。</p>
<img id="frame" alt="实时骨架与手语识别"><button onclick="fetch('/stop',{method:'POST',headers:{'X-Session':'TOKEN'}})">停止摄像头</button><details><summary>运行详情</summary><pre id="state"></pre></details>
<script>async function poll(){try{let s=await(await fetch('/state')).json(),r=s.sign_recognition||{};document.getElementById('word').textContent=r.label||'未确定';document.getElementById('candidate').textContent=(r.candidate?'候选：'+r.candidate+'；':'')+(r.reason||'等待完整动作');document.getElementById('frame').src='http://127.0.0.1:FRAME_PORT/frame.jpg?t='+Date.now();document.getElementById('state').textContent=JSON.stringify(s,null,2)}catch(e){document.getElementById('candidate').textContent='服务已停止或连接中断'}}poll();setInterval(poll,800)</script></html>'''.replace('TOKEN',token).replace('FRAME_PORT',str(a.frame_port))
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def send(self,body,ctype,status=200):
            self.send_response(status);self.send_header('Content-Type',ctype)
            self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.end_headers()
            try:self.wfile.write(body)
            except (BrokenPipeError,ConnectionResetError):pass
        def do_GET(self):
            if self.path=='/':self.send(html.encode(),'text/html; charset=utf-8')
            elif self.path=='/state':
                _,ps=pl.snapshot()
                with lock:reply=dict(state,**ps)
                self.send(json.dumps(reply,ensure_ascii=False).encode(),'application/json; charset=utf-8')
            else:self.send(b'Not found','text/plain',404)
        def do_POST(self):
            if self.headers.get('X-Session')!=token:self.send(b'Forbidden','text/plain',403);return
            if self.path=='/stop':stop.set();self.send(b'{}','application/json');return
            mode=self.path.removeprefix('/mode/')
            if mode not in ('pc','pl'):self.send(b'Not found','text/plain',404);return
            if mode=='pl' and a.no_pl:self.send(b'PL disabled','text/plain',409);return
            with lock:state['mode']=mode
            self.send(b'{}','application/json')
    control=ThreadingHTTPServer(('127.0.0.1',a.control_port),Handler);control.daemon_threads=True
    threading.Thread(target=control.serve_forever,daemon=True).start()
    fonts=[ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',size) for size in (30,22)]
    started=time.monotonic();frames=0;hand_frames=0;clip_index=0;last_write=0
    stream=(out/'teacher_frames.jsonl').open('x',encoding='utf-8')
    try:
        with LatestFrameServer(a.frame_port) as server,mp.solutions.holistic.Holistic(
            static_image_mode=False,model_complexity=1,smooth_landmarks=True,
            min_detection_confidence=.5,min_tracking_confidence=.5) as detector:
            while not stop.is_set() and time.monotonic()-started<a.seconds:
                record=sources[clip_index%len(sources)]
                if a.ov5640:
                    from .ov5640_ssh_source import OV5640SSHSource
                    source=OV5640SSHSource(password,out)
                elif a.camera is not None:source=USBCamSource(a.camera,width=1280,height=720,max_fps=15)
                else:source=ReplaySource(ROOT/record['source'],max_fps=15,loop=False)
                with source as replay:
                    while not stop.is_set() and time.monotonic()-started<a.seconds:
                        item=replay.read()
                        if item is None:
                            if live_camera:raise RuntimeError('Camera stopped delivering frames; no replay fallback')
                            break
                        bgr,local_frame,timestamp=item;tick=time.monotonic()
                        result=detector.process(cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB));inference_ms=(time.monotonic()-tick)*1000
                        frames+=1;now=time.monotonic()
                        if sign:sign.observe(result,bgr,timestamp)
                        sign_state=sign.snapshot() if sign else None
                        hands=[result.left_hand_landmarks,result.right_hand_landmarks]
                        hand=hands[record['hand_index']] or next((h for h in hands if h is not None),None)
                        inverse=None
                        if hand is not None:
                            hand_frames+=1
                            points=np.array([(p.x,p.y,p.z) for p in hand.landmark])
                            try:
                                rgb,inverse=canonical_roi(bgr,points)
                                pl.slot.put(dict(rgb=rgb,frame_id=frames,timestamp=timestamp,submitted=now,
                                                 clip=record['label'],local_frame=int(local_frame)))
                            except ValueError:pass
                        latest,ps=pl.snapshot()
                        with lock:mode=state['mode']
                        canvas=np.full((720,1280,3),(32,24,14),np.uint8)
                        if mode=='pc':
                            shown=bgr.copy();drawing=mp.solutions.drawing_utils
                            drawing.draw_landmarks(shown,result.pose_landmarks,mp.solutions.holistic.POSE_CONNECTIONS)
                            for h in hands:drawing.draw_landmarks(shown,h,mp.solutions.holistic.HAND_CONNECTIONS)
                            fit(canvas,shown,(10,100,1260,540))
                            title='视觉测试  USB手语识别' if sign else '视觉测试  摄像头实时关键点' if live_camera else '模式1  教师模型 视频关键点检测'
                            line='身体33点与双手21点  |  视频关键点叠加'
                        else:
                            shown=bgr.copy()
                            if inverse is not None:
                                corners=np.array([[0,0,1],[223,0,1],[223,223,1],[0,223,1]],np.float64)@inverse.T
                                cv2.polylines(shown,[np.rint(corners).astype(np.int32)],True,(0,220,220),3)
                            fit(canvas,shown,(10,120,880,490))
                            if latest:
                                roi=cv2.cvtColor(np.clip(latest['rgb']*255,0,255).astype(np.uint8),cv2.COLOR_RGB2BGR)
                                outputs=latest['response']['outputs'];pose=np.array(outputs[:63]).reshape(21,3)[:,:2]
                                skeleton(roi,pose,(0,220,0) if outputs[63]>.5 else (0,0,220))
                                fit(canvas,roi,(920,180,350,350))
                            title='模式2  FPGA PL实际计算 单手21点'
                            line='左侧连续视频与ROI  |  右侧实际PL输入和输出'
                        image=Image.fromarray(cv2.cvtColor(canvas,cv2.COLOR_BGR2RGB));draw=ImageDraw.Draw(image)
                        draw.text((22,12),title,font=fonts[0],fill='white')
                        draw.text((22,54),line,font=fonts[1],fill=(170,210,230))
                        stage='定位' if mode=='pl' else '检测'
                        draw.text((20,644),f'视频 {record["label"]}  帧 {frames}  处理 {frames/max(now-started,.001):.1f}fps  {stage} {inference_ms:.1f}ms',font=fonts[1],fill='white')
                        if mode=='pl':
                            detail=f'PL新结果 {ps["pl_results"]}  {ps["pl_result_hz"]:.2f}Hz'
                            if latest:detail+=f'  推理 {ps["pl_forward_ms"]:.0f}ms  来源帧 {latest["frame_id"]}  帧龄 {now-latest["submitted"]:.2f}s'
                            if pl.error:detail+='  硬件错误 '+pl.error
                            draw.text((20,681),detail,font=fonts[1],fill=(255,220,100))
                        elif sign_state:
                            label=sign_state['label'] or '未确定'
                            candidate=sign_state.get('candidate')
                            detail='手语：'+label
                            if candidate and not sign_state['accepted']:detail+='  候选：'+candidate
                            detail+='  |  演示词：谢谢 / 再见 / 没关系 / 可以 / 早上'
                            draw.text((20,681),detail,font=fonts[1],fill=(255,220,100))
                        else:draw.text((20,681),'OV5640实时采集，当前固件仅提供电脑预览。' if a.ov5640 else '输入为USB摄像头实时采集。' if a.camera is not None else '输入为录制视频节拍回放；骨架随当前画面更新。',font=fonts[1],fill=(255,220,100))
                        server.publish(cv2.cvtColor(np.asarray(image),cv2.COLOR_RGB2BGR),frames,timestamp)
                        row=dict(frame=frames,clip=record['label'],source_frame=int(local_frame),mode=mode,
                                 teacher_inference_ms=inference_ms,hands=sum(h is not None for h in hands))
                        if sign_state:row['sign_recognition']=sign_state
                        stream.write(json.dumps(row,ensure_ascii=False)+'\n')
                        with lock:state.update(video_frames=frames,teacher_frames=frames,teacher_hand_frames=hand_frames,
                            clip=record['label'],teacher_inference_ms=inference_ms,frame_requests=server.state()['frame_requests'])
                        if sign_state:
                            with lock:state['sign_recognition']=sign_state
                        if now-last_write>.5:
                            with lock:live=dict(state,**ps)
                            (out/'live.json').write_text(json.dumps(live,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
                            last_write=now;stream.flush()
                clip_index+=1
    finally:
        with lock:state['active']=False
        if sign:sign.close()
        pl.close();stream.close();control.shutdown();control.server_close()
        _,ps=pl.snapshot()
        (out/'report.json').write_text(json.dumps(dict(state,**ps),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
