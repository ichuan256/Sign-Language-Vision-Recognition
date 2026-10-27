"""ROI geometry, current-frame expiry and finger connections on the HDMI dashboard."""
from types import SimpleNamespace
import cv2
import numpy as np
from vision.keypoints.hand_dashboard import current_hand_roi,finger_skeleton,render_hand_dashboard


def hand():
    xy=np.array([[.45,.65],[.40,.59],[.36,.52],[.33,.46],[.30,.41],
        [.43,.48],[.42,.37],[.42,.29],[.42,.21],[.49,.47],[.50,.35],[.51,.25],[.52,.16],
        [.55,.49],[.58,.38],[.59,.29],[.60,.22],[.60,.54],[.65,.46],[.68,.40],[.70,.34]])
    return xy,SimpleNamespace(landmark=[SimpleNamespace(x=x,y=y) for x,y in xy])


def test_roi_mapping_matches_current_source_pixels_without_distortion():
    frame=np.full((240,320,3),160,np.uint8);xy,_=hand();points=xy*[320,240]
    roi=current_hand_roi(frame,points)
    assert roi['image'].shape==(400,400,3) and roi['inside'].all()
    assert np.allclose(roi['points'],points@roi['affine'][:,:2].T+roi['affine'][:,2])
    x0,y0,x1,y1=roi['bbox'];assert abs(x1-x0-(y1-y0))<1e-6
    assert x0>=0 and y0>=0 and x1<=319 and y1<=239


def test_missing_hand_clears_dashboard_instead_of_reusing_previous_pose():
    frame=np.full((240,320,3),160,np.uint8);_,landmarks=hand();original=frame.copy()
    present=SimpleNamespace(left_hand_landmarks=landmarks,right_hand_landmarks=None,pose_landmarks=None)
    missing=SimpleNamespace(left_hand_landmarks=None,right_hand_landmarks=None,pose_landmarks=None)
    shown,state=render_hand_dashboard(frame,present,1,0,20,30)
    cleared,next_state=render_hand_dashboard(frame,missing,2,.05,20,30)
    assert state['left']['detected'] and not next_state['left']['detected']
    assert next_state['left']['bbox'] is None and not next_state['right']['detected']
    assert not np.array_equal(shown[144:544,444:844],cleared[144:544,444:844])
    assert np.array_equal(frame,original)


def test_finger_connections_are_drawn_and_invalid_projections_are_excluded():
    frame=np.full((240,320,3),160,np.uint8);xy,_=hand();points=xy*[320,240]
    points[20]=[float('nan'),0];points[19]=[500,100]
    roi=current_hand_roi(frame,points);before=roi['image'].copy()
    assert roi['inside'].sum()==19
    finger_skeleton(roi['image'],roi['points'],roi['inside'],numbers=True)
    center=np.rint((roi['points'][5]+roi['points'][6])/2).astype(int)
    assert not np.array_equal(roi['image'][center[1],center[0]],before[center[1],center[0]])
    assert current_hand_roi(frame,np.full((21,2),np.nan)) is None


def test_mostly_outside_hand_does_not_make_an_enlarged_false_complete_roi():
    points=np.full((21,2),[500,500],np.float64);points[:5]=[[50+i,50+i] for i in range(5)]
    assert current_hand_roi(np.zeros((240,320,3),np.uint8),points) is None
