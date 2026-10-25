"""Clock-controlled file replay and the exact JPEG protocol used by W6."""
import json
from urllib.error import HTTPError
from urllib.request import build_opener, ProxyHandler

import cv2
import numpy as np
import pytest

from vision.framesource import ReplaySource, OV5640MonoSource
from vision.keypoints.frame_server import LatestFrameServer, hdmi_jpeg
from vision.keypoints.hdmi_link import HDMILink
from types import SimpleNamespace


def clip(tmp_path):
    path = tmp_path/'video.mp4'
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*'mp4v'), 10, (64, 48))
    assert writer.isOpened()
    for i in range(4):
        writer.write(np.full((48,64,3), i*40, np.uint8))
    writer.release()
    return path


class Clock:
    def __init__(self):
        self.now = 0
    def perf_counter(self):
        return self.now
    def sleep(self, seconds):
        assert seconds >= 0
        self.now += seconds


def test_replay_paces_and_loops_without_timestamp_reset(tmp_path, monkeypatch):
    import vision.framesource.replay as replay
    clock = Clock()
    monkeypatch.setattr(replay, 'time', clock)
    with ReplaySource(clip(tmp_path), max_fps=10, loop=True) as source:
        rows = [source.read() for _ in range(6)]
        assert [r[1] for r in rows] == list(range(6))
        assert [r[2] for r in rows] == pytest.approx([0,.1,.2,.3,.4,.5])
        assert clock.now == pytest.approx(.5)
        assert source.loops == 1
    assert source.read() is None


def test_replay_drops_late_frames_not_burst_catchup(tmp_path, monkeypatch):
    import vision.framesource.replay as replay
    clock = Clock()
    monkeypatch.setattr(replay, 'time', clock)
    with ReplaySource(clip(tmp_path), max_fps=10) as source:
        assert source.read()[2] == 0
        clock.now = .31
        assert source.read()[2] == pytest.approx(.3)
        assert source.dropped_late_frames == 2
        assert source.read() is None


def test_mono_ov5640_is_explicit_placeholder():
    with OV5640MonoSource() as source:
        assert source.fps == 30
        with pytest.raises(NotImplementedError, match='hardware has not arrived'):
            source.read()


def test_jpeg_has_exact_hdmi_size_and_preserves_aspect_color():
    bgr = np.full((100, 100, 3), [0, 0, 240], dtype=np.uint8)
    image = cv2.imdecode(np.frombuffer(hdmi_jpeg(bgr), np.uint8), cv2.IMREAD_COLOR)
    assert image.shape == (720,1280,3)
    assert np.max(image[360,10]) < 10  # black pillarbox
    assert image[360,640,2] > 230
    assert image[360,640,0] < 10


def test_latest_frame_server_protocol_and_no_queue():
    client = build_opener(ProxyHandler({}))
    with LatestFrameServer(port=0) as server:
        url = f'http://127.0.0.1:{server.port}'
        with pytest.raises(HTTPError) as exc:
            client.open(url+'/frame.jpg', timeout=2)
        assert exc.value.code == 503
        server.publish(np.zeros((48,64,3), np.uint8), 1, .1)
        server.publish(np.full((48,64,3), 200, np.uint8), 2, .2)
        with client.open(url+'/frame.jpg', timeout=2) as response:
            assert response.headers['Content-Type'] == 'image/jpeg'
            image = cv2.imdecode(np.frombuffer(response.read(),np.uint8),cv2.IMREAD_COLOR)
        assert image.shape == (720,1280,3)
        assert image[360,640].mean() > 190  # latest, not the old queued frame
        with client.open(url+'/state', timeout=2) as response:
            state = json.load(response)
        assert state['frames_published'] == 2
        assert state['frame_requests'] == 1
        assert state['frame_id'] == 2


def mock_link(monkeypatch, *, writers=False, pair=('bit','hwh'), boot='exited'):
    import vision.keypoints.hdmi_link as module
    import hashlib
    link = HDMILink(SimpleNamespace(board='unused'), 'dummy-test-value')
    commands = []
    monkeypatch.setattr(module, 'accepted_pairs', lambda: {('bit','hwh')})
    def ssh(command, sudo=False, **kwargs):
        commands.append((command, sudo))
        if 'systemctl show' in command:
            return boot
        if command == 'sha256sum /home/xilinx/kws_hdmi.bit /home/xilinx/kws_hdmi.hwh':
            return pair[0]+'  bit\n'+pair[1]+'  hwh'
        if command.startswith('sha256sum '):
            name = command.rsplit('/',1)[-1]
            return hashlib.sha256((module.BOARD_DIR/name).read_bytes()).hexdigest()+'  '+name
        raise AssertionError('Unexpected remote mutation: '+command)
    monkeypatch.setattr(link, 'ssh', ssh)
    monkeypatch.setattr(link, 'pids', lambda name: ([123] if name=='hdmi_display.py' else ([456] if writers else [])))
    return link, commands


def test_hdmi_attach_existing_owner_never_reloads(monkeypatch):
    link, commands = mock_link(monkeypatch)
    report = link.prepare()
    assert report['owner_pid'] == 123
    assert report['started_owner'] is False
    assert report['bitstream_downloaded'] is False
    assert not any(sudo for command,sudo in commands)


def test_hdmi_explicit_candidate_requires_both_hashes(monkeypatch,tmp_path):
    import json
    candidate=tmp_path/'candidate.json'
    candidate.write_text(json.dumps({'artifacts':{'bit':{'sha256':'newbit'},
                                                  'hwh':{'sha256':'newhwh'}}}))
    link,commands=mock_link(monkeypatch,pair=('newbit','newhwh'))
    link.args.release_manifest=candidate
    assert link.prepare()['bit_sha256']=='newbit'
    link,commands=mock_link(monkeypatch,pair=('newbit','hwh'))
    link.args.release_manifest=candidate
    with pytest.raises(RuntimeError,match='bit/hwh'):
        link.prepare()


@pytest.mark.parametrize('changes,message', [({'writers':True},'writer'),
    ({'pair':('wrong','hwh')},'bit/hwh'),({'boot':'start'},'Cold boot')])
def test_hdmi_refuses_unsafe_attach(monkeypatch, changes, message):
    link, commands = mock_link(monkeypatch, **changes)
    with pytest.raises(RuntimeError,match=message):
        link.prepare()
    assert not any(sudo for command,sudo in commands)
