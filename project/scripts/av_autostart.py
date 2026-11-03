"""Manual PC-assisted console for the current AV firmware. No saved password."""
import argparse,hashlib,json,secrets,socket,subprocess,threading,time
from http.server import ThreadingHTTPServer
from pathlib import Path
from demo_control import Controller,ROOT,fetch,app_action,alive,handler_for,remote

class AutoAVController(Controller):
    def __init__(self,args):
        super().__init__(args,'');self.auto_enabled=False;self.display_receiver=None;self.display_path=None
        self.update(console_profile='av_current_firmware_v1',device={},title='已停止',message='请选择视听三栏、USB摄像头或SD教学视频',manual_start=True)

    def gateway(self,action):
        if action not in ('preflight','owner','audio','stop'):raise ValueError('Invalid AV action')
        result=subprocess.run(['ssh',*self.line.ssh_options,self.args.board,
            'sudo -n /usr/local/sbin/sign-av-ctl '+action],capture_output=True,text=True,encoding='utf-8',
            timeout=110 if action=='stop' else 60,env=self.line.environment)
        if result.returncode:
            detail=result.stderr.strip() or result.stdout.strip()
            self.event('gateway_failed',action=action,error=detail)
            if 'color_probe.json' in detail and 'FileNotFoundError' in detail:
                message='板端显示服务尚未就绪。请保持屏幕和板卡通电，等待启动完成后重试。'
            elif 'timing not locked' in detail:
                message='HDMI视频尚未同步，已保留显示缓冲并停止启动。需要安全恢复后再开始。'
            elif result.returncode==255:
                message='暂时无法连接板卡，请检查供电和网线；控制台会等待设备恢复。'
            else:message='板端视听检查未通过，未启动采集。请展开运行详情或查看控制台日志。'
            self.update(device=dict(ready=False,error=message,detail=detail.splitlines()[-1] if detail else ''))
            raise RuntimeError(message)
        return json.loads(result.stdout)

    def single_hdmi_preflight(self,audio=False):
        result=self.gateway('preflight')
        if not result.get('ready'):raise RuntimeError('AV cold boot not ready')
        self.preflight_result=result
        self.update(device=dict(ready=True,firmware_verified=True,hdmi_locked=True,boot_id=result.get('boot_id')))

    def ensure_single_hdmi_owner(self):
        # Stream/display recheck the owner immediately before mapping it.
        value=self.preflight_result['owner']
        self.event('single_hdmi_owner',owner_pid=value['pid'],frame_address=value['frame_address'],reused=True,downloaded=False)

    def quiesce(self):
        self.update(message='正在安全停止视听任务…')
        try:app_action(8765,'stop')
        except OSError:pass
        self.gateway('stop');self.stop_worker();self.stop_tunnel()
        if alive(self.display_receiver):
            self.display_receiver.wait(timeout=15)
        self.display_receiver=None;self.display_path=None
        self.preview=None;self.preview_time=0;self.update(details={},preview_time=None)

    def start_av_audio(self):
        def healthy():
            try:return fetch('http://127.0.0.1:18766/health')==b'OK'
            except OSError:return False
        if not healthy():self.gateway('audio')
        self.wait_until(healthy,45,'板端采音接口尚未就绪')
        try:existing=json.loads(fetch('http://127.0.0.1:8765/state'))
        except OSError:existing=None
        if existing is None:
            self.audio_app=self.spawn('audio',[self.args.audio_python,'-X','utf8',str(ROOT/'ASR/audio_loop.py'),
                '--model',self.args.model,'--manifest',str(ROOT/'ASR/phrases_sd.json'),
                '--board-audio-url','http://127.0.0.1:18766/pcm'])
        def ready():
            try:
                state=json.loads(fetch('http://127.0.0.1:8765/state'))
                expected=hashlib.sha256((ROOT/'ASR/phrases_sd.json').read_bytes()).hexdigest()
                if state.get('configured_input')!='board_http' or state.get('lexicon_manifest_sha256')!=expected:
                    raise RuntimeError('已有语音服务与已冻结输入/词表不符')
                return bool(fetch('http://127.0.0.1:8765/panel.jpg'))
            except OSError:return False
        self.wait_until(ready,120,'电脑ASR与播放面板尚未就绪')

    def request(self,mode,camera=0,cold_boot=False):
        if mode not in ('av','camera','sd_teacher','idle'):raise ValueError('当前固件支持视听三栏、USB摄像头和SD教学视频')
        self.auto_enabled=False
        return super().request(mode,camera,cold_boot)

    def display_preview(self):
        if not self.display_path:raise RuntimeError('显示任务尚未启动')
        code="""import base64,json
from pathlib import Path
run=Path(RUN)
state=json.loads((run/'live.json').read_text())
image=(run/'latest.jpg').read_bytes();assert len(image)<4*1024*1024
print(json.dumps(dict(display=state,jpeg=base64.b64encode(image).decode())))
""".replace('RUN',repr(self.display_path))
        return remote(self.args.board,code,timeout=12)

    def start_video(self,mode,camera):
        if mode not in ('camera','sd_teacher'):raise ValueError('Unsupported current-firmware video mode')
        self.tunnel_for(video=True)
        self.worker_output=self.out/('video_'+str(time.time_ns()))
        command=[self.args.vision_python,'-X','utf8','-m','vision.keypoints.recording_demo',
            '--output',str(self.worker_output),'--seconds','0','--control-port','18783','--no-pl','--mode','pc']
        if mode=='camera':
            command+=['--camera',str(camera),'--hand-digits']
        else:command+=['--sd-source']
        self.worker=self.spawn('video',command)
        def ready():
            if not alive(self.worker):
                detail=(self.out/'video.stderr.log').read_text(encoding='utf-8',errors='replace')[-1600:]
                raise RuntimeError('视觉输入启动失败；请检查USB编号或SD素材。'+detail)
            try:return json.loads(fetch('http://127.0.0.1:18780/state'))['frames_published']>0
            except OSError:return False
        self.wait_until(ready,70,'视觉输入未传回完整帧，请检查摄像头或SD视频')
        run='ui_'+str(time.time_ns());self.display_path='/var/lib/sign-av/displays/'+run
        self.display_receiver=self.spawn('display_'+run,['ssh',*self.line.ssh_options,self.args.board,
            'sudo -n /usr/local/sbin/sign-av-ctl display '+run])
        def displayed():
            if not alive(self.display_receiver):raise RuntimeError('当前固件写屏任务退出，请查看display日志')
            try:
                value=self.display_preview()['display']
                return value.get('active') and value.get('hdmi_frames',0)>0
            except (OSError,subprocess.SubprocessError,RuntimeError,ValueError):return False
        self.wait_until(displayed,45,'教师画面尚未写入HDMI，请查看display日志')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--board',default='xilinx@192.168.2.99');p.add_argument('--port',type=int,default=18790)
    p.add_argument('--vision-python',default='F:/PLD/.venv-vision/Scripts/python.exe')
    p.add_argument('--audio-python',default='F:/PLD/.venv-audio/Scripts/python.exe')
    p.add_argument('--model',default='F:/PLD/asr_test/sherpa-onnx-streaming-zipformer-zh-14M-2023-02-23')
    a=p.parse_args();a.board_gateway=True;a.session_seconds=0
    with socket.socket() as probe:
        if probe.connect_ex(('127.0.0.1',a.port))==0:
            print('Existing control panel preserved; autostart did not change it.',flush=True);return
    lock=socket.socket()
    try:lock.bind(('127.0.0.1',18767))
    except OSError:
        print('An existing audio/controller process owns AV. Preserved; no duplicate start.',flush=True);return
    controller=AutoAVController(a)
    server=ThreadingHTTPServer(('127.0.0.1',a.port),handler_for(controller,secrets.token_urlsafe(32)));server.daemon_threads=True
    threading.Thread(target=controller.monitor,daemon=True).start()
    print('AV_AUTOSTART_READY http://127.0.0.1:'+str(a.port),flush=True)
    try:server.serve_forever()
    finally:controller.closed.set();server.server_close();lock.close()

if __name__=='__main__':main()
