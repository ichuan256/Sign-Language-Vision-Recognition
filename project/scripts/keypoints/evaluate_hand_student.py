"""Evaluate an explicit float model against teacher and optional manual labels; write visual checks."""
import argparse
import json
import os
from pathlib import Path
import sys
os.environ.setdefault('TF_USE_LEGACY_KERAS','1');os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL','2')
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
import cv2
import numpy as np
from vision.keypoints.student_data import load_dataset,augment,digest
from project.scripts.keypoints.train_hand_student import evaluate,predict


def main():
    import tf_keras as keras
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model',type=Path,required=True);p.add_argument('--data',type=Path,required=True)
    p.add_argument('--reviews',type=Path);p.add_argument('--split',choices=('train','validation','test'),default='test')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if out.exists() or not out.is_relative_to(ROOT/'project/_tmp'):raise ValueError('New project/_tmp evaluation output required')
    images,y,m,records,report=load_dataset(a.data,a.reviews);indices=[i for i,r in enumerate(records) if r['split']==a.split and m[i,:63].any()]
    if not indices:raise ValueError('No coordinate-labelled ROIs in split')
    model=keras.models.load_model(a.model,compile=False);size=model.input_shape[1]
    x=np.stack([augment(images[i],y[i],m[i],size)[0] for i in indices]);labels=y[indices];mask=m[indices]
    prediction=predict(model,x,16);rr=[records[i] for i in indices]
    result=evaluate(prediction,labels,mask,rr)
    result.update(model_sha256=digest(a.model),dataset_sha256=digest(a.data/'dataset.json'),
        reviews_sha256=digest(a.reviews) if a.reviews else None,split=a.split,quantized=False,board_measured=False)
    out.mkdir(parents=True);(out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    np.savez_compressed(out/'predictions.npz',predictions=prediction,targets=labels,masks=mask,sample_ids=np.array([r['sample_id'] for r in rr]))
    cards=[]
    for j in np.linspace(0,len(indices)-1,min(24,len(indices)),dtype=int):
        canvas=cv2.cvtColor((x[j]*255).astype(np.uint8),cv2.COLOR_RGB2BGR);canvas=cv2.resize(canvas,(256,256))
        for values,color in [(labels[j],(0,220,0)),(prediction[j],(0,80,255))]:
            points=values[:63].reshape(21,3)[:,:2]*255
            for k,point in enumerate(points):
                if mask[j,k*3] and np.isfinite(point).all():cv2.circle(canvas,tuple(np.clip(point,-1000,1000).astype(int)),2,color,-1)
        card=np.zeros((290,256,3),np.uint8);card[:256]=canvas
        cv2.putText(card,'green=label red=student',(5,271),cv2.FONT_HERSHEY_SIMPLEX,.44,(255,255,255),1)
        cv2.putText(card,rr[j]['sample_id'][:16],(5,287),cv2.FONT_HERSHEY_SIMPLEX,.4,(200,200,200),1);cards.append(card)
    while len(cards)%4:cards.append(np.zeros_like(cards[0]))
    sheet=np.vstack([np.hstack(cards[i:i+4]) for i in range(0,len(cards),4)])
    cv2.imwrite(str(out/'teacher_vs_student.jpg'),sheet)
    print(json.dumps({k:result[k] for k in ('teacher_agreement','human_accuracy','macro_source_group_NME')},indent=2))


if __name__=='__main__':main()
