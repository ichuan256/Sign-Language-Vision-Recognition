"""Few-shot temporal sign head over frozen Holistic sign_xy_v1 features.

Distances and margins are heuristic retrieval scores, never probabilities.
Nearest-frame temporal sampling preserves missing-data masks without imputation.
"""
from collections import deque
import json
from pathlib import Path
import threading
import time

import numpy as np

from .dtw import frame_costs,dtw_distance
from ..keypoints.holistic import _landmarks
from ..sign_video.features import build_features


def resample(features,length=24):
    values=np.asarray(features,np.float32)
    if values.ndim!=2 or values.shape[1]!=392 or len(values)<2 or not np.isfinite(values).all():
        raise ValueError('Finite [T>=2,392] sign_xy_v1 features required')
    indices=np.rint(np.linspace(0,len(values)-1,length)).astype(int)
    return values[indices].copy()


def usable(features):
    values=np.asarray(features)
    return (len(values)>=6 and float((values[:,390:392]>.5).any(axis=1).mean())>=.35
            and float((values[:,288:339]>.5).mean())>=.15)


class TemporalSignModel:
    def __init__(self,features,labels,records=None):
        self.features=np.stack([resample(x) for x in features])
        self.labels=list(labels);self.records=records or [{} for _ in labels]
        if len(self.features)!=len(self.labels) or len(set(self.labels))<2:raise ValueError('At least two sign classes required')

    @classmethod
    def load(cls,path):
        path=Path(path)
        with np.load(path,allow_pickle=False) as data:
            return cls(data['features'],data['labels'].tolist(),json.loads(str(data['records_json'])))

    def predict(self,features,exclude_group=None,exclude_sha=None):
        if not usable(features):return dict(candidate=None,label=None,accepted=False,reason='未检测到足够完整的身体和手部',ranked=[])
        query=resample(features);scores={}
        start=time.perf_counter()
        for label,template,record in zip(self.labels,self.features,self.records):
            if exclude_group is not None and record.get('source_group')==exclude_group:continue
            if exclude_sha is not None and record.get('sha256')==exclude_sha:continue
            costs=frame_costs(query,template,xy_weight=1,velocity_weight=.05,local_weight=1.5)
            score,_=dtw_distance(costs,band_ratio=.25)
            scores[label]=min(scores.get(label,float('inf')),score)
        ranked=sorted(scores.items(),key=lambda x:x[1])
        if len(ranked)<2:return dict(candidate=None,label=None,accepted=False,reason='可比较类别不足',ranked=[])
        best,distance=ranked[0];second=ranked[1][1]
        margin=(second-distance)/max(second,1e-9)
        accepted=bool(distance<.35 and margin>=.12)
        return dict(candidate=best,label=best if accepted else None,accepted=accepted,
            distance=float(distance),relative_margin=float(margin),reason='候选匹配' if accepted else '候选距离接近或超出阈值',
            ranked=[dict(label=label,distance=float(score)) for label,score in ranked[:3]],
            classifier_ms=(time.perf_counter()-start)*1000,score_is_probability=False)


class LiveSignHead:
    def __init__(self,path):
        self.generation=0
        self.model=TemporalSignModel.load(path);self.buffer=deque();self.condition=threading.Condition()
        self.pending=None;self.stop=False;self.last_submit=0;self.previous=None;self.streak=0
        self.latest=dict(label=None,candidate=None,accepted=False,reason='等待完整动作',ranked=[])
        self.completed=0;self.last_hand_time=None
        self.thread=threading.Thread(target=self.run,daemon=True);self.thread.start()

    def observe(self,result,bgr,timestamp):
        pose=_landmarks(result.pose_landmarks,33,visibility=True)
        hands=np.stack([_landmarks(result.left_hand_landmarks,21),_landmarks(result.right_hand_landmarks,21)])
        if self.buffer and timestamp<=self.buffer[-1][2]:
            self.buffer.clear()
            with self.condition:
                self.generation+=1;self.pending=None;self.previous=None;self.streak=0
                self.last_submit=timestamp-.6;self.last_hand_time=None
                self.latest=dict(label=None,candidate=None,accepted=False,reason='等待完整动作',ranked=[])
        self.buffer.append((pose,hands,timestamp))
        while self.buffer and self.buffer[0][2]<timestamp-3.5:self.buffer.popleft()
        if not np.isfinite(hands).any():
            with self.condition:
                self.latest=dict(label=None,candidate=None,accepted=False,reason='未检测到手',ranked=[])
                self.previous=None;self.streak=0;self.pending=None
                self.generation+=1
            if self.last_hand_time is None or timestamp-self.last_hand_time>.35:self.buffer.clear()
            return
        self.last_hand_time=timestamp
        if timestamp-self.last_submit<.6 or len(self.buffer)<8 or timestamp-self.buffer[0][2]<.8:return
        self.last_submit=timestamp;windows=[]
        for seconds in (1.2,2.2,3.4):
            rows=[r for r in self.buffer if r[2]>=timestamp-seconds]
            if len(rows)<8 or rows[-1][2]-rows[0][2]<.8:continue
            arrays=build_features(np.stack([r[0] for r in rows]),np.stack([r[1] for r in rows]),
                np.array([r[2] for r in rows]),width=bgr.shape[1],height=bgr.shape[0])
            windows.append(arrays['features'])
        with self.condition:
            self.pending=(timestamp,windows,self.generation);self.condition.notify()

    def run(self):
        while True:
            with self.condition:
                self.condition.wait_for(lambda:self.stop or self.pending is not None)
                if self.stop:return
                timestamp,windows,generation=self.pending;self.pending=None
            try:
                choices=[self.model.predict(x) for x in windows]
                candidates=[c for c in choices if c.get('candidate')]
                prediction=min(candidates,key=lambda x:x['distance']) if candidates else choices[0]
                with self.condition:
                    # Do not resurrect an old pose prediction after loss of hands.
                    if generation!=self.generation:continue
                    if self.buffer and timestamp<self.buffer[0][2]:continue
                    if not self.buffer:continue
                    candidate=prediction['candidate'] if prediction['accepted'] else None
                    self.streak=self.streak+1 if candidate and candidate==self.previous else 1 if candidate else 0
                    self.previous=candidate
                    prediction=dict(prediction,accepted=bool(candidate and self.streak>=2),
                        label=candidate if self.streak>=2 else None,stable_windows=self.streak,
                        source_timestamp_s=timestamp,completed_monotonic_s=time.monotonic())
                    self.latest=prediction;self.completed+=1
            except Exception as exc:
                with self.condition:self.latest=dict(label=None,candidate=None,accepted=False,reason=str(exc),ranked=[])

    def snapshot(self):
        with self.condition:
            result=dict(self.latest,classification_results=self.completed,backend='PC frozen Holistic + temporal DTW head',
                vocabulary=sorted(set(self.model.labels)))
        age=time.monotonic()-result.get('completed_monotonic_s',time.monotonic())
        if age>2.5:result.update(label=None,accepted=False,reason='识别结果已过期')
        return result

    def close(self):
        with self.condition:self.stop=True;self.condition.notify()
        self.thread.join(timeout=10)
