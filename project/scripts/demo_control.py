"""Loopback control panel for five demo paths. Never program the FPGA."""
import argparse
import base64
import getpass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import shlex
import socket
import subprocess
import sys
import threading
import time
from urllib.request import Request, build_opener, ProxyHandler

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'ASR'),str(ROOT/'project/scripts/keypoints')]
from run_audio_line import AudioLine
from run_teacher_p0 import remote
from vision.keypoints.hdmi_link import HDMILink

MODES={'teacher':'模式一 · 教师视频检测','pl':'模式二 · PL视频检测',
       'independent':'模式三 · 板端独立运行','audio':'听觉测试','camera':'视觉 · USB摄像头',
       'ov5640':'视觉 · 板端OV5640（电脑预览）','idle':'已停止'}
STAGE='/home/xilinx/independent_video_20261028'
DEPLOY=ROOT/'project/_tmp/kp_stream_deploy_v2/deployment.json'
OPENER=build_opener(ProxyHandler({}))


def fetch(url,method='GET',headers=None):
    with OPENER.open(Request(url,method=method,headers=headers or {}),timeout=4) as response:return response.read()


def app_action(port,action):
    html=fetch('http://127.0.0.1:%d/'%port).decode('utf-8')
    token=re.search(r"X-Session':'([^']+)'",html)
    if not token:raise RuntimeError('控制接口未提供会话令牌')
    return fetch('http://127.0.0.1:%d/%s'%(port,action),'POST',{'X-Session':token.group(1)})


def alive(process):return process is not None and process.poll() is None


