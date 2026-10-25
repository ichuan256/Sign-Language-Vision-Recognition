"""Read-only checks for the four-module layout; no FPGA or board operations."""
from pathlib import Path
import ast
import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]

def main():
    dirs = sorted(p.name for p in ROOT.iterdir() if p.is_dir() and p.name != '.git')
    assert dirs == ['ASR', 'docs', 'project', 'vision'], dirs
    for folder in ('ASR', 'vision', 'project/scripts'):
        for p in (ROOT/folder).rglob('*.py'):
            if not any(x in p.parts for x in ('video', '__pycache__')):
                ast.parse(p.read_text(encoding='utf-8-sig'), filename=str(p))
    for rel, count in [('vision/data/manifests/manifest_fullframe_20261024.csv',636),
                       ('vision/data/legacy/material/dataset_manifest_20261020.csv',225)]:
        with (ROOT/rel).open(encoding='utf-8-sig', newline='') as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == count
        assert all((ROOT/r['输出路径']).is_file() for r in rows), rel
    for p in (ROOT/'vision/m1/manifests').glob('*.json'):
        for r in json.loads(p.read_text(encoding='utf-8')).get('samples', []):
            assert (p.parent/r['file']).is_file(), (p, r['file'])
    manifest = ROOT/'project/board/w6/release_manifest.json'
    for r in json.loads(manifest.read_text(encoding='utf-8'))['artifacts']:
        p = manifest.parent/r['file']
        assert hashlib.sha256(p.read_bytes()).hexdigest() == r['sha256'], p
    xpr = ROOT/'project/fpga/project/glove/glove.xpr'
    tree = ET.parse(xpr)
    source_refs = []
    for node in tree.findall('.//File'):
        value = node.get('Path', '')
        if value.startswith('$PPRDIR/'):
            source_refs.append(xpr.parent/value.removeprefix('$PPRDIR/'))
        elif value.startswith('$PSRCDIR/') and node.get('Path','').endswith('.bd'):
            source_refs.append(xpr.parent/'glove.srcs'/value.removeprefix('$PSRCDIR/'))
    assert all(p.is_file() for p in source_refs), [str(p) for p in source_refs if not p.is_file()]
    docs = [ROOT/'README.md', ROOT/'AGENTS.md']
    for folder in ('docs', 'ASR', 'vision', 'project'):
        docs.extend(p for p in (ROOT/folder).rglob('*.md')
                    if not any(x in p.parts for x in ('_tmp', '_cache', 'video', 'ip_repo'))
                    and not any(x.endswith(('.runs', '.gen', '.cache')) for x in p.parts))
    broken = []
    for p in docs:
        for value in re.findall(r'\[[^\]\n]+\]\(([^)\n]+)\)', p.read_text(encoding='utf-8-sig')):
            if value.startswith(('http:', 'https:', '#', '/', 'mailto:')):
                continue
            if not (p.parent/value.split('#')[0]).exists():
                broken.append((str(p), value))
    assert not broken, broken
    print(f'PASS root layout; 636+225 media paths; M1 paths; bit/hwh hashes; {len(source_refs)} FPGA source paths; Python syntax')
    print(f'PASS relative Markdown links in {len(docs)} documents')

if __name__ == '__main__':
    main()
