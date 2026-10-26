"""One-time, workspace-confined physical source/data consolidation with SHA evidence."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
MOVES=[
    ('vision/m1/manifests','vision/data/manifests/m1_8class'),
    ('vision/m1/runs','vision/data/cache/m1'),
    ('vision/manifests/m1_vocabulary_20261023.json','vision/data/manifests/m1_26class_20261023.json'),
    ('vision/manifests/build_m1_manifest.py','vision/scripts/legacy/build_m1_manifest.py'),
    ('vision/sign_video/smoke_manifest.json','vision/data/manifests/sign_video_smoke_20261023.json'),
    ('vision/models','vision/data/models'),
    *[(f'vision/{name}',f'vision/src/vision/{name}') for name in ('framesource','keypoints','m1','classify','sign_video','webapp')],
]
SKIP={'.git','_tmp','_cache','video','__pycache__','ip_repo','losslesscut'}


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def relocated(path):
    relative=path.relative_to(ROOT).as_posix()
    for old,new in sorted(MOVES,key=lambda pair:len(pair[0]),reverse=True):
        if relative==old or relative.startswith(old+'/'):return ROOT/(new+relative[len(old):])
    return path


def files(root):
    return [p for p in root.rglob('*') if p.is_file() and not SKIP.intersection(p.relative_to(ROOT).parts)]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--apply',action='store_true');p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if out.exists() or not out.is_relative_to(ROOT/'project/_tmp'):raise ValueError('New project/_tmp evidence required')
    for old,new in MOVES:
        source=(ROOT/old).resolve();destination=(ROOT/new).resolve()
        if not source.is_relative_to(ROOT) or not destination.is_relative_to(ROOT) or source==ROOT or destination==ROOT:
            raise ValueError('Move escaped workspace')
        if not source.exists() or destination.exists():raise ValueError('Missing source or occupied destination: '+old)
    originals={p:p.read_text(encoding='utf-8-sig') for p in files(ROOT) if p.suffix=='.md'}
    code={p:p.read_text(encoding='utf-8-sig') for p in files(ROOT) if p.suffix in ('.py','.bat','.cmd','.ps1') and p!=Path(__file__).resolve()}
    moved={}
    for old,new in MOVES:
        source=ROOT/old
        for path in source.rglob('*') if source.is_dir() else [source]:
            if path.is_file():moved.setdefault(path,dict(before_sha256=digest(path),destination=relocated(path).relative_to(ROOT).as_posix()))
    manifests={}
    for old in ('vision/m1/manifests','vision/manifests/m1_vocabulary_20261023.json','vision/sign_video/smoke_manifest.json'):
        source=ROOT/old
        for path in source.glob('*.json') if source.is_dir() else [source]:
            manifests[path]=json.loads(path.read_text(encoding='utf-8-sig'))
    out.mkdir(parents=True)
    report=dict(applied=False,moves=[dict(source=s,destination=d) for s,d in MOVES],
        files=[dict(source=p.relative_to(ROOT).as_posix(),**info) for p,info in moved.items()])
    (out/'plan.json').write_text(json.dumps(report,indent=2)+'\n')
    if not a.apply:
        print('PREFLIGHT_OK',len(moved),'files;',len(MOVES),'moves');return
    for old,new in MOVES:
        source=(ROOT/old).resolve();destination=(ROOT/new).resolve()
        # Recheck the final absolute paths immediately before every recursive move.
        if not source.is_relative_to(ROOT) or not destination.is_relative_to(ROOT):raise ValueError('Unsafe move')
        destination.parent.mkdir(parents=True,exist_ok=True);source.rename(destination)
    empty=ROOT/'vision/manifests'
    if empty.is_dir() and not any(empty.iterdir()):empty.rmdir()
    prefixes=sorted(MOVES,key=lambda pair:len(pair[0]),reverse=True)
    def update_paths(text):
        # A single regex pass prevents remapping a newly inserted path a second time.
        for separator in ('/','\\','\\\\'):
            mapping={old.replace('/',separator):new.replace('/',separator) for old,new in prefixes}
            expression='(?<!'+re.escape('src'+separator)+')(?:'+'|'.join(re.escape(key) for key in mapping)+')'
            text=re.sub(expression,lambda match:mapping[match.group(0)],text)
        return text
    changed=[]
    for path,text in code.items():
        new=relocated(path);updated=update_paths(text)
        if path.parent==ROOT/'vision/keypoints' or path==ROOT/'vision/m1/build_manifest.py' or path==ROOT/'vision/manifests/build_m1_manifest.py':
            updated=updated.replace('Path(__file__).resolve().parents[2]',
                'next(p for p in Path(__file__).resolve().parents if (p / "AGENTS.md").is_file())')
        if path.parent==ROOT/'vision/src/signrec':updated=updated.replace('/ "models"','/ "data" / "models"')
        if updated!=text:new.write_text(updated,encoding='utf-8');changed.append(new.relative_to(ROOT).as_posix())
    for path,text in originals.items():
        new=relocated(path)
        def link(match):
            value=match.group(2)
            if value.startswith(('http:','https:','#','/','mailto:','codex:')):return match.group(0)
            location,sep,anchor=value.partition('#')
            target=(path.parent/location).resolve()
            if not target.is_relative_to(ROOT):return match.group(0)
            target=relocated(target)
            relative=os.path.relpath(target,new.parent).replace('\\','/')
            return match.group(1)+relative+(sep+anchor if sep else '')+')'
        updated=re.sub(r'(\[[^\]\n]+\]\()([^)\n]+)\)',link,text)
        # Current operation cards get canonical paths; historical experiment text keeps its historical meaning.
        if path.name in ('README.md','AGENTS.md','HDMI_REPLAY.md') or path.is_relative_to(ROOT/'docs/方案'):
            updated=update_paths(updated)
        if updated!=text:new.write_text(updated,encoding='utf-8');changed.append(new.relative_to(ROOT).as_posix())
    for path,data in manifests.items():
        destination=relocated(path)
        for sample in data.get('samples',[]):
            old_target=(path.parent/sample['file']).resolve()
            sample['file']=os.path.relpath(old_target,destination.parent).replace('\\','/')
            if (destination.parent/sample['file']).resolve()!=old_target:raise RuntimeError('Manifest media binding changed')
        destination.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for row in report['files']:
        destination=ROOT/row['destination'];row['after_sha256']=digest(destination)
        row['bytes_unchanged']=row['after_sha256']==row['before_sha256']
        if destination.suffix in ('.onnx','.npz','.jpg','.svg') and not row['bytes_unchanged']:
            raise RuntimeError('Binary asset changed')
    report.update(applied=True,changed_text_files=sorted(set(changed)),binary_assets_unchanged=True,
        media_paths_moved=False,functional_vision_dirs=sorted(p.name for p in (ROOT/'vision').iterdir() if p.is_dir() and p.name!='__pycache__'))
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('MIGRATION_COMPLETE',len(report['files']),'files;',len(changed),'text references updated')


if __name__=='__main__':main()
