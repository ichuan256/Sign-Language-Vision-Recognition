"""PC 常驻音频服务（开机自启）：通电就绪，BTN0 一键开始识别。

架构（2026-10-23 终版）：
- 本服务随 Windows 开机启动（Startup 里的 audio_resident_autostart.bat）；
- 拉起 run_audio_line.py 监督进程：板端准备、ssh 隧道、app（audio_loop.py）
  全部由它负责并持续自愈；app 构造即预载 ASR 模型，但不开始识别（待机页）；
- 本服务另维护一条触发隧道 ssh -R 18770（板端 127.0.0.1:18770 → 本机），
  板端 button-watch.service（BTN0）经它送来 START；
- 收到 START：等 app 就绪后 POST /start（带页面令牌）——识别即刻开始，
  字幕与手语视频经既有回传通路上屏。

板子先开、PC 后开时按键会被忽略（隧道未建），PC 就绪后再按一次即可。
"""
import argparse
import os
import re
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.request import Request, build_opener, ProxyHandler

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / '_tmp'
TRIGGER_PORT = 18770           # 本服务监听（触发隧道落点）
APP_PORT = 8765
BOARD = 'xilinx@192.168.2.99'


def log(msg):
    line = '%s %s' % (time.strftime('%H:%M:%S'), msg)
    print(line, flush=True)
    try:
        with (LOG_DIR / 'audio_resident.log').open('a', encoding='utf-8') as fh:
            fh.write(line + '\n')
    except OSError:
        pass


def fetch(url, timeout=3, method='GET', headers=None):
    req = Request(url, method=method, headers=headers or {})
    with build_opener(ProxyHandler({})).open(req, timeout=timeout) as resp:
        return resp.read()


class Resident:
    def __init__(self, model):
        self.model = model
        self.line = None
        self.tunnel = None
        self._last_trigger = 0.0

    # ---- 演示监督进程（含 app + 模型预载；板子没开时它自己重试）----
    def ensure_line(self):
        if self.line is not None and self.line.poll() is None:
            return
        env = dict(os.environ, AUDIO_BOARD_SUDO_PASSWORD='xilinx')
        self.line = subprocess.Popen(
            [sys.executable, '-X', 'utf8', str(ROOT / 'asr' / 'run_audio_line.py'),
             '--model', self.model],
            stdout=(LOG_DIR / 'audio_line.out.log').open('ab'),
            stderr=(LOG_DIR / 'audio_line.err.log').open('ab'), env=env)
        log('run_audio_line spawned pid=%d（含模型预载，板子不在线会自动重试）' % self.line.pid)

    # ---- 触发隧道：PC -> 板 ssh，反向把板端 18770 转回本机 ----
    def ensure_trigger_tunnel(self):
        if self.tunnel is not None and self.tunnel.poll() is None:
            return
        self.tunnel = subprocess.Popen(
            ['ssh', '-N', '-o', 'ExitOnForwardFailure=yes', '-o', 'ServerAliveInterval=5',
             '-o', 'ServerAliveCountMax=2', '-o', 'ConnectTimeout=8',
             '-R', '%d:127.0.0.1:%d' % (TRIGGER_PORT, TRIGGER_PORT), BOARD],
            stdout=(LOG_DIR / 'trigger_tunnel.out.log').open('ab'),
            stderr=(LOG_DIR / 'trigger_tunnel.err.log').open('ab'))
        log('trigger tunnel spawned pid=%d' % self.tunnel.pid)

    def app_ready(self):
        try:
            fetch('http://127.0.0.1:%d/state' % APP_PORT)
            return True
        except OSError:
            return False

    def start_listening(self):
        html = fetch('http://127.0.0.1:%d/' % APP_PORT).decode('utf-8', 'replace')
        m = re.search(r"X-Session':'([^']+)'", html)
        if not m:
            raise RuntimeError('app page has no session token')
        resp = fetch('http://127.0.0.1:%d/start' % APP_PORT, method='POST',
                     headers={'X-Session': m.group(1)})
        log('POST /start -> %s' % resp.decode())

    def on_trigger(self):
        if time.monotonic() - self._last_trigger < 5:
            return  # 5 秒去抖
        self._last_trigger = time.monotonic()
        log('TRIGGER received (BTN0)')
        deadline = time.monotonic() + 120   # 板子可能刚通电，给足自愈时间
        while time.monotonic() < deadline:
            if self.app_ready():
                try:
                    self.start_listening()
                except Exception as exc:
                    log('start_listening retry: %s' % exc)
                    time.sleep(2)
                    continue
                log('DEMO_UP http://127.0.0.1:%d（识别已开始）' % APP_PORT)
                return
            time.sleep(2)
        log('TRIGGER_TIMEOUT：120 秒内 app 未就绪，看 _tmp 日志')

    def serve(self):
        srv = socket.socket()
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('127.0.0.1', TRIGGER_PORT))
        srv.listen(4)
        log('resident listening on 127.0.0.1:%d' % TRIGGER_PORT)
        while True:
            conn, _ = srv.accept()
            with conn:
                data = conn.recv(64)
            if data.strip().startswith(b'START'):
                threading.Thread(target=self.on_trigger, daemon=True).start()

    def supervise(self):
        while True:
            self.ensure_line()
            self.ensure_trigger_tunnel()
            time.sleep(3)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', required=True)
    args = parser.parse_args()
    LOG_DIR.mkdir(exist_ok=True)
    resident = Resident(args.model)
    threading.Thread(target=resident.supervise, daemon=True).start()
    resident.serve()


if __name__ == '__main__':
    main()
