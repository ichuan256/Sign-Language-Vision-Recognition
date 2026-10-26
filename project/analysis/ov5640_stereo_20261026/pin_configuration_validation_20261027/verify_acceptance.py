"""Recheck saved pin evidence; does not rerun Vivado or claim timing closure."""
import hashlib
import json
import re
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'project/scripts/ov5640'))
import generate_pin_constraints as pins

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

mapping=json.loads(pins.MAP.read_text(encoding='utf-8-sig'))
rows=pins.validate(mapping)
assert pins.XDC.read_text(encoding='utf-8')==pins.render(mapping),'XDC stale'
assert pins.LOADER.read_text(encoding='utf-8')==pins.render_loader(mapping),'Loader stale'
native=json.loads((HERE/'native_load_verification.json').read_text(encoding='utf-8'))
assert native['verdict']=='PASS' and native['exit_code']==0
assert not re.search(r'CRITICAL WARNING|ERROR:',native['output'])
baseline=json.loads((HERE/'baseline_preserved_hashes.json').read_text(encoding='utf-8-sig'))
for item in baseline:
    assert sha(ROOT/item['path']).lower()==item['sha256'].lower(),item['path']+' changed'
properties={}
for line in (HERE/'package_pin_properties.txt').read_text().splitlines():
    fields=line.split()
    port=fields[0].strip('{}')
    properties[port]=fields[1:]
assert len(properties)==30
for row in rows:
    actual=properties[row['rtl_port']]
    assert actual[0]==row['package_pin'],row['rtl_port']
    if row['signal']=='PCLK':
        assert actual[1]==row['clock_pin_function'] and actual[-1]=='1'
route=(HERE/'route_status.rpt').read_text()
assert re.search(r'fully routed nets[. ]*:[ ]*2473',route)
assert re.search(r'nets with routing errors[. ]*:[ ]*0',route)
pad=(HERE/'pad_and_clock_checks.txt').read_text()
assert 'CAMERA_PORT_COUNT 30' in pad and 'UNIQUE_CAMERA_PADS 30' in pad
assert 'PIN_AND_PAD_CHECKS_PASS' in pad
assert pad.count('OPEN_DRAIN ')==4 and pad.count(' GROUND')==4
assert 'BUFGCTRL_X0Y0' in pad and 'BUFGCTRL_X0Y1' in pad
timing=(HERE/'timing_summary.rpt').read_text()
assert 'Timing constraints are not met.' in timing
assert '-20.913' in timing
generated=[]
for folder in (ROOT/'project/scripts/ov5640',HERE):
    for path in folder.glob('*.py'):
        content=path.read_text(encoding='utf-8-sig')
        assert not any(ord(c)<32 and c not in (chr(9),chr(10),chr(13)) for c in content),str(path)
for path in sorted(HERE.glob('*')):
    if path.is_file() and path.name!='verification.json':
        generated.append({'path':str(path.relative_to(ROOT)).replace(chr(92),'/'),'sha256':sha(path)})
for path in (pins.MAP,pins.XDC,pins.LOADER,ROOT/'project/scripts/ov5640/generate_pin_constraints.py',ROOT/'project/scripts/ov5640/test_pin_constraints.py'):
    generated.append({'path':str(path.relative_to(ROOT)).replace(chr(92),'/'),'sha256':sha(path)})
result={
    'date':'2026-10-27','verdict':'physical_pin_configuration_pass_timing_not_closed',
    'camera_signal_count':30,'unique_pads':30,'tool':'Vivado 2024.1','part':'xc7z020clg400-1',
    'harness_sys_clk_mhz':125,'pclk_nominal_mhz':84,
    'synth_design':'completed','place_design':'completed','route_design':'completed',
    'native_read_xdc':'passed_after_separating_guard_tcl',
    'fully_routed_nets':2473,'routing_error_nets':0,
    'overall_wns_ns':-20.913,'overall_tns_ns':-723.368,'timing_signoff_pass':False,
    'pclk_internal_wns_ns':{'OV1':6.097,'OV2':6.599},
    'drc_error_count':0,'drc_warning_count':6,
    'firmware_rebuilt':False,'firmware_deployed':False,
    'preserved_baseline':baseline,'artifacts':generated,
    'cost':{'usage':'unknown','price':'unknown','savings':'not claimed'},
    'limits':['no measured sensor input/output timing','not the integrated W6 design',
              'no physical camera capture or power validation','startup delay calculation timing violation'],
}
(HERE/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+chr(10),encoding='utf-8')
print('ACCEPTANCE_PASS: pin/clock/pad evidence consistent; baseline XPR/BD/bit/HWH unchanged; timing explicitly NOT CLOSED')
