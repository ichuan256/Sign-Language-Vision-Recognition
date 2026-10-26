"""A memorization diagnostic may use human train XY only, with immutable source arrays."""
import numpy as np
import pytest
from vision.keypoints.student_data import human_xy_training_subset


def test_human_xy_selection_excludes_teacher_auxiliary_and_holdout():
    rows=[dict(sample_id=str(i),split='train',pose_source='human') for i in range(10)]
    rows[6]['split']='validation';rows[7]['split']='test';rows[8]['pose_source']='teacher';rows[9]['pose_source']='none'
    y=np.ones((10,65),np.float32);m=np.ones_like(y)
    indices,targets,masks=human_xy_training_subset(y,m,rows)
    assert indices.tolist()==list(range(6)) and targets.shape==(6,65)
    assert not masks[:,:63].reshape(6,21,3)[:,:,2].any() and not masks[:,63:].any()
    assert masks.sum()==6*21*2
    masks[:]=0;targets[:]=0
    assert y.all() and m.all()


def test_insufficient_reviewed_train_rows_fail_without_using_holdout():
    y=np.zeros((6,65),np.float32);m=np.ones_like(y)
    rows=[dict(sample_id=str(i),split='test',pose_source='human') for i in range(6)]
    with pytest.raises(ValueError,match='found 0'):human_xy_training_subset(y,m,rows)
    with pytest.raises(ValueError,match='At least two'):human_xy_training_subset(y,m,rows,count=1)
