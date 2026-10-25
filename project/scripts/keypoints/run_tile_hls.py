"""Build/test a reusable integer MAC tile, NOT an entire landmark network."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

import numpy as np

ROOT = Path(__file__).resolve().parents[3]


def rounded_shift(value, shift):
    # Independent Python integer reference: signed nearest, ties to even.
    value,shift = int(value),int(shift)
    if shift <= 0:
        result = value << -shift
    else:
        magnitude = abs(value)
        q,r = divmod(magnitude,1<<shift)
        half = 1<<(shift-1)
        q += int(r>half or (r==half and q%2))
        result = -q if value<0 else q
    return min(32767,max(-32768,result))


def vectors():
    rng = np.random.default_rng(20261025)
    result = []
    for m,n,k in [(4,5,19),(16,16,27),(2,16,672),(1,16,1)]:
        a = rng.integers(-32768,32768,(m,k),dtype=np.int64)
        b = rng.integers(-2048,2048,(k,16),dtype=np.int64)
        bias = rng.integers(-2**32,2**32,16,dtype=np.int64)
        shifts = np.array([-31,-8,0,1,2,3,8,12,16,20,24,28,32,40,46,47])
        acc = a@b[:,:n]+bias[:n]
        expected = np.array([[rounded_shift(v,s) for v,s in zip(row,shifts)] for row in acc])
        result.append((m,n,k,a,b,bias,shifts,expected))
    # Explicit negative/positive half-way rounding and saturation cases.
    values = np.array([1,3,5,7,-1,-3,-5,-7,32767,32768,-32768,-32769,0,2**46,-2**46,0],np.int64)
    shifts = np.array([1]*8+[0]*5+[47,47,0])
    expected = np.array([[rounded_shift(v,s) for v,s in zip(values,shifts)]])
    result.append((1,16,1,np.zeros((1,1),np.int64),np.zeros((1,16),np.int64),values,shifts,expected))
    return result


def first_layer_vector(model_dir, roi_file):
    try:
        from .fixed_hand_reference import quantize
    except ImportError:
        from fixed_hand_reference import quantize
    specs = json.loads((model_dir/'graph.json').read_text(encoding='utf-8'))
    inp = next(s for s in specs if s['kind']=='InputLayer')
    conv = next(s for s in specs if s['kind']=='Conv2D')
    with np.load(roi_file) as data:
        roi = data['roi_rgb'][int(data['validation_indices'][0])]
    with np.load(model_dir/'weights.npz') as weights:
        kernel = weights[conv['name']+'_kernel'][...,:16]
        fw = np.array(conv['weight_fraction'])[:16]
        bias,_ = quantize(weights[conv['name']+'_bias_float'][:16],inp['fraction']+fw,48)
    kh,kw,ci,co = kernel.shape
    if co!=16 or conv['padding']!='same' or conv['dilation']!=[1,1]:
        raise ValueError('First-layer probe assumes a 16-column tile from SAME convolution')
    x,_ = quantize(roi,inp['fraction'],16)
    oh,ow = conv['output_shape'][1:3]
    sy,sx = conv['strides']
    py = max(0,(oh-1)*sy+kh-x.shape[0])//2
    px = max(0,(ow-1)*sx+kw-x.shape[1])//2
    patches = []
    for oy in range(2):
        for ox in range(8):
            patch = np.zeros((kh,kw,ci),np.int64)
            for ky in range(kh):
                for kx in range(kw):
                    iy,ix = oy*sy+ky-py,ox*sx+kx-px
                    if 0<=iy<x.shape[0] and 0<=ix<x.shape[1]:
                        patch[ky,kx] = x[iy,ix]
            patches.append(patch.reshape(-1))
    a = np.stack(patches)
    b = kernel.reshape(-1,16).astype(np.int64)
    shift = inp['fraction']+fw-conv['fraction']
    acc = a@b+bias
    expected = np.array([[rounded_shift(v,s) for v,s in zip(row,shift)] for row in acc])
    return (len(a),16,kh*kw*ci,a,b,bias,shift,expected)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--synth',action='store_true')
    parser.add_argument('--cosim',action='store_true',help='Run XSim C/RTL co-simulation after synthesis')
    parser.add_argument('--integer-model',type=Path)
    parser.add_argument('--rois',type=Path)
    parser.add_argument('--vitis-hls',type=Path,default=Path('F:/APP/Xilinx/Vitis_HLS/2024.1/bin/vitis_hls.bat'))
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT) or output==ROOT or output.exists():
        raise ValueError('Use a new workspace output directory')
    output.mkdir(parents=True)
    if bool(args.integer_model)!=bool(args.rois):
        raise ValueError('integer-model and rois must be supplied together')
    with (output/'vectors.txt').open('w',encoding='ascii') as stream:
        cases = vectors()
        if args.integer_model:
            cases.append(first_layer_vector(args.integer_model,args.rois))
        stream.write(str(len(cases))+'\n')
        for m,n,k,*arrays in cases:
            stream.write(f'{m} {n} {k}\n')
            for a in arrays:
                stream.write(' '.join(map(str,np.asarray(a).reshape(-1)))+'\n')
    src = ROOT/'project/algo/keypoints'
    tcl = '\n'.join([
        'open_project {'+(output/'tile_prj').as_posix()+'}',
        'set_top kp_gemm_tile',
        'add_files {'+(src/'kp_gemm_tile.cpp').as_posix()+'} -cflags {-std=c++11}',
        'add_files -tb {'+(src/'kp_gemm_tile_test.cpp').as_posix()+'} -cflags {-std=c++11}',
        'add_files -tb {'+(output/'vectors.txt').as_posix()+'}',
        'open_solution -flow_target vivado solution1',
        'set_part {xc7z020clg400-1}',
        'create_clock -period 10',
        'csim_design -clean',
        'csynth_design' if args.synth or args.cosim else '',
        'cosim_design -rtl verilog -tool xsim -trace_level none' if args.cosim else '',
        'exit',''])
    (output/'build.tcl').write_text(tcl,encoding='utf-8')
    with (output/'console.log').open('w',encoding='utf-8') as log:
        result = subprocess.run(['cmd.exe','/d','/c',str(args.vitis_hls),'-f',str(output/'build.tcl')],
                                cwd=output,stdout=log,stderr=subprocess.STDOUT)
    report = dict(scope='MAC_tile_only_not_hand_landmark_inference',tool_return_code=result.returncode,
                  target='xc7z020clg400-1',clock_target_ns=10,lanes=16,
                  test_cases=len(cases),synthesis_requested=args.synth,
                  bitstream_generated=False,board_programmed=False)
    report['rtl_cosimulation_requested'] = args.cosim
    report['real_first_convolution_probe'] = bool(args.integer_model)
    report['sources_sha256'] = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in src.glob('*') if p.is_file()}
    xml = output/'tile_prj/solution1/syn/report/kp_gemm_tile_csynth.xml'
    if xml.exists():
        tree = ET.parse(xml)
        report['resources'] = {n.tag:n.text for n in tree.findall('.//AreaEstimates/Resources/*')}
        report['timing_estimate'] = {n.tag:n.text for n in tree.findall('.//PerformanceEstimates/SummaryOfTimingAnalysis/*')}
    csim = output/'tile_prj/solution1/csim/report/kp_gemm_tile_csim.log'
    if csim.exists():
        report['csim_log_tail'] = csim.read_text(encoding='utf-8',errors='replace').splitlines()[-5:]
    cosim = output/'tile_prj/solution1/sim/report/kp_gemm_tile_cosim.rpt'
    if cosim.exists():
        report['cosim_report'] = cosim.read_text(encoding='utf-8',errors='replace')
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    if result.returncode:
        raise RuntimeError('HLS failed; inspect console.log')


if __name__=='__main__':
    main()
