"""Local streaming ASR -> captions -> real video playback. No Overlay calls."""
import argparse
import io
import json
import secrets
import threading
import time
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import build_opener, ProxyHandler

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

from loop_core import Session, VideoLexicon


def create_recognizer(model):
    import sherpa_onnx
    model = Path(model)
    return sherpa_onnx.OnlineRecognizer.from_transducer(
        tokens=str(model / 'tokens.txt'),
        encoder=str(model / 'encoder-epoch-99-avg-1.int8.onnx'),
        decoder=str(model / 'decoder-epoch-99-avg-1.int8.onnx'),
        joiner=str(model / 'joiner-epoch-99-avg-1.int8.onnx'),
        num_threads=2, decoding_method='greedy_search',
        enable_endpoint_detection=True, rule1_min_trailing_silence=2.4,
        rule2_min_trailing_silence=0.9, rule3_min_utterance_length=20)


def read_wav(path):
    with wave.open(str(path), 'rb') as wav:
        channels, width, rate = wav.getnchannels(), wav.getsampwidth(), wav.getframerate()
        raw = wav.readframes(wav.getnframes())
    if width == 2:
        samples = np.frombuffer(raw, '<i2').astype(np.float32) / 32768
    elif width == 3:
        byte = np.frombuffer(raw, np.uint8).reshape(-1, 3).astype(np.int32)
        value = byte[:, 0] | byte[:, 1] << 8 | byte[:, 2] << 16
        samples = ((value ^ 0x800000) - 0x800000).astype(np.float32) / 8388608
    else:
        raise ValueError('Only PCM16/PCM24 WAV input is supported')
    return samples.reshape(-1, channels).mean(axis=1), rate


class AudioInput:
    def __init__(self, session, model, device=None, board_audio_url=None):
        self.session, self.model, self.device = session, model, device
        self.board_audio_url = board_audio_url
        self.recognizer = None
        self.stop_event = threading.Event()
        self.guard = threading.Lock()
        self.thread = None

    def start(self, wav=None):
        with self.guard:
            if self.thread and self.thread.is_alive():
                return False
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._run, args=(wav,), daemon=True)
            self.thread.start()
            return True

    def stop(self):
        self.stop_event.set()

    def _run(self, wav):
        session = self.session
        try:
            session.update(status='加载中文语音模型', error='')
            if self.recognizer is None:
                self.recognizer = create_recognizer(self.model)
            if self.stop_event.is_set():
                session.update(status='识别已停止')
                return
            rec = self.recognizer
            stream = rec.create_stream()

            def accept(samples, rate):
                nonlocal stream
                stream.accept_waveform(rate, samples)
                while rec.is_ready(stream):
                    rec.decode_stream(stream)
                text = rec.get_result(stream)
                session.partial(text)
                if rec.is_endpoint(stream):
                    session.final(text)
                    if text:
                        print(json.dumps({'event': 'final', 'text': text}, ensure_ascii=False), flush=True)
                    rec.reset(stream)

            if wav:
                session.update(status='识别录音文件', source='录音文件：' + Path(wav).name)
                samples, rate = read_wav(wav)
                chunk = max(1, int(rate * 0.1))
                for start in range(0, len(samples), chunk):
                    if self.stop_event.is_set():
                        break
                    accept(samples[start:start + chunk], rate)
            elif self.board_audio_url:
                rate = 48000
                reconnects = 0
                while not self.stop_event.is_set():
                    try:
                        with build_opener(ProxyHandler({})).open(self.board_audio_url, timeout=5) as source:
                            rate = int(source.headers['X-Sample-Rate'])
                            if source.headers.get('X-Audio-Format') != 's16le-mono' or rate != 48000:
                                raise ValueError('Unexpected board audio format')
                            session.update(status='正在聆听板端麦克风', source='板端 LINE IN 左声道', error='')
                            while not self.stop_event.is_set():
                                raw = source.read(int(rate * 0.1) * 2)
                                if not raw or len(raw) % 2:
                                    raise OSError('板端音频流已断开')
                                samples = np.frombuffer(raw, '<i2').astype(np.float32) / 32768
                                session.update(audio_rms=float(np.sqrt(np.mean(samples ** 2))))
                                accept(samples, rate)
                    except (OSError, EOFError) as error:
                        if self.stop_event.is_set():
                            break
                        # Speech separated by a network gap is not one utterance.
                        stream = rec.create_stream()
                        reconnects += 1
                        session.update(status='板端音频已断开，正在重连', partial='',
                                       error=str(error), reconnects=reconnects)
                        print('AUDIO_RECONNECT:', error, flush=True)
                        self.stop_event.wait(min(5, reconnects))
            else:
                import sounddevice as sd
                device = sd.query_devices(self.device, 'input')
                rate = int(device['default_samplerate'])
                session.update(status='正在聆听', source='电脑麦克风：' + device['name'])
                # Blocking reads bound audio buffering and surface overflows.
                with sd.InputStream(device=self.device, channels=1, dtype='float32',
                                    samplerate=rate) as microphone:
                    while not self.stop_event.is_set():
                        samples, overflow = microphone.read(int(rate * 0.1))
                        if overflow:
                            raise RuntimeError('麦克风音频溢出，请停止其他高负载任务后重试')
                        accept(samples.reshape(-1), rate)
            accept(np.zeros(int(rate * 0.8), np.float32), rate)
            stream.input_finished()
            while rec.is_ready(stream):
                rec.decode_stream(stream)
            tail = rec.get_result(stream)
            session.final(tail)
            if tail:
                print(json.dumps({'event': 'final', 'text': tail}, ensure_ascii=False), flush=True)
            session.update(status='识别已停止', partial='')
        except Exception as error:
            session.update(status='语音输入不可用', error=str(error))
            print('ASR_ERROR:', error, flush=True)


