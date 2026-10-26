"""Head-specific supervision and fingertip scaling must retain the fixed source split."""
import numpy as np
import pytest
from vision.keypoints.student_data import training_partitions,coordinate_metrics,mask_teacher_source_exterior


def fixture():
    records=[dict(split=s,presence_source=p) for s,p in [
        ('train','teacher'),('train','human'),('train','human'),('train','none'),
        ('validation','human'),('test','human')]]
    y=np.zeros((6,65),np.float32);m=np.zeros_like(y)
    y[0,63]=1;m[0,:]=1  # positive teacher coordinates
    m[1,63]=1          # reviewed negative
    y[2,63]=1;m[2,63]=1  # presence-only partial hand
    m[4,:]=m[5,:]=1    # holdout coordinates may never enter train
    return y,m,records


def test_coordinate_only_excludes_zero_loss_auxiliary_images_from_bn():
    y,m,records=fixture();selection=training_partitions(y,m,records,disable_presence=True)
    assert selection['train'].tolist()==[0]
    assert not selection['active_masks'][:,63].any() and m[1,63]==1
    assert selection['negative_train_available']==1 and selection['negative_train_used']==0


def test_presence_training_includes_reviewed_positive_and_negative_auxiliary_rows():
    y,m,records=fixture();selection=training_partitions(y,m,records)
    assert selection['train'].tolist()==[0,1,2]
    assert selection['coordinates']['validation'].tolist()==[4]
    assert selection['coordinates']['test'].tolist()==[5]
    assert selection['presence_enabled'] and selection['negative_train_used']==1


def test_fingertips_use_the_full_visible_hand_diagonal():
    truth=np.zeros((1,65),np.float32);m=np.zeros_like(truth)
    truth[0,4*3]=1.;truth[0,8*3]=.5
    m[0,[0,1,4*3,4*3+1,8*3,8*3+1]]=1
    prediction=truth.copy();prediction[0,8*3]+=.1
    metrics=coordinate_metrics(prediction,truth,m,point_indices=(8,))
    assert metrics['visible_points']==1 and metrics['mean_normalized_error']==pytest.approx(.1)


def test_source_exterior_masking_preserves_values_human_labels_and_other_heads():
    y=np.full((2,65),.5,np.float32);m=np.ones_like(y)
    common=dict(affine_source_to_roi=[[1,0,-100],[0,1,-100]],source_size=[128,128])
    rows=[dict(common,pose_source='teacher'),dict(common,pose_source='human')]
    masked,records=mask_teacher_source_exterior(y,m,rows)
    assert not masked[0,:63].any() and masked[0,63:].all()
    assert masked[1].all() and m.all() and (y==.5).all()
    assert records[0]['source_exterior_points_masked']==21 and 'source_exterior_points_masked' not in rows[0]


def test_source_exterior_masking_uses_image_bounds_not_roi_bounds():
    y=np.full((1,65),.5,np.float32);m=np.ones_like(y);y[0,:3]=[.9,.5,0]
    rows=[dict(pose_source='teacher',affine_source_to_roi=[[1,0,0],[0,1,0]],source_size=[100,128])]
    masked,_=mask_teacher_source_exterior(y,m,rows)
    assert not masked[0,:3].any() and masked[0,3:].all()  # .9 in ROI maps outside the 100px source
