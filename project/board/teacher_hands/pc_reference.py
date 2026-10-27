"""Export PC MediaPipe graph detections and ROIs for geometric parity checks."""
import argparse
import json
from pathlib import Path
import cv2
from mediapipe.python.solution_base import SolutionBase


def rect_list(rects):
    return [dict(x_center=r.x_center,y_center=r.y_center,width=r.width,height=r.height,rotation=r.rotation)
            for r in (rects or [])]


def main():
    p=argparse.ArgumentParser();p.add_argument('--video',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--frames',type=int,default=5);a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    graph='mediapipe/modules/hand_landmark/hand_landmark_tracking_cpu.binarypb'
    side=dict(model_complexity=1,num_hands=2,use_prev_landmarks=True)
    outputs=['multi_hand_landmarks','palm_detections','hand_rects_from_palm_detections','hand_rects_from_landmarks']
    cap=cv2.VideoCapture(str(a.video));records=[]
    with SolutionBase(binary_graph_path=graph,side_inputs=side,outputs=outputs) as hands:
        for frame_id in range(a.frames):
            ok,bgr=cap.read()
            if not ok:break
            result=hands.process(cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB))
            detections=[]
            for d in result.palm_detections or []:
                box=d.location_data.relative_bounding_box
                detections.append(dict(score=list(d.score),
                    box=[box.xmin,box.ymin,box.xmin+box.width,box.ymin+box.height],
                    keypoints=[[k.x,k.y] for k in d.location_data.relative_keypoints]))
            records.append(dict(frame_id=frame_id,detections=detections,
                palm_rois=rect_list(result.hand_rects_from_palm_detections),
                tracked_rois=rect_list(result.hand_rects_from_landmarks),
                hands=[[[p.x,p.y,p.z] for p in hand.landmark] for hand in result.multi_hand_landmarks or []]))
    cap.release();a.output.write_text(json.dumps(records,indent=2)+'\n')
    print(json.dumps([dict(frame_id=r['frame_id'],detections=len(r['detections']),hands=len(r['hands'])) for r in records]))

if __name__=='__main__':main()
