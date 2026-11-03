"""Manufacturer protocol vectors and fixed CLI boundaries, without serial I/O."""
import importlib.util
from pathlib import Path
import sys,unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('syn6288',Path(__file__).resolve().parents[1]/'board/usb_tts/syn6288_gateway.py')
syn=importlib.util.module_from_spec(spec);spec.loader.exec_module(syn)

class Protocol(unittest.TestCase):
    def test_manufacturer_text_vector(self):
        self.assertEqual(syn.frame(1,b'\0'+'宇音天下'.encode('gb2312')).hex(),'fd000b0100d3eed2f4cceccfc2c1')

    def test_manufacturer_status_vector(self):
        self.assertEqual(syn.frame(0x21).hex(),'fd000221de')

    def test_digits_have_correct_length_encoding_and_whole_frame_xor(self):
        from functools import reduce
        from operator import xor
        for number,word in enumerate(syn.WORDS,1):
            packet=syn.digit_frame(number)
            self.assertEqual(int.from_bytes(packet[1:3],'big'),len(packet)-3)
            self.assertEqual(packet[3:5],b'\x01\x00')
            self.assertEqual(packet[5:-1].decode('gb2312'),'[v10]'+word)
            self.assertEqual(reduce(xor,packet,0),0)
        for value in (0,6,True,'1; reboot'):
            with self.assertRaises(ValueError):syn.digit_frame(value)

    def test_unsupported_action_rejected_before_serial_access(self):
        for value in ('0','6','probe;id','/dev/ttyS0'):
            with patch.object(sys,'argv',['sign-digit-say',value]),patch.object(syn,'execute') as execute:
                with self.assertRaises(SystemExit):syn.main()
                execute.assert_not_called()

if __name__=='__main__':unittest.main()
