"""Source grouping, ROI labels and masked metrics for student training. No detector imports."""
import hashlib
import json
import math
from pathlib import Path
import random
import cv2
import numpy as np

ROOT=next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())
SPLITS=('train','validation','test')


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def grouped_split(records,seed=20261026):
    """Union source groups sharing any SHA, then stratify components by source family."""
    parent={g:g for r in records for g in r['source_groups']}
    def find(g):
        while parent[g]!=g:parent[g]=parent[parent[g]];g=parent[g]
        return g
    for r in records:
        anchor=r['source_groups'][0]
        for g in r['source_groups'][1:]:parent[find(g)]=find(anchor)
    hashes={}
    for r in records:
        group=find(r['source_groups'][0])
        if r['sha256'] in hashes:parent[find(group)]=find(hashes[r['sha256']])
        else:hashes[r['sha256']]=group
    components={}
    for g in parent:components.setdefault(find(g),[]).append(g)
    keys={root:'+'.join(sorted(groups)) for root,groups in components.items()}
    families={}
    for r in records:
        key=keys[find(r['source_groups'][0])]
        families.setdefault(key,set()).add(r['source_family'])
    buckets={}
    for key,family in families.items():buckets.setdefault('+'.join(sorted(family)),[]).append(key)
    assignment={}
    for family,groups in sorted(buckets.items()):
        groups=sorted(groups);random.Random(str(seed)+family).shuffle(groups)
        if len(groups)<3:raise ValueError('Need three source components per family for fixed holdout: '+family)
        n=max(1,round(len(groups)*.15))
        for i,g in enumerate(groups):assignment[g]='test' if i<n else 'validation' if i<2*n else 'train'
    result=[]
    for r in records:
        g=keys[find(r['source_groups'][0])]
        result.append(dict(r,split_group=g,split=assignment[g]))
    return result,assignment


def select_balanced(records,limit,seed):
    buckets={}
    for r in records:buckets.setdefault(r['split_group'],[]).append(r)
    for key,items in buckets.items():
        items.sort(key=lambda r:r['sha256']);random.Random(str(seed)+key).shuffle(items)
    selected=[];keys=sorted(buckets)
    while any(buckets.values()) and (not limit or len(selected)<limit):
        for key in keys:
            if buckets[key] and (not limit or len(selected)<limit):selected.append(buckets[key].pop())
    if set(r['split'] for r in selected)!=set(SPLITS):raise ValueError('Pilot must include all fixed splits')
    return selected


def hand_crop(frame,hand,size=128,margin=1.7):
    points=np.asarray(hand,np.float64)
    if points.shape!=(21,3) or not np.isfinite(points).all():raise ValueError('Complete finite teacher hand required')
    pixels=points[:,:2]*[frame.shape[1],frame.shape[0]]
    upward=pixels[9]-pixels[0];norm=np.linalg.norm(upward)
    if norm<2:raise ValueError('Degenerate hand')
    y=-upward/norm;x=np.array([y[1],-y[0]]);basis=np.stack([x,y],axis=1)
    local=pixels@basis;low=local.min(0);high=local.max(0);side=float((high-low).max()*margin)
    if side<12:raise ValueError('Hand too small')
    center=basis@((low+high)/2)
    corners=np.array([center-side/2*x-side/2*y,center+side/2*x-side/2*y,center-side/2*x+side/2*y],np.float32)
    affine=cv2.getAffineTransform(corners,np.array([[0,0],[size-1,0],[0,size-1]],np.float32))
    rgb=cv2.cvtColor(cv2.warpAffine(frame,affine,(size,size)),cv2.COLOR_BGR2RGB)
    target=points.copy();target[:,:2]=(pixels@affine[:,:2].T+affine[:,2])/(size-1)
    target[:,2]=points[:,2]*frame.shape[1]/side
    return rgb,target.astype(np.float32),affine,side


