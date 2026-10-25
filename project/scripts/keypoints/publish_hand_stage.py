"""Publish small numerical/HLS evidence only; never copy model weights or ROI images to Git."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--w12-model-dir',type=Path,default=ROOT/'project/_tmp/kp_integer_w12a16_v2')
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT) or output==ROOT or output.exists():
        raise ValueError('Use a new workspace output file')
    cache = ROOT/'project/_tmp'
    candidates = []
    for bits in (8,12,16):
        directory = cache/f'kp_integer_w{bits}a16_v1'
        if bits==12:
            directory = args.w12_model_dir
        report = read(directory/'report.json')
        with np.load(directory/'validation.npz') as data:
            expected,actual = data['reference'],data['integer']
            accepted = expected[:,63]>.5
            report['float_presence_accepted_rois'] = int(accepted.sum())
            report['presence_decision_mismatches'] = int(np.count_nonzero(accepted!=(actual[:,63]>.5)))
            report['accepted_coordinate_max_abs_error_roi_units'] = float(np.max(np.abs(expected[accepted,:63]-actual[accepted,:63])))
        candidates.append(report)
    evidence_paths = [cache/'kp_float_real_v1/report.json',cache/'kp_rois_v1/report.json',
                      cache/'kp_tile_hls_v4/report.json']
    snapshot = dict(status='stage1_model_and_MAC_tile_verified_not_PL_landmark_deployed',
        user_approved_scope='single_hand_21_landmarks_first_PC_supplies_ROI',
        float_conversion=read(evidence_paths[0]),
        roi_probes={k:v for k,v in read(evidence_paths[1]).items() if k!='records'},
        integer_candidates=candidates,tile=read(evidence_paths[2]),
        evidence_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in evidence_paths},
        pending=['Independent whole-network C/integer parity, including depthwise/non-MAC operations.',
                 'DDR graph scheduler and model transport; complete AXI integration.',
                 'Full-design implementation/timing and matching bit/hwh.',
                 'Cold-boot deployment and actual ROI-to-landmark latency/accuracy evaluation.'],
        whole_landmark_network_synthesized=False,bitstream_generated=False,board_programmed=False)
    if snapshot['tile']['tool_return_code']!=0 or '|      Pass|' not in snapshot['tile']['cosim_report']:
        raise RuntimeError('Tile co-simulation did not pass')
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Published '+output.relative_to(ROOT).as_posix())


if __name__=='__main__':
    main()
