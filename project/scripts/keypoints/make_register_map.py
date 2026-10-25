"""Parse generated HLS driver headers; never guess AXI-Lite register offsets."""
import argparse
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[3]

def parse(path,prefix):
    text=path.read_text()
    addr=dict(re.findall(r'#define\s+'+prefix+r'_CONTROL_ADDR_(\w+)\s+(0x[0-9a-fA-F]+)',text))
    bits=dict(re.findall(r'#define\s+'+prefix+r'_CONTROL_BITS_(\w+)\s+(\d+)',text))
    result={}
    for key,bit in bits.items():
        name=key[:-5] if key.endswith('_DATA') else key
        result[name.lower()]=dict(offset=int(addr[key],16),bits=int(bit))
    if result.get('ap_return')!={'offset':16,'bits':32}:raise ValueError('Unexpected HLS control ABI')
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--layer-ip',type=Path)
    parser.add_argument('--vector-ip',type=Path)
    parser.add_argument('--vector-capacity',type=int,choices=(4096,65536),default=4096)
    parser.add_argument('--cached',action='store_true')
    args=parser.parse_args()
    output=args.output.resolve()
    if not output.is_relative_to(ROOT) or output.exists():raise ValueError('Use a new workspace output file')
    report={}
    for name,instance,directory,core in [
        ('mac','kp_mac','kp_mac_ip_v1/tile_prj','kp_gemm_tile'),
        ('vector','kp_vector','kp_vector_ip_v1/vector_prj','kp_vector')]:
        ip=ROOT/'project/_tmp'/directory/'solution1/impl/ip'
        if name=='mac' and args.layer_ip:
            core='kp_layer';ip=args.layer_ip
        if name=='vector' and args.vector_ip:ip=args.vector_ip
        header=ip/f'drivers/{core}_v1_0/src/x{core}_hw.h'
        report[name]=dict(instance=instance,registers=parse(header,'X'+core.upper()))
    if args.layer_ip:report['architecture']='whole_layer_v2'
    if args.vector_ip:report['vector_capacity']=args.vector_capacity
    if args.cached:report['layer_variant']='input_cache_v1'
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n')
    print('REGISTER_MAP_READY '+str(output))

if __name__=='__main__':main()
