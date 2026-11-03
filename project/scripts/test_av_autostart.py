"""Autostart contracts without hardware, model loads or privilege changes."""
import importlib.util,json,sys,threading,unittest
from pathlib import Path
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
import av_autostart as auto

class AutoAVTest(unittest.TestCase):
    def test_unsupported_modes_do_not_reach_legacy_hardware_paths(self):
        c=auto.AutoAVController.__new__(auto.AutoAVController)
        with patch.object(auto.Controller,'request') as request:
            for mode in ('ov5640','stereo','pl','independent','audio','teacher','single_hdmi'):
                with self.assertRaises(ValueError):c.request(mode,cold_boot=True)
            request.assert_not_called()

    def test_manual_stop_disables_automatic_restart(self):
        c=auto.AutoAVController.__new__(auto.AutoAVController)
        with patch.object(auto.Controller,'request') as request:
            c.request('idle');self.assertFalse(c.auto_enabled)
            c.request('av',cold_boot=True);self.assertFalse(c.auto_enabled)
            request.assert_called_with('av',0,True)

    def test_new_visual_modes_use_current_firmware_dispatch(self):
        c=auto.AutoAVController.__new__(auto.AutoAVController)
        with patch.object(auto.Controller,'request') as request:
            for mode in ('camera','sd_teacher'):
                c.request(mode,2);request.assert_called_with(mode,2,False)
                self.assertFalse(c.auto_enabled)

    def test_only_USB_uses_digit_recognition_without_speech(self):
        for mode in ('camera','sd_teacher'):
            c=auto.AutoAVController.__new__(auto.AutoAVController)
            c.out=ROOT/'project/_tmp/test_digit_commands';c.tunnel_for=Mock();c.wait_until=Mock()
            c.args=Mock(vision_python='python',board='test-board');c.line=Mock(ssh_options=[])
            c.spawn=Mock()
            c.start_video(mode,2)
            command=c.spawn.call_args_list[0].args[1]
            self.assertEqual('--hand-digits' in command,mode=='camera')
            self.assertNotIn('--speak-digits',command)
            self.assertNotIn('--sign-model',command)
            self.assertIn('--no-pl',command)

    def test_fixed_gateway_rejects_arbitrary_commands(self):
        c=auto.AutoAVController.__new__(auto.AutoAVController)
        with self.assertRaises(ValueError):c.gateway('reboot')
        with self.assertRaises(ValueError):c.gateway('audio; echo bad')

    def test_gateway_uses_noninteractive_sudo_and_no_password_input(self):
        c=auto.AutoAVController.__new__(auto.AutoAVController)
        c.args=Mock(board='test-board');c.line=Mock(ssh_options=[],environment={})
        with patch.object(auto.subprocess,'run',return_value=Mock(returncode=0,stdout='{"ready":true}')) as run:
            self.assertTrue(c.gateway('preflight')['ready'])
        args,kw=run.call_args
        self.assertEqual(args[0][-1],'sudo -n /usr/local/sbin/sign-av-ctl preflight')
        self.assertNotIn('input',kw)

class BoardCLITest(unittest.TestCase):
    def test_bad_paths_rejected_before_hardware_or_privilege_access(self):
        spec=importlib.util.spec_from_file_location('gateway',ROOT/'project/board/av_boot/board_gateway.py')
        gateway=importlib.util.module_from_spec(spec);spec.loader.exec_module(gateway)
        for action in ('stream','display'):
            for value in ('../other','ui_123;id','ui_123456789012 /etc/passwd','ui_123456789012\n'):
                with patch.object(sys,'argv',['sign-av-ctl',action,value]),patch.object(gateway,'verify') as verify:
                    with self.assertRaises(SystemExit):gateway.main()
                    verify.assert_not_called()

class SDSourceTest(unittest.TestCase):
    def test_consumed_metadata_does_not_follow_next_frame(self):
        from vision.keypoints.sd_teaching_source import SDTeachingSSHSource
        c=SDTeachingSSHSource.__new__(SDTeachingSSHSource)
        c.condition=threading.Condition();c.error=None;c.closed=False
        c.latest=('pixels',42,123.0,dict(clip='服务',source_frame=42))
        self.assertEqual(c.read(),('pixels',42,123.0))
        with c.condition:c.latest=('next',53,124.0,dict(clip='可以。',source_frame=53))
        self.assertEqual(c.last_metadata,dict(clip='服务',source_frame=42))
        c.read();self.assertEqual(c.last_metadata['source_frame'],53)

    def test_truncated_payload_is_rejected(self):
        import io
        from vision.keypoints.sd_teaching_source import SDTeachingSSHSource
        with self.assertRaises(EOFError):SDTeachingSSHSource.exact(io.BytesIO(b'short'),100)

if __name__=='__main__':unittest.main()
