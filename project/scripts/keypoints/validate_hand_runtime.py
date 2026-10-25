"""Compare actual HLS C kernels executing the WHOLE graph against its integer reference."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from project.board.keypoints.hand_runtime import DLLBackend,HandGraph


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--samples',type=int,default=1)
    parser.add_argument('--layer',action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT) or output==ROOT or output.exists():
        raise ValueError('Use a new workspace directory')
    output.mkdir(parents=True)
    src = ROOT/'project/algo/keypoints'
    tool = Path('F:/APP/Xilinx/Vitis_HLS/2024.1')
    compiler = tool/'tps/mingw/10.0.0/win64.o/nt/bin/g++.exe'
    dll = output/'kp_reference.dll'
    names=['kp_gemm_tile.cpp','kp_vector.cpp','kp_host_bridge.cpp']
    if args.layer:names+=['kp_layer.cpp','kp_layer_bridge.cpp']
    command = [str(compiler),'-O2','-std=c++11','-shared','-static-libgcc','-static-libstdc++',
               '-Wno-unknown-pragmas','-I'+str(tool/'include'),
               *[str(src/name) for name in names],'-o',str(dll)]
    with (output/'compile.log').open('w') as log:
        result = subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError('Host HLS C compile failed; inspect compile.log')
    with np.load(args.model/'probes.npz') as data:
        inputs,expected = data['roi_codes'],data['reference']
    if args.layer:
        sys.path.insert(0,str(ROOT/'project/board/keypoints'))
        from hand_layer_runtime import LayerDLLBackend
        backend=LayerDLLBackend(dll,compiler.parent)
    else:backend = DLLBackend(dll,compiler.parent)
    graph = HandGraph(args.model,backend)
    actual,traces = [],[]
    for i,roi in enumerate(inputs[:args.samples]):
        prediction,trace = graph.run(roi)
        actual.append(prediction)
        traces.append(trace)
        print('WHOLE_GRAPH_ROI_DONE '+str(i),flush=True)
    actual = np.stack(actual)
    diff = np.abs(actual-expected[:len(actual)])
    report = dict(scope='whole_hand_graph_HLS_C_execution_not_board',samples=len(actual),
        max_abs_difference=float(diff.max()),exact_match=bool(np.array_equal(actual,expected[:len(actual)])),
        traces=traces,bitstream_generated=False,board_programmed=False)
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    np.savez(output/'outputs.npz',actual=actual,expected=expected[:len(actual)])
    print(json.dumps({k:v for k,v in report.items() if k!='traces'},indent=2))
    if not report['exact_match']:
        raise RuntimeError('Whole integer graph is not bit-exact; do not deploy')


if __name__=='__main__':
    main()
