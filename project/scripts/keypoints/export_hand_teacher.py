"""Fresh Holistic pseudo-labels from a SHA-bound plan; missing detections remain unknown."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
import cv2
import numpy as np
from vision.keypoints.student_data import digest,hand_crop
from vision.keypoints.review_sampling import hand_focus_score
from vision.keypoints.review_geometry import review_context


def main():
    import mediapipe as mp
    from vision.keypoints.student_review import write_review
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--fps',type=float,default=5);p.add_argument('--max-frames-per-clip',type=int,default=20)
    p.add_argument('--review-samples',type=int,default=200)
    p.add_argument('--clear-review',action='store_true')
    a=p.parse_args();out=a.output.resolve()
    if out.exists() or not out.is_relative_to(ROOT/'project/_tmp'):raise ValueError('New project/_tmp dataset required')
    if not 0<a.fps<=30 or a.max_frames_per_clip<1:raise ValueError('Invalid sampling limits')
    plan=json.loads(a.plan.read_text(encoding='utf-8'))
    if plan['schema']!='hand_teacher_plan_v1':raise ValueError('Wrong source plan')
    out.mkdir(parents=True);(out/'shards').mkdir();(out/'review/images').mkdir(parents=True);(out/'review/context').mkdir()
    options=dict(static_image_mode=False,model_complexity=1,smooth_landmarks=False,
        enable_segmentation=False,refine_face_landmarks=False,min_detection_confidence=.5,min_tracking_confidence=.5)
    records=[];shards=[];frame_count=0;no_hand_frames=0;skipped=Counter()
    for clip in plan['selected']:
        path=ROOT/clip['path']
        if digest(path)!=clip['sha256']:raise ValueError('Source SHA changed')
        cap=cv2.VideoCapture(str(path));images=[];targets=[];masks=[];ids=[]
        if not cap.isOpened():raise ValueError('Source cannot decode')
        fps=cap.get(cv2.CAP_PROP_FPS)
        if not np.isfinite(fps) or fps<=0:raise ValueError('Source FPS invalid')
        frame_id=0;next_time=0.;sampled=0
        try:
            with mp.solutions.holistic.Holistic(**options) as teacher:
                while sampled<a.max_frames_per_clip:
                    ok,frame=cap.read()
                    if not ok:break
                    index=frame_id;frame_id+=1;timestamp=index/fps
                    if timestamp+1e-9<next_time:continue
                    next_time+=1/min(a.fps,fps);sampled+=1;frame_count+=1
                    result=teacher.process(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB));items=[];teacher_hands=0
                    for side,landmarks in enumerate((result.left_hand_landmarks,result.right_hand_landmarks)):
                        if landmarks is None:continue
                        teacher_hands+=1
                        hand=np.array([[v.x,v.y,v.z] for v in landmarks.landmark],np.float32)
                        try:rgb,points,affine,roi_side=hand_crop(frame,hand)
                        except ValueError as error:skipped[str(error)]+=1;continue
                        target=np.r_[points.reshape(-1),1.,float(side)].astype(np.float32)
                        items.append((str(side),rgb,target,np.ones(65,np.float32),affine,roi_side,'teacher_positive'))
                    if teacher_hands==0:no_hand_frames+=1
                    # One deterministic candidate region: never assume it is background truth.
                    h,w=frame.shape[:2];side=max(16,int(min(h,w)*.45));spanx=max(1,w-side);spany=max(1,h-side)
                    rng=np.random.default_rng(int(clip['sha256'][:8],16)+index)
                    x=int(rng.integers(0,spanx));y=int(rng.integers(0,spany))
                    affine=np.array([[127/side,0,-x*127/side],[0,127/side,-y*127/side]],np.float32)
                    rgb=cv2.cvtColor(cv2.warpAffine(frame,affine,(128,128)),cv2.COLOR_BGR2RGB)
                    items.append(('unknown',rgb,np.zeros(65,np.float32),np.zeros(65,np.float32),affine,side,'unknown_candidate'))
                    context_id=clip['sha256'][:16]+'_'+str(index)
                    for suffix,rgb,target,mask,affine,roi_side,kind in items:
                        sid=context_id+'_'+suffix
                        images.append(rgb);targets.append(target);masks.append(mask);ids.append(sid)
                        initial=target[:63].reshape(21,3)[:,:2].tolist() if suffix!='unknown' else None
                        cv2.imwrite(str(out/'review/context'/(sid+'.jpg')),review_context(frame,affine,initial))
                        review_affine=affine*(511/127)
                        native_size=min(256,max(32,round(roi_side)))
                        native=cv2.warpAffine(frame,affine*((native_size-1)/127),(native_size,native_size))
                        focus=hand_focus_score(native,target[:63].reshape(21,3)[:,:2]) if kind=='teacher_positive' else 0.
                        review_image=cv2.warpAffine(frame,review_affine,(512,512))
                        cv2.imwrite(str(out/'review/images'/(sid+'.jpg')),review_image,[cv2.IMWRITE_JPEG_QUALITY,95])
                        records.append(dict(sample_id=sid,source_path=clip['path'],source_sha256=clip['sha256'],
                            source_groups=clip['source_groups'],split_group=clip['split_group'],split=clip['split'],
                            performer_id=None,source_frame=index,source_timestamp_s=timestamp,kind=kind,
                            pose_source='teacher' if suffix!='unknown' else 'none',presence_source='teacher' if suffix!='unknown' else 'none',
                            handedness_source='teacher' if suffix!='unknown' else 'none',teacher_confidence=None,
                            source_size=[w,h],affine_source_to_roi=affine.tolist(),affine_dtype=str(affine.dtype),ROI_side_source_pixels=float(roi_side),
                            focus_score=focus,focus_method='eroded_hand_hull_clipped_Laplacian_energy_v1',review_image_size=512,
                            context='context/'+sid+'.jpg',image='images/'+sid+'.jpg',
                            initial_xy=initial,
                            review_status='pending'))
        finally:cap.release()
        if not sampled:raise ValueError('No frames from source')
        file='shards/'+clip['sha256'][:20]+'.npz'
        np.savez_compressed(out/file,images=np.stack(images),targets=np.stack(targets),masks=np.stack(masks),sample_ids=np.array(ids))
        shards.append(dict(file=file,sha256=digest(out/file),rows=len(ids),split=clip['split']))
        print('TEACHER_CLIP_DONE',len(shards),'frames',sampled,'ROIs',sum(k.endswith(('_0','_1')) for k in ids),flush=True)
    metadata=out/'records.jsonl'
    metadata.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records),encoding='utf-8')
    policy=dict(min_source_width=1280,min_source_height=720,min_native_side=96,min_hand_focus=15,
        max_per_clip=2,min_time_gap_s=.4) if a.clear_review else None
    review=write_review(out/'review',records,a.review_samples,policy)
    model_hashes={}
    for name in ('hand_landmark/hand_landmark_full.tflite','pose_landmark/pose_landmark_full.tflite','holistic_landmark/hand_recrop.tflite'):
        path=Path(mp.__file__).parent/'modules'/name
        if path.is_file():model_hashes[name]=digest(path)
    report=dict(schema='hand_teacher_dataset_v1',completed=True,plan_sha256=digest(a.plan),
        teacher=dict(name='MediaPipe Holistic',version=mp.__version__,options=options,model_sha256=model_hashes,
            handedness='unmirrored anatomical association from Holistic, weak labels, left=0 right=1',confidence_available=False),
        frames_sampled=frame_count,frames_without_teacher_hand=no_hand_frames,records=len(records),
        counts=dict(Counter(r['kind'] for r in records)),split_counts=dict(Counter(r['split'] for r in records)),
        records_sha256=digest(metadata),shards=shards,review_candidates=review,review_selection_policy=policy,skipped_geometry=dict(skipped),
        output_ABI='hand_student_65_v1',targets='63 normalized ROI xyz; presence; right-hand label',
        limitations=['All teacher landmarks are pseudo-labels; visibility and confidence are not supplied by Holistic',
            'Unknown candidate masks are zero; undetected hand is never a no-hand training label',
            'Teacher-guided crops do not validate autonomous detection; no manual GT until named review imported'])
    (out/'dataset.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('completed','frames_sampled','counts','split_counts','review_candidates')},indent=2))


if __name__=='__main__':main()
