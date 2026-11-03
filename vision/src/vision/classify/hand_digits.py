"""Single-hand finger counts over frozen teacher landmarks; no trained head."""
import math


def classify_hand(points, image_size=(1280,720)):
    """Frontal palm, any in-plane rotation or mirroring. Return 1..5 or None."""
    if len(points)!=21:return dict(value=None,reason='手部关键点不完整',fingers=[])
    width,height=image_size
    xy=[(float(p[0])*width,float(p[1])*height) for p in points]
    if not all(math.isfinite(v) for p in xy for v in p):
        return dict(value=None,reason='手部关键点无效',fingers=[])
    def distance(a,b):return math.dist(xy[a],xy[b])
    def angle(a,b,c):
        u=[xy[a][i]-xy[b][i] for i in range(2)];v=[xy[c][i]-xy[b][i] for i in range(2)]
        denominator=math.hypot(*u)*math.hypot(*v)
        if denominator<1e-6:return 0
        return math.degrees(math.acos(max(-1,min(1,sum(x*y for x,y in zip(u,v))/denominator))))
    palm=distance(5,17)
    if palm<20 or distance(0,9)<20:return dict(value=None,reason='请将手掌靠近并朝向镜头',fingers=[])
    thumb=(angle(2,3,4)>=150 and distance(4,5)>.75*palm and distance(4,17)>1.12*distance(3,17))
    fingers=[thumb]
    for mcp,pip,dip,tip in ((5,6,7,8),(9,10,11,12),(13,14,15,16),(17,18,19,20)):
        bend=angle(mcp,pip,tip);ratio=distance(0,tip)/max(distance(0,pip),1e-6)
        if bend>=155 and ratio>=1.08:fingers.append(True)
        elif bend<=130 or ratio<=.95:fingers.append(False)
        else:return dict(value=None,reason='请伸直手指并保持手势',fingers=[])
    count=sum(fingers)
    return dict(value=count or None,reason='手势已识别' if count else '请伸出1～5根手指',fingers=fingers)


class StableHandDigits:
    def __init__(self, stable_seconds=.6, min_frames=4, reset_seconds=.7, cooldown_seconds=1.0):
        self.stable_seconds=stable_seconds;self.min_frames=min_frames;self.reset_seconds=reset_seconds
        self.cooldown_seconds=cooldown_seconds;self.candidate=None;self.since=0;self.frames=0
        self.last_time=None;self.invalid_since=None;self.last_emitted=None;self.last_emitted_time=-math.inf
        self.events=0

    def update(self,hands,now,image_size=(1280,720)):
        if self.last_time is not None and (now<self.last_time or now-self.last_time>.45):
            self.candidate=None;self.frames=0
            if now<self.last_time or now-self.last_time>=self.reset_seconds:self.last_emitted=None
        self.last_time=now
        present=[h for h in hands if h is not None]
        result=(classify_hand(present[0],image_size) if len(present)==1 else
                dict(value=None,reason='请只伸出一只手' if present else '请伸出一只手',fingers=[]))
        raw=result['value'];stable=False;announce=None
        if raw is None:
            self.candidate=None;self.frames=0
            if self.invalid_since is None:self.invalid_since=now
            if now-self.invalid_since>=self.reset_seconds:self.last_emitted=None
        else:
            self.invalid_since=None
            if raw!=self.candidate:self.candidate=raw;self.since=now;self.frames=0
            self.frames+=1
            stable=now-self.since>=self.stable_seconds and self.frames>=self.min_frames
            if stable and raw!=self.last_emitted and now-self.last_emitted_time>=self.cooldown_seconds:
                announce=raw;self.last_emitted=raw;self.last_emitted_time=now;self.events+=1
        return dict(value=raw if stable else None,candidate=raw,stable=stable,hand_count=len(present),
            fingers=result['fingers'],reason='已识别' if stable else '请保持手势' if raw else result['reason'],
            announce=announce,recognition_events=self.events)
