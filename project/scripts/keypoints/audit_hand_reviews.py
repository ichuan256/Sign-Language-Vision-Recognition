"""Validate returned reviews and crop pixels; retain originals and prepare an unchanged-crop recheck page."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
import cv2
import numpy as np
from vision.keypoints.student_data import load_dataset,digest,apply_reviews
from vision.keypoints.student_review import write_review
from vision.keypoints.review_geometry import review_context,source_affine


def counts(reviews):
    return dict(rows=len(reviews),status=dict(Counter(r['status'] for r in reviews)),
        accepted_presence_positive=sum(r['status']=='accepted' and r.get('presence') is True for r in reviews),
        accepted_presence_negative=sum(r['status']=='accepted' and r.get('presence') is False for r in reviews),
        coordinate_annotations=sum(r['status']=='accepted' and r.get('landmarks_xy') is not None for r in reviews))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',type=Path,required=True);p.add_argument('--queue',type=Path,required=True)
    p.add_argument('--reviews',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--hold-id',action='append',default=[])
    p.add_argument('--hold-reason',default='ROI与有手记录存在疑点，请只根据左侧裁剪重新判断。原标注保留，暂不用于训练。')
    a=p.parse_args();out=a.output.resolve();data=a.data.resolve()
    if out.exists() or not out.is_relative_to(ROOT/'project/_tmp'):raise ValueError('New project/_tmp audit required')
    original=a.reviews.read_bytes();original_sha=hashlib.sha256(original).hexdigest()
    reviews=[json.loads(s) for s in original.decode('utf-8-sig').splitlines() if s.strip()]
    queue=[json.loads(s) for s in a.queue.read_text(encoding='utf-8-sig').splitlines() if s.strip()]
    images,targets,masks,records,info=load_dataset(data)
    apply_reviews(targets,masks,records,a.reviews)  # strict named-human schema and coordinate validation
    by={r['sample_id']:i for i,r in enumerate(records)};ids=[r['sample_id'] for r in queue]
    review_ids={r['sample_id'] for r in reviews};held=set(a.hold_id)
    if len(ids)!=len(set(ids)) or not review_ids.issubset(ids) or not held.issubset(review_ids):
        raise ValueError('Review queue or held ID mismatch')
    checked_sources={};checks=[];frames={}
    for row in queue:
        sid=row['sample_id']
        if not re.fullmatch(r'[A-Za-z0-9_]+',sid) or sid not in by:raise ValueError('Invalid review ID')
        source=records[by[sid]]
        for key in ('source_path','source_sha256','source_frame','split','split_group','kind','affine_source_to_roi','initial_xy'):
            if row[key]!=source[key]:raise ValueError('Queue metadata mismatch: '+key)
        path=(ROOT/row['source_path']).resolve();image_path=(a.queue.parent/row['image']).resolve()
        if not path.is_relative_to(ROOT) or not image_path.is_relative_to(data):raise ValueError('Media path outside bound dataset')
        if path not in checked_sources:checked_sources[path]=digest(path)
        if checked_sources[path]!=row['source_sha256']:raise ValueError('Source SHA mismatch')
        cap=cv2.VideoCapture(str(path))
        try:
            if not cap.isOpened():raise ValueError('Cannot decode source')
            cap.set(cv2.CAP_PROP_POS_FRAMES,row['source_frame']);ok,frame=cap.read()
            if not ok:raise ValueError('Source frame missing')
        finally:cap.release()
        matrix=source_affine(row)
        crop=cv2.warpAffine(frame,matrix*(511/127),(512,512))
        ok,encoded=cv2.imencode('.jpg',crop,[cv2.IMWRITE_JPEG_QUALITY,95])
        jpeg_match=ok and hashlib.sha256(encoded).hexdigest()==digest(image_path)
        tensor=cv2.cvtColor(cv2.warpAffine(frame,matrix,(128,128)),cv2.COLOR_BGR2RGB)
        tensor_match=bool(np.array_equal(tensor,images[by[sid]]))
        checks.append(dict(sample_id=sid,source_SHA_passed=True,affine_dtype=str(matrix.dtype),review_JPEG_exact_match=bool(jpeg_match),training_tensor_exact_match=tensor_match))
        if not jpeg_match or not tensor_match:raise ValueError('Crop pixels differ; do not rebind annotations: '+sid)
        frames[sid]=frame
    if digest(a.reviews)!=original_sha:raise ValueError('Reviews changed during audit; retry from current file')
    out.mkdir(parents=True);(out/'context').mkdir()
    (out/'reviews_original.jsonl').write_bytes(original)
    usable=[r for r in reviews if r['sample_id'] not in held]
    (out/'reviews_usable.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in usable),encoding='utf-8')
    recheck=[]
    for row in queue:
        row=dict(row);sid=row['sample_id'];initial=row.get('initial_xy')
        if not cv2.imwrite(str(out/'context'/(sid+'.jpg')),review_context(frames[sid],row['affine_source_to_roi'],initial)):
            raise OSError('Cannot write recheck context')
        row['image']=Path(os.path.relpath((a.queue.parent/row['image']).resolve(),out)).as_posix()
        row['context']='context/'+sid+'.jpg'
        if sid in held:row['audit_note']=a.hold_reason
        recheck.append(row)
    write_review(out,recheck,len(recheck),annotations=reviews,preserve_order=True)
    report=dict(scope='Human review intake and unchanged-crop audit; not training or independent accuracy acceptance',
        source_reviews=a.reviews.resolve().relative_to(ROOT).as_posix(),source_review_sha256=original_sha,
        dataset_sha256=digest(data/'dataset.json'),records_sha256=info['records_sha256'],source_queue_sha256=digest(a.queue),
        original_counts=counts(reviews),usable_counts=counts(usable),unreviewed_queue_items=len(queue)-len(reviews),
        held_for_human_recheck=[dict(sample_id=sid,reason=a.hold_reason,origin='agent_visual_audit_not_new_label') for sid in sorted(held)],
        checked_sources=len(checked_sources),mapping_checks=checks,original_annotations_modified=False,crop_coordinates_modified=False,
        usable_reviews_sha256=digest(out/'reviews_usable.jsonl'),review_page_sha256=digest(out/'index.html'),new_student_trained=False)
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('original_counts','usable_counts','held_for_human_recheck','unreviewed_queue_items','checked_sources')},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
