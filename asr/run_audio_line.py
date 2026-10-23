"""Start and supervise the existing W6 audio/HDMI line. Never load a bitstream."""
import argparse
import getpass
import json
import os
import re
import shlex
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import build_opener, ProxyHandler

ROOT = Path(__file__).resolve().parents[1]
BOARD_DIR = ROOT / 'pynq-vision' / 'board' / 'w6'
BOARD_PYTHON = '/usr/local/share/pynq-venv/bin/python'


def accepted_bit_hashes():
    """发布版(2026-10-18)与本仓库全部已验收重建版的 kws_hdmi.bit 哈希集合。"""
    hashes = set()
    manifest = json.loads((BOARD_DIR / 'release_manifest.json').read_text())
    for item in manifest['artifacts']:
        if item['file'] == 'kws_hdmi.bit':
            hashes.add(item['sha256'])
    candidates = BOARD_DIR.parent.parent / 'board_validation' / 'w6' / 'timing_candidate'
    for rebuild in candidates.glob('build_manifest_*.json'):
        entry = json.loads(rebuild.read_text())['artifacts']['kws_hdmi.bit']
        hashes.add(entry['sha256'])
    return hashes


def fetch(url):
    with build_opener(ProxyHandler({})).open(url, timeout=3) as response:
        return response.read()


