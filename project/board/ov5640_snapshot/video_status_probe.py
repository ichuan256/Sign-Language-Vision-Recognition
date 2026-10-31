"""Read-only diagnostic GPIO sampling; never configure video or download a bit."""
import argparse
import hashlib
import json
import time
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--samples',type=int,default=16)
    args=parser.parse_args()
    if not 2<=args.samples<=100:parser.error('samples must be between 2 and 100')
    root=args.manifest.resolve().parent
    manifest=json.loads(args.manifest.read_text())
    spec=manifest['design']['video_status']
    assert spec['ip']=='video_status_gpio' and spec['base']==0x41210000
    assert spec['status_offset']==0 and spec['flags_offset']==8 and spec['cdc_stages']==4
    assert spec['bus_coherent'] is False and len(spec['flags'])==8
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    marker=json.loads(Path('/run/ov1_hdmi_boot.json').read_text())
    assert marker['boot_id']==boot and marker['bit_sha256']==manifest['files']['bit']['sha256']
    files={}
    for kind in ('bit','hwh'):
        item=manifest['files'][kind];path=(root/item['path']).resolve()
        assert path.parent==root and path.suffix=='.'+kind
        assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']
        files[kind]=path
    assert files['bit'].with_suffix('.hwh')==files['hwh']
    from pynq import Overlay,MMIO
    overlay=Overlay(str(files['bit']),download=False)
    ip=overlay.ip_dict[spec['ip']]
    assert ip['phys_addr']==spec['base']
    assert int(ip['parameters']['C_ALL_INPUTS'])==1 and int(ip['parameters']['C_ALL_INPUTS_2'])==1
    mmio=MMIO(spec['base'],65536)
    samples=[]
    for _ in range(args.samples):
        status=mmio.read(0);flags=mmio.read(8)&255
        samples.append(dict(monotonic_s=time.monotonic(),status=hex(status),state_bits=hex(status&0x1fff),
            VTG_lag=status>>16,flags=flags,**{name:bool(flags&(1<<index)) for index,name in enumerate(spec['flags'])}))
        time.sleep(.05)
    stable={name:all(s[name]==samples[0][name] for s in samples) for name in spec['flags']}
    print(json.dumps(dict(boot_id=boot,bit_sha256=marker['bit_sha256'],samples=samples,stable_flags=stable,
        downloaded=False,video_reconfigured=False,DMA_touched=False,bus_coherent=False,
        note='Independent synchronized bits; compare repeated stable states, not atomic multi-bit transitions')))


if __name__=='__main__':main()
