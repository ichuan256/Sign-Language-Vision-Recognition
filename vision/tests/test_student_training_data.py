"""Leakage, human-label provenance, masked metrics and geometric invariants."""
import json
import numpy as np
import pytest
from vision.keypoints.student_data import (grouped_split,select_balanced,hand_crop,
    apply_reviews,coordinate_metrics,augment,load_dataset,digest)
from vision.keypoints.student_review import write_review


def test_duplicate_content_and_source_aliases_never_cross_splits():
    rows=[dict(sha256=str(i),source_groups=['g'+str(i)],source_family='family') for i in range(7)]
    rows.append(dict(sha256='0',source_groups=['g1'],source_family='family'))
    rows.append(dict(sha256='extra',source_groups=['g2','g3'],source_family='family'))
    planned,assignment=grouped_split(rows)
    assert planned[0]['split_group']==planned[1]['split_group']
    assert planned[2]['split_group']==planned[3]['split_group']
    assert {r['split'] for r in planned}=={'train','validation','test'}
    assert assignment==grouped_split(list(reversed(rows)))[1]
    assert len(select_balanced(planned,0,123))==len(rows)


def review_file(tmp_path,**updates):
    item=dict(sample_id='unknown',status='accepted',reviewer='human-reviewer',
        annotation_origin='human',human_verified=True,presence=False,landmarks_xy=None)
    item.update(updates);path=tmp_path/'reviews.jsonl';path.write_text(json.dumps(item)+'\n');return path


def test_unknown_region_is_not_a_negative_until_named_human_review(tmp_path):
    y=np.zeros((1,65),np.float32);m=np.zeros_like(y);records=[dict(sample_id='unknown',pose_source='none')]
    _,unreviewed,_=apply_reviews(y,m,records)
    assert not unreviewed.any()
    _,reviewed,meta=apply_reviews(y,m,records,review_file(tmp_path))
    assert np.flatnonzero(reviewed[0]).tolist()==[63] and meta[0]['presence_source']=='human'
    assert not m.any()  # immutable teacher arrays
    with pytest.raises(ValueError,match='human verification'):
        apply_reviews(y,m,records,review_file(tmp_path,human_verified=False))
    with pytest.raises(ValueError,match='boolean presence'):
        apply_reviews(y,m,records,review_file(tmp_path,presence=0))


def test_manual_partial_xy_does_not_turn_relative_z_into_human_truth(tmp_path):
    y=np.zeros((1,65),np.float32);m=np.ones_like(y);records=[dict(sample_id='unknown',pose_source='teacher')]
    flags=[True,True]+[False]*19;xy=[[.1,.2],[.5,.7]]+[None]*19
    labels,mask,meta=apply_reviews(y,m,records,review_file(tmp_path,presence=True,landmarks_xy=xy,visible=flags))
    assert mask[0,:63].reshape(21,3)[:,2].sum()==0
    assert mask[0,:63].sum()==4 and meta[0]['pose_source']=='human'
    assert labels[0,:2].tolist()==pytest.approx([.1,.2])
    with pytest.raises(ValueError,match='visibility'):
        apply_reviews(y,m,records,review_file(tmp_path,presence=True,landmarks_xy=xy,visible=[1]*21))


def test_pck_ignores_missing_points_and_uses_visible_hand_scale():
    truth=np.zeros((1,65),np.float32);mask=np.zeros_like(truth);prediction=np.full_like(truth,99.)
    truth[0,3]=1.;mask[0,[0,1,3,4]]=1.;prediction[0,:6]=[0,0,0,1.1,0,0]
    metrics=coordinate_metrics(prediction,truth,mask)
    assert metrics['visible_points']==2 and metrics['PCK_at_005']==.5
    assert metrics['mean_normalized_error']==pytest.approx(.05)
    assert coordinate_metrics(prediction,truth,np.zeros_like(mask)) is None


def test_roi_affine_maps_teacher_xy_and_z_consistently():
    image=np.zeros((200,300,3),np.uint8)
    hand=np.random.default_rng(4).uniform(.3,.6,(21,3));hand[0,:2]=[.5,.6];hand[9,:2]=[.5,.3]
    crop,target,affine,side=hand_crop(image,hand)
    pixels=hand[:,:2]*[300,200]
    assert crop.shape==(128,128,3)
    assert np.allclose(target[:,:2]*127,pixels@affine[:,:2].T+affine[:,2],atol=1e-4)
    assert np.allclose(target[:,2],hand[:,2]*300/side)
    y=np.r_[target.reshape(-1),1,0].astype(np.float32);m=np.ones(65,np.float32)
    a=augment(crop,y,m,96,np.random.default_rng(8));b=augment(crop,y,m,96,np.random.default_rng(8))
    assert all(np.array_equal(x,z) for x,z in zip(a,b))
    assert a[0].shape==(96,96,3) and 0<=a[0].min()<=a[0].max()<=1
    assert a[1][64]==0  # no implicit mirrored anatomical label


def test_dataset_loader_rejects_cross_split_same_video_content(tmp_path):
    records=[dict(sample_id=str(i),split_group='g'+str(i),split=s,source_sha256='same')
        for i,s in enumerate(['train','test'])]
    metadata=tmp_path/'records.jsonl';metadata.write_text(''.join(json.dumps(r)+'\n' for r in records))
    shard=tmp_path/'data.npz';np.savez(shard,images=np.zeros((2,128,128,3),np.uint8),
        targets=np.zeros((2,65),np.float32),masks=np.ones((2,65),np.float32),sample_ids=np.array(['0','1']))
    (tmp_path/'dataset.json').write_text(json.dumps(dict(completed=True,records_sha256=digest(metadata),
        shards=[dict(file='data.npz',sha256=digest(shard))])))
    with pytest.raises(ValueError,match='leakage'):load_dataset(tmp_path)


def test_review_tool_escapes_embedded_script_end(tmp_path):
    record=dict(sample_id='</script>',split='test',kind='unknown_candidate')
    assert write_review(tmp_path,[record],1)==1
    html=(tmp_path/'index.html').read_text(encoding='utf-8')
    assert html.count('</script>')==1 and 'human_verified:true' in html
