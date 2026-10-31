"""Physical channel protocol checks, without FPGA or camera hardware."""
import io,json,threading,time,unittest
from types import SimpleNamespace
import numpy as np
from vision.keypoints.stereo_demo import StereoSource


class StereoProtocolTests(unittest.TestCase):
    def run_stream(self,frames):
        payload=json.dumps(dict(event='ready',pid=42,cameras=[1,2])).encode()+b'\n'
        for camera,value in frames:
            raw=np.full((720,1280),value,dtype='<u2').tobytes()
            header=dict(event='frame',camera=camera,frame=camera,bytes=len(raw),format='RGB565_LE',
                width=1280,height=720,dma_shutdown_confirmed=True,capture_completed_monotonic_s=1.+camera*.1)
            payload+=json.dumps(header).encode()+b'\n'+raw
        source=StereoSource.__new__(StereoSource)
        source.channels={};source.pair_sequence=0;source.channel_errors={}
        source.process=SimpleNamespace(stdout=io.BytesIO(payload))
        source.stop=threading.Event();source.condition=threading.Condition();source.latest=None
        source.started=time.monotonic();source.error=None
        source.receive();return source

    def test_one_camera_never_becomes_a_pair(self):
        source=self.run_stream([(1,0xF800)])
        self.assertIsNone(source.latest);self.assertEqual(set(source.channels),{1})

    def test_distinct_physical_frames_and_timestamps_preserved(self):
        source=self.run_stream([(1,0xF800),(2,0x001F)])
        pair,sequence,_=source.latest
        self.assertEqual(sequence,1);self.assertEqual(tuple(pair[1]['image'][0,0]),(0,0,248))
        self.assertEqual(tuple(pair[2]['image'][0,0]),(248,0,0))
        self.assertNotEqual(pair[1]['board_time'],pair[2]['board_time'])

    def test_unknown_camera_id_rejected(self):
        source=self.run_stream([(3,0)])
        self.assertIsNone(source.latest);self.assertIn('Invalid',source.error)


if __name__=='__main__':unittest.main()
