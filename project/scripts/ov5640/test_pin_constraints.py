"""Wiring contract and XDC failure-atomicity regression."""
import copy
import json
import re
import tkinter
import unittest
from pathlib import Path
import generate_pin_constraints as pins

class PinMapTests(unittest.TestCase):
    def setUp(self):
        self.mapping = json.loads(pins.MAP.read_text(encoding='utf-8-sig'))

    def test_current_wiring_and_rtl_ports(self):
        rows = pins.validate(self.mapping)
        actual = {(r['camera'],r['signal']):r['package_pin'] for r in rows}
        self.assertEqual(actual['OV1','PCLK'],'Y9')
        self.assertEqual(actual['OV1','VSYNC'],'W10')
        self.assertEqual(actual['OV2','PCLK'],'U7')
        self.assertEqual(actual['OV2','D2'],'W18')
        self.assertEqual(actual['OV1','PWDN'],'R16')
        self.assertEqual(actual['OV2','PWDN'],'U17')
        rtl = (pins.ROOT/'project/fpga/rtl/ov5640_stereo/ov5640_stereo_startup_capture.v').read_text()
        for r in rows:
            base = r['rtl_port'].split('[')[0]
            self.assertIn(base, rtl)

    def test_generated_file_is_current(self):
        self.assertEqual(pins.XDC.read_text(encoding='utf-8'), pins.render(self.mapping))
        self.assertEqual(pins.LOADER.read_text(encoding='utf-8'), pins.render_loader(self.mapping))
        commands=[line for line in pins.render(self.mapping).splitlines() if not line.startswith('#')]
        self.assertEqual(len(commands),30)
        self.assertTrue(all(line.startswith('set_property ') for line in commands))

    def test_duplicate_pad_missing_signal_wrong_header_and_port(self):
        for mutation in ('duplicate','missing','header','port','direction','camera_pin','voltage'):
            with self.subTest(mutation=mutation):
                m=copy.deepcopy(self.mapping)
                if mutation=='duplicate': m['signals'][1]['package_pin']=m['signals'][0]['package_pin']
                elif mutation=='missing': m['signals'].pop()
                elif mutation=='header': m['signals'][0]['board_pin']=1
                elif mutation=='port': m['signals'][0]['rtl_port']='ov2_vsync'
                elif mutation=='direction': m['signals'][1]['direction']='fpga_to_camera'
                elif mutation=='camera_pin': m['signals'][0]['camera_pin']=38
                else: m['signals'][0]['io_standard']='LVCMOS18'
                with self.assertRaises(ValueError): pins.validate(m)

    def test_reject_original_non_clock_pin_and_wrong_p_side(self):
        for pad in ('W10','Y8'):
            with self.subTest(pad=pad):
                m=copy.deepcopy(self.mapping)
                clock=next(r for r in m['signals'] if r['camera']=='OV1' and r['signal']=='PCLK')
                other=next(r for r in m['signals'] if r['package_pin']==pad)
                clock['package_pin'],other['package_pin']=other['package_pin'],clock['package_pin']
                clock['board_pin'],other['board_pin']=other['board_pin'],clock['board_pin']
                with self.assertRaises(ValueError): pins.validate(m)

    def test_no_collision_with_retained_w6_constraints(self):
        camera={r['package_pin'] for r in self.mapping['signals']}
        for name in ('sign_glove_master.xdc','audio_w6.xdc','hdmi_w6.xdc'):
            content=(pins.ROOT/'project/fpga/xdc'/name).read_text(encoding='utf-8')
            for line in content.splitlines():
                if line.lstrip().startswith('#'): continue
                match=re.search(r'PACKAGE_PIN[ ]+([A-Z]+[0-9]+)',line)
                if match: self.assertNotIn(match.group(1),camera,name)

    def tcl(self, missing=None, conflict=False):
        t=tkinter.Tcl()
        ports=[r['rtl_port'] for r in self.mapping['signals']]
        if missing: ports.remove(missing)
        if conflict: ports.append('legacy_spi')
        t.call('set','test_ports',t.call('list',*ports))
        t.call('set','xdc_text',pins.render(self.mapping))
        t.eval('array set assigned {} ; set writes 0')
        if conflict: t.call('set','assigned(legacy_spi)','Y9')
        t.eval('''
proc get_ports {args} {
    global test_ports
    set filter [lsearch -exact $args -filter]
    if {$filter < 0} {
        set wanted [lindex $args end]
        if {$wanted eq "*"} {return $test_ports}
        if {[lsearch -exact $test_ports $wanted] >= 0} {return [list $wanted]}
        return {}
    }
    set expression [lindex $args [expr {$filter+1}]]
    regexp {^NAME == "(.*)"$} $expression -> wanted
    if {[lsearch -exact $test_ports $wanted] >= 0} {return [list $wanted]}
    return {}
}
proc get_property {prop port} {
    global assigned
    set port [lindex $port 0]
    if {$prop eq "NAME"} {return $port}
    if {[info exists assigned($port)]} {return $assigned($port)}
    return {}
}
proc set_property {option props port} {
    global assigned writes
    set port [lindex $port 0]
    set assigned($port) [dict get $props PACKAGE_PIN]
    incr writes
}
proc read_xdc {path} {
    global xdc_text
    uplevel #0 $xdc_text
}
''')
        return t

    def test_xdc_bus_bit_names_and_idempotency(self):
        t=self.tcl()
        xdc=pins.render_loader(self.mapping)
        t.eval(xdc)
        self.assertEqual(int(t.eval('set writes')),30)
        for row in self.mapping['signals']:
            self.assertEqual(t.call('set',f"assigned({row['rtl_port']})"),row['package_pin'])
        t.eval(xdc)
        self.assertEqual(int(t.eval('set writes')),60)

    def test_xdc_missing_last_port_is_atomic(self):
        t=self.tcl(missing='ov2_pwdn')
        with self.assertRaises(tkinter.TclError): t.eval(pins.render_loader(self.mapping))
        self.assertEqual(int(t.eval('set writes')),0)

    def test_xdc_legacy_pad_conflict_is_atomic(self):
        t=self.tcl(conflict=True)
        with self.assertRaises(tkinter.TclError): t.eval(pins.render_loader(self.mapping))
        self.assertEqual(int(t.eval('set writes')),0)

if __name__=='__main__':
    unittest.main(verbosity=2)