def apply_reviews(targets,masks,records,path=None):
    """Manual corrections overlay immutable teacher data; absent hand never becomes a negative by default."""
    targets=targets.copy();masks=masks.copy();records=[dict(r) for r in records]
    if path is None:return targets,masks,records
    by_id={r['sample_id']:i for i,r in enumerate(records)};seen=set()
    for line in Path(path).read_text(encoding='utf-8-sig').splitlines():
        if not line.strip():continue
        item=json.loads(line);sid=item['sample_id']
        if sid not in by_id or sid in seen:raise ValueError('Unknown or duplicate review ID: '+sid)
        seen.add(sid)
        if item.get('status') not in ('accepted','ungradable','roi_rejected') or not str(item.get('reviewer','')).strip():
            raise ValueError('Accepted named reviewer required')
        if item.get('annotation_origin')!='human' or item.get('human_verified') is not True:
            raise ValueError('Explicit human verification required')
        roi_status=item.get('roi_status')
        if roi_status not in (None,'usable','partial','wrong'):raise ValueError('Invalid ROI review status')
        if item['status']=='roi_rejected' or roi_status=='wrong':
            i=by_id[sid];masks[i,:]=0;records[i].update(pose_source='none',presence_source='none',handedness_source='none',quality_status='human_roi_rejected')
            continue
        if item['status']=='ungradable':
            i=by_id[sid];masks[i,:]=0;records[i].update(pose_source='none',presence_source='none',handedness_source='none',quality_status='human_ungradable')
            continue
        if type(item.get('presence')) is not bool:raise ValueError('Explicit boolean presence required')
        i=by_id[sid];targets[i,63]=int(item['presence']);masks[i,63]=1
        records[i]['presence_source']='human';records[i]['scenario']=item.get('scenario','unassigned')
        if not item['presence']:
            masks[i,:63]=0;masks[i,64]=0;continue
        handed=item.get('handedness')
        if handed is not None:
            if type(handed) is not int or handed not in (0,1):raise ValueError('Handedness must be 0/1 or null')
            targets[i,64]=handed;masks[i,64]=1;records[i]['handedness_source']='human'
        xy=item.get('landmarks_xy')
        if xy is not None:
            flags=item.get('visible')
            if not isinstance(flags,list) or len(flags)!=21 or any(type(v) is not bool for v in flags):
                raise ValueError('Explicit boolean visibility flags required')
            visible=np.asarray(flags,bool)
            if len(xy)!=21 or visible.shape!=(21,):raise ValueError('21 points and visibility flags required')
            normalized=np.full((21,2),np.nan,np.float32)
            for j,p in enumerate(xy):
                if visible[j]:
                    if p is None or len(p)!=2:raise ValueError('Visible point needs xy')
                    normalized[j]=p
            if not np.isfinite(normalized[visible]).all() or np.any((normalized[visible]<0)|(normalized[visible]>1)):
                raise ValueError('Finite normalized visible xy required')
            t=targets[i,:63].reshape(21,3);m=masks[i,:63].reshape(21,3)
            t[:,:2]=np.nan_to_num(normalized);m[:,:2]=visible[:,None];m[:,2]=0
            records[i]['pose_source']='human'
    return targets,masks,records


def mask_teacher_source_exterior(targets,masks,records):
    """Mask geometrically impossible teacher coordinates; retain labels and explicit human review."""
    from .review_geometry import source_exterior_flags
    masks=masks.copy();records=[dict(r) for r in records]
    for i,row in enumerate(records):
        if row.get('pose_source')!='teacher' or not masks[i,:63].any():continue
        outside=source_exterior_flags(targets[i,:63].reshape(21,3)[:,:2],row['affine_source_to_roi'],row['source_size'])
        masks[i,:63].reshape(21,3)[outside]=0
        row['source_exterior_points_masked']=int(outside.sum())
    return masks,records


def load_dataset(directory,reviews=None,mask_outside_source=False):
    directory=Path(directory);report=json.loads((directory/'dataset.json').read_text())
    if not report['completed']:raise ValueError('Completed dataset required')
    if digest(directory/'records.jsonl')!=report['records_sha256']:raise ValueError('Metadata SHA mismatch')
    records=[json.loads(s) for s in (directory/'records.jsonl').read_text(encoding='utf-8').splitlines()]
    images=[];targets=[];masks=[];ids=[]
    for shard in report['shards']:
        path=(directory/shard['file']).resolve()
        if not path.is_relative_to(directory.resolve()) or digest(path)!=shard['sha256']:raise ValueError('Shard path/SHA mismatch')
        with np.load(path,allow_pickle=False) as data:
            images.append(data['images']);targets.append(data['targets']);masks.append(data['masks']);ids.extend(data['sample_ids'].tolist())
    if ids!=[r['sample_id'] for r in records] or len(ids)!=len(set(ids)):raise ValueError('Record order or duplicate IDs')
    groups={};hashes={}
    for r in records:
        for key,mapping in [(r['split_group'],groups),(r['source_sha256'],hashes)]:
            if key in mapping and mapping[key]!=r['split']:raise ValueError('Source leakage across splits')
            mapping[key]=r['split']
    targets,masks,records=apply_reviews(np.concatenate(targets),np.concatenate(masks),records,reviews)
    if mask_outside_source:masks,records=mask_teacher_source_exterior(targets,masks,records)
    return np.concatenate(images),targets,masks,records,report


