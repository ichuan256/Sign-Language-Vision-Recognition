"""Geometry and temporal safety tests; no camera or speech device required."""
import math
import unittest
from vision.classify.hand_digits import classify_hand,StableHandDigits


def hand(number):
    points=[[.5,.9,0],[.38,.76,0],[.30,.68,0],[.42,.70,0],[.48,.68,0]]
    for i,(x,y) in enumerate(((.4,.65),(.5,.62),(.6,.65),(.69,.70))):
        up=i<min(number,4)
        points.extend([[x,y,0],[x,y-(.20 if up else .13),0],
            [x if up else x+.02,y-(.32 if up else .03),0],
            [x if up else x+.02,y-.43 if up else y+.05,0]])
    if number==5:points[3:5]=[[.22,.59,0],[.14,.50,0]]
    return points


class Geometry(unittest.TestCase):
    def test_numbers_survive_mirroring_rotation_and_uniform_scale(self):
        for number in range(1,6):
            for rotation in (0,.8,math.pi/2,math.pi):
                for mirrored in (False,True):
                    points=[]
                    for x,y,z in hand(number):
                        x=(x-.5)*(-1 if mirrored else 1);y-=.5
                        points.append([.5+.8*(x*math.cos(rotation)-y*math.sin(rotation)),
                            .5+.8*(x*math.sin(rotation)+y*math.cos(rotation)),z])
                    with self.subTest(number=number,rotation=rotation,mirrored=mirrored):
                        self.assertEqual(classify_hand(points,(1000,1000))['value'],number)

    def test_fist_missing_tiny_and_nonfinite_hands_do_not_count(self):
        self.assertIsNone(classify_hand(hand(0),(1000,1000))['value'])
        self.assertIsNone(classify_hand([])['value'])
        points=hand(5);points[8][0]=math.nan
        self.assertIsNone(classify_hand(points)['value'])
        self.assertIsNone(classify_hand([[.5,.5,0]]*21)['value'])


class Temporal(unittest.TestCase):
    def observe(self,model,value,start,duration=1.0):
        return [model.update([hand(value),None],start+i*.1,(1000,1000)) for i in range(round(duration*10))]

    def test_brief_motion_does_not_announce_and_held_digit_announces_once(self):
        model=StableHandDigits()
        rows=self.observe(model,1,0,.3)+self.observe(model,2,.3,2)
        self.assertEqual([r['announce'] for r in rows if r['announce'] is not None],[2])
        self.assertEqual(rows[-1]['value'],2)

    def test_changed_digits_announce_and_repeating_after_hand_removal_rearms(self):
        model=StableHandDigits()
        rows=self.observe(model,1,0)+self.observe(model,2,1)
        rows += [model.update([None,None],2+i*.1,(1000,1000)) for i in range(10)]
        rows += self.observe(model,2,3)
        self.assertEqual([r['announce'] for r in rows if r['announce'] is not None],[1,2,2])

    def test_two_hands_are_rejected(self):
        model=StableHandDigits()
        for i in range(20):
            row=model.update([hand(2),hand(3)],i*.1,(1000,1000))
            self.assertIsNone(row['value']);self.assertIsNone(row['announce'])
        self.assertEqual(row['hand_count'],2)

    def test_large_frame_gap_does_not_count_as_stable_hold(self):
        model=StableHandDigits()
        self.observe(model,3,0,.3)
        row=model.update([hand(3)],2,(1000,1000))
        self.assertFalse(row['stable']);self.assertIsNone(row['announce'])

if __name__=='__main__':unittest.main()
