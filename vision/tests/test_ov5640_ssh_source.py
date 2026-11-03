"""Live camera protocol must reject incomplete data rather than pad/replay."""
import io
import json
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
import numpy as np
from vision.keypoints.ov5640_ssh_source import OV5640SSHSource


class CameraProtocol(unittest.TestCase):
    def source(self,packet):
        source=OV5640SSHSource.__new__(OV5640SSHSource)
        source.process=SimpleNamespace(stdout=io.BytesIO(packet))
        source.condition=threading.Condition();source.stop=threading.Event()
        source.latest=None;source.error=None;source.sequence=0;source.started=time.monotonic()
        source.receive();return source

    @staticmethod
    def packet(header,raw):
        ready=json.dumps({'event':'ready','pid':123}).encode()+b'\n'
        return ready+json.dumps(header).encode()+b'\n'+raw

    def header(self):
        return dict(event='frame',frame=7,bytes=1280*720*2,width=1280,height=720,
            format='RGB565_LE',dma_shutdown_confirmed=True)

    def test_complete_RGB565_frame_decodes_true_input(self):
        raw=np.full((720,1280),0xF800,dtype='<u2').tobytes()
        source=self.source(self.packet(self.header(),raw))
        frame,index,_=source.read()
        self.assertEqual(index,7);self.assertEqual(frame.shape,(720,1280,3))
        self.assertEqual(tuple(frame[0,0]),(0,0,248))

    def test_truncated_frame_not_emitted(self):
        source=self.source(self.packet(self.header(),b'\x00\x00'))
        self.assertIsNone(source.latest);self.assertIn('truncated',source.error)

    def test_partial_or_unconfirmed_DMA_not_emitted(self):
        for changes in ({'bytes':2},{'dma_shutdown_confirmed':False}):
            header=self.header();header.update(changes)
            source=self.source(self.packet(header,b'\x00\x00'))
            self.assertIsNone(source.latest);self.assertIn('unconfirmed',source.error)

class DisconnectedCleanup(unittest.TestCase):
    def source(self):
        source=OV5640SSHSource.__new__(OV5640SSHSource)
        source.stop=threading.Event();source.board_gateway=True;source.pid=123
        source.process=Mock();source.process.poll.return_value=255
        source.thread=Mock();source.log=Mock()
        return source

    def test_lost_local_SSH_still_requires_remote_DMA_stop(self):
        source=self.source()
        with patch('vision.keypoints.ov5640_ssh_source.subprocess.run',return_value=SimpleNamespace(returncode=0)) as run:
            source.release()
        self.assertEqual(run.call_args.args[0][-1],'sudo -n /usr/local/sbin/sign-av-ctl stop')
        self.assertTrue(source.stop.is_set());source.log.close.assert_called_once()
        source.process.wait.assert_not_called()

    def test_remote_stop_failure_is_not_hidden_by_local_SSH_exit(self):
        source=self.source()
        with patch('vision.keypoints.ov5640_ssh_source.subprocess.run',return_value=SimpleNamespace(returncode=1)):
            with self.assertRaisesRegex(RuntimeError,'safe stop'):source.release()
        self.assertFalse(source.stop.is_set());source.log.close.assert_not_called()


if __name__=='__main__':unittest.main()
