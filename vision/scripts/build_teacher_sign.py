"""Build a small audited temporal template head; never train/alter Holistic."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import cv2
import mediapipe as mp
import numpy as np
from vision.classify.teacher_sign import TemporalSignModel,resample,usable
from vision.keypoints.holistic import _landmarks
from vision.sign_video.features import build_features


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):h.update(block)
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--labels',nargs='+',default=['谢谢','再见','没关系','可以。','早上'])
    a=p.parse_args();out=a.output.resolve()
    if out.exists() or not out.is_relative_to(ROOT):raise ValueError('New workspace output required')
    out.mkdir(parents=True)
    pointer=json.loads((ROOT/'vision/data/manifests/current_available_fullframe.json').read_text(encoding='utf-8'))
    manifest=ROOT/pointer['manifest']
    if sha(manifest)!=pointer['sha256']:raise RuntimeError('Active source manifest changed')
    audit=json.loads((ROOT/'vision/analysis/dataset/label_source_audit_20261025.json').read_text(encoding='utf-8'))
    by_sha={r['sha256']:r for r in audit['records']};records=[];features=[];skipped=[];seen=set()
    with manifest.open(encoding='utf-8-sig',newline='') as stream:rows=list(csv.DictReader(stream))
    chosen=[r for r in rows if r['类别'] in a.labels]
    frozen={str(f.relative_to(Path(mp.__file__).parent)):sha(f) for f in (Path(mp.__file__).parent/'modules').rglob('*.tflite')}
    configuration=dict(method='frozen Holistic sign_xy_v1 + temporal nearest-template DTW',
        mediapipe_version=mp.__version__,model_complexity=1,teacher_weights_trained=False,
        teacher_package_tflite_hashes=frozen,source_manifest=pointer,requested_labels=a.labels,
        frames_per_clip_max=48,teacher_input='original video resolution; RGB; no mirror',
        threshold_status='heuristic; not camera-calibrated',new_human_annotations=False)
    (out/'configuration.json').write_text(json.dumps(configuration,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for index,row in enumerate(chosen):
        path=ROOT/row['输出路径'];digest=sha(path)
        if digest not in by_sha:raise RuntimeError('Unknown source SHA: '+str(path))
        provenance=by_sha[digest]['provenance']
        if digest in seen:continue
        if '上下文' in (provenance.get('label_scope') or ''):
            skipped.append(dict(path=row['输出路径'],reason='sentence-context action cycle, not verified isolated word'));continue
        seen.add(digest);cap=cv2.VideoCapture(str(path));fps=cap.get(cv2.CAP_PROP_FPS)
        n=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));poses=[];hands=[];times=[]
        width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH));height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if not cap.isOpened() or not np.isfinite(fps) or fps<=0 or n<2:raise RuntimeError('Cannot decode source')
        indices=np.unique(np.rint(np.linspace(0,n-1,min(48,n))).astype(int));wanted=set(indices);frame_id=0
        with mp.solutions.holistic.Holistic(static_image_mode=False,model_complexity=1,smooth_landmarks=True,
                min_detection_confidence=.5,min_tracking_confidence=.5) as teacher:
            while True:
                ok,bgr=cap.read()
                if not ok:break
                if frame_id in wanted:
                    result=teacher.process(cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB))
                    poses.append(_landmarks(result.pose_landmarks,33,visibility=True))
                    hands.append(np.stack([_landmarks(result.left_hand_landmarks,21),_landmarks(result.right_hand_landmarks,21)]))
                    times.append(frame_id/fps)
                frame_id+=1
        cap.release()
        if frame_id!=n:raise RuntimeError('Source decode truncated')
        arrays=build_features(np.stack(poses),np.stack(hands),np.array(times),width=width,height=height)
        if not usable(arrays['features']):
            skipped.append(dict(path=row['输出路径'],reason='insufficient teacher body/hand detections'));continue
        record=dict(label=row['类别'],source=row['输出路径'],sha256=digest,
            source_group=provenance.get('source_group'),candidate_id=provenance.get('candidate_id'),
            label_scope=provenance.get('label_scope'),duration_s=n/fps,hand_frame_rate=float(arrays['local_hand_valid'].any(axis=1).mean()))
        records.append(record);features.append(resample(arrays['features']))
        print(json.dumps(dict(processed=index+1,total=len(chosen),label=record['label'],templates=len(records)),ensure_ascii=False),flush=True)
    model=TemporalSignModel(features,[r['label'] for r in records],records)
    np.savez_compressed(out/'model.npz',features=np.stack(features),labels=np.array([r['label'] for r in records]),records_json=json.dumps(records,ensure_ascii=False))
    evaluation=[]
    for feature,record in zip(features,records):
        prediction=model.predict(feature,exclude_group=record['source_group'])
        present=any(r['label']==record['label'] and r['source_group']!=record['source_group'] for r in records)
        evaluation.append(dict(label=record['label'],sha256=record['sha256'],known_in_gallery=present,
            candidate=prediction.get('candidate'),correct=prediction.get('candidate')==record['label']))
    eligible=[r for r in evaluation if r['known_in_gallery']]
    report=dict(configuration=configuration,templates=len(records),classes=sorted(set(model.labels)),records=records,
        skipped=skipped,evaluation=dict(protocol='leave-source-group-out; candidate top1; no threshold tuning',
        eligible=len(eligible),correct=sum(r['correct'] for r in eligible),rows=evaluation),
        camera_accuracy=None,unknown_rejection_validated=False,model_sha256=sha(out/'model.npz'))
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    pointer_path=ROOT/'vision/data/models/usb_sign_current.json'
    pointer_path.write_text(json.dumps(dict(model=str((out/'model.npz').relative_to(ROOT)).replace('\\','/'),sha256=report['model_sha256'],labels=report['classes']),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(completed=True,templates=len(records),classes=report['classes'],group_test_eligible=len(eligible),group_test_correct=sum(r['correct'] for r in eligible)),ensure_ascii=False),flush=True)


if __name__=='__main__':main()
