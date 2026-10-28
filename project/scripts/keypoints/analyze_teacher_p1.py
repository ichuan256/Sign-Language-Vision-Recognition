"""Audit P1 CPU parity and estimate an explicit, non-measured offload budget."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from run_teacher_p0 import ROOT
from analyze_teacher_p0 import compatible, stats


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def analyze(a):
    if a.output.exists() or not a.output.resolve().is_relative_to(ROOT/'project/analysis'):
        raise ValueError('New analysis file required')
    post=read(a.postprocess/'report.json'); boundary=read(a.boundary/'report.json')
    transfer=read(a.transfer/'report.json')
    before=read(a.before/'board_inventory.json'); after=read(a.after/'board_inventory.json')
    if not all(r['completed'] for r in (post,boundary,transfer)):
        raise ValueError('All bounded diagnostics must complete')
    if before['boot_id']!=after['boot_id'] or before['files']!=after['files'] or before['firmware_files']!=after['firmware_files']:
        raise ValueError('Original board artifacts or boot changed')
    def services(inv):
        return sorted((p['pid'],tuple(p['scripts'])) for p in inv['processes']
                      if any(s in ('button_watch.py','hdmi_display.py') for s in p['scripts']))
    if services(before)!=services(after):
        raise ValueError('Existing service PID changed')
    pairs=[]
    fast_rows=[]
    for pair in post['pairs']:
        r=pair['round']
        original=read(a.postprocess/('frames_%d_original.json'%r))
        fast=read(a.postprocess/('frames_%d_fast.json'%r))
        if len(original)!=pair['frames'] or len(fast)!=pair['frames'] or not all(
            x['frame']==y['frame'] and x['behavior_sha256']==y['behavior_sha256']
            for x,y in zip(original,fast)):
            raise ValueError('Full autonomous behavior mismatch')
        old=stats([x['processing_ms'] for x in original]); new=stats([x['processing_ms'] for x in fast])
        pairs.append(dict(round=r,frames=len(fast),exact_all_inputs_outputs_and_tracking=True,
            original_ms=old,optimized_ms=new,mean_speedup=old['mean']/new['mean'],
            p50_reduction=1-new['p50']/old['p50'],p95_reduction=1-new['p95']/old['p95']))
        fast_rows.append(fast)
    if len(boundary['cases'])!=100 or not all(d['allclose'] for c in boundary['cases'] for d in c['original_output_differences']):
        raise ValueError('100 real boundary cases required')
    node_plan=boundary['full_boundary_execution']['nodes']
    if len(node_plan)!=1 or node_plan[0]['custom']!='TfLiteXNNPackDelegate' or not all(t in node_plan[0]['outputs'] for t in (134,138,142)):
        raise ValueError('Boundary capture did not use expected XNNPACK output bindings')
    p0=read(ROOT/'project/_tmp/teacher_p0_baseline_20261028_v1/diagnostic_landmark_default.json')
    inventory=read(ROOT/'project/analysis/teacher_partition_20261028/model_inventory.json')
    logical=[n for n in inventory['models'][1]['nodes'] if n['op']!='DEQUANTIZE']
    events=[[e for e in c['events'] if e['type']==8] for c in p0['cases']]
    if not all(len(row)==len(logical) and all(compatible(n['op'],e['tag']) for n,e in zip(logical,row)) for row in events):
        raise ValueError('Original-node/XNN event signature changed')
    candidates=[]
    frozen=read(ROOT/'project/analysis/teacher_partition_20261028/partition_manifest.json')
    original_parameters={x['tensor']:x['fp32_sha256'] for x in frozen['constants']}
    for candidate in boundary['manifest']['candidates']:
        name=candidate['name']; selected=set(candidate['selected_nodes'])
        parameters={x['tensor']:x['fp32_sha256'] for x in candidate['parameters']}
        if any(parameters.get(t)!=sha for t,sha in original_parameters.items()):
            raise ValueError('Replay parameters differ from frozen original constants')
        differences=[c['replays'][name]['difference'] for c in boundary['cases']]
        if not all(d['allclose'] for d in differences):
            raise ValueError('Independent replay failed')
        timing=stats([sum(e['elapsed_us']/1000 for n,e in zip(logical,row) if n['node'] in selected) for row in events])
        cpu=timing['mean']
        ceilings=[]
        for rows in fast_rows:
            original=np.asarray([x['processing_ms'] for x in rows])
            calls=np.asarray([len(x['landmark_ms']) for x in rows])
            def projected(cost):
                return original-calls*(cpu-cost)
            free=projected(0.)
            baseline50=float(np.percentile(original,50))
            # Hypothetical constant per-ROI offload cost, same remaining CPU
            # behavior and invocation counts. This is a sensitivity budget,
            # not a measured timing or guaranteed P50/P95 bound.
            low,high=0.,cpu
            feasible=float(np.percentile(free,50))<=.95*baseline50
            for _ in range(50):
                mid=(low+high)/2
                if float(np.percentile(projected(mid),50))<=.95*baseline50:
                    low=mid
                else:
                    high=mid
            ceilings.append(dict(estimated_average_application_fraction=float(calls.sum()*cpu/original.sum()),
                free_block_mean_speedup=float(original.sum()/free.sum()),
                free_block_projected_p50_reduction=1-float(np.percentile(free,50))/baseline50,
                max_total_offload_ms_for_5percent_p50=low if feasible else None))
        mac=sum(n['conv_mac'] for n in logical if n['node'] in selected)
        candidates.append(dict(name=name,nodes=candidate['selected_nodes'],input_tensor=candidate['input_tensor'],
            output_tensor=candidate['output_tensor'],boundary_bytes=candidate['boundary_bytes'],
            parameter_bytes=candidate['parameter_bytes'],conv_mac=mac,
            independent_CPU_replay_ms=boundary['cpu_replay_abi_ms'][name],
            replay_all_exact=all(d['exact'] for d in differences),replay_max_abs=max(d['max_abs'] for d in differences),
            xnn_original_graph_inferred_ms=timing,projected_budgets=ceilings,
            arithmetic_lower_bound_100MHz_ms={str(lanes):mac/(lanes*100e6)*1000 for lanes in (4,8,16)},
            arithmetic_caveat='Ideal one FP32 MAC per lane per cycle; no measured HLS II, memory, driver, or partition overhead. Not a resource or performance prediction.'))
    source_paths=[a.postprocess/'report.json',a.boundary/'report.json',a.transfer/'report.json',
                  a.before/'board_inventory.json',a.after/'board_inventory.json']
    result=dict(status='postprocess_validated_P1_boundaries_replayed_hardware_net_gain_unproven',
        scope='original_teacher_CPU_optimization_and_partial_PL_feasibility_no_training',
        paired_runs=pairs,
        cached_postprocess=dict(cases=len(post['cached']),all_exact=all(c['exact'] for c in post['cached']),
            original_ms=stats([v for c in post['cached'] for v in c['original_ms']]),
            optimized_ms=stats([v for c in post['cached'] for v in c['fast_ms']])),
        boundary_capture=dict(cases=len(boundary['cases']),tensors=[134,138,142],
            original_four_outputs_all_exact=all(d['exact'] for c in boundary['cases'] for d in c['original_output_differences']),
            execution_plan=node_plan,source= a.boundary.relative_to(ROOT).as_posix()),
        runtime_boundary_files=[{k:c[k] for k in ('input','input_archive_sha256','boundary_file','boundary_file_sha256')}
                                for c in boundary['cases']],
        candidates=candidates,cma_host= {k:v for k,v in transfer.items() if k!='samples'},
        board_invariants=dict(boot_unchanged=True,models_runtime_sources_unchanged=True,
            firmware_file_hashes_unchanged=True,display_button_pids_unchanged=True,
            caveat='File hashes do not prove loaded FPGA identity; no reprogramming performed'),
        artifacts=[dict(file=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in source_paths],
        limitations=['P0 XNN node mapping is inferred by ordered signatures, not an instrumented partition',
            'CPU replay artifacts are diagnostic subsets, not deployed replacement models',
            'CMA benchmark excludes PL AXI traffic, accelerator, driver and XNNPACK repartition cost',
            'One video, two alternating pairs of 120 frames, no HDMI writes or general accuracy claim',
            'No actual PL accelerator, new firmware, full hybrid gate or 10-minute stability validation'])
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=result['status'],candidates=[dict(name=c['name'],cpu_ms=c['xnn_original_graph_inferred_ms'],
        budgets=c['projected_budgets']) for c in candidates],cma_host_ms=transfer['timing']['total_host_ms'])))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('postprocess','boundary','transfer','before','after','output'):
        p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args()
    for name,value in vars(args).items():
        setattr(args,name,value.resolve())
    analyze(args)
