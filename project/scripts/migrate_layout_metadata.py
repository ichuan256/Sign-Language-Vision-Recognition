"""Mechanical migration of path metadata; numerical arrays remain unchanged."""
from pathlib import Path
import csv
import io
import json
import os
import re
import shutil
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BACKUP = ROOT / 'project/_tmp/layout_cleanup_20261025/path_metadata_backups'
BACKUP.mkdir(parents=True, exist_ok=True)
MAPPING = [('analysis/r3', 'project/analysis/r3'), ('scripts/r3', 'project/scripts/r3'),
           ('pynq-vision', 'project'), ('asr', 'ASR'),
           *[(p, 'vision/' + p) for p in ('analysis', 'scripts', 'src', 'data', 'tools', 'models', 'webapp', 'video')],
           ('tests', 'vision/tests/integration'), ('_tmp', 'project/_tmp')]

def mapped(value):
    value = value.replace('\\', '/')
    for old, new in MAPPING:
        if value == old or value.startswith(old + '/'):
            return new + value[len(old):]
    return value

def backup(path):
    dest = BACKUP / path.relative_to(ROOT)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        shutil.copy2(path, dest)

# Operational manifests only, not historical source annotations.
for path in [ROOT/'vision/data/manifests/manifest_fullframe_20261024.csv',
             ROOT/'vision/data/legacy/material/dataset_manifest_20261020.csv']:
    backup(path)
    with path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        rows, fields = list(reader), reader.fieldnames
    for row in rows:
        for key in ('输出路径', '原片路径'):
            if key in row:
                row[key] = mapped(row[key])
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

for path in [ROOT/'project/_tmp/r3/tensors.npz', *list((ROOT/'vision/models').glob('sign_templates*.npz'))]:
    backup(path)
    with np.load(path, allow_pickle=False) as archive:
        arrays = {k: archive[k] for k in archive.files}
    old = {k: v.copy() for k, v in arrays.items()}
    if 'meta' in arrays:
        meta = json.loads(str(arrays['meta']))
        for record in meta:
            record['path'] = mapped(record['path'])
        arrays['meta'] = np.array(json.dumps(meta, ensure_ascii=False))
    if 'sources' in arrays:
        arrays['sources'] = np.array([mapped(str(v)) for v in arrays['sources']])
    np.savez_compressed(path, **arrays)
    with np.load(path, allow_pickle=False) as check:
        for k in arrays:
            if k not in ('meta', 'sources'):
                assert np.array_equal(old[k], check[k]), (path, k)

for folder in ('vision/m1/manifests', 'vision/manifests'):
    for path in (ROOT/folder).glob('*.json'):
        data = json.loads(path.read_text(encoding='utf-8-sig'))
        changed = False
        for record in data.get('samples', []):
            value = record.get('file', '').replace('\\', '/')
            if 'video/' not in value:
                continue
            suffix = value[value.index('video/'):]
            target = ROOT / mapped(suffix)
            record['file'] = os.path.relpath(target, path.parent).replace('\\', '/')
            assert (path.parent / record['file']).is_file(), record['file']
            changed = True
        if changed:
            backup(path)
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def old_location(rel):
    for old, new in sorted(MAPPING, key=lambda pair: len(pair[1]), reverse=True):
        if rel == new or rel.startswith(new+'/'):
            return old + rel[len(new):]
    return rel

def migrate_doc(path):
    text = path.read_text(encoding='utf-8-sig')
    old_rel = old_location(path.relative_to(ROOT).as_posix())
    # Protect/translate relative hyperlink targets using their pre-move location.
    links = []
    def link(match):
        target = match[2]
        if target.startswith(('http:', 'https:', '#', 'mailto:', '/')):
            result = match[0]
        else:
            base, sep, anchor = target.partition('#')
            absolute = (ROOT / Path(old_rel).parent / base.replace('\\', '/')).resolve()
            try:
                rel = absolute.relative_to(ROOT).as_posix()
                new_target = ROOT/mapped(rel)
                new_rel = os.path.relpath(new_target, path.parent).replace('\\', '/')
                result = '[' + match[1] + '](' + new_rel + (sep+anchor if sep else '') + ')'
            except ValueError:
                result = match[0]
        links.append(result)
        return f'LAYOUTLINKTOKEN{len(links)-1}END'
    text = re.sub(r'\[([^\]\n]+)\]\(([^)\n]+)\)', link, text)
    pattern = r'(?<![\w/\\-])(' + '|'.join(re.escape(p[0]) for p in MAPPING) + r')([/\\])'
    replacements = dict(MAPPING)
    text = re.sub(pattern, lambda m: replacements[m[1]].replace('/', m[2])+m[2], text)
    for i, value in enumerate(links):
        text = text.replace(f'LAYOUTLINKTOKEN{i}END', value)
    path.write_text(text, encoding='utf-8', newline='')

docs = [ROOT/'README.md', ROOT/'AGENTS.md']
for folder in ('docs', 'ASR', 'vision', 'project'):
    docs.extend(p for p in (ROOT/folder).rglob('*.md')
                if not any(x in p.parts for x in ('_tmp', '_cache', 'video', 'ip_repo'))
                and not any(x.endswith(('.runs', '.gen', '.cache')) for x in p.parts))
for path in docs:
    migrate_doc(path)
print('Path metadata migrated; all model/tensor numerical arrays verified unchanged')