class AudioLine:
    def __init__(self, args):
        self.args = args
        self.password = os.environ.get('AUDIO_BOARD_SUDO_PASSWORD')
        if self.password is None:
            self.password = getpass.getpass('Board sudo password: ')
        self.directory = ROOT / '_tmp' / 'audio_line'
        self.directory.mkdir(parents=True, exist_ok=True)
        self.tunnel = self.app = None
        self.boot_id = None
        self.environment = dict(os.environ)
        self.environment.pop('AUDIO_BOARD_SUDO_PASSWORD', None)
        self.ssh_options = ['-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5']

    def ssh(self, command, sudo=False):
        if sudo:
            command = 'sudo -S -p \'\' sh -c ' + shlex.quote(command)
        result = subprocess.run(['ssh', *self.ssh_options, self.args.board, command],
                                input=self.password + '\n' if sudo else None,
                                capture_output=True, text=True, encoding='utf-8',
                                errors='replace', timeout=45, env=self.environment)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        return result.stdout.strip()

    def pids(self, name):
        pattern = '^' + re.escape(BOARD_PYTHON + ' -u /home/xilinx/' + name) + '( |$)'
        result = self.ssh('pgrep -f ' + shlex.quote(pattern) + ' || true')
        return [int(p) for p in result.split()]

    def start_remote(self, name, arguments=''):
        self.ssh('nohup env XILINX_XRT=/usr ' + BOARD_PYTHON + ' -u /home/xilinx/' +
                 name + ' ' + arguments + ' > /home/xilinx/' + name +
                 '.log 2>&1 < /dev/null &', sudo=True)

    def prepare(self, deploy=False):
        if self.ssh('systemctl show -p SubState --value bootpy.service') != 'exited':
            raise RuntimeError('Waiting for bootpy.service to finish')
        current_boot = self.ssh('cat /proc/sys/kernel/random/boot_id')
        if self.ssh('sha256sum /home/xilinx/kws_hdmi.bit').split()[0] not in accepted_bit_hashes():
            raise RuntimeError('Board bit file differs from the accepted W6 release')
        if deploy or current_boot != self.boot_id:
            sources = [ROOT / 'asr/board_audio_stream.py', ROOT / 'asr/board_pcm_capture.c',
                       BOARD_DIR / 'hdmi_audio_receiver.py',
                       BOARD_DIR / 'hdmi_display.py']
            subprocess.run(['scp', *self.ssh_options, *map(str, sources),
                            self.args.board + ':/home/xilinx/'], check=True, timeout=45,
                           env=self.environment)
            self.ssh('gcc -O2 -Wall -Wextra /home/xilinx/board_pcm_capture.c '
                     '-o /home/xilinx/board_pcm_capture.new && '
                     'mv /home/xilinx/board_pcm_capture.new /home/xilinx/board_pcm_capture')
        owners = self.pids('hdmi_display.py')
        if not owners:
            self.start_remote('hdmi_display.py')
            deadline = time.monotonic() + 60
            while time.monotonic() < deadline:
                log = self.ssh('cat /home/xilinx/hdmi_display.py.log 2>/dev/null || true')
                if 'DISPLAY_RUNNING:' in log:
                    break
                time.sleep(2)
            else:
                raise RuntimeError('Original HDMI output did not finish startup')
            owners = self.pids('hdmi_display.py')
        if len(owners) != 1:
            raise RuntimeError('Expected exactly one original HDMI frame owner')
        if deploy:
            for pid in self.pids('hdmi_audio_receiver.py') + self.pids('board_audio_stream.py'):
                self.ssh('kill ' + str(pid), sudo=True)
        if not self.pids('board_audio_stream.py'):
            self.start_remote('board_audio_stream.py')
        self.boot_id = current_boot
        return owners[0]

    def child(self, label, command):
        with (self.directory / (label + '.stdout.log')).open('ab') as out, \
                (self.directory / (label + '.stderr.log')).open('ab') as err:
            return subprocess.Popen(command, stdout=out, stderr=err, env=self.environment)

    def ensure_tunnel(self):
        if self.tunnel is None or self.tunnel.poll() is not None:
            self.tunnel = self.child('tunnel', ['ssh', '-N', *self.ssh_options,
                '-o', 'ExitOnForwardFailure=yes', '-o', 'ServerAliveInterval=5',
                '-o', 'ServerAliveCountMax=2', '-L', '18766:127.0.0.1:8766',
                '-R', '18765:127.0.0.1:8765', self.args.board])

    def ensure_app(self):
        if self.app is None or self.app.poll() is not None:
            if self.app is None:
                with socket.socket() as probe:
                    in_use = probe.connect_ex(('127.0.0.1', 8765)) == 0
                if in_use:
                    # 常驻服务已预载模型并占用 8765：/state 正常即收养，不重复加载
                    try:
                        fetch('http://127.0.0.1:8765/state')
                        return
                    except OSError:
                        raise RuntimeError('Port 8765 in use by an unhealthy app; stop it first')
            self.app = self.child('app', [sys.executable, '-X', 'utf8',
                str(ROOT / 'asr/audio_loop.py'), '--model', self.args.model,
                '--manifest', str(ROOT / 'asr/phrases_sd.json'),
                '--board-audio-url', 'http://127.0.0.1:18766/pcm'])
                # 不带 --listen-on-start：模型在构造时已预载，识别由 BTN0 触发 POST /start

    def run(self):
        owner = self.prepare(deploy=True)
        self.ensure_tunnel()
        deadline = time.monotonic() + 60
        while True:
            try:
                fetch('http://127.0.0.1:18766/health')
                break
            except OSError:
                if time.monotonic() > deadline:
                    raise RuntimeError('Board audio service unavailable; inspect tunnel logs')
                time.sleep(1)
        self.ensure_app()
        print('AUDIO_LINE_STARTING http://127.0.0.1:8765', flush=True)
        last_error = None
        next_board_check = 0
        while True:
            try:
                self.ensure_tunnel()
                fetch('http://127.0.0.1:18766/health')
                self.ensure_app()
                fetch('http://127.0.0.1:8765/state')
                if time.monotonic() >= next_board_check:
                    owner = self.prepare()
                    if not self.pids('hdmi_audio_receiver.py'):
                        self.start_remote('hdmi_audio_receiver.py', '--owner-pid %d '
                            '--url http://127.0.0.1:18765/frame.jpg --fps 10' % owner)
                    next_board_check = time.monotonic() + 15
                if last_error:
                    print('AUDIO_LINE_RECOVERED', flush=True)
                last_error = None
            except (OSError, RuntimeError, subprocess.SubprocessError) as error:
                if str(error) != last_error:
                    print('AUDIO_LINE_RETRY:', error, flush=True)
                last_error = str(error)
                # Restore board services after power loss; never reload FPGA here.
                try:
                    owner = self.prepare()
                except (OSError, RuntimeError, subprocess.SubprocessError):
                    pass
            time.sleep(2)

    def close(self):
        for child in [self.app, self.tunnel]:
            if child and child.poll() is None:
                if os.name == 'nt':
                    # Windows venv python.exe may have a separate interpreter child.
                    subprocess.run(['taskkill', '/PID', str(child.pid), '/T', '/F'],
                                   capture_output=True, env=self.environment, timeout=10,
                                   check=True)
                else:
                    child.terminate()
                child.wait(timeout=10)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', default='xilinx@192.168.2.99')
    parser.add_argument('--model', required=True)
    args = parser.parse_args()
    lock = socket.socket()
    lock.bind(('127.0.0.1', 18767))
    line = AudioLine(args)
    try:
        line.run()
    except KeyboardInterrupt:
        pass
    finally:
        line.close()
        lock.close()


if __name__ == '__main__':
    main()
