"""Independent integer layer vectors, HLS C/RTL validation and IP export."""
import argparse,json,subprocess,hashlib
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
try:
    from .run_tile_hls import rounded_shift
except ImportError:
    from run_tile_hls import rounded_shift
ROOT=Path(__file__).resolve().parents[3]

def cases():
    rng=np.random.default_rng(20261026)
    for ih,iw,ci,co,k,stride,dw,relu,rs,limit in [
        (5,7,3,17,3,2,0,1,-3,3072),(3,4,17,9,1,1,0,0,0,-1),
        (5,5,17,17,5,2,1,1,-2,6144),(3,4,3,3,3,1,1,0,0,-1),
        (1,1,672,63,1,1,0,0,0,-1),(2,3,16,16,1,1,0,1,2,100),
        (2,2,16,16,3,1,1,1,0,-1),
        (9,7,17,17,5,1,1,1,-2,6144),(9,7,3,17,3,1,0,1,-3,3072),
        (9,14,64,64,3,2,1,1,-2,6144)]:
        oh,ow=(ih+stride-1)//stride,(iw+stride-1)//stride
        py,px=max(0,(oh-1)*stride+k-ih)//2,max(0,(ow-1)*stride+k-iw)//2
        cfg=[ih,iw,ci,oh,ow,co,k,k,stride,stride,py,px,dw,relu,rs,limit]
        a=rng.integers(-32768,32768,(ih,iw,ci),dtype=np.int64)
        b=rng.integers(-2048,2048,(k,k,1 if dw else ci,co),dtype=np.int64)
        bias=rng.integers(-2**30,2**30,co,dtype=np.int64)
        shift=np.resize(np.array([-31,0,1,8,12,20,32,47]),co)
        gold=np.zeros((oh,ow,co),np.int16)
        for y in range(oh):
            for x in range(ow):
                acc=[int(v) for v in bias]
                for ky in range(k):
                    for kx in range(k):
                        iy,ix=y*stride+ky-py,x*stride+kx-px
                        if 0<=iy<ih and 0<=ix<iw:
                            for c in range(co):
                                acc[c]+=int(a[iy,ix,c])*int(b[ky,kx,0,c]) if dw else sum(int(a[iy,ix,j])*int(b[ky,kx,j,c]) for j in range(ci))
                for c in range(co):
                    value=rounded_shift(acc[c],shift[c])
                    if relu:value=rounded_shift(min(limit,max(0,value)) if limit>=0 else max(0,value),rs)
                    gold[y,x,c]=value
        yield cfg,(a,b,bias,shift,gold)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--export-ip',action='store_true');p.add_argument('--cached',action='store_true')
    p.add_argument('--wide',action='store_true');p.add_argument('--stream',action='store_true')
    a=p.parse_args();out=a.output.resolve()
    if a.stream:a.wide=True
    if a.wide:a.cached=True
    if out.exists() or not out.is_relative_to(ROOT/'project/_tmp'):raise ValueError('New project/_tmp output required')
    out.mkdir(parents=True);data=list(cases())
    with (out/'layer_cases.txt').open('w') as f:
        f.write(str(len(data))+'\n')
        for cfg,arrays in data:
            f.write(' '.join(map(str,cfg))+'\n')
            for array in arrays:f.write(' '.join(map(str,array.reshape(-1)))+'\n')
    src=ROOT/'project/algo/keypoints'
    source=src/('kp_layer_cached.cpp' if a.cached else 'kp_layer.cpp')
    flags='-std=c++11'+(' -DKP_WIDE=1' if a.wide else '')+(' -DKP_STREAM=1' if a.stream else '')
    tcl=['open_project {'+(out/'layer_prj').as_posix()+'}','set_top kp_layer',
         'add_files {'+source.as_posix()+'} -cflags {'+flags+'}',
         'add_files -tb {'+(src/'kp_layer_test.cpp').as_posix()+'} -cflags {-std=c++11}',
         'add_files -tb {'+(out/'layer_cases.txt').as_posix()+'}',
         'open_solution -flow_target vivado solution1','set_part {xc7z020clg400-1}','create_clock -period 10',
         'config_interface -m_axi_alignment_byte_size 64 -m_axi_max_widen_bitwidth 128' if a.wide else '',
         'csim_design -clean','csynth_design','cosim_design -rtl verilog -tool xsim -trace_level none']
    if a.export_ip:tcl+=['export_design -format ip_catalog -rtl verilog']
    (out/'build.tcl').write_text('\n'.join(tcl+['exit','']))
    with (out/'console.log').open('w') as log:
        result=subprocess.run(['cmd.exe','/d','/c','F:/APP/Xilinx/Vitis_HLS/2024.1/bin/vitis_hls.bat','-f',str(out/'build.tcl')],cwd=out,stdout=log,stderr=subprocess.STDOUT)
    report=dict(scope='whole_layer_kernel_not_board',return_code=result.returncode,cases=len(data))
    report['cached']=a.cached
    report.update(wide=a.wide,stream=a.stream,compile_flags=flags)
    report['sources_sha256']={path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in
        (source,src/'kp_layer.hpp',src/'kp_layer_test.cpp',src/'kp_layer_math.hpp',src/'kp_layer_stream.hpp')}
    xml=out/'layer_prj/solution1/syn/report/kp_layer_csynth.xml'
    if xml.exists():
        tree=ET.parse(xml);report['resources']={n.tag:n.text for n in tree.findall('.//AreaEstimates/Resources/*')}
    cosim=out/'layer_prj/solution1/sim/report/kp_layer_cosim.rpt'
    if cosim.exists():report['cosim']=cosim.read_text()
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    if result.returncode:raise RuntimeError('Layer HLS failed; inspect console.log')
if __name__=='__main__':main()
