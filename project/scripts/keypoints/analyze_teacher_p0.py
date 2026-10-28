"""Summarize real teacher profiling without conflating diagnostic CPU modes."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[3]


def stats(values):
    if not values:return None
    return dict(count=len(values),mean=float(np.mean(values)),p50=float(np.percentile(values,50)),
                p95=float(np.percentile(values,95)))


def compatible(kind,tag):
    tag=tag.lower()
    if kind=='CONV_2D':return 'convolution' in tag and 'dwconv' not in tag
    if kind=='DEPTHWISE_CONV_2D':return 'dwconv' in tag or 'depthwise' in tag
    if kind=='ADD':return tag.startswith('add ')
    if kind=='MEAN':return any(x in tag for x in ('mean','average','pooling'))
    if kind=='FULLY_CONNECTED':return 'fully connected' in tag or 'fullyconnected' in tag
    if kind=='LOGISTIC':return 'sigmoid' in tag or 'logistic' in tag
    return False


def analyze(source,output):
    if output.exists() or not output.is_relative_to(ROOT/'project/analysis'):
        raise ValueError('Use a new analysis evidence file')
    report=json.loads((source/'report.json').read_text(encoding='utf-8'))
    if not report['completed'] or report.get('landmark_probe_count',0)<6:
        raise ValueError('Completed real landmark profile required')
    frozen=json.loads((ROOT/'project/_tmp/teacher_partition_frozen_20261028_v1/partition_manifest.json').read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'project/analysis/teacher_partition_20261028/model_inventory.json').read_text(encoding='utf-8'))
    selected={87,90,93,94}
    summaries=[]
    app_candidate_fraction=None
    for model in ('palm','landmark'):
        for mode in ('default','builtin_only'):
            path=source/('diagnostic_%s_%s.json'%(model,mode))
            data=json.loads(path.read_text(encoding='utf-8'))
            rows=[]
            for case in data['cases']:
                events=[e for e in case['events'] if e['type']==(8 if mode=='default' else 2)]
                rows.append(events)
            top={}
            for events in rows:
                for event in events:
                    key=(event['node'],event['tag'])
                    top.setdefault(key,[]).append(event['elapsed_us']/1000)
            summary=dict(model=model,mode=mode,cases=len(rows),
                executed_nodes=len(data['plan']['nodes']),
                delegated_nodes=sum(n['delegated'] for n in data['plan']['nodes']),
                extension_parity_all_outputs=all(d['allclose'] for c in data['cases'] for d in c['output_differences']),
                extension_parity_all_exact=all(d['exact'] for c in data['cases'] for d in c['output_differences']),
                profiled_outputs_allclose=all(c['profiled_outputs_allclose'] for c in data['cases']),
                unprofiled_api_wall_ms=stats([c['unprofiled_abi_wall_ms'] for c in data['cases']]),
                profiler_operator_sum_ms=stats([sum(e['elapsed_us'] for e in events)/1000 for events in rows]),
                top_operators=sorted([dict(node=k[0],tag=k[1],elapsed_ms=stats(v)) for k,v in top.items()],
                                     key=lambda x:x['elapsed_ms']['mean'],reverse=True)[:12])
            if mode=='default' and not (summary['extension_parity_all_outputs'] and summary['profiled_outputs_allclose']):
                raise ValueError('Optimized diagnostic extension failed original output parity')
            if model=='landmark':
                if mode=='builtin_only':
                    times=[sum(e['elapsed_us'] for e in events if e['node'] in selected)/1000 for events in rows]
                    summary['candidate_original_node_ms']=stats(times)
                    summary['candidate_timing_scope']='builtin_diagnostic_only_not_optimized_baseline'
                else:
                    logical=[n for n in inventory['models'][1]['nodes'] if n['op']!='DEQUANTIZE']
                    matches=all(len(events)==len(logical) and
                        all(compatible(n['op'],e['tag']) for n,e in zip(logical,events)) for events in rows)
                    summary['xnn_sequence_mapping']=dict(signature_match=matches,
                        original_nonconstant_ops=len(logical),event_counts=[len(e) for e in rows],
                        caveat='Inferred from equal-length ordered operator signatures; XNN internal IDs are not original TFLite node IDs. Confirm with partition runtime before using as exact hotspot budget.')
                    if matches:
                        times=[sum(e['elapsed_us'] for n,e in zip(logical,events) if n['node'] in selected)/1000 for events in rows]
                        fractions=[t/(sum(e['elapsed_us'] for e in events)/1000) for t,events in zip(times,rows)]
                        summary['candidate_xnn_inferred_ms']=stats(times)
                        summary['candidate_xnn_inferred_fraction']=stats(fractions)
                        app_candidate_fraction=float(np.mean(fractions))
            summaries.append(summary)
    baseline=report['baseline']
    processing_sum=baseline['processing_ms']['mean']*baseline['frames']
    landmark=baseline['landmark_abi_wall_ms']
    ceiling=None
    if app_candidate_fraction is not None:
        f=landmark['mean']*landmark['count']*app_candidate_fraction/processing_sum
        ceiling=dict(estimated_mean_application_fraction=f,
            ideal_mean_speedup_if_block_free=1/(1-f),
            caveat='Inference from diagnostic operator fraction and recorded ABI time, zero offload overhead and unchanged remaining CPU performance; not a measured PL gain or P50/P95 guarantee.')
    result=dict(status='P0_initial_baseline_and_diagnostics_complete_P1_runtime_gate_pending',
        source=source.relative_to(ROOT).as_posix(),scope='PS full teacher; no training, labels or FPGA loading',
        baseline=baseline,display_enabled=report['display_enabled'],
        video_sha256=report['video_sha256'],models_and_runtime=report['models_and_runtime'],
        landmark_probes=report['landmark_probe_count'],palm_probes=report['palm_probe_count'],
        diagnostics=summaries,candidate_ideal_budget=ceiling,
        partition_manifest_canonical_json_sha256=hashlib.sha256(json.dumps(frozen,sort_keys=True).encode()).hexdigest(),
        limitations=['one bounded video and one baseline run, not paired hybrid acceptance',
            'no HDMI output in this baseline','first captured ROI inputs may be temporally correlated',
            'builtin profile is diagnostic, not the optimized baseline',
            'no actual PL or CMA transfer benchmark yet',
            'no complete P1 runtime boundary or P2 delegate validation yet'])
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(output=str(output),baseline=baseline,candidate_ideal_budget=ceiling)))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();analyze(a.source.resolve(),a.output.resolve())


if __name__=='__main__':main()
