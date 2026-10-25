"""Validate/export non-MAC neural operators. No board programming."""
import argparse
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
import numpy as np
try:
    from .run_tile_hls import rounded_shift
except ImportError:
    from run_tile_hls import rounded_shift

ROOT=Path(__file__).resolve().parents[3]

def cases():
    rng=np.random.default_rng(20261025)
    result=[]
    lut=np.rint(32768/(1+np.exp(-np.arange(-512,513)/64))).astype(int)
    for op,shift,alpha,beta,limit,kernel in [(0,12,4,2,-1,1),(1,3,0,0,100,1),
        (2,-2,0,0,-1,4),(3,3,0,0,-1,49),(3,-3,0,0,-1,49),
        (4,8,0,0,-1,1),(4,-6,1,0,-1,1),(5,-2,0,0,-1,1)]:
        n=257
        a=rng.integers(-32768,32768,(n,kernel),dtype=np.int64)
        b=rng.integers(-32768,32768,n,dtype=np.int64)
        output=[]
        for i in range(n):
            value=int(a[i,0])
            if op==0: y=rounded_shift((value<<alpha)+(int(b[i])<<beta),shift)
            elif op==1: y=rounded_shift(min(limit,max(0,value)),shift)
            elif op==2: y=rounded_shift(int(a[i].max()),shift)
            elif op==3:
                total=int(a[i].sum()); sign=-1 if total<0 else 1
                numerator,denominator=abs(total),49
                if shift<0:numerator<<=-shift
                else:denominator<<=shift
                q,r=divmod(numerator,denominator)
                q+=int(2*r>denominator or (2*r==denominator and q%2))
                y=max(-32768,min(32767,sign*q))
            elif op==4:
                index=min(512,max(-512,rounded_shift(value,shift)))+512
                y=rounded_shift(int(lut[index]),alpha)
            else:y=rounded_shift(value,shift)
            output.append(y)
        result.append((n,op,shift,alpha,beta,limit,kernel,a,b,np.array(output)))
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--export-ip',action='store_true')
    args=parser.parse_args()
    out=args.output.resolve()
    if not out.is_relative_to(ROOT) or out==ROOT or out.exists():raise ValueError('Use a new workspace output')
    out.mkdir(parents=True)
    with (out/'vector_cases.txt').open('w') as f:
        data=cases();f.write(str(len(data))+'\n')
        for n,op,shift,alpha,beta,limit,kernel,a,b,y in data:
            f.write(f'{n} {op} {shift} {alpha} {beta} {limit} {kernel} {a.size}\n')
            for x in (a,b,y):f.write(' '.join(map(str,x.reshape(-1)))+'\n')
    src=ROOT/'project/algo/keypoints'
    tcl='\n'.join(['open_project {'+(out/'vector_prj').as_posix()+'}',
        'set_top kp_vector','add_files {'+(src/'kp_vector.cpp').as_posix()+'} -cflags {-std=c++11}',
        'add_files -tb {'+(src/'kp_vector_test.cpp').as_posix()+'} -cflags {-std=c++11}',
        'add_files -tb {'+(out/'vector_cases.txt').as_posix()+'}',
        'open_solution -flow_target vivado solution1','set_part {xc7z020clg400-1}','create_clock -period 10',
        'csim_design -clean','csynth_design','cosim_design -rtl verilog -tool xsim -trace_level none',
        'export_design -format ip_catalog -rtl verilog' if args.export_ip else '','exit',''])
    (out/'build.tcl').write_text(tcl,encoding='utf-8')
    tool='F:/APP/Xilinx/Vitis_HLS/2024.1/bin/vitis_hls.bat'
    with (out/'console.log').open('w') as log:
        result=subprocess.run(['cmd.exe','/d','/c',tool,'-f',str(out/'build.tcl')],cwd=out,stdout=log,stderr=subprocess.STDOUT)
    report=dict(scope='non_MAC_neural_ops',return_code=result.returncode,test_cases=len(data),board_programmed=False)
    xml=out/'vector_prj/solution1/syn/report/kp_vector_csynth.xml'
    if xml.exists():
        tree=ET.parse(xml)
        report['resources']={n.tag:n.text for n in tree.findall('.//AreaEstimates/Resources/*')}
        report['timing']={n.tag:n.text for n in tree.findall('.//PerformanceEstimates/SummaryOfTimingAnalysis/*')}
    cosim=out/'vector_prj/solution1/sim/report/kp_vector_cosim.rpt'
    if cosim.exists():report['cosim']=cosim.read_text()
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    if result.returncode:raise RuntimeError('Vector HLS failed; inspect console.log')

if __name__=='__main__':main()
