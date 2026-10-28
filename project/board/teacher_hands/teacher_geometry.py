"""MediaPipe Hands geometry, ported from the official calculator configurations/source."""
import math
import cv2
import numpy as np

EDGES = ((0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),(5,9),(9,10),
    (10,11),(11,12),(9,13),(13,14),(14,15),(15,16),(13,17),(17,18),(18,19),(19,20),(0,17))
PARTIAL = (0,1,2,3,5,6,9,10,13,14,17,18)


def normalize_radians(angle):
    return angle - 2 * math.pi * math.floor((angle + math.pi) / (2 * math.pi))


def anchors_192():
    # Official generator: two scales per layer (interpolated_scale_aspect_ratio=1),
    # and all equal strides share one feature map. 2*24^2 + 6*12^2 = 2016.
    anchors = []
    strides = (8,16,16,16)
    layer = 0
    while layer < len(strides):
        last = layer
        scales = []
        while last < len(strides) and strides[last] == strides[layer]:
            scale = 0.1484375 + (0.75 - 0.1484375) * last / 3
            next_scale = 1. if last == len(strides)-1 else 0.1484375 + (0.75 - 0.1484375) * (last+1) / 3
            scales.extend((scale,math.sqrt(scale*next_scale)))
            last += 1
        grid = math.ceil(192/strides[layer])
        for y in range(grid):
            for x in range(grid):
                for _ in scales:
                    anchors.append(((x+.5)/grid,(y+.5)/grid,1.,1.))
        layer = last
    result = np.asarray(anchors,np.float32)
    if result.shape != (2016,4):
        raise RuntimeError(f"Anchor contract mismatch: {result.shape}")
    return result

ANCHORS = anchors_192()


def letterbox_rgb(rgb, size=192):
    height, width = rgb.shape[:2]
    scale = min(size / width, size / height)
    dx = (size - width * scale) / 2
    dy = (size - height * scale) / 2
    matrix = np.asarray([[scale,0,dx],[0,scale,dy]], np.float32)
    tensor = cv2.warpAffine(rgb, matrix, (size,size), flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0))
    padding = np.asarray([dx/size,dy/size,dx/size,dy/size], np.float32)
    return np.asarray(tensor,np.float32)/255., padding


def _iou(a, b):
    ax0,ay0,ax1,ay1 = a
    bx0,by0,bx1,by1 = b
    intersection = max(0.,min(ax1,bx1)-max(ax0,bx0)) * max(0.,min(ay1,by1)-max(ay0,by0))
    return intersection / max(1e-9,(ax1-ax0)*(ay1-ay0)+(bx1-bx0)*(by1-by0)-intersection)


def weighted_nms(detections, threshold=.3):
    remaining = sorted(detections, key=lambda d:d["score"], reverse=True)
    output = []
    while remaining:
        best = remaining.pop(0)
        group = [best]
        kept = []
        for other in remaining:
            (group if _iou(best["box"],other["box"]) > threshold else kept).append(other)
        if len(group) > 1:
            total = sum(d["score"] for d in group)
            for key in ("box","keypoints"):
                best[key] = sum(d[key]*d["score"] for d in group) / total
            best["score"] = max(d["score"] for d in group)
        output.append(best)
        remaining = kept
    return output


def _palm_candidate_indices(scores, min_score):
    valid = scores > -100.
    if min_score == .5 and scores.dtype in (np.dtype('float32'), np.dtype('float64')):
        # sigmoid(-1) < 0.269, far below 0.5 even with floating-point rounding.
        # Keep the original scalar sigmoid for all survivors, especially tiny
        # negative logits that can round to a score of exactly 0.5. Filtering
        # at zero or vectorizing exp would change that boundary or its scores.
        valid &= scores >= -1.
    return np.flatnonzero(valid)


def decode_palms(outputs, padding, min_score=.5):
    arrays = [np.asarray(x).reshape(-1) for x in outputs]
    encoded = next(x for x in arrays if x.size == 2016*18).reshape(2016,18)
    scores = next(x for x in arrays if x.size == 2016)
    left,top,right,bottom = map(float,padding)
    candidates = []
    for index in _palm_candidate_indices(scores, min_score):
        score = float(1/(1+np.exp(-np.clip(scores[index],-100,100))))
        if score < min_score:
            continue
        raw = encoded[index]
        cx = raw[0]/192 + ANCHORS[index,0]
        cy = raw[1]/192 + ANCHORS[index,1]
        width = raw[2]/192 * ANCHORS[index,2]
        height = raw[3]/192 * ANCHORS[index,3]
        keypoints = raw[4:].reshape(7,2).copy()
        keypoints[:,0] = keypoints[:,0]/192 + ANCHORS[index,0]
        keypoints[:,1] = keypoints[:,1]/192 + ANCHORS[index,1]
        # Official removal: (coordinate-padding)/(1-sum_of_opposite_padding).
        cx = (cx-left)/(1-left-right); cy = (cy-top)/(1-top-bottom)
        width /= 1-left-right; height /= 1-top-bottom
        keypoints[:,0] = (keypoints[:,0]-left)/(1-left-right)
        keypoints[:,1] = (keypoints[:,1]-top)/(1-top-bottom)
        candidates.append(dict(score=score,
            box=np.asarray([cx-width/2,cy-height/2,cx+width/2,cy+height/2]),
            keypoints=keypoints))
    return weighted_nms(candidates)


