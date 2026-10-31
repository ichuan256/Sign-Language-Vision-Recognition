"""OV1 local HDMI raw preview plus exact-source PC Holistic annotation."""
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
from .ov5640_ssh_source import OV5640SSHSource
from .frame_server import LatestFrameServer


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--seconds',type=int,default=3600)
    parser.add_argument('--sign-model',type=Path)
    parser.add_argument('--av',action='store_true',help='Simultaneous board audio and three-column HDMI')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    password=os.environ.pop('KEYPOINT_BOARD_SUDO_PASSWORD',None)
    if password is None:password=getpass.getpass('Board sudo password: ')
    stop=threading.Event();lock=threading.Lock();token=secrets.token_urlsafe(24)
    state=dict(mode='av' if args.av else 'single_hdmi',active=True,input='OV1 physical camera',inference='PC Holistic',
               local_raw_preview_independent=True,results=0,error=None)
    html="""<!doctype html><meta charset='utf-8'><title>OV1 HDMI</title><button onclick="fetch('/stop',{method:'POST',headers:{'X-Session':'TOKEN'}})">停止</button>""".replace('TOKEN',token)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*_):pass
        def send(self,body,ctype):
            self.send_response(200);self.send_header('Content-Type',ctype)
            self.send_header('Content-Length',str(len(body)));self.end_headers()
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
    started=time.monotonic();count=0;head=None
    try:
        with ExitStack() as stack:
            server=stack.enter_context(LatestFrameServer(18780))
            source=stack.enter_context(OV5640SSHSource(password,args.output,
                work='/home/xilinx/ov1_hdmi_20261031',worker='split_hdmi_stream.py',worker_args=('--triple',) if args.av else ()))
            with lock:state['board_capture_path']=source.capture_output
            teacher=stack.enter_context(mp.solutions.holistic.Holistic(static_image_mode=False,model_complexity=1,
                smooth_landmarks=True,min_detection_confidence=.5,min_tracking_confidence=.5))
            if args.sign_model:
                from ..classify.teacher_sign import LiveSignHead
                head=LiveSignHead(args.sign_model)
            while not stop.is_set() and time.monotonic()-started<args.seconds:
                frame,number,board_time=source.read(timeout=120 if args.av and count==0 else 45);tick=time.monotonic()
                result=teacher.process(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB));teacher_ms=(time.monotonic()-tick)*1000
                if head:head.observe(result,frame,board_time)
                overlay=frame.copy();drawing=mp.solutions.drawing_utils
                drawing.draw_landmarks(overlay,result.pose_landmarks,mp.solutions.holistic.POSE_CONNECTIONS)
                for hand in (result.left_hand_landmarks,result.right_hand_landmarks):
                    drawing.draw_landmarks(overlay,hand,mp.solutions.holistic.HAND_CONNECTIONS)
                sign=head.snapshot() if head else {}
                server.publish(overlay,number,board_time,dict(sign_recognition=sign,teacher_ms=teacher_ms))
                count+=1
                with lock:state.update(video_frame=number,results=count,result_hz=count/(time.monotonic()-started),
                    teacher_ms=teacher_ms,source_board_monotonic_s=board_time,sign_recognition=sign)
                (args.output/'live.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
    except Exception as exc:
        with lock:state['error']=str(exc)
        raise
    finally:
        if head:head.close()
        with lock:state['active']=False
        control.shutdown();control.server_close()
        (args.output/'report.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':main()
