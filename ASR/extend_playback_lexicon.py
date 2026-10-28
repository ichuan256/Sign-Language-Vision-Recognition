"""Build an auditable playback extension from frozen local inventories; no training."""
import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tarfile

import cv2
from loop_core import normalize

ROOT=Path(__file__).resolve().parents[1]
ALIASES={
 '不认识_陌生':['不认识','陌生'],'事情_办事':['事情','办事'],
 '碰面_遇见':['碰面','遇见'],'祝贺_祝福':['祝贺','祝福'],
 '预订_订':['预订','订'],'咖啡色_棕色':['咖啡色','棕色'],
 '手机_电话':['手机','电话'],'颜色_彩色':['颜色','彩色'],
 '亲戚-亲人':['亲戚','亲人'],'她-他是谁？':['她是谁','他是谁'],
 '不懂-不知道':['不懂','不知道'],'专心-认真':['专心','认真'],
 '懂-明白-知道':['懂','明白','知道'],'手语-打手语':['手语','打手语'],
 '现在-今天':['现在','今天'],
 '(无线上网)WiFi':['无线上网','WiFi','wifi','WIFI'],
}


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()


def csv_rows(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))


def build(output,sd_inventory):
    if output.exists() or not output.resolve().is_relative_to(ROOT/'project/_tmp'):
        raise ValueError('New workspace scratch output required')
    current=ROOT/'ASR/phrases_sd.json'
    base=json.loads(current.read_text(encoding='utf-8'))
    inventory=json.loads(sd_inventory.read_text(encoding='utf-8'))
    sd_by_sha={r['sha256']:r for r in inventory['files']}
    bound=json.loads((ROOT/'vision/data/manifests/protected_media_current.json').read_text(encoding='utf-8'))
    protected_path=ROOT/bound['protected_manifest']
    if sha(protected_path)!=bound['sha256']:
        raise RuntimeError('Protected inventory changed')
    protected={r['path']:r for r in csv_rows(protected_path) if r['availability']=='present'}
    full=ROOT/'vision/data/manifests/manifest_fullframe_20261024.csv'
    groups=collections.defaultdict(list)
    for row in csv_rows(full):groups[row['类别']].append(row)
    used={normalize(p) for e in base['clips'] for p in e['phrases']}
    output.mkdir(parents=True)
    (output/'phrases_sd_original.json').write_bytes(current.read_bytes())
    manifest=dict(base)
    manifest['clips']=list(base['clips'])
    manifest.update(asset_cache_dir='../project/_cache/asr_playback_20261028',prefer_verified_cache=True,
        playback_extension_date='2026-10-28',training_manifest_unchanged=True,
        extension_sources=['manifest_fullframe_20261024.csv','media_reconciled_20261026/protected.csv'],
        label_policy='Preserve original 142 mappings; explicit alternatives follow source labels; retain every ordered cycle of the chosen source candidate')
    sources=[];transfer={};excluded=[]
    cache=(ROOT/'ASR'/manifest['asset_cache_dir']).resolve();cache.mkdir(parents=True,exist_ok=True)
    for e in base['clips']:
        if e['sha256'] not in sd_by_sha:raise RuntimeError('Original SD asset absent: '+e['label'])
        p=ROOT/'ASR/.sd_cache'/(e['sha256']+'.mp4')
        if sha(p)!=e['sha256']:raise RuntimeError('Original cache changed')
        destination=cache/p.name
        if destination.exists() and sha(destination)!=e['sha256']:raise RuntimeError('Cache collision')
        if not destination.exists():shutil.copyfile(p,destination)
    for label,rows in sorted(groups.items()):
        aliases=ALIASES.get(label,[label])
        phrases=[]
        for phrase in aliases:
            key=normalize(phrase)
            if key and key not in used and key not in {normalize(p) for p in phrases}:phrases.append(phrase)
        if not phrases:continue
        candidates=[]
        for row in rows:
            relative=row['输出路径'];entry=protected.get(relative)
            if entry is None:continue
            path=(ROOT/relative).resolve()
            if not path.is_relative_to(ROOT/'vision/video/done') or sha(path)!=entry['sha256']:
                raise RuntimeError('Frozen source mismatch: '+relative)
            if path.stat().st_size>16*1024*1024:
                excluded.append(dict(label=label,file=relative,reason='Exceeds existing 16MiB asset download limit'));continue
            cap=cv2.VideoCapture(str(path))
            w=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH));h=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps=cap.get(cv2.CAP_PROP_FPS);frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));cap.release()
            if not w or not h or fps<=0 or frames<2:continue
            candidates.append((w*h,-len(path.name),row,path,entry,dict(width=w,height=h,fps=fps,frames=frames)))
        if not candidates:
            excluded.append(dict(label=label,reason='No hash-verified decodable bounded source'));continue
        chosen=max(candidates,key=lambda r:(r[0],r[1],r[3].name))
        candidate=re.match(r'(NL\d{2}_\d+)_C(\d+)',chosen[2]['样本编号'])
        selected=[chosen]
        if candidate:
            prefix=candidate.group(1)+'_C'
            selected=[c for c in candidates if c[2]['样本编号'].startswith(prefix)]
            selected.sort(key=lambda c:int(re.match(r'NL\d{2}_\d+_C(\d+)',c[2]['样本编号']).group(1)))
            cycles=[int(re.match(r'NL\d{2}_\d+_C(\d+)',c[2]['样本编号']).group(1)) for c in selected]
            if cycles!=list(range(1,max(cycles)+1)):raise RuntimeError('Missing source cycle for '+label)
        parts=[]
        for _,_,row,path,protected_row,media in selected:
            cap=cv2.VideoCapture(str(path));decoded=0
            while True:
                ok,frame=cap.read()
                if not ok:break
                decoded+=1
            cap.release()
            if decoded!=media['frames']:raise RuntimeError('Incomplete decode: '+str(path))
            digest=protected_row['sha256']
            on_sd=sd_by_sha.get(digest)
            sd_file=on_sd['file'] if on_sd else 'clips_extension_20261028/'+digest+'.mp4'
            if on_sd is None:transfer[digest]=dict(source=row['输出路径'],file=sd_file,bytes=path.stat().st_size,sha256=digest)
            destination=cache/(digest+'.mp4')
            if destination.exists() and sha(destination)!=digest:raise RuntimeError('Cache collision')
            if not destination.exists():shutil.copyfile(path,destination)
            parts.append(dict(file=sd_file,sha256=digest,source_file=row['输出路径'],
                              source_sample_id=row['样本编号'],media=media))
        row=selected[0][2]
        pending='/第2 第3课/' in row['输出路径']
        entry=dict(phrases=phrases,label=label,file=parts[0]['file'],sha256=parts[0]['sha256'],
            source_file=row['输出路径'],source_sample_id=row['样本编号'],
            source_review_status='original_audit_SHA_pending_training_review' if pending else 'original_inventory_SHA_verified',
            playback_only=True,media=parts[0]['media'])
        if len(parts)>1:entry['sequence']=parts
        manifest['clips'].append(entry)
        used.update(normalize(p) for p in phrases)
        sources.append(entry)
        print('PLAYBACK_BUILD',len(sources),label,flush=True)
    added_bytes=sum(r['bytes'] for r in transfer.values())
    if added_bytes+64*1024*1024>inventory['free_bytes']:raise RuntimeError('Insufficient SD space')
    report=dict(original_entries=len(base['clips']),total_entries=len(manifest['clips']),
        total_video_files=len({part['sha256'] for entry in manifest['clips'] for part in entry.get('sequence',[entry])}),
        sequenced_entries=sum('sequence' in e for e in manifest['clips']),
        total_match_phrases=len(used),new_entries=len(sources),new_SD_files=len(transfer),new_SD_bytes=added_bytes,
        original_manifest_sha256=sha(current),protected_manifest_sha256=sha(protected_path),
        fullframe_manifest_sha256=sha(full),training=False,training_pool_unchanged=True,
        added=sources,excluded=excluded,transfer=list(transfer.values()),
        cache_directory=cache.relative_to(ROOT).as_posix())
    (output/'phrases_sd_extended.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (output/'build_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with tarfile.open(output/'new_sd_assets.tar','w') as archive:
        for item in transfer.values():archive.add(ROOT/item['source'],arcname=item['sha256']+'.mp4',recursive=False)
    print(json.dumps({k:v for k,v in report.items() if k not in ('added','transfer','excluded')},ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--sd-inventory',type=Path,required=True)
    a=p.parse_args();build(a.output.resolve(),a.sd_inventory.resolve())
