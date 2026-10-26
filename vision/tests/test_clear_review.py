"""A clear annotation seed must not recycle adjacent frames or invent negative labels."""
import json
import numpy as np
from vision.keypoints.review_sampling import select_clear_review,hand_focus_score
from vision.keypoints.student_data import apply_reviews

POLICY=dict(min_source_width=1280,min_source_height=720,min_native_side=96,min_hand_focus=15,
    max_per_clip=2,min_time_gap_s=.4)


def test_external_text_edges_do_not_raise_hand_focus():
    image=np.zeros((128,128,3),np.uint8);image[:,::2]=255
    image[35:95,35:95]=100
    xy=np.tile([[.4,.4],[.6,.4],[.6,.6],[.4,.6]],(6,1))[:21]
    assert hand_focus_score(image,xy)==0


def record(i,**changes):
    r=dict(sample_id=str(i),source_size=[1920,1080],ROI_side_source_pixels=180,focus_score=30,
        kind='teacher_positive',split_group='a',source_sha256='clip',source_frame=i*20,source_timestamp_s=i*.8)
    r.update(changes);return r


def test_low_resolution_and_small_or_blurred_hands_cannot_fill_queue():
    records=[record(0,source_size=[352,288],focus_score=999),record(1,ROI_side_source_pixels=60),
        record(2,focus_score=1),record(3),record(4,kind='unknown_candidate',focus_score=0)]
    selected,report=select_clear_review(records,20,POLICY)
    assert {r['sample_id'] for r in selected}=={'3','4'}
    assert report['selected']==2  # no low-quality padding
    assert report['rejected']==dict(source_resolution=1,native_ROI_too_small=1,hand_focus=1)


def test_unique_frames_temporal_separation_and_source_quotas():
    records=[record(0),record(1,source_frame=0,source_timestamp_s=0,kind='unknown_candidate'),
        record(2,source_frame=2,source_timestamp_s=.1),record(3),record(4),
        record(5,split_group='b',source_sha256='other')]
    selected,report=select_clear_review(records,6,POLICY)
    for clip in {r['source_sha256'] for r in selected}:
        items=[r for r in selected if r['source_sha256']==clip]
        assert len(items)<=2
        if len(items)==2:assert abs(items[0]['source_timestamp_s']-items[1]['source_timestamp_s'])>=.4
    assert len({(r['source_sha256'],r['source_frame']) for r in selected})==len(selected)
    assert report['source_groups']=={'a':2,'b':1}
    assert select_clear_review(list(reversed(records)),6,POLICY)[0]==selected


def test_agent_quality_screen_excludes_whole_caption_obscured_clip():
    selected,report=select_clear_review([record(0),record(1),record(2,source_sha256='clear')],
        20,dict(POLICY,excluded_source_sha256=['clip']))
    assert [r['sample_id'] for r in selected]==['2']
    assert report['rejected']['visual_quality_screen']==2


def test_ungradable_human_review_masks_teacher_without_creating_absence(tmp_path):
    targets=np.ones((1,65),np.float32);masks=np.ones_like(targets)
    reviews=tmp_path/'reviews.jsonl'
    reviews.write_text(json.dumps(dict(sample_id='a',status='ungradable',reviewer='tester',
        annotation_origin='human',human_verified=True,presence=None,landmarks_xy=None)))
    y,m,records=apply_reviews(targets,masks,[dict(sample_id='a',pose_source='teacher')],reviews)
    assert not m.any() and y[0,63]==1 and masks.all()
    assert records[0]['quality_status']=='human_ungradable'
    assert records[0]['pose_source']==records[0]['presence_source']=='none'
