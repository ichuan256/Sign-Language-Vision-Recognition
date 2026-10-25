"""Bounded PC JPEG -> SSH -> existing W6 HDMI buffer link. Never load a bitstream."""
import argparse
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import time
from urllib.request import build_opener, ProxyHandler

ROOT = Path(__file__).resolve().parents[2]
BOARD_PYTHON = '/usr/local/share/pynq-venv/bin/python'
BOARD_DIR = ROOT/'project/board/w6'


def accepted_pairs():
    paths = [BOARD_DIR/'release_manifest.json']
    paths += list((ROOT/'project/board_validation/w6/timing_candidate').glob('build_manifest_*.json'))
    pairs = set()
    for path in paths:
        artifacts = json.loads(path.read_text(encoding='utf-8'))['artifacts']
        if isinstance(artifacts, list):
            artifacts = {a['file']: a for a in artifacts}
        pairs.add(tuple(artifacts[k]['sha256'] for k in ('kws_hdmi.bit','kws_hdmi.hwh')))
    return pairs


class HDMILink:
    def __init__(self, args, password):
        self.args, self.password = args, password
        self.options = ['-o','BatchMode=yes','-o','ConnectTimeout=8',
                        '-o','ServerAliveInterval=5','-o','ServerAliveCountMax=2']
        self.environment = dict(os.environ)
        self.environment.pop('KEYPOINT_BOARD_SUDO_PASSWORD', None)

    def ssh(self, command, sudo=False, timeout=30, allow_timeout=False):
        if sudo:
            command = 'sudo -S -p '+shlex.quote('')+' sh -c '+shlex.quote(command)
        result = subprocess.run(['ssh',*self.options,self.args.board,command],
            input=self.password+'\n' if sudo else None, capture_output=True,
            text=True, encoding='utf-8', errors='replace', timeout=timeout, env=self.environment)
        if result.returncode != 0 and not (allow_timeout and result.returncode == 124):
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f'SSH exit {result.returncode}')
        return result.stdout.strip()

    def pids(self, script):
        pattern = '^'+re.escape(BOARD_PYTHON)+r'( -u)? /home/xilinx/'+re.escape(script)+r'( |$)'
        output = self.ssh('pgrep -f '+shlex.quote(pattern)+' || true')
        return [int(s) for s in output.split()]

    def state(self):
        with build_opener(ProxyHandler({})).open(f'http://127.0.0.1:{self.args.pc_port}/state', timeout=3) as response:
            return json.load(response)

    def prepare(self):
        if self.ssh('systemctl show -p SubState --value bootpy.service') != 'exited':
            raise RuntimeError('Cold boot has not finished; do not load/reconfigure FPGA')
        hashes = self.ssh('sha256sum /home/xilinx/kws_hdmi.bit /home/xilinx/kws_hdmi.hwh').splitlines()
        pair = tuple(row.split()[0] for row in hashes)
        if pair not in accepted_pairs():
            raise RuntimeError('Board bit/hwh pair does not match an accepted local release')
        for script in ('hdmi_display.py','hdmi_audio_receiver.py'):
            expected = hashlib.sha256((BOARD_DIR/script).read_bytes()).hexdigest()
            if self.ssh('sha256sum /home/xilinx/'+script).split()[0] != expected:
                raise RuntimeError(f'{script} differs; inspect/deploy explicitly, never overwrite automatically')
        if self.pids('hdmi_audio_receiver.py') or self.pids('hdmi_renderer.py'):
            raise RuntimeError('Another known HDMI writer is active. Stop it only with user approval; keep the display owner alive.')
        owners = self.pids('hdmi_display.py')
        started_owner = False
        if not owners:
            # This exact script is verified above and defaults to Overlay(download=False).
            log = '/home/xilinx/keypoint_hdmi_display_'+str(time.time_ns())+'.log'
            self.ssh('nohup env XILINX_XRT=/usr '+BOARD_PYTHON+' -u /home/xilinx/hdmi_display.py > '+
                     shlex.quote(log)+' 2>&1 < /dev/null &', sudo=True)
            started_owner = True
            for _ in range(20):
                if 'DISPLAY_RUNNING:' in self.ssh('cat '+shlex.quote(log)+' 2>/dev/null || true'):
                    break
                time.sleep(.5)
            else:
                raise RuntimeError('HDMI owner did not reach DISPLAY_RUNNING; inspect its unique log, do not reload FPGA')
            owners = self.pids('hdmi_display.py')
        if len(owners) != 1:
            raise RuntimeError('Expected exactly one retained-frame HDMI owner')
        return dict(owner_pid=owners[0], started_owner=started_owner,
                    bit_sha256=pair[0], hwh_sha256=pair[1], bitstream_downloaded=False)

    def run(self):
        output = self.args.output.resolve()
        if not output.is_relative_to(ROOT) or output == ROOT:
            raise ValueError('Output must be a dedicated workspace directory')
        if output.exists():
            raise FileExistsError(output)
        before = self.state()
        if not before['frames_published']:
            raise RuntimeError('Start replay with --serve-hdmi and wait for its first frame')
        output.mkdir(parents=True)
        report = dict(valid_run=False, screen_visually_confirmed=False, source_state_before=before)
        tunnel = None
        try:
            report.update(self.prepare())
            with (output/'tunnel.log').open('xb') as log:
                tunnel = subprocess.Popen(['ssh','-N',*self.options,'-o','ExitOnForwardFailure=yes',
                    '-R',f'{self.args.remote_port}:127.0.0.1:{self.args.pc_port}',self.args.board],
                    stdout=log, stderr=log, env=self.environment)
                time.sleep(1)
                if tunnel.poll() is not None:
                    raise RuntimeError('SSH forwarding failed; inspect tunnel.log')
                # No MMIO writes until the remote URL serves a valid frame.
                probe = "from urllib.request import urlopen; r=urlopen('http://127.0.0.1:%d/frame.jpg',timeout=3); assert r.status==200; print('FRAME_LINK_READY')" % self.args.remote_port
                self.ssh(BOARD_PYTHON+' -c '+shlex.quote(probe))
                print('HDMI_LINK_READY owner='+str(report['owner_pid'])+
                      f' duration={self.args.seconds}s; please inspect the physical screen', flush=True)
                receiver = (f'timeout --signal=TERM {self.args.seconds}s env XILINX_XRT=/usr '+
                    BOARD_PYTHON+' -u /home/xilinx/hdmi_audio_receiver.py '+
                    f'--owner-pid {report["owner_pid"]} --url http://127.0.0.1:{self.args.remote_port}/frame.jpg --fps {self.args.fps}')
                text = self.ssh(receiver, sudo=True, timeout=self.args.seconds+20, allow_timeout=True)
                (output/'receiver.log').write_text(text+'\n', encoding='utf-8')
                report['receiver_log'] = text
                report['source_state_after'] = self.state()
                after = report['source_state_after']
                report['source_progress_observed'] = after['frames_published'] > before['frames_published']
                report['frame_requests_during_link'] = after['frame_requests']-before['frame_requests']
                counts = [int(v) for v in re.findall(r'AUDIO_HDMI frames=(\d+)', text)]
                report['frame_writes_confirmed_at_least'] = max(counts, default=0)
                report['valid_run'] = (bool(counts) and report['source_progress_observed'] and
                    report['frame_requests_during_link'] > 1 and 'AUDIO_HDMI_DISCONNECTED' not in text)
        except Exception as exc:
            report['error'] = str(exc)
            raise
        finally:
            if tunnel is not None and tunnel.poll() is None:
                tunnel.terminate()
                try:
                    tunnel.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    tunnel.kill()
                    tunnel.wait(timeout=5)
            report['receiver_bounded_seconds'] = self.args.seconds
            report['display_owner_left_alive'] = True
            (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if not report['valid_run']:
            raise RuntimeError('No clean frame-write confirmation; inspect receiver.log')
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', default='xilinx@192.168.2.99')
    parser.add_argument('--pc-port', type=int, default=18780)
    parser.add_argument('--remote-port', type=int, default=18781)
    parser.add_argument('--seconds', type=int, default=600, help='Link duration, default 10 minutes; last frame remains after exit')
    parser.add_argument('--fps', type=int, default=15)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.seconds <= 600 or not 1 <= args.fps <= 30:
        parser.error('seconds must be in [1,600]; fps in [1,30]')
    if not all(1 <= p <= 65535 for p in (args.pc_port,args.remote_port)):
        parser.error('ports must be in [1,65535]')
    password = os.environ.get('KEYPOINT_BOARD_SUDO_PASSWORD')
    if password is None:
        password = getpass.getpass('Board sudo password (not saved): ')
    HDMILink(args,password).run()


if __name__ == '__main__':
    main()
