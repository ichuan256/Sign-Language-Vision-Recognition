"""Publish compact measured evidence, excluding model weights/media/local network."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[3]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,required=True)
    p.add_argument('--result',type=Path,required=True)
    p.add_argument('--hdmi',type=Path,required=True)
    p.add_argument('--screen-confirmed',action='store_true',help='Only after explicit physical screen confirmation')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists() or not a.output.resolve().is_relative_to(ROOT):raise ValueError('Use a new workspace output file')
    board=json.loads((a.result/'report.json').read_text())
    alignment=json.loads((a.result/'alignment.json').read_text())
    hdmi=json.loads((a.hdmi/'report.json').read_text())
    if not board['completed'] or not alignment['exact_match'] or not hdmi['valid_run']:
        raise RuntimeError('Board numeric/HDMI gate missing')
    resource=(a.build/'utilization_routed.rpt').read_text()
    used={}
    for label,key in [('Slice LUTs','lut'),('Slice Registers','ff'),('Block RAM Tile','bram36_tiles'),('DSPs','dsp')]:
        match=re.search(r'\| '+re.escape(label)+r'\s*\|\s*(\d+)\s*\|\s*0\s*\|\s*0\s*\|\s*(\d+)',resource)
        if not match:raise RuntimeError('Resource report format changed: '+label)
        used[key]=dict(used=int(match[1]),available=int(match[2]))
    timing=(a.build/'timing_routed.rpt').read_text()
    match=re.search(r'WNS\(ns\).*?\n\s*[- ]+\n\s*([-\d.]+)\s+([-\d.]+)\s+\d+\s+\d+\s+([-\d.]+)\s+([-\d.]+)',timing)
    if not match:raise RuntimeError('Timing report format changed')
    wns,tns,whs,ths=map(float,match.groups())
    if min(wns,whs)<0 or tns or ths:raise RuntimeError('Timing gate failed')
    totals=defaultdict(float)
    for layer in board['trace']:totals[layer['kind']]+=layer['seconds']
    data=dict(scope='single_hand_21_points_PL_graph_PC_supplied_ROI',tool='Vivado/Vitis HLS 2024.1',
        device='xc7z020clg400-1',clock_mhz=100,activation_bits=16,weight_bits=12,accumulator_bits=48,
        board_samples=1,outputs_per_sample=64,integer_reference_exact_match=alignment['exact_match'],
        max_abs_difference=alignment['max_abs_difference'],cpu_neural_fallback=False,
        input_sha256=alignment['input_sha256'],output_sha256=alignment['output_sha256'],
        artifacts={suffix:dict(sha256=alignment[suffix+'_sha256']) for suffix in ('bit','hwh')},
        resources=used,timing_ns=dict(wns=wns,tns=tns,whs=whs,ths=ths),
        latency_s=dict(board_forward=board['elapsed_s'],setup_and_model_load=board['wall_with_setup_s']-board['elapsed_s'],
            board_with_setup=board['wall_with_setup_s'],ssh_request=alignment['ssh_request_wall_s']),
        layer_group_wall_s=dict(totals),mac_calls=board['mac_calls'],vector_calls=board['vector_calls'],
        hand_presence=board['hand_presence'],coordinates_roi_units=board['coordinates_roi_units'],
        cold_boot_confirmed=True,overlay_downloaded_by_test=False,
        hdmi=dict(static_ROI=True,frame_writes_confirmed_at_least=hdmi['frame_writes_confirmed_at_least'],
            receiver_bounded_seconds=hdmi['receiver_bounded_seconds'],screen_visually_confirmed=a.screen_confirmed,
            confirmation='User explicitly confirmed ROI and skeleton overlay normal' if a.screen_confirmed else None),
        limitations=['One ROI hardware numeric test; not annotated landmark accuracy or arbitrary-video generalization',
            'PS schedules and packs tensors; forward wall time includes this overhead and DDR transfers',
            'Not real time; no camera/video decode/automatic ROI/body/both-hands included',
            'Routed methodology retains TIMING-18 I/O budgets and vendor LUTAR/control-set warnings'],
        evidence_dirs=[str(path.relative_to(ROOT)) if path.is_absolute() else path.as_posix() for path in (a.build,a.result,a.hdmi)])
    a.output.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    print('Published',a.output)

if __name__=='__main__':main()