def transform_rect(rect, image_shape, scale_x, scale_y, shift_y):
    height,width = image_shape[:2]
    cx,cy,w,h,rotation = rect
    x_shift = (width*w*0*math.cos(rotation)-height*h*shift_y*math.sin(rotation))/width
    y_shift = (width*w*0*math.sin(rotation)+height*h*shift_y*math.cos(rotation))/height
    cx += x_shift; cy += y_shift
    side = max(w*width,h*height)
    return np.asarray([cx,cy,side/width*scale_x,side/height*scale_y,rotation],np.float32)


def roi_from_palm(detection, image_shape):
    height,width = image_shape[:2]
    x0,y0,x1,y1 = detection["box"]
    kp = detection["keypoints"]
    rotation = normalize_radians(math.pi/2 - math.atan2(-(kp[2,1]-kp[0,1])*height,
        (kp[2,0]-kp[0,0])*width))
    raw = np.asarray([(x0+x1)/2,(y0+y1)/2,x1-x0,y1-y0,rotation],np.float32)
    return transform_rect(raw,image_shape,2.6,2.6,-.5)


def roi_matrix(roi, image_shape, size=224):
    height,width = image_shape[:2]
    cx,cy,w,h,angle = map(float,roi)
    cx *= width; cy *= height; w *= width; h *= height
    # This is the official crop->image transform used by LandmarkProjection.
    cosine,sine = math.cos(angle),math.sin(angle)
    matrix = np.asarray([[cosine*w/size,-sine*h/size,cx],
        [sine*w/size,cosine*h/size,cy]],np.float32)
    matrix[:,2] -= matrix[:,:2] @ np.asarray([size/2,size/2])
    return matrix


def run_landmark(model, rgb, roi):
    matrix = roi_matrix(roi,rgb.shape)
    crop = cv2.warpAffine(rgb,matrix,(224,224),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,
        borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0))
    outputs = model.invoke(np.asarray(crop,np.float32)/255.)
    landmarks = outputs[0].reshape(21,3).copy()
    # XY stay in 224-pixel units for roi_matrix; only Z uses normalized scaling.
    landmarks[:,2] *= .4/224.
    xy = np.c_[landmarks[:,:2],np.ones(21)]
    projected = xy @ matrix.T
    height,width = rgb.shape[:2]
    projected[:,0] /= width; projected[:,1] /= height
    landmarks[:,:2] = projected
    landmarks[:,2] *= float(roi[2])
    presence = float(outputs[1].reshape(-1)[0])
    handedness = float(outputs[2].reshape(-1)[0])
    world = outputs[3].reshape(21,3).copy() if len(outputs)>3 else None
    return dict(points=landmarks,presence=presence,right_score=handedness,
        world=world,roi=roi,accepted=presence>.5)


def roi_from_landmarks(points, image_shape):
    height,width = image_shape[:2]
    points = np.asarray(points)[list(PARTIAL)]
    wrist = points[0,:2]*[width,height]
    target = (points[[4,8],:2].mean(axis=0)+points[6,:2])/2*np.asarray([width,height])
    rotation = normalize_radians(math.pi/2-math.atan2(-(target[1]-wrist[1]),target[0]-wrist[0]))
    center = (points[:,:2].max(axis=0)+points[:,:2].min(axis=0))/2
    delta = (points[:,:2]-center)*[width,height]
    cosine,sine = math.cos(-rotation),math.sin(-rotation)
    rotated = delta @ np.asarray([[cosine,sine],[-sine,cosine]])
    low,high = rotated.min(axis=0),rotated.max(axis=0)
    projected_center = (low+high)/2
    center_px = projected_center @ np.asarray([[math.cos(rotation),math.sin(rotation)],
        [-math.sin(rotation),math.cos(rotation)]]) + center*[width,height]
    raw = np.asarray([center_px[0]/width,center_px[1]/height,
        (high[0]-low[0])/width,(high[1]-low[1])/height,rotation],np.float32)
    return transform_rect(raw,image_shape,2.,2.,-.1)


def associate(new_rois, previous, threshold=.5):
    if len(previous) != 2:
        return new_rois
    unused = set(range(len(new_rois)))
    result = []
    for old in previous:
        best,best_iou = None,0.
        for index in unused:
            a,b = old,new_rois[index]
            box_a = [a[0]-a[2]/2,a[1]-a[3]/2,a[0]+a[2]/2,a[1]+a[3]/2]
            box_b = [b[0]-b[2]/2,b[1]-b[3]/2,b[0]+b[2]/2,b[1]+b[3]/2]
            value = _iou(box_a,box_b)
            if value > best_iou:
                best,best_iou = index,value
        if best is not None and best_iou >= threshold:
            result.append(new_rois[best]);unused.remove(best)
        else:
            result.append(old)
    result.extend(new_rois[i] for i in sorted(unused))
    return result[:2]


def draw_hands(image, hands):
    for hand in hands:
        if not hand["accepted"]:
            continue
        points = np.asarray(hand["points"])[:,:2]*[image.shape[1],image.shape[0]]
        points = np.rint(points).astype(np.int32)
        for a,b in EDGES:
            cv2.line(image,tuple(points[a]),tuple(points[b]),(0,220,0),2,cv2.LINE_AA)
        for point in points:
            cv2.circle(image,tuple(point),3,(0,180,255),-1,cv2.LINE_AA)
    return image
