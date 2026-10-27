"""Structural acceptance for the Pmod SPI source change."""
from pathlib import Path
import hashlib
import json
import re
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BEFORE = HERE / 'before'
bd = Path('project/fpga/project/glove/glove.srcs/sources_1/bd/system/system.bd')
old = json.loads((BEFORE / bd).read_text(encoding='utf-8-sig'))['design']
new = json.loads((ROOT / bd).read_text(encoding='utf-8-sig'))['design']
spi = {bus + suffix for bus in ('spia_', 'spib_')
       for suffix in ('sclk', 'mosi', 'miso', 'cs')}
assert set(old['ports']) - set(new['ports']) == spi
assert not (set(new['ports']) - set(old['ports']))
assert all(new['ports'][p] == old['ports'][p] for p in new['ports'])
assert new['interface_ports'] == old['interface_ports']
assert new['components'] == old['components']
assert all(new.get(k) == old.get(k) for k in old
           if k not in {'ports', 'nets', 'design_info'})
assert set(new['nets']['const_zero_dout']['ports']) == (
    set(old['nets']['const_zero_dout']['ports']) | {'sif_l/miso', 'sif_r/miso'})
assert new['components']['const_zero']['parameters']['CONST_VAL']['value'] == '0'
removed = {k for k, v in old['nets'].items() if spi & set(v['ports'])}
assert len(removed) == 8 and set(old['nets']) - set(new['nets']) == removed
assert all(new['nets'][k] == v for k, v in old['nets'].items()
           if k not in removed | {'const_zero_dout'})
assert not any(p in json.dumps(new) for p in ('spia_', 'spib_'))
active = lambda s: [line.strip() for line in s.splitlines()
                    if line.strip() and not line.lstrip().startswith('#')]
master = Path('project/fpga/xdc/sign_glove_master.xdc')
old_xdc = active((BEFORE / master).read_text(encoding='utf-8-sig'))
new_xdc = active((ROOT / master).read_text(encoding='utf-8-sig'))
removed_xdc = [x for x in old_xdc if 'spia_' in x or 'spib_' in x]
assert len(removed_xdc) == 12
assert new_xdc == [x for x in old_xdc if x not in removed_xdc]
timing = Path('project/fpga/xdc/w6_interfaces.xdc')
old_timing = (BEFORE / timing).read_text(encoding='utf-8-sig')
new_timing = (ROOT / timing).read_text(encoding='utf-8-sig')
anchor = '# PYNQ audio core:'
assert old_timing[old_timing.index(anchor):] == new_timing[new_timing.index(anchor):]
assert not any(x in new_timing for x in ('spia_', 'spib_'))
pmod = {'Y18','Y19','Y16','Y17','U18','U19','W18','W19',
        'W14','Y14','T11','T10','V16','W16','V12','W13'}
# Camera candidates have separate pin constraints; inspect only W6 constraints.
for xdc in (ROOT / master, ROOT / timing):
    for line in active(xdc.read_text(encoding='utf-8-sig')):
        match = re.search('PACKAGE_PIN +([A-Z]+[0-9]+)', line)
        assert not match or match[1] not in pmod, (str(xdc), line)
wrapper_path = ROOT / 'project/fpga/project/glove/glove.srcs/sources_1/imports/hdl/system_wrapper.v'
generated_path = ROOT / 'project/fpga/project/glove/glove.gen/sources_1/bd/system/hdl/system_wrapper.v'
wrapper = wrapper_path.read_text(encoding='utf-8')
assert not any(x in wrapper for x in ('spia_', 'spib_'))
assert wrapper_path.read_bytes() == generated_path.read_bytes()
assert all(x in wrapper for x in ('hdmi_out', 'bclk', 'sdata_i', 'sdata_o',
                                  'DDR_addr', 'FIXED_IO_mio', 'btn', 'IIC_1'))
for name in ('w6_hdmi_build.tcl', 'w6_timing_inspect.tcl'):
    script = (ROOT / 'project/fpga/scripts' / name).read_text(encoding='utf-8')
    assert not any('get_ports' in x and ('spia_' in x or 'spib_' in x)
                   for x in script.splitlines())
for name in ('w6_hdmi_bd.tcl', 'w6_timing_prepare.tcl'):
    assert 'w6_release_pmod_spi.tcl' in (
        ROOT / 'project/fpga/scripts' / name).read_text(encoding='utf-8')
expected = {
    'kws_hdmi.bit': '8ecb4eb10b1f11c22bd8e8a3505e4fb1c42b9fe23e8ba4bfdb4a1ebe6e878a00',
    'kws_hdmi.hwh': 'd84e1dfdcd35ea6a29ffab658e8e086ce8fd9455a49d0d8c44d6fe42d5b4d3e5',
}
for name, digest in expected.items():
    rel = 'project/board/w6/' + name
    assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == digest
    assert hashlib.sha256(subprocess.check_output(
        ['git', 'show', 'HEAD:' + rel], cwd=ROOT)).hexdigest() == digest
result = {
    'status': 'PASS', 'removed_bd_port_groups': 8, 'removed_pin_assignments': 12,
    'removed_external_nets': 8, 'retained_interfaces': ['HDMI', 'audio/IIC_1', 'DDR', 'FIXED_IO', 'buttons'],
    'retained_components_and_other_connections': 'identical to original',
    'miso_inputs': 'both tied to const_zero', 'pmod_signal_pins_unassigned_in_w6_xdc': 16,
    'audio_and_hdmi_timing': 'identical to original',
    'tracked_wrapper': 'identical to new generated wrapper; no SPI ports',
    'published_firmware_sha256_unchanged': expected,
    'vivado_2024_1': {'validate_bd_design_exit_code': 0, 'make_wrapper_exit_code': 0,
                     'repeated_release_hook_exit_code': 0},
    'not_run': ['synthesis', 'implementation', 'bitstream generation', 'deployment', 'board test'],
}
(HERE / 'verification.json').write_text(json.dumps(result, indent=2) + chr(10), encoding='utf-8')
print(json.dumps(result, indent=2))
