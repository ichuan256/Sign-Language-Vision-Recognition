"""Rebind historical media references only by exact SHA; preserve missing/extra records explicitly."""
import argparse
from collections import Counter,defaultdict
import csv
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from vision.keypoints.student_data import digest

EXT={'.mp4','.mov','.avi','.mkv','.webm','.m4v','.wmv','.mpg','.mpeg','.mts','.m2ts','.3gp'}


def read_csv(path):
    with path.open(encoding='utf-8-sig',newline='') as stream:return list(csv.DictReader(stream))


def write_csv(path,rows):
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fields);writer.writeheader();writer.writerows(rows)


def reconcile(expected,actual):
    """Keep each historical row. Do not collapse byte-identical but separately recorded files."""
    by_hash=defaultdict(list)
    for path,row in actual.items():by_hash[row['sha256']].append(path)
    claimed=set();result=[dict(row,previous_path=row['path']) for row in expected]
    for row in result:
        found=actual.get(row['path'])
        if found and found['sha256']==row['sha256']:
            row.update(availability='present',path_resolution='same_path_SHA');claimed.add(row['path'])
    for row in result:
        if row.get('availability')=='present':continue
        matches=[p for p in by_hash[row['sha256']] if p not in claimed]
        if len(matches)==1:
            row.update(path=matches[0],availability='present',path_resolution='unique_SHA_relocated');claimed.add(matches[0])
        elif matches:row.update(availability='ambiguous',path_resolution='multiple_SHA_matches')
        else:row.update(availability='missing',path_resolution='expected_SHA_not_found')
    extras=[dict(path=p,**r,availability='unregistered',approved_for_training='False') for p,r in actual.items() if p not in claimed]
    return result,extras


def restored_original(row,actual,audited_hashes):
    originals=[p for p,v in actual.items() if v['sha256']==row['old_expected_sha256'] and v['sha256'] in audited_hashes]
    if row['old_expected_path'] in originals:return row['old_expected_path']
    return originals[0] if len(originals)==1 else None


