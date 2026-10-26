"""Make local-only canonical hand ROI probes from existing, audited extraction results."""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[3]


def canonical_roi(bgr, normalized_hand, margin=1.6):
    hand = np.asarray(normalized_hand, dtype=np.float64)
    if hand.ndim!=2 or hand.shape[0]!=21 or hand.shape[1]<2:
        raise ValueError('Expected 21 normalized hand points')
    points = hand[:, :2]*[bgr.shape[1],bgr.shape[0]]
    if points.shape != (21,2) or not np.isfinite(points).all():
        raise ValueError('A complete finite 21-point hand is required')
    upward = points[9]-points[0]
    norm = np.linalg.norm(upward)
    if norm < 2:
        raise ValueError('Hand is too small or degenerate')
    y_axis = -upward/norm
    x_axis = np.array([y_axis[1],-y_axis[0]])
    basis = np.stack([x_axis,y_axis],axis=1)
    local = points@basis
    low, high = local.min(axis=0),local.max(axis=0)
    side = float((high-low).max()*margin)
    if side < 8:
        raise ValueError('Hand ROI is too small')
    center = basis@((low+high)/2)
    corners = np.array([center-side/2*x_axis-side/2*y_axis,
                        center+side/2*x_axis-side/2*y_axis,
                        center-side/2*x_axis+side/2*y_axis],np.float32)
    affine = cv2.getAffineTransform(corners,np.array([[0,0],[223,0],[0,223]],np.float32))
    crop = cv2.warpAffine(bgr,affine,(224,224),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
    return cv2.cvtColor(crop,cv2.COLOR_BGR2RGB).astype(np.float32)/255,cv2.invertAffineTransform(affine)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT) or output==ROOT or output.exists():
        raise ValueError('Use a new workspace output directory')
    audit = json.loads((ROOT/'vision/analysis/dataset/label_source_audit_20261025.json').read_text(encoding='utf-8'))
    by_hash = {r['sha256']:r for r in audit['records']}
    rois, inverses, records = [],[],[]
    for report in sorted((ROOT/'vision/data/cache/m1').glob('extract_part*/report.json')):
        for sample in json.loads(report.read_text(encoding='utf-8'))['samples']:
            source = by_hash[sample['source_sha256']]
            path = ROOT/source['path']
            if hashlib.sha256(path.read_bytes()).hexdigest()!=source['sha256']:
                raise ValueError('Source SHA mismatch')
            with np.load(report.parent/sample['npz']) as data:
                hands = data['hands']
                frames = data['frame_indices']
                candidates = np.argwhere(np.isfinite(hands).all(axis=(2,3)))
                capture = cv2.VideoCapture(str(path))
                try:
                    for frame_index, hand_index in candidates:
                        capture.set(cv2.CAP_PROP_POS_FRAMES,int(frames[frame_index]))
                        ok,bgr = capture.read()
                        if not ok:
                            continue
                        try:
                            roi,inverse = canonical_roi(bgr,hands[frame_index,hand_index])
                        except ValueError:
                            continue
                        rois.append(roi)
                        inverses.append(inverse)
                        records.append(dict(source=source['path'],sha256=source['sha256'],
                            source_group=source['provenance']['source_group'],
                            frame_index=int(frames[frame_index]),hand_index=int(hand_index)))
                        break  # at most one probe per clip; no repeated-frame inflation
                finally:
                    capture.release()
    if not rois:
        raise RuntimeError('No complete hand ROI found')
    # Existing source groups, never ROI-random split. This is numerical validation, not task accuracy.
    validation_groups = {'NL_lesson_08','NL_lesson_09','NL_lesson_10'}
    validation = [i for i,r in enumerate(records) if r['source_group'] in validation_groups]
    calibration = [i for i in range(len(records)) if i not in validation]
    if not validation or not calibration:
        raise RuntimeError('Need distinct calibration and validation source groups')
    output.mkdir(parents=True)
    np.savez_compressed(output/'rois.npz',roi_rgb=np.stack(rois),inverse_affine=np.stack(inverses),
                        calibration_indices=np.array(calibration),validation_indices=np.array(validation))
    report = dict(samples=len(records),calibration=len(calibration),validation=len(validation),
        validation_source_groups=sorted(validation_groups),records=records,
        limitations=['PC supplies landmark-guided rotated ROIs; this is not autonomous PL detection.',
                     'ROIs are numerical probes, not manually annotated hand-landmark ground truth.',
                     'Crop follows a documented canonical transform, not a bit-exact reconstruction of MediaPipe ROI calculators.'])
    (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='records'},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
