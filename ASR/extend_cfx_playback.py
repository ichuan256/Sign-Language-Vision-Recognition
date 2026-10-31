"""Add a user-specified local playback batch; never change ASR acoustic models."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tarfile
from unittest.mock import patch

import cv2
from loop_core import VideoLexicon,normalize

ROOT=Path(__file__).resolve().parents[1]


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):h.update(block)
    return h.hexdigest()


def build(source,output,date):
    source=source.resolve();output=output.resolve()
    if not source.is_relative_to(ROOT/'vision/video/done') or not source.is_dir():raise ValueError('Explicit local done batch required')
    if output.exists() or not output.is_relative_to(ROOT/'project/_tmp'):raise ValueError('New scratch output required')
    output.mkdir(parents=True)
    active=ROOT/'ASR/phrases_sd.json';original=active.read_bytes();base=json.loads(original)
    (output/'phrases_sd_before.json').write_bytes(original)
    manifest=json.loads(original);used={normalize(p) for e in base['clips'] for p in e['phrases']}
    cache=(ROOT/'ASR'/base['asset_cache_dir']).resolve()
    if not cache.is_relative_to(ROOT/'project/_cache'):raise ValueError('Unexpected existing playback cache')
    inventory=[];added=[];duplicates=[];transfer=[];seen_labels=set();alternates=[]
    for path in sorted(source.rglob('*.mp4')):
        if not path.resolve().is_relative_to(source):raise ValueError('Media path escapes the requested batch')
        if len(path.relative_to(source).parts)!=2:
            raise ValueError('Ambiguous folder/file label: '+str(path))
        label=path.parent.name;key=normalize(label)
        if path.stem!=label:
            import re
            if re.fullmatch(re.escape(label)+r'_P\d+',path.stem) and (path.parent/(label+'.mp4')).is_file():
                alternates.append(dict(label=label,source=path.relative_to(ROOT).as_posix(),sha256=sha(path),
                    bytes=path.stat().st_size,reason='Explicit lesson suffix alternate; exact-label primary retained'))
                continue
            raise ValueError('Ambiguous folder/file label: '+str(path))
        if not key or key in seen_labels:raise ValueError('Duplicate local phrase: '+label)
        seen_labels.add(key);digest=sha(path);size=path.stat().st_size
        if size>16*1024*1024:raise ValueError('Video exceeds existing 16MiB playback limit: '+label)
        cap=cv2.VideoCapture(str(path));fps=cap.get(cv2.CAP_PROP_FPS)
        frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));w=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH));h=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if not cap.isOpened() or fps<=0 or frames<2 or min(w,h)<=0:raise ValueError('Invalid video: '+label)
        decoded=0
        while True:
            ok,_=cap.read()
            if not ok:break
            decoded+=1
        cap.release()
        if decoded!=frames:raise ValueError('Incomplete video decode: '+label)
        media=dict(width=w,height=h,fps=fps,frames=frames,duration_s=frames/fps)
        row=dict(label=label,source=path.relative_to(ROOT).as_posix(),sha256=digest,bytes=size,
            media=media,fully_decoded=True,action='preserve_existing' if key in used else 'add')
        inventory.append(row)
        (output/'progress.json').write_text(json.dumps(dict(processed=len(inventory),last_label=label,
            added_so_far=len(added)),ensure_ascii=False)+'\n',encoding='utf-8')
        if key in used:duplicates.append(row);continue
        sd_file='clips_cfx567_'+date.replace('-','')+'/'+digest+'.mp4'
        entry=dict(phrases=[label],label=label,file=sd_file,sha256=digest,source_file=row['source'],
            source_review_status='user_requested_playback_batch; folder_and_filename_agree; SHA_and_decode_verified',
            playback_only=True,media=media)
        manifest['clips'].append(entry);added.append(entry);used.add(key)
        target=cache/(digest+'.mp4')
        if target.exists() and sha(target)!=digest:raise RuntimeError('Cache collision')
        if not target.exists():shutil.copyfile(path,target)
        transfer.append(dict(source=row['source'],file=sd_file,sha256=digest,bytes=size))
        print('CFX_PLAYBACK_ADD',len(added),label,flush=True)
    manifest.update(playback_extension_date=date,training_manifest_unchanged=True,prefer_verified_cache=True)
    manifest['extension_sources']=list(base.get('extension_sources',[]))+[source.relative_to(ROOT).as_posix()]
    manifest['label_policy']=base.get('label_policy','')+'; cfx/567 adds exact folder labels only, keeps every existing mapping unchanged'
    candidate=output/'phrases_sd_extended.json'
    candidate.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if manifest['clips'][:len(base['clips'])]!=base['clips']:raise RuntimeError('Old entries changed')
    with patch('loop_core.build_opener',side_effect=AssertionError('Offline validation must use verified cache')):
        lexicon=VideoLexicon(candidate_for_cache(candidate,manifest,output))
    # candidate_for_cache uses an absolute local cache path, while the deployable
    # manifest retains the original path relative to ASR/.
    cases=[]
    sentences=['今天上午下雨，下午多云。','明天上午去公园。','今年中秋节放假。','坐公交车到人民广场，换乘地铁。',
        '为什么担心？','准备雨伞，注意安全。','冬天下雪，夏天下雨。','元宵节、劳动节、国庆节。']
    for sentence in sentences:
        clips,missing=lexicon.match(sentence)
        cases.append(dict(sentence=sentence,missing=missing,labels=[c['label'] for c in clips]))
    for entry in added:
        clips,missing=lexicon.match(entry['phrases'][0])
        if missing or len(clips)!=1 or clips[0]['label']!=entry['label']:raise RuntimeError('New phrase does not match: '+entry['label'])
    report=dict(date=date,source_directory=source.relative_to(ROOT).as_posix(),input_files=len(inventory)+len(alternates),
        validated_primary_files=len(inventory),alternate_files_preserved=alternates,
        original_entries=len(base['clips']),new_entries=len(added),preserved_duplicate_words=len(duplicates),
        total_entries=len(manifest['clips']),total_phrases=len(used),
        total_videos=len({p['sha256'] for e in manifest['clips'] for p in e.get('sequence',[e])}),
        original_manifest_sha256=hashlib.sha256(original).hexdigest(),candidate_sha256=sha(candidate),
        original_entries_unchanged=True,old_cache_preserved=True,training_changed=False,ASR_model_changed=False,
        new_SD_bytes=sum(t['bytes'] for t in transfer),transfer=transfer,added=added,duplicates=duplicates,
        source_inventory=inventory,sentence_cases=cases,SD_sync_completed=False)
    (output/'build_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with tarfile.open(output/'new_sd_assets.tar','w') as archive:
        for item in transfer:archive.add(ROOT/item['source'],arcname=item['sha256']+'.mp4',recursive=False)
    print(json.dumps({k:report[k] for k in ('input_files','new_entries','preserved_duplicate_words','total_entries','total_phrases','total_videos','new_SD_bytes')},ensure_ascii=False),flush=True)


def candidate_for_cache(candidate,manifest,output):
    data=dict(manifest);data['asset_cache_dir']=str((ROOT/'ASR'/manifest['asset_cache_dir']).resolve())
    check=output/'offline_cache_validation.json'
    check.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return check


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=ROOT/'vision/video/done/cfx/567')
    p.add_argument('--output',type=Path,required=True);p.add_argument('--date',default='2026-10-31')
    args=p.parse_args();build(args.source,args.output,args.date)
