"""Resample a review queue without rerunning or approving teacher labels."""
import argparse
import json
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from vision.keypoints.student_data import digest
from vision.keypoints.student_review import write_review


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
    for row in records:
        for field in ('image','context'):
            path=(data/'review'/row[field]).resolve()
            if not path.is_relative_to(data) or not path.is_file():raise ValueError('Missing/conflicting review image')
            row[field]=Path(os.path.relpath(path,out)).as_posix()
    out.mkdir(parents=True)
    count=write_review(out,records,a.samples,policy['selection'])
    report=dict(dataset_sha256=digest(data/'dataset.json'),records_sha256=expected,policy_sha256=digest(a.policy),
        selection_count=count,human_labels_created=False,source_images_modified=False)
    (out/'provenance.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