class Controller:
    def __init__(self,args,password):
        self.args=args;self.password=password
        self.out=ROOT/'project/_tmp/demo_control'/time.strftime('%Y%m%d_%H%M%S')
        self.out.mkdir(parents=True)
        os.environ['AUDIO_BOARD_SUDO_PASSWORD']=password
        self.line=AudioLine(argparse.Namespace(board=args.board,model=args.model))
        os.environ.pop('AUDIO_BOARD_SUDO_PASSWORD',None)
        self.lock=threading.Lock();self.transition=threading.Lock();self.closed=threading.Event()
        self.worker=None;self.tunnel=None;self.audio_app=None;self.worker_output=None
        self.preview=None;self.preview_time=0;self.request_id=0
        self.ov_manifest=ROOT/'project/board/ov5640_snapshot/release_remove_pl_bad_frame_20261028/release_manifest.json'
        self.state=dict(mode='idle',title=MODES['idle'],busy=False,message='正在连接板卡…',error=None,
                        connected=False,details={},camera_index=0,preview_time=None,
                        service_pid=os.getpid(),camera_sources=['USB','OV5640'])
        self.events=(self.out/'events.jsonl').open('a',encoding='utf-8')

    def update(self,**values):
        with self.lock:self.state.update(values)

    def event(self,kind,**values):
        record=dict(time=time.strftime('%Y-%m-%d %H:%M:%S'),event=kind,**values)
        self.events.write(json.dumps(record,ensure_ascii=False)+'\n');self.events.flush()

    def board(self,image=False):
        code="""import base64,json
from pathlib import Path
stage=Path('/home/xilinx/independent_video_20261028');processes=[]
for p in Path('/proc').iterdir():
    if not p.name.isdigit():continue
    try:
        if 'python' not in (p/'comm').read_text():continue
        args=(p/'cmdline').read_bytes().split(b'\\0')
        scripts=[x.decode() for x in args if x.endswith(b'.py')]
        for script in scripts:processes.append({'pid':int(p.name),'script':script})
    except (OSError,ValueError):pass
state=None;preview=None;run_path=None
current=stage/'current_run.txt'
if current.exists():
    run=Path(current.read_text().strip())
    if run.parent==stage:
        run_path=str(run)
        f=run/'state.json'
        if f.exists():state=json.loads(f.read_text())
        jpg=run/'latest.jpg'
        if WANT_IMAGE and jpg.exists():preview=base64.b64encode(jpg.read_bytes()).decode()
print(json.dumps({'processes':processes,'independent':state,'preview':preview,'run_path':run_path,
    'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}))
""".replace('WANT_IMAGE',repr(image))
        return remote(self.args.board,code,timeout=20)

    @staticmethod
    def matching(snapshot,name):return [p['pid'] for p in snapshot['processes'] if Path(p['script']).name==name]

    def spawn(self,label,command,env=None):
        environment=dict(os.environ,PYTHONUTF8='1')
        environment.pop('KEYPOINT_BOARD_SUDO_PASSWORD',None)
        environment.pop('AUDIO_BOARD_SUDO_PASSWORD',None)
        if env:environment.update(env)
        flags=(subprocess.CREATE_NO_WINDOW|subprocess.CREATE_NEW_PROCESS_GROUP) if os.name=='nt' else 0
        with (self.out/(label+'.stdout.log')).open('ab') as out,(self.out/(label+'.stderr.log')).open('ab') as err:
            return subprocess.Popen(command,cwd=ROOT,env=environment,stdin=subprocess.DEVNULL,
                stdout=out,stderr=err,creationflags=flags)

    def wait_until(self,predicate,seconds,message):
        deadline=time.monotonic()+seconds
        while time.monotonic()<deadline:
            if predicate():return
            time.sleep(.5)
        raise RuntimeError(message)

    def stop_worker(self):
        if alive(self.worker):
            app_action(18783,'stop')
            try:self.worker.wait(timeout=100)
            except subprocess.TimeoutExpired:
                raise RuntimeError('当前任务未安全退出；请查看日志，不会强杀在途PL推理')
        self.worker=None

    def stop_tunnel(self):
        if alive(self.tunnel):
            self.tunnel.terminate();self.tunnel.wait(timeout=12)
        self.tunnel=None

    def quiesce(self):
        self.update(message='正在结束当前任务，等待在途推理完成…')
        try:app_action(8765,'stop')
        except OSError:pass
        # The OV worker handles SIGINT through the original DMA Halted path.
        # Signal before joining the host read, which may be waiting for a frame.
        if self.state['mode']=='ov5640':
            snapshot=self.board()
            for pid in self.matching(snapshot,'demo_stream.py'):
                self.line.ssh('kill -INT '+str(pid),sudo=True)
        self.stop_worker()
        snapshot=self.board()
        if self.matching(snapshot,'demo_stream.py'):
            raise RuntimeError('OV5640进程仍保留DMA缓冲；停止状态未确认，请检查板端，不会强杀')
        # Never kill an unowned neural worker in an active DMA call.
        if self.matching(snapshot,'stream_hand_board.py'):
            raise RuntimeError('仍有外部PL推理进程，请先从其控制页正常停止')
        for name in ('independent_video.py','hdmi_audio_receiver.py'):
            for pid in self.matching(snapshot,name):
                self.line.ssh('kill -TERM '+str(pid),sudo=True)
        def stopped():
            s=self.board()
            return not any(self.matching(s,n) for n in ('independent_video.py','hdmi_audio_receiver.py'))
        self.wait_until(stopped,120,'原写屏任务未安全退出，未启动新任务')
        self.stop_tunnel()
        self.preview=None;self.preview_time=0;self.update(details={},preview_time=None)

    def display_ready(self):
        args=argparse.Namespace(board=self.args.board,release_manifest=DEPLOY)
        release=HDMILink(args,self.password).prepare()
        return release['owner_pid']

    def w6_preflight(self):
        # Firmware files alone do not identify what is actually loaded. Check the
        # per-boot OV marker first, then PYNQ's loaded-bitfile record; no MMIO.
        code="""import json
from pathlib import Path
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
p=Path('/run/ov5640_snapshot_download_attempted')
print(json.dumps({'ov5640_boot':p.exists() and p.read_text().strip()==boot}))
"""
        state=remote(self.args.board,code,timeout=20)
        if state['ov5640_boot']:
            raise RuntimeError('本次启动加载的是OV5640独立采集固件，不含HDMI/音频/PL关键点；UI不会换固件，请使用OV5640电脑预览入口')
        code="from pynq import PL; import json; print(json.dumps({'loaded':PL.bitfile_name}))"
        loaded=json.loads(self.line.ssh('env XILINX_XRT=/usr /usr/local/share/pynq-venv/bin/python -c '+shlex.quote(code)))['loaded']
        if not loaded or Path(loaded).name!='kws_hdmi.bit':
            raise RuntimeError('无法确认当前已加载HDMI/PL固件，请核对冷启动记录；UI不会访问硬件或加载位流')

    def tunnel_for(self,video=False):
        command=['ssh','-N','-o','BatchMode=yes','-o','ExitOnForwardFailure=yes',
            '-o','ConnectTimeout=8','-o','ServerAliveInterval=5','-o','ServerAliveCountMax=2']
        if video:command+=['-R','18781:127.0.0.1:18780']
        else:command+=['-L','18766:127.0.0.1:8766','-R','18765:127.0.0.1:8765']
        self.tunnel=self.spawn('tunnel_'+str(time.time_ns()),command+[self.args.board])
        time.sleep(1)
        if not alive(self.tunnel):raise RuntimeError('SSH隧道未建立，请检查端口或网络')

    def start_video(self,mode,camera):
        self.worker_output=self.out/('video_'+str(time.time_ns()))
        command=[self.args.vision_python,'-X','utf8','-m','vision.keypoints.recording_demo',
            '--output',str(self.worker_output),'--seconds','86400','--control-port','18783',
            '--mode','pl' if mode=='pl' else 'pc']
        if mode!='pl':command+=['--no-pl']
        if mode=='camera':command+=['--camera',str(camera)]
        elif mode=='ov5640':command+=['--ov5640']
        self.worker=self.spawn('video',command,{'KEYPOINT_BOARD_SUDO_PASSWORD':self.password})
        def ready():
            if not alive(self.worker):
                log=(self.out/'video.stderr.log').read_text(encoding='utf-8',errors='replace')[-1800:]
                raise RuntimeError('摄像头/视频检测启动失败：'+log)
            try:return json.loads(fetch('http://127.0.0.1:18780/state'))['frames_published']>0
            except OSError:return False
        self.wait_until(ready,90,'尚未获得首帧，请检查摄像头和视频日志')
        if mode=='ov5640':return  # Snapshot firmware contains no HDMI.
        owner=self.display_ready();self.tunnel_for(video=True)
        self.line.start_remote('hdmi_audio_receiver.py','--owner-pid %d --url http://127.0.0.1:18781/frame.jpg --fps 15'%owner)

    def start_independent(self):
        previous_run=self.board()['run_path']
        owner=self.display_ready()
        command=('nohup env XILINX_XRT=/usr OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 '
            '/usr/local/share/pynq-venv/bin/python -u '+STAGE+'/independent_video.py --stage '+STAGE+
            ' --pl-work /home/xilinx/hand_pl_20261026_120256 --teacher-work /home/xilinx/hands_teacher_20261027_v1'
            ' --owner-pid '+str(owner)+' > '+STAGE+'/daemon.stdout.log 2> '+STAGE+'/daemon.stderr.log < /dev/null &')
        self.line.ssh(command,sudo=True)
        def ready():
            s=self.board()
            return (bool(self.matching(s,'independent_video.py')) and s['run_path']!=previous_run
                    and bool(s['independent']) and s['independent']['active'])
        self.wait_until(ready,90,'板端独立模式未就绪，请查看板端daemon.stderr.log')

    def start_audio(self):
        owner=self.display_ready()
        if not self.line.pids('board_audio_stream.py'):self.line.start_remote('board_audio_stream.py')
        try:fetch('http://127.0.0.1:18766/health')
        except OSError:self.tunnel_for(video=False)
        def health():
            try:fetch('http://127.0.0.1:18766/health');return True
            except OSError:return False
        self.wait_until(health,20,'板端采音服务不可用')
        try:fetch('http://127.0.0.1:8765/state')
        except OSError:
            self.audio_app=self.spawn('audio',[self.args.audio_python,'-X','utf8',str(ROOT/'ASR/audio_loop.py'),
                '--model',self.args.model,'--manifest',str(ROOT/'ASR/phrases_sd.json'),
                '--board-audio-url','http://127.0.0.1:18766/pcm'])
        def app_ready():
            try:fetch('http://127.0.0.1:8765/state');return True
            except OSError:return False
        self.wait_until(app_ready,60,'语音识别服务未就绪')
        app_action(8765,'start')
        self.line.start_remote('hdmi_audio_receiver.py','--owner-pid %d --url http://127.0.0.1:18765/frame.jpg --fps 10'%owner)

    def ov5640_preflight(self):
        manifest=json.loads(self.ov_manifest.read_text(encoding='utf-8'))
        expected={name:manifest['files'][name]['sha256'] for name in ('bit','hwh')}
        helpers={name:__import__('hashlib').sha256((ROOT/'project/board/ov5640_snapshot'/name).read_bytes()).hexdigest()
                 for name in ('capture.py','continuous_capture.py')}
        code="""import hashlib,json
from pathlib import Path
work=Path('/home/xilinx/jupyter_notebooks/ov5640_snapshot')
expected=EXPECTED;helpers=HELPERS
manifest=json.loads((work/'release/release_manifest.json').read_text())
for kind,sha in expected.items():
    f=work/'release'/manifest['files'][kind]['path']
    assert f.resolve().parent==(work/'release').resolve(), 'Unsafe firmware path'
    assert hashlib.sha256(f.read_bytes()).hexdigest()==sha, 'OV5640 firmware mismatch'
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
assert Path('/run/ov5640_snapshot_download_attempted').read_text().strip()==boot, 'OV5640 cold boot marker missing'
for name,sha in helpers.items():
    assert hashlib.sha256((work/name).read_bytes()).hexdigest()==sha, 'OV5640 helper version mismatch'
print(json.dumps({'verified':True,'boot_id':boot}))
""".replace('EXPECTED',repr(expected)).replace('HELPERS',repr(helpers))
        try:remote(self.args.board,code,timeout=25)
        except Exception as exc:
            raise RuntimeError('OV5640需要配套抓图固件已冷启动；本UI不会更换固件。'+str(exc))
        result=subprocess.run(['scp','-o','BatchMode=yes','-o','ConnectTimeout=8',
            str(ROOT/'project/board/ov5640_snapshot/demo_stream.py'),
            self.args.board+':/home/xilinx/jupyter_notebooks/ov5640_snapshot/demo_stream.py'],
            capture_output=True,text=True,timeout=25)
        if result.returncode:raise RuntimeError('OV5640流接口部署失败：'+result.stderr)

    def request(self,mode,camera=0,cold_boot=False):
        if mode not in MODES or not isinstance(camera,int) or not 0<=camera<=9:raise ValueError('无效模式或摄像头编号')
        if mode=='ov5640' and cold_boot is not True:raise ValueError('请先确认OV5640配套固件已在本次冷启动加载')
        if not self.transition.acquire(blocking=False):raise RuntimeError('正在切换，请等待当前操作完成')
        self.update(busy=True,message='准备切换至'+MODES[mode],error=None)
        def work():
            mutating=False
            try:
                self.event('switch_requested',mode=mode,camera_index=camera)
                if mode=='ov5640':self.ov5640_preflight()
                elif mode!='idle':self.w6_preflight()
                mutating=True
                self.quiesce();self.update(mode='idle',title=MODES['idle'])
                self.update(message='正在启动'+MODES[mode]+'…')
                if mode in ('teacher','pl','camera','ov5640'):self.start_video(mode,camera)
                elif mode=='independent':self.start_independent()
                elif mode=='audio':self.start_audio()
                self.update(mode=mode,title=MODES[mode],camera_index=camera,message='运行中' if mode!='idle' else '已停止，HDMI保留最后一帧',error=None)
                self.event('switch_completed',mode=mode)
            except Exception as exc:
                # A failed start may have allocated a PL worker: stop by its API,
                # never terminate the process tree while hardware is in flight.
                cleanup=None
                if mutating:
                    try:self.quiesce()
                    except Exception as stop_error:cleanup=str(stop_error)
                    self.update(mode='idle',title='启动失败')
                self.update(error=str(exc),message=cleanup or '请检查设备连接后重试；OV5640须使用配套冷启动固件')
                self.event('switch_failed',mode=mode,error=str(exc),cleanup_error=cleanup)
            finally:self.update(busy=False);self.transition.release()
        threading.Thread(target=work,daemon=True).start()

    def monitor(self):
        first=True
        while not self.closed.is_set():
            try:
                with self.lock:mode=self.state['mode'];busy=self.state['busy']
                snapshot=self.board(image=(mode=='independent' or first) and not busy)
                if first and self.matching(snapshot,'independent_video.py'):
                    self.update(mode='independent',title=MODES['independent'],message='已接管现有板端独立模式')
                    mode='independent'
                first=False
                details={};jpeg=None
                if not busy:
                    if mode=='independent':
                        details=snapshot['independent'] or {}
                        if snapshot['preview']:jpeg=base64.b64decode(snapshot['preview'])
                        if not self.matching(snapshot,'independent_video.py'):raise RuntimeError('板端独立进程已退出')
                    elif mode=='audio':
                        details=json.loads(fetch('http://127.0.0.1:8765/state'))
                        jpeg=fetch('http://127.0.0.1:8765/frame.jpg')
                    elif mode in ('teacher','pl','camera','ov5640'):
                        if not alive(self.worker):raise RuntimeError('视频进程已结束，请重新启动')
                        details=json.loads(fetch('http://127.0.0.1:18783/state'))
                        jpeg=fetch('http://127.0.0.1:18780/frame.jpg')
                    if jpeg:self.preview=jpeg;self.preview_time=time.time()
                    self.update(details=details,preview_time=self.preview_time or None)
                self.update(connected=True,board_boot_id=snapshot['boot_id'],last_poll=time.time())
            except Exception as exc:self.update(connected=False,error=str(exc))
            self.closed.wait(3)


