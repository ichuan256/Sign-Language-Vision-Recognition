"""Two live OV5640 inputs, independent PC Holistic trackers, web preview.

No depth/3-D claim: exposures are not synchronized or stereo-calibrated.
"""
import argparse
from contextlib import ExitStack
import getpass
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import threading
import time

import cv2
import mediapipe as mp
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from .ov5640_ssh_source import OV5640SSHSource
from .frame_server import LatestFrameServer


class StereoSource(OV5640SSHSource):
    def __init__(self,password,output):
        self.channels={};self.pair_sequence=0;self.channel_errors={}
        super().__init__(password,output,work='/home/xilinx/ov5640_stereo_20261031',worker='stereo_stream.py')

    def receive(self):
        try:
            first=self.process.stdout.readline()
            if not first:
                detail=Path(self.log.name).read_text(encoding='utf-8',errors='replace')[-1500:]
                raise RuntimeError('Board stereo worker exited before ready: '+detail)
            ready=json.loads(first)
            if ready.get('event')!='ready' or ready.get('cameras')!=[1,2]:raise RuntimeError('Dual camera worker not ready')
            self.pid=int(ready['pid'])
            while not self.stop.is_set():
                line=self.process.stdout.readline(8192)
                if not line:raise EOFError('Dual camera stream ended')
                header=json.loads(line)
                if header.get('event')=='finished':
                    raise EOFError('Dual capture stopped safely')
                if header.get('event')=='channel_finished':
                    self.channel_errors[header['camera']]=header['result']
                    # Keep draining stdout so the other camera can finish safely.
                    continue
                if (header.get('event'),header.get('camera') in (1,2),header.get('bytes'),
                    header.get('width'),header.get('height'),header.get('format'),header.get('dma_shutdown_confirmed'))!=('frame',True,1280*720*2,1280,720,'RGB565_LE',True):
                    raise RuntimeError('Invalid/incomplete physical camera frame')
                raw=self.exact(self.process.stdout,header['bytes'])
                bgr=cv2.cvtColor(np.frombuffer(raw,np.uint8).reshape(720,1280,2),cv2.COLOR_BGR5652BGR)
                self.channels[header['camera']]=dict(image=bgr,frame=header['frame'],
                    board_time=header['capture_completed_monotonic_s'],received=time.monotonic())
                if set(self.channels)=={1,2}:
                    self.pair_sequence+=1
                    with self.condition:
                        self.latest=(dict(self.channels),self.pair_sequence,time.monotonic()-self.started)
                        self.condition.notify_all()
        except Exception as exc:
            with self.condition:
                self.error=str(exc)+' '+json.dumps(self.channel_errors,ensure_ascii=False)[-1200:]
                self.condition.notify_all()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--seconds',type=int,default=3600)
    p.add_argument('--sign-model',type=Path)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    password=os.environ.pop('KEYPOINT_BOARD_SUDO_PASSWORD',None)
    if password is None:password=getpass.getpass('Board sudo password: ')
    stop=threading.Event();lock=threading.Lock();token=secrets.token_urlsafe(24)
    state=dict(mode='stereo',active=True,input='OV1 + OV2 physical cameras',inference='two independent PC Holistic trackers',
        exposure_synchronized=False,depth_estimation=False,frames=0,cameras={},error=None)
    html="""<!doctype html><meta charset='utf-8'><title>双目实时识别</title><h1>OV双路实时识别</h1><p>左右相机独立采集，PC教师识别；未校准曝光同步或三维深度。</p><img id='v' style='max-width:100%'><pre id='s'></pre><button onclick="fetch('/stop',{method:'POST',headers:{'X-Session':'TOKEN'}})">安全停止</button><script>setInterval(async()=>{let s=await(await fetch('/state')).json();document.getElementById('s').textContent=JSON.stringify(s,null,2);document.getElementById('v').src='http://127.0.0.1:18780/frame.jpg?t='+Date.now()},800)</script>""".replace('TOKEN',token)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*_):pass
        def send(self,body,ctype):
            self.send_response(200);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(body)));self.end_headers()
            try:self.wfile.write(body)
            except (BrokenPipeError,ConnectionResetError):pass
        def do_GET(self):
            if self.path=='/':self.send(html.encode(),'text/html; charset=utf-8')
            elif self.path=='/state':
                with lock:body=json.dumps(state,ensure_ascii=False).encode()
                self.send(body,'application/json; charset=utf-8')
            else:self.send_error(404)
        def do_POST(self):
            if self.headers.get('X-Session')!=token:self.send_error(403);return
            if self.path!='/stop':self.send_error(404);return
            stop.set();self.send(b'{}','application/json')
    control=ThreadingHTTPServer(('127.0.0.1',18783),Handler);control.daemon_threads=True
    threading.Thread(target=control.serve_forever,daemon=True).start()
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',24)
    started=time.monotonic();last_ids={};shown={};heads={}
    try:
        with ExitStack() as stack:
            server=stack.enter_context(LatestFrameServer(18780))
            source=stack.enter_context(StereoSource(password,a.output))
            trackers={camera:stack.enter_context(mp.solutions.holistic.Holistic(static_image_mode=False,model_complexity=1,
                smooth_landmarks=True,min_detection_confidence=.5,min_tracking_confidence=.5)) for camera in (1,2)}
            if a.sign_model:
                from ..classify.teacher_sign import LiveSignHead
                heads={camera:LiveSignHead(a.sign_model) for camera in (1,2)}
            while not stop.is_set() and time.monotonic()-started<a.seconds:
                pair,number,timestamp=source.read();camera_states={}
                for camera,item in pair.items():
                    if item['frame']!=last_ids.get(camera):
                        frame=item['image'];tick=time.monotonic()
                        result=trackers[camera].process(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB));inference_ms=(time.monotonic()-tick)*1000
                        if camera in heads:heads[camera].observe(result,frame,item['board_time'])
                        overlay=frame.copy();drawing=mp.solutions.drawing_utils
                        drawing.draw_landmarks(overlay,result.pose_landmarks,mp.solutions.holistic.POSE_CONNECTIONS)
                        for hand in (result.left_hand_landmarks,result.right_hand_landmarks):
                            drawing.draw_landmarks(overlay,hand,mp.solutions.holistic.HAND_CONNECTIONS)
                        shown[camera]=(overlay,inference_ms);last_ids[camera]=item['frame']
                    camera_states[str(camera)]=dict(frame=item['frame'],teacher_ms=shown[camera][1],
                        received_age_s=time.monotonic()-item['received'],capture_completed_monotonic_s=item['board_time'])
                    if camera in heads:camera_states[str(camera)]['sign_recognition']=heads[camera].snapshot()
                canvas=np.full((720,1280,3),20,np.uint8)
                for camera,x in ((1,0),(2,640)):canvas[135:495,x:x+640]=cv2.resize(shown[camera][0],(640,360))
                image=Image.fromarray(cv2.cvtColor(canvas,cv2.COLOR_BGR2RGB));draw=ImageDraw.Draw(image)
                draw.text((20,20),'OV双路实时识别 / 两路独立PC教师 / 网页预览',font=font,fill='white')
                for camera,x in ((1,20),(2,660)):
                    cs=camera_states[str(camera)]
                    draw.text((x,90),('左目 OV1' if camera==1 else '右目 OV2')+'  帧 '+str(cs['frame']),font=font,fill=(100,235,190))
                    draw.text((x,520),'教师 %.0fms / 接收帧龄 %.2fs'%(cs['teacher_ms'],cs['received_age_s']),font=font,fill='white')
                    sign=cs.get('sign_recognition',{})
                    draw.text((x,565),'手语：'+(sign.get('label') or '未确定')+'  候选：'+(sign.get('candidate') or '无'),font=font,fill='white')
                skew=abs(pair[1]['board_time']-pair[2]['board_time'])
                draw.text((20,640),'采集完成时间差 %.1fms；未验证曝光同步，不提供三维深度。'%(skew*1000),font=font,fill=(255,210,90))
                server.publish(cv2.cvtColor(np.asarray(image),cv2.COLOR_RGB2BGR),number,timestamp)
                with lock:state.update(frames=number,cameras=camera_states,pair_completion_skew_s=skew)
                (a.output/'live.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    except Exception as exc:
        with lock:state['error']=str(exc)
        raise
    finally:
        for head in heads.values():head.close()
        with lock:state['active']=False
        control.shutdown();control.server_close()
        (a.output/'report.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
