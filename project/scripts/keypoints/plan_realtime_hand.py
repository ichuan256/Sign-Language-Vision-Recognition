"""Read-only model analysis and untrained student workload budget, never a speed claim."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT=Path(__file__).resolve().parents[3]


def student_layers(spec,size):
    h=w=size;channels=spec['input_channels'];layers=[]
    def conv(name,co,k,stride,depthwise=False):
        nonlocal h,w,channels
        ih,iw,ci=h,w,channels
        h=math.ceil(h/stride);w=math.ceil(w/stride)
        weights=k*k*ci if depthwise else k*k*ci*co
        layers.append(dict(name=name,kind='DepthwiseConv2D' if depthwise else 'Conv2D',
            input_shape=[ih,iw,ci],output_shape=[h,w,co],kernel_values=weights,
            bias_values=co,macs=h*w*weights))
        channels=co
    stem=spec['stem'];conv('stem',stem['channels'],stem['kernel'],stem['stride'])
    for i,block in enumerate(spec['separable_blocks']):
        conv(f'dw_{i}',channels,block['kernel'],block['stride'],True)
        conv(f'pw_{i}',block['channels'],1,1)
    outputs=sum(spec['outputs'].values());depth=h*w*channels
    layers.append(dict(name='coordinate_presence_handedness_head',kind='Dense',
        input_shape=[depth],output_shape=[outputs],kernel_values=depth*outputs,
        bias_values=outputs,macs=depth*outputs))
    return layers


def summarize_candidate(spec,size,old_macs,old_ms,clock_mhz,lanes):
    layers=student_layers(spec,size)
    macs=sum(s['macs'] for s in layers);weights=sum(s['kernel_values'] for s in layers)
    peak=max(math.prod(s['output_shape']) for s in layers)
    # Capacity lower bounds; exclude channel padding, FIFO, line buffers and double buffering.
    peak_pair=max(math.prod(s['input_shape'])+math.prod(s['output_shape']) for s in layers)
    return dict(input_size=size,trained=False,accuracy_measured=False,board_measured=False,
        layers=layers,learned_layers=len(layers),macs_per_ROI=macs,kernel_values=weights,
        kernel_bytes_at_W8=weights,largest_activation_bytes_at_A8=peak,
        largest_adjacent_tensor_pair_bytes_at_A8=peak_pair,
        operation_reduction=old_macs/macs,
        arithmetic_only_floor_ms=macs/(clock_mhz*1000*lanes),
        same_effective_MAC_rate_heuristic_ms=old_ms*macs/old_macs,
        caveats=['Heuristic is not an HLS latency or board FPS prediction',
            'No trained accuracy, detector cost, memory stalls, pipeline fill, quantization or display cost measured',
            'Activation capacity excludes padding, banking, FIFOs, line buffers and double buffering'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--graph',type=Path,required=True)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--student',type=Path,default=ROOT/'project/algo/keypoints/hand_student_v1.json')
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();out=args.output.resolve()
    if out.exists() or not out.is_relative_to(ROOT):raise ValueError('New workspace output directory required')
    graph=json.loads(args.graph.read_text());baseline=json.loads(args.baseline.read_text())
    spec=json.loads(args.student.read_text())
    neural=[s for s in graph if s['kind'] in ('Conv2D','DepthwiseConv2D','Dense')]
    if not neural or any('macs' not in s or 'kernel_shape' not in s for s in neural):
        raise ValueError('Complete graph MAC and kernel metadata required')
    macs=sum(s['macs'] for s in neural);weights=sum(math.prod(s['kernel_shape']) for s in neural)
    old_ms=1000*statistics.median(baseline['repeat_forward_s'])
    clock=baseline['clock_mhz'];lanes=16
    candidates=[summarize_candidate(spec,n,macs,old_ms,clock,lanes) for n in spec['input_sizes']]
    report=dict(scope='analytic_design_budget_not_training_or_hardware_result',
        source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (args.graph,args.baseline,args.student)},
        baseline=dict(macs_per_ROI=macs,kernel_values=weights,learned_layers=len(neural),
            median_forward_ms=old_ms,clock_mhz=clock,MAC_lanes_assumed_for_floor=lanes,
            measured_effective_GMAC_s=macs/old_ms/1e6,resources=baseline['resources']),
        targets=dict(annotated_frame_hz_min=20,annotated_frame_hz_stretch=30,capture_fps=30,
            display_scan_hz=60,per_hand_updates_hz=20,hands=2,ROI_inferences_per_s=40,
            frame_budget_ms=50,ROI_slot_ms=20,detector_and_control_budget_ms_per_pair=10,
            display_age_p95_ms=100,capture_width=640,capture_height=480,
            display_modes_budget=[dict(width=w,height=h,triple_RGB888_frame_bytes=w*h*3*3,
                frame_write_30fps_MB_s=w*h*3*30/1e6,display_read_60Hz_MB_s=w*h*3*60/1e6,
                total_minimum_MB_s=w*h*3*90/1e6) for w,h in [(640,480),(1280,720)]],
            resource_ceiling_fraction=.8,
            notes=['Targets only; detector+crop+control must fit the remaining shared budget',
                'Frame buffers reside in DDR; display bandwidth excludes inference, detector, extra copies and arbitration',
                '720p is the known display mode; VGA output requires monitor and timing validation',
                '20 Hz hands does not include body pose; body network needs an additional measured budget']),
        candidates=candidates)
    out.mkdir(parents=True);(out/'budget.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    rows=['# 独立上板：关键点模型工作量预算','',
        '分析预算，未训练、未做候选 HLS/上板验证；不能把估算写成达标 FPS。','',
        f'旧图：{macs:,} MAC/ROI，{weights:,} kernel 值，{len(neural)} 个学习层；',
        f'实际重复前向中位数 {old_ms:.3f}ms。','',
        '| 输入 | MAC/ROI | W8 kernel 字节 | 工作量缩减 | 同旧有效 MAC 速率估算 ms |',
        '|---|---:|---:|---:|---:|']
    for c in candidates:
        rows.append(f"| {c['input_size']}×{c['input_size']} | {c['macs_per_ROI']:,} | {c['kernel_bytes_at_W8']:,} | {c['operation_reduction']:.2f}× | {c['same_effective_MAC_rate_heuristic_ms']:.2f} |")
    rows+=['','最后一列忽略形状、并行利用率、访存和固定开销变化，只作选型初筛。',
        '输出是新的 65 项协议（63 坐标＋presence＋handedness logits），不能复用旧 64 项协议。',
        'W8/A8 是候选目标，现有 W12/A16 的逐位一致结论不继承到新模型。','']
    (out/'README.md').write_text('\n'.join(rows),encoding='utf-8')
    print(json.dumps(dict(baseline_macs=macs,candidates=[{k:c[k] for k in
        ('input_size','macs_per_ROI','kernel_values','operation_reduction','same_effective_MAC_rate_heuristic_ms')} for c in candidates]),indent=2))


if __name__=='__main__':main()
