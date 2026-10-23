#!/bin/env python3.10
# boot_netfix_only.py - network fix ONLY (no overlay load), for A/B base.bit test
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
        _f.write('done\n')
except Exception:
    try:
        with open('/boot/net_debug_err.txt', 'w') as _f:
            traceback.print_exc(file=_f)
    except Exception:
        pass
print('netfix-only boot.py done (no overlay load)')
