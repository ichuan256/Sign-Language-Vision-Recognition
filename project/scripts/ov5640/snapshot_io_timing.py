"""Validate specification/measurement-backed pad delay budgets and emit Tcl."""
import argparse
import json
import math
from pathlib import Path

DVP = [f'ov1_data[{i}]' for i in range(8)] + ['ov1_href', 'ov1_vsync']
INPUTS = DVP + ['ov1_sda']
OUTPUTS = ['ov1_scl', 'ov1_sda', 'ov1_reset_n', 'ov1_pwdn']

def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('Timing value must be finite numeric')
    return value

def validate(data):
    if data.get('schema_version') != 1 or data.get('launch_edge') != 'falling':
        raise ValueError('Profile incompatible with falling-edge DVP output')
    if number(data['pclk_period_ns']) <= 0:
        raise ValueError('Invalid PCLK period')
    required = ('evidence', 'input_delays_ns', 'output_delays_ns', 'clock_uncertainty_ns')
    missing = [key for key in required if data.get(key) is None]
    if missing:
        return dict(constrained=False, missing=missing)
    if not isinstance(data['evidence'], str) or not data['evidence'].strip():
        raise ValueError('Timing evidence/reference required')
    if number(data['clock_uncertainty_ns']) < 0:
        raise ValueError('Negative clock uncertainty')
    for key, ports in [('input_delays_ns', INPUTS), ('output_delays_ns', OUTPUTS)]:
        if set(data[key]) != set(ports):
            raise ValueError(f'Exact active port coverage required: {key}')
        for port, item in data[key].items():
            if number(item['min']) > number(item['max']):
                raise ValueError(f'Reversed min/max: {port}')
            if item.get('clock') not in ('ov1_pclk', 'sys_clk'):
                raise ValueError(f'Unknown clock: {port}')
            if port in DVP and item['clock'] != 'ov1_pclk':
                raise ValueError('DVP must be relative to forwarded PCLK')
    return dict(constrained=True, missing=[])

def render(data):
    status = validate(data)
    lines = [f'create_clock -name ov1_pclk -period {data["pclk_period_ns"]} [get_ports ov1_pclk]']
    if not status['constrained']:
        lines.append('puts {EXTERNAL_IO_UNVERIFIED: no fabricated delays applied}')
        return '\n'.join(lines)
    lines.append('set snapshot_sys_clock [get_clocks -of_objects [get_pins system_i/camera/inst/sys_clk]]')
    lines.append('if {[llength $snapshot_sys_clock]!=1} {error {System timing clock missing or ambiguous}}')
    for direction, key in [('input', 'input_delays_ns'), ('output', 'output_delays_ns')]:
        for port, item in data[key].items():
            clk = '[get_clocks ov1_pclk]' if item['clock'] == 'ov1_pclk' else '$snapshot_sys_clock'
            edge = ' -clock_fall' if port in DVP else ''
            for bound in ('min', 'max'):
                lines.append(f'set_{direction}_delay -clock {clk}{edge} -{bound} {item[bound]} [get_ports {{{port}}}]')
    lines.append(f'set_clock_uncertainty {data["clock_uncertainty_ns"]} [get_clocks ov1_pclk]')
    return '\n'.join(lines)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('profile', type=Path)
    p.add_argument('--status', type=Path)
    p.add_argument('--require-complete', action='store_true')
    args = p.parse_args()
    data = json.loads(args.profile.read_text(encoding='utf-8'))
    status = validate(data)
    if args.require_complete and not status['constrained']:
        raise ValueError('External timing profile incomplete: ' + ', '.join(status['missing']))
    if args.status:
        args.status.write_text(json.dumps(status, indent=2), encoding='utf-8')
    print(render(data))

if __name__ == '__main__': main()
