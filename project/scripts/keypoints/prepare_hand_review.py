"""Resample a review queue without rerunning or approving teacher labels."""
import argparse
import json
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
import cv2
from vision.keypoints.student_data import digest
from vision.keypoints.student_review import write_review
from vision.keypoints.review_sampling import select_clear_review
from vision.keypoints.review_geometry import source_affine,review_context


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',type=Path,required=True);p.add_argument('--policy',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--samples',type=int,default=20)
    a=p.parse_args();data=a.data.resolve();out=a.output.resolve()
    if out.exists() or not out.is_relative_to(ROOT/'project/_tmp') or a.samples<1:
        raise ValueError('New bounded workspace review output required')
    info=json.loads((data/'dataset.json').read_text());policy=json.loads(a.policy.read_text(encoding='utf-8'))
    expected=digest(data/'records.jsonl')
    if not info['completed'] or expected!=info['records_sha256'] or expected!=policy['records_sha256']:
        raise ValueError('Review policy/dataset SHA mismatch')
    records=[json.loads(s) for s in (data/'records.jsonl').read_text(encoding='utf-8').splitlines()]
    selected,selection=select_clear_review(records,a.samples,policy['selection'])
    out.mkdir(parents=True);(out/'context').mkdir()
    checked=set()
    for row in selected:
        image=(data/'review'/row['image']).resolve();source=(ROOT/row['source_path']).resolve()
        if not image.is_relative_to(data) or not image.is_file() or not source.is_relative_to(ROOT):
            raise ValueError('Missing/conflicting review image')
        if source not in checked:
            if digest(source)!=row['source_sha256']:raise ValueError('Source SHA mismatch')
            checked.add(source)
        capture=cv2.VideoCapture(str(source))
        try:
            capture.set(cv2.CAP_PROP_POS_FRAMES,row['source_frame']);ok,frame=capture.read()
            if not ok:raise ValueError('Cannot decode context frame')
        finally:capture.release()
        context=out/'context'/(row['sample_id']+'.jpg')
        if not context.resolve().is_relative_to(out) or not cv2.imwrite(str(context),review_context(frame,source_affine(row),row.get('initial_xy'))):
            raise ValueError('Invalid context output')
        row['image']=Path(os.path.relpath(image,out)).as_posix();row['context']=context.relative_to(out).as_posix()
    count=write_review(out,selected,len(selected),preserve_order=True)
    (out/'selection.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    report=dict(dataset_sha256=digest(data/'dataset.json'),records_sha256=expected,policy_sha256=digest(a.policy),
        selection_count=count,human_labels_created=False,source_images_modified=False)
    (out/'provenance.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
