"""Bind approved media/SHA/provenance and fix source-group splits before teacher extraction."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from vision.keypoints.student_data import digest,grouped_split,select_balanced


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--max-clips',type=int,default=40,help='0 selects all eligible unique files')
    p.add_argument('--seed',type=int,default=20261026)
    p.add_argument('--min-source-width',type=int,default=0);p.add_argument('--min-source-height',type=int,default=0)
    a=p.parse_args();out=a.output.resolve()
    if a.max_clips<0 or out.exists() or not out.is_relative_to(ROOT):raise ValueError('New workspace output required')
    pointer=ROOT/'vision/data/manifests/current_available_fullframe.json'
    current=json.loads(pointer.read_text(encoding='utf-8'));manifest=ROOT/current['manifest']
    if digest(manifest)!=current['sha256']:raise ValueError('Approved manifest SHA mismatch')
    audit_path=ROOT/'vision/analysis/dataset/label_source_audit_20261025.json'
    audit=json.loads(audit_path.read_text(encoding='utf-8'));by_hash={}
    for item in audit['records']:by_hash.setdefault(item.get('sha256'),[]).append(item)
    records=[];excluded=[];seen=set()
    with manifest.open(encoding='utf-8-sig',newline='') as stream:rows=list(csv.DictReader(stream))
    if len(rows)!=current['rows']:raise ValueError('Approved manifest row count mismatch')
    for row in rows:
        path=(ROOT/row['输出路径']).resolve()
        if not path.is_relative_to(ROOT/'vision/video') or not path.is_file():raise ValueError('Invalid media path: '+str(path))
        sha=digest(path)
        if sha not in by_hash:raise ValueError('Media absent from historical SHA audit: '+str(path))
        matches=[r for r in by_hash[sha] if r['provenance'].get('status')=='resolved' and r['provenance'].get('source_group')]
        if not matches:excluded.append(dict(sha256=sha,reason='no_resolved_provenance'));continue
        if sha in seen:continue
        seen.add(sha);families={r['provenance']['source_family'] for r in matches}
        if len(families)!=1:raise ValueError('Ambiguous source family')
        records.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=sha,
            source_groups=sorted({r['provenance']['source_group'] for r in matches}),
            source_family=next(iter(families)),performer_id=None,
            source_size=[matches[0]['media']['width'],matches[0]['media']['height']],
            sample_id=row['样本编号'],contributor=row['part']))
    records,assignment=grouped_split(records,a.seed)
    eligible=[r for r in records if r['source_size'][0]>=a.min_source_width and r['source_size'][1]>=a.min_source_height]
    selected=select_balanced(eligible,a.max_clips,a.seed)
    report=dict(schema='hand_teacher_plan_v1',seed=a.seed,approved_pointer=pointer.relative_to(ROOT).as_posix(),
        approved_pointer_sha256=digest(pointer),approved_manifest=current['manifest'],approved_manifest_sha256=digest(manifest),
        audit_sha256=digest(audit_path),approved_rows=len(rows),eligible_unique_files=len(records),
        excluded=excluded,group_assignment=assignment,selected=selected,
        source_resolution_filter=dict(min_width=a.min_source_width,min_height=a.min_source_height,eligible_files=len(eligible)),
        counts=dict(clips=len(selected),splits=dict(Counter(r['split'] for r in selected)),
            source_components=dict(Counter(assignment.values()))),
        limitations=['Contributor is not performer ID; this is source-video holdout, not cross-person evaluation',
            'Word labels are not used as landmark truth; no review-negative labels exist yet'])
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report['counts'],indent=2))


if __name__=='__main__':main()