def training_partitions(targets,masks,records,disable_presence=False):
    """Choose supervised rows explicitly; zero-loss negative crops must not affect coordinate-only BN."""
    coordinates={s:np.array([i for i,r in enumerate(records) if r['split']==s and masks[i,:63].any()],dtype=int) for s in SPLITS}
    negatives=np.array([i for i,r in enumerate(records) if r['split']=='train' and r.get('presence_source')=='human'
        and masks[i,63] and targets[i,63]==0],dtype=int)
    presence_enabled=bool(len(negatives)) and not disable_presence
    auxiliary=[i for i,r in enumerate(records) if r['split']=='train' and r.get('presence_source')=='human' and masks[i,63]]
    train=np.unique(np.r_[coordinates['train'],np.asarray(auxiliary,dtype=int)]) if presence_enabled else coordinates['train']
    active=masks.copy()
    if not presence_enabled:active[:,63]=0
    handedness_enabled=len(set(targets[train,64][masks[train,64]>0].tolist()))==2
    if not handedness_enabled:active[:,64]=0
    return dict(coordinates=coordinates,train=train,active_masks=active,presence_enabled=presence_enabled,
        handedness_enabled=handedness_enabled,negative_train_available=len(negatives),
        negative_train_used=len(negatives) if presence_enabled else 0)


def coordinate_metrics(predictions,targets,masks,point_indices=None):
    pred=np.asarray(predictions)[:,:63].reshape(-1,21,3)[:,:,:2]
    truth=np.asarray(targets)[:,:63].reshape(-1,21,3)[:,:,:2]
    valid=np.asarray(masks)[:,:63].reshape(-1,21,3)[:,:,:2].all(2)
    selection=np.ones(21,bool)
    if point_indices is not None:
        selection[:]=False;selection[list(point_indices)]=True
    errors=[];frames=0
    for p,t,v in zip(pred,truth,valid):
        if v.sum()<2:continue
        diagonal=np.linalg.norm(t[v].max(0)-t[v].min(0))
        if diagonal<1e-6:continue
        chosen=v&selection
        if not chosen.any():continue
        errors.extend((np.linalg.norm(p[chosen]-t[chosen],axis=1)/diagonal).tolist());frames+=1
    return None if not errors else dict(ROIs=frames,visible_points=len(errors),
        mean_normalized_error=float(np.mean(errors)),PCK_at_005=float(np.mean(np.asarray(errors)<=.05)))


def augment(image,target,mask,size,rng=None):
    image=np.asarray(image);target=target.copy();mask=mask.copy()
    original=image.shape[0];scale=(size-1)/(original-1)
    image=cv2.warpAffine(image,np.array([[scale,0,0],[0,scale,0]],np.float32),(size,size))
    if rng is not None:
        s=float(rng.uniform(.85,1.15));angle=float(rng.uniform(-15,15))
        affine=cv2.getRotationMatrix2D(((size-1)/2,(size-1)/2),angle,s)
        affine[:,2]+=rng.uniform(-.08,.08,2)*(size-1)
        image=cv2.warpAffine(image,affine,(size,size))
        points=target[:63].reshape(21,3);valid=mask[:63].reshape(21,3)
        points[:,:2]=(points[:,:2]*(size-1)@affine[:,:2].T+affine[:,2])/(size-1)
        points[:,2]*=s
        inside=((points[:,:2]>=0)&(points[:,:2]<=1)).all(1);valid[~inside]=0
        image=np.clip((image.astype(np.float32)-127.5)*rng.uniform(.8,1.2)+127.5+rng.uniform(-15,15),0,255)
    return image.astype(np.float32)/255,target,mask
