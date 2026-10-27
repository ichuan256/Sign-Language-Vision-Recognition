"""Compare board frames.json with pc_reference.py output, frame by frame."""
import argparse
import json
import numpy as np

KEYS=('x_center','y_center','width','height','rotation')

def rect(values):
    if isinstance(values,dict):values=[values[k] for k in KEYS]
    return np.asarray(values,dtype=float)

def main():
    p=argparse.ArgumentParser();p.add_argument('board');p.add_argument('pc');a=p.parse_args()
    board=json.load(open(a.board));pc=json.load(open(a.pc))
    for b,r in zip(board,pc):
        roi_errors=[float(np.max(np.abs(rect(x)-rect(y)))) for x,y in zip(b['input_rois'],r['palm_rois'])]
        detection_errors=[]
        for x,y in zip(b['palm_detections'],r['detections']):
            detection_errors.append(dict(score=abs(x['score']-y['score'][0]),
                box=float(np.max(np.abs(np.asarray(x['box'])-y['box']))),
                keypoints=float(np.max(np.abs(np.asarray(x['keypoints'])-y['keypoints'])))))
        print(json.dumps(dict(frame=b['frame_id'],board_hands=b['hands'],pc_hands=len(r['hands']),
            board_detections=b['detections'],pc_detections=len(r['detections']),
            roi_max=roi_errors,detection_errors=detection_errors,
            presence=b.get('presence_scores',b['presence']))))

if __name__=='__main__':main()
