"""Current-frame hand ROIs with source-aligned finger connections. No cached pose or semantic model."""
import cv2
import numpy as np

FINGERS=[((0,130,255),(0,1,2,3,4),'THUMB'),((0,230,255),(5,6,7,8),'INDEX'),
    ((80,235,80),(9,10,11,12),'MIDDLE'),((230,210,0),(13,14,15,16),'RING'),
    ((220,90,255),(17,18,19,20),'LITTLE')]
MIN_ROI_IN_FRAME_POINTS=12  # display geometry gate, not a landmark confidence score


def hand_points(hand,width,height):
    if hand is None:return None
    points=np.array([[p.x*width,p.y*height] for p in hand.landmark],np.float64)
    return points if points.shape==(21,2) else None


def current_hand_roi(frame,points,size=400):
    if points is None:return None
    height,width=frame.shape[:2]
    inside=np.isfinite(points).all(1)&(points[:,0]>=0)&(points[:,0]<=width-1)&(points[:,1]>=0)&(points[:,1]<=height-1)
    if inside.sum()<MIN_ROI_IN_FRAME_POINTS:return None
    low=points[inside].min(0);high=points[inside].max(0);center=(low+high)/2
    side=min(max(float((high-low).max())*1.45,48.),width-1,height-1)
    if side<2:return None
    start=np.clip(center-side/2,[0,0],[width-1-side,height-1-side]);scale=(size-1)/side
    affine=np.array([[scale,0,-start[0]*scale],[0,scale,-start[1]*scale]],np.float64)
    crop=cv2.warpAffine(frame,affine,(size,size))
    mapped=points@affine[:,:2].T+affine[:,2]
    return dict(image=crop,points=mapped,inside=inside,affine=affine,
        bbox=[float(start[0]),float(start[1]),float(start[0]+side),float(start[1]+side)])


def finger_skeleton(image,points,inside,thickness=3,numbers=False):
    def line(a,b,color):
        if inside[a] and inside[b]:
            pa=tuple(np.rint(points[a]).astype(int));pb=tuple(np.rint(points[b]).astype(int))
            cv2.line(image,pa,pb,(12,15,18),thickness+2,cv2.LINE_AA)
            cv2.line(image,pa,pb,color,thickness,cv2.LINE_AA)
    for a,b in [(0,5),(5,9),(9,13),(13,17),(17,0)]:line(a,b,(230,235,235))
    for color,indices,_ in FINGERS:
        for a,b in zip(indices,indices[1:]):line(a,b,color)
        for j in indices:
            if not inside[j]:continue
            point=tuple(np.rint(points[j]).astype(int))
            cv2.circle(image,point,5 if numbers else 3,(15,18,20),-1,cv2.LINE_AA)
            cv2.circle(image,point,3 if numbers else 2,color,-1,cv2.LINE_AA)
            if numbers and j in (0,4,8,12,16,20):
                cv2.putText(image,str(j),(point[0]+6,point[1]-6),cv2.FONT_HERSHEY_SIMPLEX,.43,(255,255,255),2,cv2.LINE_AA)


def place_image(canvas,image,box):
    x,y,w,h=box;scale=min(w/image.shape[1],h/image.shape[0]);iw=max(1,round(image.shape[1]*scale));ih=max(1,round(image.shape[0]*scale))
    ox=x+(w-iw)//2;oy=y+(h-ih)//2
    canvas[oy:oy+ih,ox:ox+iw]=cv2.resize(image,(iw,ih))


def render_hand_dashboard(frame,result,frame_id,timestamp,processed_fps,inference_ms):
    canvas=np.full((720,1280,3),(25,21,17),np.uint8);scene=frame.copy();state={}
    def text(value,xy,color=(235,240,245),scale=.6):
        cv2.putText(canvas,value,xy,cv2.FONT_HERSHEY_SIMPLEX,scale,color,1,cv2.LINE_AA)
    text('PC MEDIAPIPE LIVE INFERENCE | VIDEO REPLAY AS CAMERA',(18,30),(70,230,245),.8)
    text(f'FRAME {frame_id} | SOURCE {timestamp:.2f}s | PC RESULTS {processed_fps:.1f} Hz | NN {inference_ms:.1f} ms',(18,65),scale=.65)
    text('FULL FRAME / CURRENT RESULT',(18,113))
    pose=getattr(result,'pose_landmarks',None)
    if pose is not None:
        points=np.array([[p.x*frame.shape[1],p.y*frame.shape[0]] for p in pose.landmark])
        for a,b in [(11,12),(11,13),(13,15),(12,14),(14,16)]:
            if len(points)>max(a,b) and np.isfinite(points[[a,b]]).all():
                cv2.line(scene,tuple(points[a].astype(int)),tuple(points[b].astype(int)),(200,190,170),2,cv2.LINE_AA)
    for name,hand,x,border in [('LEFT',getattr(result,'left_hand_landmarks',None),444,(70,225,70)),
            ('RIGHT',getattr(result,'right_hand_landmarks',None),860,(0,155,255))]:
        text(name+' HAND ROI / CURRENT FRAME',(x,113),border,.55)
        points=hand_points(hand,frame.shape[1],frame.shape[0]);roi=current_hand_roi(frame,points)
        cv2.rectangle(canvas,(x-2,142),(x+401,545),border,2)
        if roi is None:
            text('NO HAND' if hand is None else 'NO VALID ROI',(x+70,320),scale=.85)
            text('No old skeleton retained',(x+62,350),scale=.55)
            state[name.lower()]=dict(detected=False,bbox=None,in_frame_points=0,
                reason='no_hand' if hand is None else 'insufficient_in_frame_projection')
        else:
            finger_skeleton(roi['image'],roi['points'],roi['inside'],numbers=True)
            canvas[144:544,x:x+400]=roi['image']
            finger_skeleton(scene,points,roi['inside'],thickness=3)
            a,b,c,d=np.rint(roi['bbox']).astype(int)
            cv2.rectangle(scene,(a,b),(c,d),border,3,cv2.LINE_AA)
            text(str(int(roi['inside'].sum()))+'/21 projected points inside frame',(x,580),scale=.53)
            state[name.lower()]=dict(detected=True,bbox=roi['bbox'],in_frame_points=int(roi['inside'].sum()))
    place_image(canvas,scene,(16,134,410,520))
    for i,(color,_,name) in enumerate(FINGERS):
        x=444+i*162;cv2.line(canvas,(x,628),(x+25,628),color,4,cv2.LINE_AA);text(name,(x+31,634),scale=.47)
    text('Each frame is inferred on PC; PYNQ provides HDMI display.',(444,670),scale=.53)
    text('Model estimates | missing hands clear immediately | no semantic classification',(18,705),scale=.53)
    return canvas,state
