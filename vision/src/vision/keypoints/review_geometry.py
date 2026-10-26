"""Show only the active crop in source context; preserve the original frame and affine."""
import cv2
import numpy as np


def source_affine(record):
    # Historical exporter used OpenCV float64 hand affines and explicit float32 random-candidate affines.
    dtype=record.get('affine_dtype','float32' if record['kind']=='unknown_candidate' else 'float64')
    if dtype not in ('float32','float64'):raise ValueError('Unsupported ROI affine dtype')
    return np.asarray(record['affine_source_to_roi'],dtype=dtype)


def roi_polygon(affine):
    matrix=np.asarray(affine,np.float64)
    if matrix.shape!=(2,3) or not np.isfinite(matrix).all() or abs(np.linalg.det(matrix[:,:2]))<1e-12:
        raise ValueError('Finite invertible ROI affine required')
    inverse=cv2.invertAffineTransform(matrix)
    polygon=np.array([[0,0],[127,0],[127,127],[0,127]],np.float64)@inverse[:,:2].T+inverse[:,2]
    return polygon,inverse


def source_exterior_flags(normalized_xy,affine,source_size):
    _,inverse=roi_polygon(affine)
    xy=np.asarray(normalized_xy)*127
    source=xy@inverse[:,:2].T+inverse[:,2];w,h=source_size
    return ((source[:,0]<0)|(source[:,0]>w-1)|(source[:,1]<0)|(source[:,1]>h-1))


def review_context(frame,affine,initial_xy=None,width=960):
    polygon,inverse=roi_polygon(affine)
    image=frame.copy()
    cv2.polylines(image,[np.round(polygon).astype(np.int32)],True,(0,0,255),max(2,round(frame.shape[1]/480)))
    if initial_xy is not None:
        wrist=np.asarray(initial_xy[0],np.float64)*127
        xy=np.round(wrist@inverse[:,:2].T+inverse[:,2]).astype(int)
        cv2.circle(image,tuple(xy),max(4,round(frame.shape[1]/180)),(255,255,255),-1)
        cv2.circle(image,tuple(xy),max(2,round(frame.shape[1]/260)),(0,0,255),-1)
    scale=min(1,width/frame.shape[1])
    return cv2.resize(image,None,fx=scale,fy=scale)
