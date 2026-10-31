"""Serve current W6 LINE IN as mono PCM16, with no overlay download."""
import argparse
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

from pynq import Overlay
from pynq.lib.audio import AudioADAU1761


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8766)
    parser.add_argument('--capture', default=str(Path(__file__).with_name('board_pcm_capture')))
    args = parser.parse_args()
    overlay = Overlay('/home/xilinx/kws_hdmi.bit', download=False)
    description = overlay.ip_dict['audio_codec_ctrl_0']
    if description['phys_addr'] != 0x43C00000:
        raise RuntimeError('Unexpected audio hardware mapping')
    audio = AudioADAU1761(description)
    audio.configure()
    audio.select_line_in()
    owner = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/health':
                self.send_response(200)
                self.send_header('Content-Length', '2')
                self.end_headers()
                self.wfile.write(b'OK')
                return
            if self.path.startswith('/assets/'):
                root = Path('/home/xilinx/video').resolve()
                asset = (root / unquote(self.path[len('/assets/'):])).resolve()
                if not asset.is_relative_to(root) or asset.suffix != '.mp4' or not asset.is_file():
                    self.send_error(404)
                    return
                data = asset.read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', 'video/mp4')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            if self.path != '/pcm':
                self.send_error(404)
                return
            if not owner.acquire(blocking=False):
                self.send_error(409, 'Audio input already in use')
                return
            child = None
            try:
                child = subprocess.Popen([args.capture, '/dev/uio%d' % audio.uio_index],
                                         stdout=subprocess.PIPE)
                self.send_response(200)
                self.send_header('Content-Type', 'application/octet-stream')
                self.send_header('X-Sample-Rate', '48000')
                self.send_header('X-Audio-Format', 's16le-mono')
                self.end_headers()
                while True:
                    data = child.stdout.read(9600)
                    if not data:
                        break
                    self.wfile.write(data)
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                if child:
                    child.terminate()
                    child.wait(timeout=3)
                    child.stdout.close()
                owner.release()

    print('BOARD_AUDIO_READY LINE_IN_LEFT 48000Hz PCM16', flush=True)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    server.daemon_threads = True
    server.serve_forever()


if __name__ == '__main__':
    main()