def handler_for(controller,token):
    html=(Path(__file__).with_name('demo_control.html')).read_text(encoding='utf-8').replace('__SESSION__',token)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def send(self,body,ctype,status=200):
            self.send_response(status);self.send_header('Content-Type',ctype)
            self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff');self.end_headers()
            try:self.wfile.write(body)
            except (BrokenPipeError,ConnectionResetError):pass
        def do_GET(self):
            path=self.path.split('?',1)[0]
            if path=='/':self.send(html.encode(),'text/html; charset=utf-8')
            elif path=='/api/state':
                with controller.lock:value=dict(controller.state)
                self.send(json.dumps(value,ensure_ascii=False).encode(),'application/json; charset=utf-8')
            elif path=='/api/preview.jpg':
                if controller.preview:self.send(controller.preview,'image/jpeg')
                else:self.send(b'Preview not ready','text/plain',503)
            else:self.send(b'Not found','text/plain',404)
        def do_POST(self):
            if self.headers.get('X-Session')!=token:self.send(b'Forbidden','text/plain',403);return
            if self.path!='/api/switch':self.send(b'Not found','text/plain',404);return
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=2048:raise ValueError('请求长度无效')
                data=json.loads(self.rfile.read(size))
                if data['mode']=='ov5640':controller.request(data['mode'],data.get('camera',0),data.get('cold_boot',False))
                else:controller.request(data['mode'],data.get('camera',0))
                self.send(b'{"accepted":true}','application/json',202)
            except (KeyError,ValueError) as exc:self.send(json.dumps({'error':str(exc)}).encode(),'application/json',400)
            except RuntimeError as exc:self.send(json.dumps({'error':str(exc)}).encode(),'application/json',409)
    return Handler


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--board',default='xilinx@192.168.2.99')
    p.add_argument('--port',type=int,default=18790)
    p.add_argument('--vision-python',default='F:/PLD/.venv-vision/Scripts/python.exe')
    p.add_argument('--audio-python',default='F:/PLD/.venv-audio/Scripts/python.exe')
    p.add_argument('--model',default='F:/PLD/asr_test/sherpa-onnx-streaming-zipformer-zh-14M-2023-02-23')
    p.add_argument('--child',action='store_true')
    a=p.parse_args()
    if not a.child:
        with socket.socket() as probe:
            if probe.connect_ex(('127.0.0.1',a.port))==0:
                print('CONTROL_URL=http://127.0.0.1:'+str(a.port)+' (already running)');return
        password=getpass.getpass('Board sudo password: ')
        out=ROOT/'project/_tmp/demo_control';out.mkdir(exist_ok=True)
        environment=dict(os.environ,DEMO_CONTROL_SUDO_PASSWORD=password,PYTHONUTF8='1')
        args=[a.vision_python,'-X','utf8',str(Path(__file__).resolve()),'--child','--port',str(a.port),
              '--board',a.board,'--vision-python',a.vision_python,'--audio-python',a.audio_python,'--model',a.model]
        with (out/'service.stdout.log').open('ab') as stdout,(out/'service.stderr.log').open('ab') as stderr:
            child=subprocess.Popen(args,cwd=ROOT,env=environment,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,
                creationflags=subprocess.CREATE_NO_WINDOW|subprocess.CREATE_NEW_PROCESS_GROUP)
        (out/'launch.json').write_text(json.dumps({'pid':child.pid,'url':'http://127.0.0.1:'+str(a.port)},indent=2))
        print('CONTROL_URL=http://127.0.0.1:'+str(a.port));return
    password=os.environ.pop('DEMO_CONTROL_SUDO_PASSWORD')
    controller=Controller(a,password)
    server=ThreadingHTTPServer(('127.0.0.1',a.port),handler_for(controller,secrets.token_urlsafe(32)))
    server.daemon_threads=True
    # Reserve the existing audio supervisor lock so it cannot race a mode switch.
    audio_lock=socket.socket();audio_lock.bind(('127.0.0.1',18767))
    threading.Thread(target=controller.monitor,daemon=True).start()
    print('CONTROL_READY http://127.0.0.1:'+str(a.port),flush=True)
    try:server.serve_forever()
    finally:
        controller.closed.set();server.server_close();audio_lock.close()
        # Board-independent mode intentionally survives the control panel.


if __name__=='__main__':main()
