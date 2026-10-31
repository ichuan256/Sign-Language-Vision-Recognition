"""Actual JPEG/metadata and independent-column contracts; no audio hardware."""
import base64,json,sys,threading,unittest
from pathlib import Path
from types import SimpleNamespace
from http.server import ThreadingHTTPServer
from urllib.request import build_opener,ProxyHandler
import cv2
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'ASR'),str(ROOT/'project/board/ov5640_snapshot')]
from audio_loop import Screen,make_handler
from loop_core import Session
from av_layout import ThreePanel


class Panels(unittest.TestCase):
    def test_audio_panel_carries_same_subtitle_and_playback_frame(self):
        lexicon=SimpleNamespace(asset_source='test',entries=[],asset_paths=[],manifest_sha256='test')
        session=Session(lexicon);screen=Screen(session)
        session.update(partial='你好，谢谢',playing='你好',video_frames=17,completed=2,status='正在聆听板端麦克风')
        screen.compose(Image.new('RGB',(640,360),(0,230,0)))
        server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(session,SimpleNamespace(),screen))
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            opener=build_opener(ProxyHandler({}))
            with opener.open('http://127.0.0.1:%d/panel.jpg'%server.server_port) as response:
                metadata=json.loads(base64.b64decode(response.headers['X-Frame-Metadata']))
                frame=cv2.imdecode(np.frombuffer(response.read(),np.uint8),cv2.IMREAD_COLOR)
            self.assertEqual(frame.shape,(570,426,3))
            self.assertEqual(metadata['partial'],'你好，谢谢');self.assertEqual(metadata['video_frames'],17)
            self.assertEqual(metadata['playing'],'你好')
            self.assertGreater(frame[275,210,1],220)
        finally:server.shutdown();server.server_close();thread.join()

    def test_camera_updates_without_waiting_for_either_remote_panel(self):
        layout=ThreePanel();raw=np.full((240,426,3),(0,0,255),np.uint8)
        teacher=np.full_like(raw,(0,255,0));audio=dict(image=np.full((570,426,3),(255,0,0),np.uint8),received=100)
        info=dict(frame_id=3,source_timestamp_s=99,sign_recognition={})
        first=layout.compose(raw,teacher,audio,raw_item=dict(frame=4,captured=100),teacher_info=info,counts=(4,1),now=100.2)
        second=layout.compose(np.full_like(raw,(0,255,255)),teacher,audio,
            raw_item=dict(frame=5,captured=100.4),teacher_info=info,counts=(5,2),now=100.5)
        self.assertEqual(first.shape,(720,1280,3))
        np.testing.assert_array_equal(first[200,200],(0,0,255))
        np.testing.assert_array_equal(second[200,200],(0,255,255))
        np.testing.assert_array_equal(first[200,600],second[200,600])
        np.testing.assert_array_equal(first[200,1000],second[200,1000])
        disconnected=layout.compose(raw,teacher,audio,raw_item=dict(frame=6,captured=105),teacher_info=info,counts=(6,3),now=105)
        np.testing.assert_array_equal(disconnected[200,200],(0,0,255))
        self.assertFalse(np.array_equal(disconnected[155,1000],(255,0,0)))


if __name__=='__main__':unittest.main()