class Screen:
    def __init__(self, session, font=None):
        candidates = [font] if font else [
            'C:/Windows/Fonts/msyh.ttc',
            '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf']
        path = next((p for p in candidates if p and Path(p).is_file()), None)
        if not path:
            raise ValueError('Chinese font missing: supply --font')
        self.font = ImageFont.truetype(path, 30)
        self.large = ImageFont.truetype(path, 40)
        self.small = ImageFont.truetype(path, 23)
        self.session = session
        self.frame_lock = threading.Lock()
        self.jpeg = b''
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def current(self):
        with self.frame_lock:
            return self.jpeg

    def compose(self, video=None):
        state = self.session.snapshot()
        image = Image.new('RGB', (1280, 720), (13, 22, 39))
        draw = ImageDraw.Draw(image)
        draw.text((40, 18), '妙手通言  语音字幕与手语播放', font=self.font, fill='white')
        draw.text((40, 68), state['status'], font=self.small, fill=(125, 218, 198))
        text = state['partial'] or state['final'] or '等待说话'
        lines, line = [], ''
        for char in text:
            if draw.textlength(line + char, font=self.large) > 1180:
                lines.append(line)
                line = ''
            line += char
        lines.append(line)
        for number, line in enumerate(lines[-2:]):
            draw.text((40, 108 + number * 51), line, font=self.large, fill='white')
        draw.rectangle((40, 222, 1239, 583), fill=(24, 39, 61))
        if video is not None:
            fitted = ImageOps.contain(video, (1200, 360))
            image.paste(fitted, (40 + (1200 - fitted.width) // 2,
                                 222 + (360 - fitted.height) // 2))
        else:
            draw.text((80, 360), '等待对应手语视频', font=self.font, fill=(151, 171, 195))
        draw.text((40, 600), ('播放：' + state['playing'])[:45], font=self.small, fill='white')
        message = state['error'] or ('缺少素材：' + state['missing'] if state['missing'] else '')
        draw.text((40, 637), message[:52], font=self.small, fill=(255, 194, 102))
        draw.text((40, 678), ('当前片段所属字幕：' + state['playback_text'])[:52],
                  font=self.small, fill=(151, 171, 195))
        output = io.BytesIO()
        image.save(output, 'JPEG', quality=88)
        with self.frame_lock:
            self.jpeg = output.getvalue()

    def _run(self):
        import cv2
        while not self.stop_event.is_set():
            job = self.session.pop()
            if job is None:
                self.compose()
                self.stop_event.wait(0.1)
                continue
            self.session.update(playback_text=job['text'])
            success = True
            for clip in job['clips']:
                capture = cv2.VideoCapture(clip['path'])
                try:
                    if not capture.isOpened():
                        raise ValueError('无法打开视频：' + Path(clip['path']).name)
                    fps = capture.get(cv2.CAP_PROP_FPS)
                    if not np.isfinite(fps) or fps <= 0:
                        raise ValueError('视频帧率无效：' + Path(clip['path']).name)
                    self.session.update(playing=clip['label'])
                    print(json.dumps({'event': 'video_start', 'utterance_id': job['utterance_id'],
                                      'label': clip['label'], 'file': clip['path']},
                                     ensure_ascii=False), flush=True)
                    start, index = time.monotonic(), 0
                    while not self.stop_event.is_set():
                        ok, frame = capture.read()
                        if not ok:
                            if index == 0:
                                raise ValueError('视频没有可解码画面')
                            break
                        target = start + index / fps
                        # Skip rendering late frames while keeping source order.
                        if time.monotonic() - target < max(0.15, 2 / fps):
                            state = self.session.snapshot()
                            self.session.update(video_frames=state['video_frames'] + 1,
                                                clip_time_ms=round(index / fps * 1000))
                            self.compose(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
                        index += 1
                        self.stop_event.wait(max(0, start + index / fps - time.monotonic()))
                except Exception as error:
                    success = False
                    self.session.update(error=str(error))
                    print('VIDEO_ERROR:', error, flush=True)
                finally:
                    capture.release()
            state = self.session.snapshot()
            self.session.update(playing='', completed=state['completed'] +
                                int(success and not self.stop_event.is_set()))
            print(json.dumps({'event': 'video_job_end', 'utterance_id': job['utterance_id'],
                              'success': success and not self.stop_event.is_set()}), flush=True)


HTML = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>妙手通言 · 实时语音</title><style>
body{margin:0;background:#0d1627;color:#eaf1fa;font:18px system-ui;padding:24px}
main{max-width:1280px;margin:auto}img{width:100%;border-radius:16px}
button{padding:14px 24px;border:0;border-radius:10px;margin:16px 12px 12px 0;
background:#77ebb7;color:#10221b;font:inherit;cursor:pointer}#stop{background:#dae4f0}
p{color:#b4c2d7}button:disabled{opacity:.5}</style><main>
<img src="/stream.mjpg" alt="实时字幕与手语视频">
<button id="start">开始聆听</button><button id="stop">停止聆听</button>
<p id="state">正在连接本地识别服务…</p><p>临时字幕实时更新；确认一句话后播放对应手语片段。</p>
</main><script>
async function action(name){let r=await fetch('/'+name,{method:'POST',headers:{'X-Session':'TOKEN'}});
if(!r.ok)document.getElementById('state').textContent='操作失败，请检查服务日志';}
document.getElementById('start').onclick=()=>action('start');
document.getElementById('stop').onclick=()=>action('stop');
setInterval(async()=>{try{let r=await fetch('/state');let s=await r.json();
document.getElementById('state').textContent=s.status+' · '+s.source+' · 待播放 '+s.queued+' 句';
}catch(e){document.getElementById('state').textContent='识别服务已断开';}},700);
</script></html>'''


def make_handler(session, audio, screen):
    token = secrets.token_urlsafe(24)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def respond(self, data, content_type, status=200):
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            path = urlsplit(self.path).path
            try:
                if path == '/':
                    self.respond(HTML.replace('TOKEN', token).encode(), 'text/html; charset=utf-8')
                elif path == '/state':
                    self.respond(json.dumps(session.snapshot(), ensure_ascii=False).encode(),
                                 'application/json; charset=utf-8')
                elif path == '/frame.jpg':
                    self.respond(screen.current(), 'image/jpeg')
                elif path == '/stream.mjpg':
                    self.send_response(200)
                    self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
                    self.end_headers()
                    while not screen.stop_event.is_set():
                        frame = screen.current()
                        self.wfile.write(b'--frame\r\nContent-Type: image/jpeg\r\nContent-Length: ' +
                                         str(len(frame)).encode() + b'\r\n\r\n' + frame + b'\r\n')
                        self.wfile.flush()
                        screen.stop_event.wait(0.1)
                else:
                    self.respond(b'Not found', 'text/plain', 404)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass

        def do_POST(self):
            if self.headers.get('X-Session') != token:
                self.respond(b'Forbidden', 'text/plain', 403)
                return
            if self.path == '/start':
                started = audio.start()
                self.respond(json.dumps({'started': started}).encode(), 'application/json')
            elif self.path == '/stop':
                audio.stop()
                self.respond(b'{}', 'application/json')
            else:
                self.respond(b'Not found', 'text/plain', 404)
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', required=True)
    parser.add_argument('--manifest', default=str(Path(__file__).with_name('videos.example.json')))
    parser.add_argument('--font')
    parser.add_argument('--device', type=int)
    parser.add_argument('--board-audio-url', help='PCM stream through SSH local forwarding')
    parser.add_argument('--listen-on-start', action='store_true')
    parser.add_argument('--wav', help='Run a real WAV through ASR; microphone starts only from UI')
    parser.add_argument('--bind', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    session = Session(VideoLexicon(args.manifest))
    audio = AudioInput(session, args.model, args.device, args.board_audio_url)
    screen = Screen(session, args.font)
    screen.compose()
    server = ThreadingHTTPServer((args.bind, args.port), make_handler(session, audio, screen))
    server.daemon_threads = True
    screen.thread.start()
    if args.wav:
        audio.start(args.wav)
    elif args.listen_on_start:
        audio.start()
    print('AUDIO_LOOP_URL=http://%s:%d' % (args.bind, args.port), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        audio.stop()
        screen.stop_event.set()
        server.server_close()


if __name__ == '__main__':
    main()
