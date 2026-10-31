#!/bin/env python3.10

# --- 2026-10-08 network fix v3: restore static IP 192.168.2.99 first ---
import subprocess, traceback
try:
    with open('/boot/net_debug.txt', 'w') as _f:
        _f.write('boot.py netfix start\n')
        _f.flush()
        def _run(cmd):
            _f.write('$ ' + cmd + '\n')
            _f.flush()
            subprocess.call(cmd, stdout=_f, stderr=_f, shell=True,
                            executable='/bin/sh')
        _run('export PATH=/sbin:/usr/sbin:/bin:/usr/bin:$PATH; ip link set eth0 up')
        _run('export PATH=/sbin:/usr/sbin:/bin:/usr/bin:$PATH; ifconfig eth0 192.168.2.99 netmask 255.255.255.0 || ip addr add 192.168.2.99/24 dev eth0')
        _run('export PATH=/sbin:/usr/sbin:/bin:/usr/bin:$PATH; ifconfig -a')
        _run('export PATH=/sbin:/usr/sbin:/bin:/usr/bin:$PATH; ip addr')
        _f.write('done\n')
except Exception:
    try:
        with open('/boot/net_debug_err.txt', 'w') as _f:
            traceback.print_exc(file=_f)
    except Exception:
        pass

# --- 2026-10-17 unified overlay: load kws_hdmi.bit ONCE at boot, never reload ---

# OV1 HDMI: one download only, on a new boot, never run interactively.
import hashlib,json,os
from pathlib import Path
root=Path('/home/xilinx/ov1_hdmi_20261031')
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
plan=json.loads((root/'deployment_plan.json').read_text())
if boot==plan['before']['boot_id']:raise RuntimeError('A new cold startup is required')
attempt=Path('/run/ov1_hdmi_download_attempted')
if attempt.exists():raise RuntimeError('Only one download attempt per boot')
m=json.loads((root/'release/release_manifest.json').read_text())
for kind in ('bit','hwh'):
    f=root/'release'/m['files'][kind]['path']
    if hashlib.sha256(f.read_bytes()).hexdigest()!=m['files'][kind]['sha256']:raise RuntimeError('Paired firmware SHA mismatch')
attempt.write_text(boot)
os.environ['XILINX_XRT']='/usr'
from pynq import Overlay,Clocks
overlay=Overlay(str(root/'release'/m['files']['bit']['path']),download=True)
Clocks.fclk0_mhz=100
for name in ('capture_dma','camera_control','video/axi_vdma'):
    if name not in overlay.ip_dict:raise RuntimeError('Missing OV1 HDMI AXI hardware metadata')
Path('/run/ov1_hdmi_boot.json').write_text(json.dumps(dict(boot_id=boot,bit_sha256=m['files']['bit']['sha256'])))
print('OV1 HDMI loaded ONCE at cold startup; no capture started')
