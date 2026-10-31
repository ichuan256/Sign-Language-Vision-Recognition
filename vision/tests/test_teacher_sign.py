import unittest
from collections import deque
from types import SimpleNamespace
import threading
import numpy as np
from vision.classify.teacher_sign import TemporalSignModel,LiveSignHead,resample


def sample(offset=0):
    features=np.zeros((24,392),np.float32)
    features[:,288:]=1
    features[:,:102]=np.linspace(0,1,24)[:,None]+offset
    features[:,204:288]=offset
    return features


class SignHeadTests(unittest.TestCase):
    def test_nearest_template_retains_semantic_label(self):
        model=TemporalSignModel([sample(),sample(2)],['谢谢','再见'])
        result=model.predict(sample())
        self.assertEqual(result['candidate'],'谢谢');self.assertTrue(result['accepted'])
        self.assertFalse(result['score_is_probability'])

    def test_missing_hands_rejected_even_with_matching_body(self):
        model=TemporalSignModel([sample(),sample(2)],['谢谢','再见'])
        query=sample();query[:,390:]=0
        self.assertFalse(model.predict(query)['accepted'])

    def test_identical_classes_not_forced_to_known_word(self):
        model=TemporalSignModel([sample(),sample()],['谢谢','再见'])
        result=model.predict(sample());self.assertFalse(result['accepted'])
        self.assertIsNone(result['label'])

    def test_source_group_holdout_excludes_all_its_clips(self):
        model=TemporalSignModel([sample(),sample(2),sample(.1)],['谢谢','再见','早上'],
            [{'source_group':'A'},{'source_group':'B'},{'source_group':'B'}])
        result=model.predict(sample(),exclude_group='A')
        self.assertNotIn('谢谢',[r['label'] for r in result['ranked']])

    def test_resampling_does_not_interpolate_missing_masks(self):
        features=sample();features[3:8,288:]=0
        result=resample(features,31)
        self.assertTrue(np.isin(result[:,288:],[0,1]).all())

    def test_video_time_reset_clears_stale_label_and_submit_timer(self):
        head=LiveSignHead.__new__(LiveSignHead)
        head.buffer=deque([(None,None,5.)]);head.condition=threading.Condition()
        head.generation=0;head.pending=None;head.previous='谢谢';head.streak=4
        head.last_submit=5.;head.last_hand_time=5.;head.latest={'label':'谢谢'}
        result=SimpleNamespace(pose_landmarks=None,left_hand_landmarks=None,right_hand_landmarks=None)
        head.observe(result,np.zeros((10,10,3),np.uint8),0.)
        self.assertIsNone(head.latest['label']);self.assertLess(head.last_submit,0.)


if __name__=='__main__':unittest.main()