def restored_bindings(pending):
    result={}
    for row in pending:
        if row.get('status')=='original_audit_SHA_restored_not_in_approved_subset':
            if row['sha256']!=row['old_expected_sha256']:raise ValueError('Restored SHA lineage mismatch')
            result[(row['prior_pending_sha256'],row['previous_path'])]=row['path']
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--apply-pointers',action='store_true')
    a=p.parse_args();out=a.output.resolve()
    if out.exists() or not out.is_relative_to(ROOT):raise ValueError('New workspace output required')
    current_path=ROOT/'vision/data/manifests/current_available_fullframe.json'
    current=json.loads(current_path.read_text(encoding='utf-8'))
    historical=ROOT/'vision/analysis/materials/20261025_merge/protected_media_layout.csv'
    expected=read_csv(historical);pending_path=ROOT/current['pending_manifest'];pending=read_csv(pending_path)
    actual={}
    for folder in ('vision/video','ASR/.sd_cache','vision/data/legacy/material'):
        for file in sorted((ROOT/folder).rglob('*')):
            if file.is_file() and file.suffix.lower() in EXT:
                actual[file.relative_to(ROOT).as_posix()]=dict(sha256=digest(file),bytes=file.stat().st_size)
    protected,extras=reconcile(expected,actual)
    audit=json.loads((ROOT/'vision/analysis/dataset/label_source_audit_20261025.json').read_text(encoding='utf-8'))
    audited_hashes={r['sha256'] for r in audit['records']}
    rebound_pending=[]
    restored={}
    for row in pending:
        old=row['path'];matches=[p for p,v in actual.items() if v['sha256']==row['sha256']]
        if old in matches:path=old;state='present'
        elif len(matches)==1:path=matches[0];state='present'
        else:
            originals=[p for p,v in actual.items() if v['sha256']==row['old_expected_sha256'] and v['sha256'] in audited_hashes]
            original=restored_original(row,actual,audited_hashes)
            if not matches and original is not None:
                path=original;state='present'
                rebound_pending.append(dict(row,path=path,sha256=actual[path]['sha256'],prior_pending_sha256=row['sha256'],
                    previous_path=old,availability=state,status='original_audit_SHA_restored_not_in_approved_subset'))
                continue
            path=old;state='ambiguous' if matches or len(originals)>1 else 'missing'
        rebound_pending.append(dict(row,path=path,previous_path=row.get('previous_path',old),availability=state))
    restored=restored_bindings(rebound_pending)
    for row in protected:
        key=(row['sha256'],row['previous_path'])
        if row['availability']=='missing' and key in restored:
            target=restored[key]
            row.update(historical_sha256=row['sha256'],sha256=actual[target]['sha256'],bytes=actual[target]['bytes'],
                path=target,availability='present',path_resolution='original_audit_SHA_restored')
    claimed={row['path'] for row in protected if row['availability']=='present'}
    extras=[row for row in extras if row['path'] not in claimed]
    out.mkdir(parents=True)
    write_csv(out/'protected.csv',protected);write_csv(out/'pending.csv',rebound_pending)
    write_csv(out/'unregistered.csv',extras or [dict(path='',sha256='',bytes='',availability='none',approved_for_training='False')])
    registry_path=ROOT/'vision/data/manifests/source_registry_current.json'
    registry_info=json.loads(registry_path.read_text());registry=read_csv(ROOT/registry_info['registry'])
    for row in registry:
        old=row['path'];matches=[p for p,v in actual.items() if v['sha256']==row['sha256'] and p.startswith('vision/video/raw/')]
        if old not in actual and len(matches)==1:row.update(previous_path=old,path=matches[0])
        row['availability']='present' if row['path'] in actual and actual[row['path']]['sha256']==row['sha256'] else 'missing'
    write_csv(out/'sources.csv',registry)
    report=dict(scope='media_inventory_reconciliation_no_media_moves_or_training_admission',
        actual_files=len(actual),historical_rows=len(expected),protected_status=dict(Counter(r['availability'] for r in protected)),
        relocated=sum(r['path']!=r['previous_path'] for r in protected),pending_status=dict(Counter(r['availability'] for r in rebound_pending)),
        original_audit_versions_restored=len(restored),source_status=dict(Counter(r['availability'] for r in registry)),
        unregistered_files=len(extras),missing=[r for r in protected if r['availability']!='present'],
        unregistered=extras,source_inventory_sha256=digest(historical),source_pending_sha256=digest(pending_path),
        approved_manifest_sha256=current['sha256'],media_files_modified=False,pointers_applied=False)
    if a.apply_pointers:
        if report['pending_status'].get('ambiguous') or report['protected_status'].get('ambiguous'):
            raise ValueError('Ambiguous SHA mapping requires review before pointer update')
        current.update(pending_manifest=(out/'pending.csv').relative_to(ROOT).as_posix(),
            pending_sha256=digest(out/'pending.csv'),pending_rows=len(rebound_pending))
        pointer=dict(protected_manifest=(out/'protected.csv').relative_to(ROOT).as_posix(),
            sha256=digest(out/'protected.csv'),rows=len(protected),
            unregistered_manifest=(out/'unregistered.csv').relative_to(ROOT).as_posix(),
            unregistered_sha256=digest(out/'unregistered.csv'),unregistered_rows=len(extras),
            historical_manifest=historical.relative_to(ROOT).as_posix(),
            declared_missing=sum(r['availability']=='missing' for r in protected))
        (ROOT/'vision/data/manifests/protected_media_current.json').write_text(json.dumps(pointer,indent=2)+'\n')
        current_path.write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');report['pointers_applied']=True
        registry_info.update(registry=(out/'sources.csv').relative_to(ROOT).as_posix(),sha256=digest(out/'sources.csv'),
            rows=len(registry),declared_missing=sum(r['availability']=='missing' for r in registry))
        registry_path.write_text(json.dumps(registry_info,indent=2)+'\n')
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('actual_files','historical_rows','protected_status','relocated','pending_status','original_audit_versions_restored','source_status','unregistered_files')},indent=2))


if __name__=='__main__':main()
