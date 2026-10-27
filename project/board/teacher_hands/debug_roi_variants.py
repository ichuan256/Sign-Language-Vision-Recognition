"""Diagnose ImageToTensor orientation using an official PC ROI on one identical frame."""
import json
import math
from pathlib import Path
import cv2
import numpy as np
from teacher_runtime import TFLiteModel

work=Path(__file__).resolve().parent
reference=json.loads((work/'pc_reference_hello_v2.json').read_text())[0]
r=reference['palm_rois'][0]
roi=np.asarray([r[k] for k in ('x_center','y_center','width','height','rotation')],np.float32)
cap=cv2.VideoCapture('/home/xilinx/video/clips/hello.mp4');ok,bgr=cap.read();cap.release()
rgb=cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB);height,width=rgb.shape[:2]
model=TFLiteModel(work/'libhands_tflite.so',work/'hand_landmark_full.tflite',2)
crops=[]
try:
    for sign in (1.,-1.):
        cx,cy,w,h,angle=map(float,roi);angle*=sign
        cx*=width;cy*=height;w*=width;h*=height
        co,si=math.cos(angle),math.sin(angle)
        matrix=np.asarray([[co*w/224,-si*h/224,cx],[si*w/224,co*h/224,cy]],np.float32)
        matrix[:,2]-=matrix[:,:2]@np.asarray([112.,112.])
        for inverse in (False,True):
            flags=cv2.INTER_LINEAR|(cv2.WARP_INVERSE_MAP if inverse else 0)
            crop=cv2.warpAffine(rgb,matrix,(224,224),flags=flags,borderMode=cv2.BORDER_CONSTANT)
            outputs=model.invoke(np.asarray(crop,np.float32)/255.)
            print('VARIANT',sign,inverse,'presence',float(outputs[1].reshape(-1)[0]),flush=True)
            crops.append(crop)
finally:model.close()
cv2.imwrite(str(work/'roi_variants.jpg'),cv2.cvtColor(np.hstack(crops),cv2.COLOR_RGB2BGR))
