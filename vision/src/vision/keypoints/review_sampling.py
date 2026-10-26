"""Deterministic review sampling by native image quality, source quotas and temporal separation."""
from collections import Counter,defaultdict
import math
import cv2
import numpy as np


def hand_focus_score(native_bgr,normalized_xy):
    """Use the eroded hand hull, limiting isolated text edges; this remains a heuristic."""
    n=native_bgr.shape[0]
    xy=np.asarray(normalized_xy,np.float32)*(n-1)
    mask=np.zeros(native_bgr.shape[:2],np.uint8)
    cv2.fillConvexPoly(mask,cv2.convexHull(xy.astype(np.int32)),255)
    mask=cv2.erode(mask,np.ones((5,5),np.uint8))>0
    if mask.sum()<16:return 0.
    lap=cv2.Laplacian(cv2.cvtColor(native_bgr,cv2.COLOR_BGR2GRAY),cv2.CV_64F)
    return float(np.minimum(lap[mask]**2,1000).mean())


def select_clear_review(records,limit,policy):
    rejected=Counter();buckets=defaultdict(list)
    for record in records:
        if record['sample_id'] in policy.get('excluded_sample_ids',[]) or record['source_sha256'] in policy.get('excluded_source_sha256',[]):
            rejected['visual_quality_screen']+=1;continue
        w,h=record.get('source_size',[0,0])
        if w<policy['min_source_width'] or h<policy['min_source_height']:
            rejected['source_resolution']+=1;continue
        if record.get('ROI_side_source_pixels',0)<policy['min_native_side']:
            rejected['native_ROI_too_small']+=1;continue
        if record['kind']=='teacher_positive' and record.get('focus_score',0)<policy['min_hand_focus']:
            rejected['hand_focus']+=1;continue
        buckets[(record['split_group'],record['kind'])].append(record)
    for rows in buckets.values():rows.sort(key=lambda r:(-r.get('focus_score',0),r['sample_id']))
    group_cap=math.ceil(limit/max(1,len({k[0] for k in buckets})))
    selected=[];frames=set();counts=Counter();group_counts=Counter();times=defaultdict(list)
    while len(selected)<limit:
        progress=False
        for key in sorted(buckets):
            if len(selected)>=limit:break
            if group_counts[key[0]]>=group_cap:continue
            while buckets[key]:
                r=buckets[key].pop(0);source=r['source_sha256'];frame=(source,r['source_frame'])
                if frame in frames:rejected['same_source_frame']+=1;continue
                if counts[source]>=policy['max_per_clip']:rejected['clip_quota']+=1;continue
                if any(abs(r['source_timestamp_s']-t)<policy['min_time_gap_s']-1e-8 for t in times[source]):
                    rejected['temporal_neighbor']+=1;continue
                selected.append(r);frames.add(frame);counts[source]+=1;group_counts[key[0]]+=1
                times[source].append(r['source_timestamp_s']);progress=True;break
        if not progress:break
    return selected,dict(policy=policy,requested=limit,selected=len(selected),unique_frames=len(frames),
        source_clips=len(counts),source_groups=dict(group_counts),rejected=dict(rejected),
        note='Automatic pre-screen only. Human may mark any item ungradable; no quality or absence label is invented.')
