"""Control contract tests; no board, camera, or model execution."""
import importlib.util
import json
from pathlib import Path
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, build_opener, ProxyHandler
from unittest.mock import Mock,patch

spec=importlib.util.spec_from_file_location('demo_control',Path(__file__).with_name('demo_control.py'))
control=importlib.util.module_from_spec(spec);spec.loader.exec_module(control)


class HTTPContract(unittest.TestCase):
    def setUp(self):
        self.controller=Mock()
        self.controller.lock=threading.Lock()
        self.controller.state={'mode':'idle','busy':False}
        self.controller.preview=None
        self.server=ThreadingHTTPServer(('127.0.0.1',0),control.handler_for(self.controller,'test-session'))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.url='http://127.0.0.1:'+str(self.server.server_port)
        self.opener=build_opener(ProxyHandler({}))

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join()

    def post(self,data,token):
        return self.opener.open(Request(self.url+'/api/switch',data=json.dumps(data).encode(),
            headers={'X-Session':token,'Content-Type':'application/json'}))

    def test_switch_requires_session(self):
        with self.assertRaises(HTTPError) as error:self.post({'mode':'pl'},'wrong')
        self.assertEqual(error.exception.code,403);self.controller.request.assert_not_called()

    def test_valid_camera_request_preserves_device(self):
        with self.post({'mode':'camera','camera':2},'test-session') as response:self.assertEqual(response.status,202)
        self.controller.request.assert_called_once_with('camera',2)

    def test_AV_request_preserves_cold_boot_guard(self):
        with self.post({'mode':'av','cold_boot':True},'test-session') as response:self.assertEqual(response.status,202)
        self.controller.request.assert_called_once_with('av',0,True)

    def test_conflicting_transition_is_reported(self):
        self.controller.request.side_effect=RuntimeError('正在切换')
        with self.assertRaises(HTTPError) as error:self.post({'mode':'pl'},'test-session')
        self.assertEqual(error.exception.code,409)

    def test_preview_unavailable_is_not_fake_success(self):
        with self.assertRaises(HTTPError) as error:self.opener.open(self.url+'/api/preview.jpg')
        self.assertEqual(error.exception.code,503)


class SafetyContract(unittest.TestCase):
    def test_unowned_PL_worker_prevents_writer_handoff(self):
        c=control.Controller.__new__(control.Controller)
        c.update=Mock();c.stop_worker=Mock();c.stop_tunnel=Mock();c.line=Mock()
        c.state={'mode':'pl'}
        c.board=Mock(return_value={'processes':[{'pid':101,'script':'/home/xilinx/work/stream_hand_board.py'}]})
        with patch.object(control,'app_action'):
            with self.assertRaisesRegex(RuntimeError,'外部PL'):c.quiesce()
        c.line.ssh.assert_not_called();c.stop_tunnel.assert_not_called()

    def test_invalid_mode_and_device_rejected_before_mutation(self):
        c=control.Controller.__new__(control.Controller)
        for mode,index in [('unknown',0),('camera',-1),('camera',10)]:
            with self.assertRaises(ValueError):c.request(mode,index)

    def test_concurrent_switch_rejected(self):
        c=control.Controller.__new__(control.Controller);c.transition=threading.Lock();c.transition.acquire()
        with self.assertRaisesRegex(RuntimeError,'正在切换'):c.request('teacher')
        c.transition.release()

    def test_OV5640_requires_explicit_cold_boot_confirmation(self):
        c=control.Controller.__new__(control.Controller)
        with self.assertRaisesRegex(ValueError,'冷启动'):c.request('ov5640')
        with self.assertRaisesRegex(ValueError,'冷启动'):c.request('stereo')
        with self.assertRaisesRegex(ValueError,'冷启动'):c.request('single_hdmi')
        with self.assertRaisesRegex(ValueError,'冷启动'):c.request('av')

    def test_camera_firmware_blocks_W6_before_PYNQ_access(self):
        c=control.Controller.__new__(control.Controller)
        c.args=Mock(board='test-board');c.line=Mock()
        with patch.object(control,'remote',return_value={'ov5640_boot':True}):
            with self.assertRaisesRegex(RuntimeError,'独立采集固件'):c.w6_preflight()
        c.line.ssh.assert_not_called()


if __name__=='__main__':unittest.main()
